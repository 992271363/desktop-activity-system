import os
import psutil
import datetime
import time
import win32gui
import win32process
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker
from typing import List, Dict, TypedDict

# --- 基础类型 ---
class ProcessInfo(TypedDict):
    pid: int
    name: str
    exe: str

# --- 获取进程列表 (保留原逻辑) ---
def get_process_list() -> List[ProcessInfo]:
    attrs = ['pid', 'name', 'exe']
    process_data: List[ProcessInfo] = []
    path_separator = os.sep
    for proc in psutil.process_iter(attrs=attrs):
        try:
            proc_info = {
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'exe': proc.info['exe'] or 'N/A'
            }
            if not proc_info['exe'] or path_separator not in proc_info['exe'] or proc_info['pid'] in [0, 4]:
                continue
            process_data.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_data

# --- 全局监控 Worker ---
class ActiveSession:
    def __init__(self, pid, exe_name, start_time):
        self.pid = pid
        self.exe_name = exe_name
        self.start_time = start_time
        self.focus_seconds = 0
        self.focus_details = {}
        self.is_focused = False

class GlobalMonitorWorker(QObject):
    status_updated = Signal(dict)
    session_finished = Signal(str, int)
    finished = Signal()

    def __init__(self, watched_apps_list: List[str]):
        super().__init__()
        self._target_apps = set(app.lower() for app in watched_apps_list)
        self._running = True
        self._mutex = QMutex()
        self._active_sessions: Dict[int, ActiveSession] = {}

    def update_watch_list(self, new_list: List[str]):
        with QMutexLocker(self._mutex):
            self._target_apps = set(app.lower() for app in new_list)

    def stop(self):
        self._running = False

    def run(self):
        print("[Global Monitor] 服务启动...")
        while self._running:
            try:
                self._check_processes_lifecycle_nonblocking()
                self._check_focus_nonblocking()
                self._emit_status()

                # 灵敏等待，每 0.1 秒检查一次是否停止，总共 1 秒
                for _ in range(10):
                    if not self._running:
                        break
                    time.sleep(0.1)

            except Exception as e:
                print(f"[Global Monitor] 异常: {e}")
                time.sleep(0.1)

        self._force_close_all()
        self.finished.emit()

    def _check_processes_lifecycle_nonblocking(self):
        current_pids = set()
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            if not self._running:
                break
            try:
                if not proc.info['exe']:
                    continue
                p_name = proc.info['name']
                p_lower = p_name.lower()
                p_pid = proc.info['pid']
                if p_lower in self._target_apps:
                    current_pids.add(p_pid)
                    if p_pid not in self._active_sessions:
                        self._active_sessions[p_pid] = ActiveSession(p_pid, p_name, datetime.datetime.now())
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        active_pids = list(self._active_sessions.keys())
        for pid in active_pids:
            if pid not in current_pids:
                self._save_session(self._active_sessions[pid])
                del self._active_sessions[pid]

    def _check_focus_nonblocking(self):
        if not self._running:
            return
        try:
            fg_window = win32gui.GetForegroundWindow()
            if not fg_window: return
            _, fg_pid = win32process.GetWindowThreadProcessId(fg_window)
            if fg_pid in self._active_sessions:
                session = self._active_sessions[fg_pid]
                session.is_focused = True
                session.focus_seconds += 1
                window_title = win32gui.GetWindowText(fg_window) or "未知窗口"
                session.focus_details[window_title] = session.focus_details.get(window_title, 0) + 1
        except Exception:
            pass

    def _save_session(self, session: ActiveSession):
        from local_database import SessionLocal
        from tracking_service import record_process_session
        end_time = datetime.datetime.now()
        if (end_time - session.start_time).total_seconds() < 2: return
        db = SessionLocal()
        try:
            record_process_session(db=db,
                                   executable_name=session.exe_name,
                                   start_time=session.start_time,
                                   end_time=end_time,
                                   focus_details=session.focus_details)
            self.session_finished.emit(session.exe_name, int((end_time - session.start_time).total_seconds()))
        except Exception as e:
            print(f"[DB Save Error] {e}")
        finally:
            db.close()

    def _force_close_all(self):
        for pid, session in self._active_sessions.items():
            self._save_session(session)
        self._active_sessions.clear()

    def _emit_status(self):
        status_data = {}
        now = datetime.datetime.now()
        for pid, session in self._active_sessions.items():
            name = session.exe_name
            runtime_seconds = int((now - session.start_time).total_seconds())
            status_data[name] = {
                "pid": pid,
                "focus": session.focus_seconds,
                "runtime_seconds": runtime_seconds,
                "start_str": session.start_time.strftime("%H:%M:%S"),
                "is_focused": session.is_focused
            }
        self.status_updated.emit(status_data)