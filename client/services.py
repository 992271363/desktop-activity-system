import os
import time
import psutil
import datetime
import win32gui
import win32process
from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session
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

# 进程焦点时间监控
class FocusTimeWorker(QObject):
    finished = Signal()
    # 这个信号仍然发送总时长，专门用于更新UI显示
    time_updated = Signal(int)
    def __init__(self, pid: int):
        super().__init__()
        self._pid = pid
        self._is_running = True
        self.focus_details = {}  # <-- 核心变化：用字典记录详细焦点信息
        self.total_focus_seconds = 0 # <-- 仍然保留总秒数，方便发信号
    def run_focus_check(self):
        print(f"[Focus Worker] 开始为 PID {self._pid} 检查窗口焦点...")
        while self._is_running:
            try:
                # 获取当前前台窗口的句柄和PID
                fg_window = win32gui.GetForegroundWindow()
                _, fg_pid = win32process.GetWindowThreadProcessId(fg_window)
                # 检查前台窗口的PID是否是我们正在监视的PID
                if fg_pid == self._pid:
                    window_title = win32gui.GetWindowText(fg_window)
                    if not window_title:
                        window_title = "[无标题]"
                    
                    # 更新字典
                    self.focus_details[window_title] = self.focus_details.get(window_title, 0) + 1
                    
                    # 更新总时长并发送信号
                    self.total_focus_seconds += 1
                    self.time_updated.emit(self.total_focus_seconds)
                time.sleep(1) # 每秒检查一次
            except Exception as e:
                # 如果进程已不存在，优雅地退出循环
                if not psutil.pid_exists(self._pid):
                    print(f"[Focus Worker] 监视的 PID {self._pid} 已消失，线程退出。")
                    break
                print(f"[Focus Worker] 检查焦点时出错: {e}")
        
        print(f"[Focus Worker] 焦点计时结束。最终焦点详情: {self.focus_details}")
        self.finished.emit()
    def stop(self):
        self._is_running = False
    def get_focus_details(self) -> dict: 
        """获取详细的焦点时间和标题的字典"""
        return self.focus_details