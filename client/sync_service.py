# sync_service.py
import time
from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import selectinload

from local_database import SessionLocal
from local_models import ProcessSession, FocusActivity
from client_api import send_data_to_api

def get_and_prepare_sync_data():
    """
    查询本地未同步的会话数据，并打包成后端 API 需要的格式。
    返回打包好的数据列表，以及需要更新状态的 Activity 对象列表。
    """
    db = SessionLocal()
    try:
        # 高效查询：找到所有包含未同步活动(synced=False)的会话(ProcessSession)
        sessions_to_sync = db.query(ProcessSession).filter(
            ProcessSession.activities.any(FocusActivity.synced == False)
        ).options(
            # 使用 selectinload 一次性加载所有关联的 activities，避免 N+1 查询
            selectinload(ProcessSession.activities)
        ).all()
        
        if not sessions_to_sync:
            return [], [] # 没有数据需要同步

        payload = []
        activities_to_update = []

        # 遍历这些会话，打包成 JSON 字典
        for session in sessions_to_sync:
            session_activities = []
            for activity in session.activities:
                # 把所有活动都打包进去，后端可以根据需要进行覆盖或忽略
                session_activities.append({
                    "window_title": activity.window_title,
                    "focus_duration_seconds": activity.focus_duration_seconds
                })
                # 只记录下那些真正需要更新状态的活动
                if not activity.synced:
                    activities_to_update.append(activity)
            
            # 创建符合后端接口要求的会话数据包
            session_payload = {
                "process_name": session.process_name,
                "session_start_time": session.session_start_time.isoformat(),
                "session_end_time": session.session_end_time.isoformat(),
                "total_lifetime_seconds": session.total_lifetime_seconds,
                "activities": session_activities
            }
            payload.append(session_payload)

        print(f"[Sync Service] 数据准备: 已打包 {len(payload)} 个会话，涉及 {len(activities_to_update)} 条新活动。")
        return payload, activities_to_update

    finally:
        db.close()

def mark_activities_as_synced(activities: list):
    """在成功发送 API 后，将 activity 标记为已同步。"""
    if not activities:
        return

    db = SessionLocal()
    try:
        activity_ids = [act.id for act in activities]
        # 一次性更新所有匹配的 activity 的 synced 字段为 True
        db.query(FocusActivity).filter(
            FocusActivity.id.in_(activity_ids)
        ).update({"synced": True}, synchronize_session=False)
        db.commit()
        print(f"[Sync Service] 数据标记: 已成功将 {len(activity_ids)} 条活动标记为已同步。")
    except Exception as e:
        db.rollback()
        print(f"[Sync Service] 数据标记: 标记同步状态失败！错误: {e}")
    finally:
        db.close()


class ApiSyncWorker(QObject):
    finished = Signal()
    status_updated = Signal(str) # 用于向主窗口状态栏发送消息

    def __init__(self, interval_seconds=60):
        super().__init__()
        self._is_running = True
        self.interval = interval_seconds

    def run_sync(self):
        print(f"[Sync Service] 同步服务已启动，每 {self.interval} 秒检查一次。")
        while self._is_running:
            print("\n--- [Sync Service] 开始新一轮同步检查 ---")
            
            # 1. 从本地数据库准备数据
            data_to_send, activities_to_mark = get_and_prepare_sync_data()

            if not data_to_send:
                self.status_updated.emit("没有需要同步的新数据。")
            else:
                self.status_updated.emit(f"发现 {len(data_to_send)} 个新会话，准备上传...")
                
                # 2. 发送数据到新的 API 端点
                # 注意！endpoint 改为了 /sync/sessions/
                success = send_data_to_api(data_to_send, endpoint="/sync/sessions/")

                # 3. 如果发送成功，则更新本地状态
                if success:
                    mark_activities_as_synced(activities_to_mark)
                    self.status_updated.emit(f"成功同步 {len(data_to_send)} 个会话到云端。")
                else:
                    self.status_updated.emit("同步失败，请检查网络或服务器状态。")
            
            # 等待下一个周期
            for _ in range(self.interval):
                if not self._is_running:
                    break
                time.sleep(1)
        
        self.finished.emit()

    def stop(self):
        self._is_running = False
