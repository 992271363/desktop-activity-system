import psutil, datetime, time
from PySide6.QtCore import Qt, QObject, Signal, QThread
from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog,QTableWidgetItem,
                               QHeaderView, QAbstractItemView)
from services import (ProcessMonitorWorker,  FocusTimeWorker,
                      get_process_list)
from tracking_service import add_or_get_watched_app, record_process_session 
from local_database import SessionLocal 
from Ui_PidSelect import Ui_desktopActivitySystem
from Ui_ProcListDialog import Ui_ProcList

class Mywindow(QMainWindow,Ui_desktopActivitySystem):
    def __init__(self):
        super().__init__()  
        self.setupUi(self)

        self.jwt_token = None #存放token
        
        self.proc_pid = None
        self.current_executable_name = None 
        self.current_proc_start_time = None
        
        # 这些线程和worker的引用是好的实践
        self.monitor_thread = None 
        self.monitor_worker = None
        # self.sync_thread = None # 暂时禁用
        # self.sync_worker = None # 暂时禁用
        self.focus_thread = None 
        self.focus_worker = None
        self.pushButton_procs.clicked.connect(self.open_process_dialog)
        self.proc_name_show.setText("尚未选择进程") 
        self.proc_path_show.setText("尚未选择进程") 
        self.proc_start_time_show.setText("尚未选择进程")
        self.proc_end_time_show.setText("尚未选择进程")
        self.label_focus_time_show.setText(" 0 秒")
        
        # self.start_api_sync_service() # <-- 暂时禁用同步服务
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
                        self.statusBar().showMessage(
                            f"'{executable_name}' 已追踪。累计运行: {summary.total_lifetime_seconds}s, "
                            f"累计焦点: {summary.total_focus_time_seconds}s", 10000
                        )
                    self.update_proc_info(selected_pid)
                    self.start_monitoring_process(pid=selected_pid, executable_name=executable_name)
                
                except psutil.NoSuchProcess:
                    self.statusBar().showMessage(f"错误：进程 {selected_pid} 已消失。", 5000)
                except Exception as e:
                    print(f"[UI Error] 处理选中进程时出错: {e}")
                    self.statusBar().showMessage(f"发生内部错误: {e}", 5000)
    def update_proc_info(self, pid):
        try:
            proc = psutil.Process(pid)
            self.proc_pid = pid
            self.current_executable_name = proc.name() # 使用 executable_name 保持一致
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
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_worker.stop()
            self.monitor_thread.quit()
            self.monitor_thread.wait()
        if self.focus_thread and self.focus_thread.isRunning():
            self.focus_worker.stop()
            self.focus_thread.quit()
            self.focus_thread.wait()
            
        self.label_focus_time_show.setText(" 0 秒")
        self.current_executable_name = executable_name
        self.monitor_thread = QThread()
        self.monitor_worker = ProcessMonitorWorker(pid)
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.run_check)
        self.monitor_worker.process_terminated.connect(self.on_process_terminated)
        self.monitor_worker.finished.connect(self.monitor_thread.quit)
        self.monitor_thread.finished.connect(self.monitor_worker.deleteLater)
        self.monitor_thread.start()
        self.focus_thread = QThread()
        self.focus_worker = FocusTimeWorker(pid) # 使用我们新的 FocusTimeWorker
        self.focus_worker.moveToThread(self.focus_thread)
        self.focus_thread.started.connect(self.focus_worker.run_focus_check)
        self.focus_worker.time_updated.connect(self.on_focus_time_updated)
        self.focus_worker.finished.connect(self.focus_thread.quit)
        self.focus_thread.finished.connect(self.focus_worker.deleteLater)
        self.focus_thread.start()
    def on_focus_time_updated(self, seconds: int):
        self.label_focus_time_show.setText(f" {seconds} 秒")


    def closeEvent(self, event):
        print("[Main Window] 关闭事件触发，正在清理所有后台线程...")
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_worker.stop()
            self.monitor_thread.quit()
            self.monitor_thread.wait(2000)
        if self.focus_thread and self.focus_thread.isRunning():
            self.focus_worker.stop()
            self.focus_thread.quit()
            self.focus_thread.wait(2000)
        # if self.sync_thread and self.sync_thread.isRunning(): ... # 暂时禁用
        super().closeEvent(event)

    def on_process_terminated(self, pid: int, end_time: datetime.datetime):
        if self.proc_pid != pid:
            return
        
        # 确保焦点线程也停止
        if self.focus_thread and self.focus_thread.isRunning():
            self.focus_worker.stop()
        
        # 从 focus_worker 获取详细的焦点数据字典
        focus_details = self.focus_worker.get_focus_details()
        
        end_time_str = end_time.strftime("%Y年%m月%d日 %H:%M:%S")
        self.proc_end_time_show.setText(end_time_str)
        
        print(f"[Manager] 进程终止，准备写入数据库。焦点详情: {focus_details}")
        db = None
        try:
            db = SessionLocal() 
            # 调用新的 record_process_session 函数，并传入正确的参数
            record_process_session(
                db=db,
                executable_name=self.current_executable_name,
                start_time=self.current_proc_start_time,
                end_time=end_time,
                focus_details=focus_details # <-- 传入字典，而不是整数！
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
