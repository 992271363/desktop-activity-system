import os
import time
import psutil
import datetime
from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session
from local_models import ActivityLog
from client_api import send_data_to_api 
from local_database import SessionLocal
def get_process_list():
    attrs = ['pid', 'name', 'exe']
    process_data = []
    path_separator = os.sep
    for proc in psutil.process_iter(attrs=attrs):
        try:
            proc_info = {
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'exe': proc.info['exe'] or 'N/A'
            }
            if not proc_info['exe']:
                continue
            if path_separator not in proc_info['exe']:
                continue
            if proc_info['pid'] in [0, 4]:
                continue
            process_data.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_data

class ProcessMonitorWorker(QObject):
    process_terminated = Signal(int, datetime.datetime) 
    error_occurred = Signal(str)
    finished = Signal()
    def __init__(self, pid_to_watch):
        super().__init__()
        self._pid = pid_to_watch
        self._is_running = True
    def run_check(self):
        try:
            if not psutil.pid_exists(self._pid):
                self.error_occurred.emit(f"进程 {self._pid} 在监视开始前就不存在。")
                self.finished.emit()
                return
            proc = psutil.Process(self._pid)
            while self._is_running:
                if not proc.is_running():
                    break
                time.sleep(1)
            
            if self._is_running:
                self.process_terminated.emit(self._pid, datetime.datetime.now())
        except psutil.NoSuchProcess:
             if self._is_running:
                 self.process_terminated.emit(self._pid, datetime.datetime.now())
        except Exception as e:
            self.error_occurred.emit(f"监视 PID {self._pid} 时发生意外错误: {e}")
        finally:
            self.finished.emit()
    def stop(self):
        self._is_running = False

def kill_for_pid(self, pid):
    if psutil.pid_exists(self._pid):
        try:
            proc = psutil.Process(self._pid)
            username = proc.username()
            print(f"终止进程'{proc.name()}' (PID: {self._pid}) 由'{username}'执行")
            is_system_process = False
            if os.name == 'nt':
                if username.upper().startswith('NT AUTHORITY\\') or username.upper() == 'LOCAL SERVICE' or username.upper() == 'NETWORK SERVICE':
                    is_system_process = True
            else:
                if username == 'root':
                    is_system_process = True
            if is_system_process:
                print(f"删除系统进程'{proc.name()}'不应该由'{username}'执行。")
                return
            print(f"进程'{proc.name()}'正在终止")
            proc.kill()
            
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            print(f"权限不足，无法终止进程 {self._pid}")

def log_activity(db: Session, proc_name: str, start: datetime.datetime, end: datetime.datetime):
    """
    计算活动时长，并创建一个 ActivityLog 对象存入数据库。
    """
    if not proc_name or not start or not end:
        print("[DB Service] 错误：缺少必要参数，无法记录活动。")
        return None
    duration = end - start
    duration_in_seconds = int(duration.total_seconds())
    # 忽略过短的活动记录
    if duration_in_seconds <= 1:
        print(f"[DB Service] 活动时长过短 ({duration_in_seconds}s)，已忽略。")
        return None
    db_log = ActivityLog(
        process_name=proc_name,
        start_time=start,
        end_time=end,
        duration_seconds=duration_in_seconds
    )
    
    try:
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        print(f"[DB Service] 成功记录活动: {db_log}")
        return db_log
    except Exception as e:
        print(f"[DB Service] 数据库写入失败: {e}")
        db.rollback()
        return None
    
class ApiSyncWorker(QObject):
    """
    一个专门负责将本地数据同步到远程API的工人。
    """
    status_updated = Signal(str)
    finished = Signal()
    def __init__(self, interval_seconds=60):
        super().__init__()
        self._is_running = True
        self.interval = interval_seconds
    def run_sync(self):
        """
        线程启动后循环执行这个同步任务。
        """
        self.status_updated.emit("云同步服务已启动...")
        while self._is_running:
            try:
                self.status_updated.emit("开始检查本地数据...")
                db = SessionLocal()
                
                # 1. 查询所有未同步的记录
                unsynced_logs = db.query(ActivityLog).filter(ActivityLog.synced == False).all()
                if not unsynced_logs:
                    self.status_updated.emit(f"本地没有需要同步的数据，将在 {self.interval} 秒后再次检查。")
                else:
                    self.status_updated.emit(f"发现 {len(unsynced_logs)} 条未同步记录，准备发送...")
                    
                    # 2. 将 SQLAlchemy 对象转换为 API 需要的字典列表
                    data_to_send = [
                        {
                            "process_name": log.process_name,
                            "window_title": log.window_title, # 即使是None也要发送
                            "start_time": log.start_time.isoformat(),
                            "end_time": log.end_time.isoformat(),
                            "duration_seconds": log.duration_seconds,
                            "user_id": 0 # 暂时硬编码为0，未来可以关联真实用户
                        } for log in unsynced_logs
                    ]
                    
                    # 3. 调用API 发送数据
                    success = send_data_to_api(data_to_send)
                    if success:
                        # 4. 如果发送成功，更新本地记录的状态
                        self.status_updated.emit("数据同步成功！正在更新本地状态...")
                        for log in unsynced_logs:
                            log.synced = True
                        db.commit()
                        self.status_updated.emit(f"本地状态更新完毕，将在 {self.interval} 秒后再次检查。")
                    else:
                        # 发送失败，什么都不做，下次循环会再次尝试
                        self.status_updated.emit(f"数据同步失败，将在 {self.interval} 秒后重试。")
                db.close()
                
                # 5. 等待指定时间
                for i in range(self.interval):
                    if not self._is_running:
                        break
                    time.sleep(1)
            except Exception as e:
                self.status_updated.emit(f"云同步服务发生严重错误: {e}")
                time.sleep(self.interval) # 出错后也等待，避免CPU飙升
        
        self.status_updated.emit("云同步服务已停止。")
        self.finished.emit()
    def stop(self):
        self._is_running = False