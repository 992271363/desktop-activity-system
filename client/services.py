# services.py (完整、最终、QTimer版)

import os
import psutil
import datetime
import win32gui
import win32process
from PySide6.QtCore import QObject, Signal, QTimer

def get_process_list():
    """
    获取当前系统中可用的进程列表。
    """
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
            # 过滤掉没有可执行文件路径、不包含路径分隔符或系统核心进程
            if not proc_info['exe'] or path_separator not in proc_info['exe'] or proc_info['pid'] in [0, 4]:
                continue
            process_data.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_data

def kill_for_pid(pid: int):
    """
    根据 PID 终止进程（如果权限允许）。
    """
    if psutil.pid_exists(pid):
        try:
            proc = psutil.Process(pid)
            username = proc.username()
            print(f"尝试终止进程 '{proc.name()}' (PID: {pid})，由 '{username}' 执行")
            
            is_system_process = False
            if os.name == 'nt':
                if username.upper().startswith(('NT AUTHORITY\\', 'LOCAL SERVICE', 'NETWORK SERVICE')):
                    is_system_process = True
            elif username == 'root':
                is_system_process = True

            if is_system_process:
                print(f"警告：不允许终止系统进程 '{proc.name()}'。")
                return

            print(f"正在终止进程 '{proc.name()}'...")
            proc.kill()
        except psutil.NoSuchProcess:
            print(f"终止失败：进程 {pid} 已不存在。")
        except psutil.AccessDenied:
            print(f"终止失败：权限不足，无法终止进程 {pid}。")

class ProcessMonitorWorker(QObject):
    process_terminated = Signal(int, datetime.datetime)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, pid_to_watch):
        super().__init__()
        self._pid = pid_to_watch
        self._timer = None

    def start_monitoring(self):
        if not psutil.pid_exists(self._pid):
            self.error_occurred.emit(f"进程 {self._pid} 在监视开始前就不存在。")
            self.finished.emit()
            return

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_pid_status)
        self._timer.start(1000)
        print(f"[Process Monitor] QTimer 已启动，监控 PID: {self._pid}")

    def _check_pid_status(self):
        if not psutil.pid_exists(self._pid):
            print(f"[Process Monitor] 检测到 PID {self._pid} 已终止。")
            self.process_terminated.emit(self._pid, datetime.datetime.now())
            self.stop()

    def stop(self):
        if self._timer and self._timer.isActive():
            self._timer.stop()
            print(f"[Process Monitor] PID {self._pid} 的监控定时器已停止。")
        self.finished.emit()


class FocusTimeWorker(QObject):
    finished = Signal()
    time_updated = Signal(int)

    def __init__(self, pid: int):
        super().__init__()
        self._pid = pid
        self._timer = None
        self.focus_details = {}
        self.total_focus_seconds = 0

    def start_focus_check(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_focus)
        self._timer.start(1000)
        print(f"[Focus Worker] QTimer 已启动，为 PID {self._pid} 检查焦点...")

    def _check_focus(self):
        try:
            if not psutil.pid_exists(self._pid):
                print(f"[Focus Worker] 监视的 PID {self._pid} 已消失，停止计时。")
                self.stop()
                return

            fg_window = win32gui.GetForegroundWindow()
            _, fg_pid = win32process.GetWindowThreadProcessId(fg_window)

            if fg_pid == self._pid:
                window_title = win32gui.GetWindowText(fg_window) or "[无标题]"
                self.focus_details[window_title] = self.focus_details.get(window_title, 0) + 1
                self.total_focus_seconds += 1
                self.time_updated.emit(self.total_focus_seconds)
        except Exception as e:
            print(f"[Focus Worker] 检查焦点时出错: {e}")
            self.stop()

    def stop(self):
        if self._timer and self._timer.isActive():
            self._timer.stop()
            print(f"[Focus Worker] PID {self._pid} 的焦点计时器已停止。")
        self.finished.emit()

    def get_focus_details(self) -> dict:
        return self.focus_details
