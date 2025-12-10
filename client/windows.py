import psutil
import datetime
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog, QTableWidgetItem,
                               QHeaderView, QAbstractItemView)
from tracking_service import add_or_get_watched_app, record_process_session
from local_database import SessionLocal
from login_dialog import LoginDialog
from sync_service import ApiSyncWorker, get_and_prepare_sync_data, mark_activities_as_synced
from client_api import send_data_to_api

from services import ProcessMonitorWorker, FocusTimeWorker, get_process_list
from UiFile.Ui_PidSelect import Ui_desktopActivitySystem
from UiFile.Ui_ProcListDialog import Ui_ProcList

def format_seconds_to_text(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} 秒"
    
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    
    text = ""
    if d > 0:
        text += f"{int(d)}天 "
    if h > 0:
        text += f"{int(h)}小时 "
    if m > 0:
        text += f"{int(m)}分钟 "
    
    if d == 0 and h == 0: 
        text += f"{int(s)}秒"
        
    return text.strip()

class Mywindow(QMainWindow, Ui_desktopActivitySystem):
    request_stop_monitor = Signal()
    request_stop_focus = Signal()
    request_stop_sync = Signal()
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        
        self.token = None
        self.username = None
        self.proc_pid = None
        self.current_executable_name = None
        self.current_proc_start_time = None
        self.monitor_thread = None
        self.monitor_worker = None
        self.focus_thread = None
        self.focus_worker = None
        self.sync_thread = None
        self.sync_worker = None

        self._setup_ui_and_connections()
        self.start_api_sync_service()

    def _setup_ui_and_connections(self):
        self.login_button.clicked.connect(self.open_login_dialog)
        self.pushButton_procs.clicked.connect(self.open_process_dialog)
        self.user_show.setText("未登录")
        self.proc_name_show.setText("尚未选择进程")
        self.proc_path_show.setText("尚未选择进程")
        self.proc_start_time_show.setText("尚未选择进程")
        self.proc_end_time_show.setText("尚未选择进程")
        self.label_focus_time_show.setText(" 0 秒")
        self.statusBar().showMessage("欢迎使用桌面活动追踪系统", 5000)

    # 这是一个新的槽函数，专门用来安全地更新状态栏
    def update_status_bar(self, msg: str):
        self.statusBar().showMessage(msg, 5000)

    def open_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.token = dialog.token
            self.username = dialog.username
            self.user_show.setText(self.username)
            print(f"登录成功！欢迎, {self.username}。")
            self.run_immediate_sync()
        else:
            print("用户取消了登录，程序将以离线模式继续运行。")
            
    def start_api_sync_service(self):
        if self.sync_thread and self.sync_thread.isRunning():
            return
            
        print("[Sync Manager] 正在启动后台自动同步服务...")
        self.sync_thread = QThread(self)
        self.sync_worker = ApiSyncWorker(parent_window=self)
        self.sync_worker.moveToThread(self.sync_thread)
        self.sync_thread.finished.connect(self.sync_worker.deleteLater)
        self.sync_thread.started.connect(self.sync_worker.start_service)
        self.request_stop_sync.connect(self.sync_worker.stop)
        
        self.sync_worker.finished.connect(self.sync_thread.quit)
        self.sync_worker.finished.connect(self.sync_worker.deleteLater)
        self.sync_thread.finished.connect(self.sync_thread.deleteLater)
        
        # --- 这是本次唯一的、核心的修改！ ---
        # 我们不再使用 lambda，而是连接到一个专用的槽函数，
        # 并且强制指定连接模式为 Qt.QueuedConnection。
        self.sync_worker.status_updated.connect(self.update_status_bar, Qt.QueuedConnection)
        
        self.sync_thread.start()

    # (从这里往下的所有其他代码都与上一版完全相同，无需关注)
    
    def run_immediate_sync(self):
        if not self.token:
            print("[Immediate Sync] 未登录，跳过立即同步。")
            return

        print("[Immediate Sync] 响应关键事件，开始立即同步...")
        self.statusBar().showMessage("正在同步数据到云端...", 3000)
        data_to_send, activities_to_mark = get_and_prepare_sync_data()

        if not data_to_send:
            print("[Immediate Sync] 没有需要立即同步的新数据。")
            self.statusBar().showMessage("数据已是最新。", 3000)
            return

        success = send_data_to_api(data_to_send, "/sync/sessions/", self.token)
        if success:
            mark_activities_as_synced(activities_to_mark)
            print("[Immediate Sync] 立即同步成功。")
            self.statusBar().showMessage("数据同步成功！", 3000)
        else:
            print("[Immediate Sync] 立即同步失败。数据将在后台重试。")
            self.statusBar().showMessage("同步失败，后台将自动重试。", 3000)
    
    def open_process_dialog(self):
        dialog = DialogWindow(self)
        if dialog.exec() == QDialog.Accepted:
            selected_pid = dialog.get_selected_pid()
            if selected_pid:
                try:
                    proc = psutil.Process(selected_pid)
                    executable_name = proc.name()
                    db = SessionLocal()
                    summary = add_or_get_watched_app(db, executable_name)
                    db.close()
                    if summary:
                        self.statusBar().showMessage(f"'{executable_name}' 已追踪。累计运行: {summary.total_lifetime_seconds}s", 10000)
                    self.update_proc_info(selected_pid)
                    self.start_monitoring_process(pid=selected_pid, executable_name=executable_name)
                except psutil.NoSuchProcess:
                    self.statusBar().showMessage(f"错误：进程 {selected_pid} 已消失。", 5000)
                except Exception as e:
                    self.statusBar().showMessage(f"发生内部错误: {e}", 5000)

    def update_proc_info(self, pid):
        try:
            proc = psutil.Process(pid)
            self.proc_pid = pid
            self.current_executable_name = proc.name()
            self.current_proc_start_time = datetime.datetime.fromtimestamp(proc.create_time())
            self.proc_name_show.setText(proc.name())
            self.proc_path_show.setText(proc.exe())
            self.proc_start_time_show.setText(self.current_proc_start_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.proc_end_time_show.setText("监视中...")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.proc_name_show.setText(f"无法访问进程 {pid}")

    def start_monitoring_process(self, pid: int, executable_name: str):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.request_stop_monitor.emit()
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        if self.focus_thread and self.focus_thread.isRunning():
            self.request_stop_focus.emit()
            self.focus_thread.quit()
            self.focus_thread.wait()
        
        self.label_focus_time_show.setText(" 0 秒")
        self.current_executable_name = executable_name
        
        self.monitor_thread = QThread()
        self.monitor_worker = ProcessMonitorWorker(pid)
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.start_monitoring)
        self.request_stop_monitor.connect(self.monitor_worker.stop)
        self.monitor_worker.process_terminated.connect(self.on_process_terminated)
        self.monitor_worker.finished.connect(self.monitor_thread.quit)
        self.monitor_thread.start()

        self.focus_thread = QThread()
        self.focus_worker = FocusTimeWorker(pid)
        self.focus_worker.moveToThread(self.focus_thread)
        self.focus_thread.started.connect(self.focus_worker.start_focus_check)
        self.request_stop_focus.connect(self.focus_worker.stop)
        self.focus_worker.time_updated.connect(self.on_focus_time_updated)
        self.focus_worker.finished.connect(self.focus_thread.quit)
        self.focus_thread.start()

    def on_process_terminated(self, pid: int, end_time: datetime.datetime):
        if self.proc_pid != pid:
            return
            
        if self.focus_thread and self.focus_thread.isRunning():
            self.request_stop_focus.emit()
            self.focus_thread.wait(500)
            
        focus_details = self.focus_worker.get_focus_details()
        self.proc_end_time_show.setText(end_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        db = SessionLocal()
        try:
            record_process_session(
                db=db,
                executable_name=self.current_executable_name,
                start_time=self.current_proc_start_time,
                end_time=end_time,
                focus_details=focus_details
            )
        finally:
            db.close()

    def on_focus_time_updated(self, seconds: int):
        # 使用上面的格式化函数
        time_text = format_seconds_to_text(seconds)
        self.label_focus_time_show.setText(time_text)


    def closeEvent(self, event):
        print("[Main Window] 关闭事件触发...")
        self.run_immediate_sync()

        print("--> 正在通过信号请求所有后台服务优雅停止...")
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.request_stop_monitor.emit()
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        if self.focus_thread and self.focus_thread.isRunning():
            self.request_stop_focus.emit()
            self.focus_thread.quit()
            self.focus_thread.wait()
        if self.sync_thread and self.sync_thread.isRunning():
            self.request_stop_sync.emit()
            self.sync_thread.quit()
            self.sync_thread.wait()
            
        print("[Main Window] 所有后台服务已确认停止，程序即将退出。")
        super().closeEvent(event)

class DialogWindow(QDialog, Ui_ProcList):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.proc_pid = None

        self.lineEdit_search.textChanged.connect(self.populate_process_list)
        self.list_brush.clicked.connect(self.populate_process_list) 

        header = self.procTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.procTable.setSortingEnabled(True)
        self.procTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.procTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.procTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pushButton_accept.clicked.connect(self.accept)
        self.pushButton_reject.clicked.connect(self.reject)

        self.populate_process_list()

    def get_selected_pid(self): 
        selected_rows_indexes = self.procTable.selectionModel().selectedRows()
        if not selected_rows_indexes:
            return None
        row = selected_rows_indexes[0].row()
        return self.procTable.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def populate_process_list(self):
        search_term = self.lineEdit_search.text().lower().strip()

        self.procTable.setSortingEnabled(False)
        self.procTable.setRowCount(0) 
        
        processes = get_process_list() 

        if not search_term:
            filtered_processes = processes
        else:
            filtered_processes = []
            for proc in processes:
                pid_str = str(proc['pid'])
                name_str = proc['name'].lower()
                path_str = proc['exe'].lower()
                if (search_term in pid_str or 
                    search_term in name_str or 
                    search_term in path_str):
                    filtered_processes.append(proc)
        self.procTable.setRowCount(len(filtered_processes))
        for row, proc_info in enumerate(filtered_processes):
            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.ItemDataRole.DisplayRole, proc_info['pid'])
            pid_item.setData(Qt.ItemDataRole.UserRole, proc_info['pid'])
            pid_item.setToolTip(str(proc_info['pid']))
            name_item = QTableWidgetItem(proc_info['name'])
            name_item.setToolTip(proc_info['name'])
            path_item = QTableWidgetItem(proc_info['exe'])
            path_item.setToolTip(proc_info['exe'])
            self.procTable.setItem(row, 0, pid_item)
            self.procTable.setItem(row, 1, name_item)
            self.procTable.setItem(row, 2, path_item)
        self.procTable.setSortingEnabled(True)

