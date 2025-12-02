import psutil, datetime, time
from PySide6.QtCore import Qt, QObject, Signal, QThread
from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog,QTableWidgetItem,
                               QHeaderView, QAbstractItemView)
from services import (ProcessMonitorWorker, ApiSyncWorker, FocusTimeWorker,
                      get_process_list)
from tracking_service import add_or_get_watched_app, record_process_session 
from local_database import SessionLocal 
from Ui_PidSelect import Ui_desktopActivitySystem
from Ui_ProcListDialog import Ui_ProcList

class Mywindow(QMainWindow,Ui_desktopActivitySystem):
    def __init__(self):
        super().__init__()  
        self.setupUi(self)
        self.proc_pid = None
        self.current_executable_name = None # 使用完整可执行文件名作为唯一标识
        self.current_proc_start_time = None # 用于记录进程启动时间
        self.current_focus_seconds = 0 # 用于累计当前会话的焦点时间
        self.monitor_thread = None # 用于监控进程的线程
        self.monitor_worker = None # 用于监控进程的工作线程
        self.sync_thread = None # 用于同步数据的线程
        self.sync_worker = None # 用于同步数据的工作线程
        self.focus_thread = None # 用于计算焦点时间的线程
        self.focus_worker = None # 用于计算焦点时间的工作线程

        self.pushButton_procs.clicked.connect(self.open_process_dialog)
        self.proc_name_show.setText("尚未选择进程") 
        self.proc_path_show.setText("尚未选择进程") 
        self.proc_start_time_show.setText("尚未选择进程")
        self.proc_end_time_show.setText("尚未选择进程")
        self.label_focus_time_show.setText(" 0 秒")
        self.start_api_sync_service()

    def open_process_dialog(self):
        dialog = DialogWindow(self)
        try:
            if dialog.exec() == QDialog.Accepted:
                selected_pid = dialog.get_selected_pid()
                if selected_pid:
                   try:
                       proc = psutil.Process(selected_pid)
                       executable_name = proc.name() # 使用 proc.name() 作为唯一标识
                       # 与数据库交互
                       db = SessionLocal()
                       summary = add_or_get_watched_app(db, executable_name)
                       db.close()
                       
                       if summary:
                           self.statusBar().showMessage(
                               f"'{executable_name}' 已追踪。累计运行: {summary.total_lifetime_seconds}s, "
                               f"累计焦点: {summary.total_focus_time_seconds}s", 10000 # 显示10秒
                           )
                       # 启动监视
                       self.update_proc_info(selected_pid)
                       self.start_monitoring_process(pid=selected_pid, executable_name=executable_name)
                   
                   except psutil.NoSuchProcess:
                       self.statusBar().showMessage(f"错误：进程 {selected_pid} 已消失。", 5000)
                   except Exception as e:
                       print(f"[UI Error] 处理选中进程时出错: {e}")
                       self.statusBar().showMessage(f"发生内部错误: {e}", 5000)
                   # --- 主要修改 END ---
        except KeyboardInterrupt:
            print("[UI] 在打开对话框时捕获到意外的 KeyboardInterrupt，已忽略。程序将继续运行。")
            pass

    def update_proc_info(self, pid):
        try:
            proc = psutil.Process(pid)
            self.proc_pid = pid
            self.current_proc_name = proc.name() 
            self.current_proc_start_time = datetime.datetime.fromtimestamp(proc.create_time())
            self.proc_name_show.setText(proc.name())
            self.proc_path_show.setText(proc.exe())
            create_time_str = self.current_proc_start_time.strftime("%Y年%m月%d日 %H:%M:%S")
            self.proc_start_time_show.setText(create_time_str)
            self.proc_end_time_show.setText("监视中...") 
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.proc_name_show.setText(f"无法访问进程 {pid}")
            self.proc_path_show.setText("N/A")
            self.proc_start_time_show.setText("N/A")
            self.proc_end_time_show.setText("N/A")

    def start_monitoring_process(self, pid: int, executable_name: str):
        # 停止旧的监控线程（如果存在）
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_worker.stop()
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        # 停止旧的焦点计时线程（如果存在）
        if self.focus_thread and self.focus_thread.isRunning():
            self.focus_worker.stop()
            self.focus_thread.quit()
            self.focus_thread.wait()
            
        # 重置UI
        self.label_focus_time_show.setText(" 0 秒")
        self.current_focus_seconds = 0 # 重置焦点时间计数器
        self.current_executable_name = executable_name # 保存当前监视的程序名

        # 启动新的进程生命周期监控线程
        self.monitor_thread = QThread()
        self.monitor_worker = ProcessMonitorWorker(pid)
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.run_check)
        self.monitor_worker.process_terminated.connect(self.on_process_terminated)
        self.monitor_worker.finished.connect(self.monitor_thread.quit)
        self.monitor_thread.finished.connect(self.on_monitor_finished)
        self.monitor_thread.finished.connect(self.monitor_worker.deleteLater)
        self.monitor_thread.start()

        # 启动新的焦点计时线程
        self.focus_thread = QThread()
        self.focus_worker = FocusTimeWorker(pid)
        self.focus_worker.moveToThread(self.focus_thread)
        self.focus_thread.started.connect(self.focus_worker.run_focus_check)
        self.focus_worker.time_updated.connect(self.on_focus_time_updated)
        self.focus_worker.finished.connect(self.focus_thread.quit)
        self.focus_thread.finished.connect(self.focus_worker.deleteLater)
        self.focus_thread.start()

    def on_focus_time_updated(self, seconds: int):
        self.label_focus_time_show.setText(f" {seconds} 秒")
        self.current_focus_seconds = seconds # 持续更新当前会话的焦点总时长
    def start_api_sync_service(self):
        if self.sync_thread and self.sync_thread.isRunning():
            print("[Sync Service] 服务已经在运行中，无需重复启动。")
            return
        self.sync_thread = QThread()
        self.sync_worker = ApiSyncWorker(interval_seconds=15) 
        self.sync_worker.moveToThread(self.sync_thread)
        self.sync_thread.started.connect(self.sync_worker.run_sync)
        self.sync_worker.finished.connect(self.sync_thread.quit)
        self.sync_worker.status_updated.connect(self.update_status_bar)
        self.sync_thread.finished.connect(self.sync_worker.deleteLater)
        self.sync_thread.start()
        print("[Sync Service] 云同步服务线程已启动。")

    def update_status_bar(self, message: str):
        print(f"[Sync Status] {message}") 

    def closeEvent(self, event):
        """重写关闭事件，确保所有后台线程都安全退出"""
        print("[Main Window] 关闭事件触发，正在清理所有后台线程...")
        
        # 停止进程监视线程
        if self.monitor_thread and self.monitor_thread.isRunning():
            print("  -> 正在停止进程监视线程...")
            self.monitor_worker.stop()
            self.monitor_thread.quit()
            self.monitor_thread.wait(2000)
            print("  -> 进程监视线程已停止。")
            
        # 停止焦点计时线程
        if self.focus_thread and self.focus_thread.isRunning():
            print("  -> 正在停止焦点计时线程...")
            self.focus_worker.stop()
            self.focus_thread.quit()
            self.focus_thread.wait(2000)
            print("  -> 焦点计时线程已停止。")

        # 停止云同步线程
        if self.sync_thread and self.sync_thread.isRunning():
            print("  -> 正在停止云同步线程...")
            self.sync_worker.stop()
            self.sync_thread.quit()
            self.sync_thread.wait(2000)
            print("  -> 云同步线程已停止。")
            
        super().closeEvent(event)

    def on_process_terminated(self, pid: int, end_time: datetime.datetime):
        if self.proc_pid != pid:
            return
        
 
        if self.focus_thread and self.focus_thread.isRunning():
            self.focus_worker.stop()
        
        end_time_str = end_time.strftime("%Y年%m月%d日 %H:%M:%S")
        self.proc_end_time_show.setText(end_time_str)
        
        print("[Manager] 进程终止，准备写入数据库...")
        db = None
        try:
            db = SessionLocal() 
            record_process_session(
                db=db,
                executable_name=self.current_executable_name,
                start_time=self.current_proc_start_time,
                end_time=end_time,
                focus_seconds=self.current_focus_seconds # 传入累计的焦点时间
            )
        except Exception as e:
            print(f"[Manager] 数据库操作时发生错误: {e}")
        finally:
            if db:
                db.close()
                print("[Manager] 数据库会话已关闭。")

    def on_monitor_finished(self):
        print("[Manager] 确认监视线程已结束。")

    def on_monitor_error(self, error_message):
        print(f"[Manager] 接到错误报告: {error_message}")

    def get_create_timestamp(self,pid):
        proc = psutil.Process(pid)
        create_timestamp = proc.create_time()
        create_datetime = datetime.datetime.fromtimestamp(create_timestamp)
        return create_datetime

class DialogWindow(QDialog, Ui_ProcList):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.proc_pid = None
        self.proc_name = None
        self.proc_path = None
        self.list_brush.clicked.connect(self.populate_process_list) # 列表刷新按钮
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
        self.procTable.setSortingEnabled(False)
        self.procTable.setRowCount(0) # 清空旧数据
        processes = get_process_list() # 获取新数据
        self.procTable.setRowCount(len(processes))
        for row, proc_info in enumerate(processes):
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
