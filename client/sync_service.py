from PySide6.QtCore import QObject, Signal, QTimer
from sqlalchemy.orm import joinedload, Session
from local_database import SessionLocal
from local_models import ProcessSession, FocusActivity
from client_api import send_data_to_api

def get_and_prepare_sync_data():
    db = SessionLocal()
    try:
        activities_to_sync = db.query(FocusActivity).options(
            joinedload(FocusActivity.session)
        ).filter(FocusActivity.synced == False).all()
        if not activities_to_sync:
            return [], []
        sessions_map = {}
        for activity in activities_to_sync:
            session_id = activity.session_id
            if session_id not in sessions_map:
                sessions_map[session_id] = {
                    "process_name": activity.session.process_name,
                    "session_start_time": activity.session.session_start_time.isoformat(),
                    "session_end_time": activity.session.session_end_time.isoformat(),
                    "total_lifetime_seconds": activity.session.total_focus_seconds,
                    "activities": []
                }
            
            sessions_map[session_id]["activities"].append({
                "window_title": activity.window_title,
                "focus_duration_seconds": activity.focus_duration_seconds
            })
            
        data_to_send = list(sessions_map.values())
        
        print(f"[Sync Util] 发现 {len(data_to_send)} 个会话包含未同步数据，准备上传...")
        return data_to_send, activities_to_sync
    finally:
        db.close()

def mark_activities_as_synced(activities: list[FocusActivity]):
    if not activities:
        return
    db = SessionLocal()
    try:
        activity_ids = [activity.id for activity in activities]
        db.query(FocusActivity).filter(FocusActivity.id.in_(activity_ids)).update({"synced": True})
        db.commit()
        print(f"[Sync Util] 已将 {len(activity_ids)} 条焦点活动记录标记为已同步。")
    except Exception as e:
        print(f"[Sync Util] 标记同步状态时出错: {e}")
        db.rollback()
    finally:
        db.close()

class ApiSyncWorker(QObject):
    finished = Signal()
    status_updated = Signal(str)

    def __init__(self, parent_window, interval_seconds=60):
        super().__init__()
        self.main_window = parent_window
        self.interval = interval_seconds * 1000
        self._timer = None

    def start_service(self):  # <--- 请确保你的文件里有这个方法！
        """这是新的启动方法，将在后台线程中被调用。"""
        print(f"[Sync Service] QTimer 服务已在后台线程启动，每 {self.interval // 1000} 秒检查一次。")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.perform_sync_check)
        self._timer.start(self.interval)
        self.perform_sync_check()

    def perform_sync_check(self):
        print("\n--- [Sync Service] QTimer 触发新一轮后台同步检查 ---")
        token = self.main_window.token
        if not token:
            self.status_updated.emit("未登录，跳过后台同步。")
            return

        data_to_send, activities_to_mark = get_and_prepare_sync_data()
        if not data_to_send:
            self.status_updated.emit("后台检查：数据已是最新。")
        else:
            self.status_updated.emit(f"后台发现 {len(data_to_send)} 个新会话，上传中...")
            success = send_data_to_api(data_to_send, endpoint="/sync/sessions/", token=token)
            if success:
                mark_activities_as_synced(activities_to_mark)
                self.status_updated.emit(f"后台成功同步 {len(data_to_send)} 个会话。")
            else:
                self.status_updated.emit("后台同步失败，将在下一周期重试。")
    
    def stop(self):
        print("[Sync Service] 收到停止信号...")
        if self._timer and self._timer.isActive():
            self._timer.stop()
            print("[Sync Service] QTimer 已停止。")
        self.finished.emit()

