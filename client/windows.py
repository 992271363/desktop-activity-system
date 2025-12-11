import datetime
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (QApplication, QMainWindow, QDialog, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QMenu, QMessageBox,
                               QFormLayout, QLabel, QFrame, QDialogButtonBox)
from PySide6.QtGui import QFont, QColor, QBrush

# 业务引用
from services import GlobalMonitorWorker, get_process_list
from local_database import SessionLocal
from local_models import WatchedApplication
from tracking_service import add_or_get_watched_app

# 窗口引用
from login_dialog import LoginDialog
from sync_service import ApiSyncWorker, get_and_prepare_sync_data, mark_activities_as_synced
from client_api import send_data_to_api
from UiFile.Ui_Main import Ui_desktopActivitySystem 
from UiFile.Ui_ProcListDialog import Ui_ProcList

def format_seconds_to_text(seconds: int) -> str:
    if seconds < 60: return f"{seconds} 秒"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    text = ""
    if d > 0: text += f"{int(d)}天 "
    if h > 0: text += f"{int(h)}小时 "
    if m > 0: text += f"{int(m)}分钟 "
    if d == 0 and h == 0: text += f"{int(s)}秒"
    return text.strip()

# 详细信息弹窗
class AppDetailDialog(QDialog):
    def __init__(self, app_data: WatchedApplication, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"详细信息 - {app_data.executable_name}")
        self.resize(400, 300)
        
        layout = QFormLayout(self)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setContentsMargins(30, 20, 30, 20)
        
        layout.addRow("<b>应用名称:</b>", QLabel(app_data.executable_name))
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addRow(line)
        
        summary = app_data.summary
        def fmt_time(dt): return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "从未"
        
        layout.addRow("总焦点时长:", QLabel(format_seconds_to_text(summary.total_focus_time_seconds)))
        layout.addRow("总运行时长:", QLabel(format_seconds_to_text(summary.total_lifetime_seconds)))
        
        ratio = 0
        if summary.total_lifetime_seconds > 0:
            ratio = (summary.total_focus_time_seconds / summary.total_lifetime_seconds) * 100
        layout.addRow("焦点时长占比:", QLabel(f"{ratio:.1f}%"))

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        layout.addRow(line2)

        layout.addRow("首次启动:", QLabel(fmt_time(summary.first_seen_at)))
        layout.addRow("最后启动:", QLabel(fmt_time(summary.last_seen_start_at)))
        layout.addRow("最后结束:", QLabel(fmt_time(summary.last_seen_end_at)))

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

# 主窗口
class Mywindow(QMainWindow, Ui_desktopActivitySystem):
    request_stop_sync = Signal()
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # 7 列设置
        columns = ["状态", "应用名称", "本次焦点", "本次运行", "启动时间", "总焦点时长", "总运行时长"]
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)
        
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.Interactive)          
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.doubleClicked.connect(self.open_detail_dialog)
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.tableWidget.setColumnWidth(1, 250)

        self.token = None
        self.username = None
        self.monitor_thread = None
        self.monitor_worker = None
        self.sync_thread = None
        self.sync_worker = None

        self.login_button.clicked.connect(self.open_login_dialog)
        self.pushButton_procs.clicked.connect(self.open_add_app_dialog) 
        
        self.user_show.setText("未登录")
        self.statusBar().showMessage("系统就绪，正在初始化...", 3000)

        self.refresh_table_from_db()
        self.start_global_monitor()
        self.start_api_sync_service() # 缩进正确

    def create_status_item(self, color_hex: str):
        item = QTableWidgetItem("●")
        item.setTextAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        item.setFont(font)
        item.setForeground(QBrush(QColor(color_hex)))
        return item

    def start_global_monitor(self):
        watched_list = self.get_watched_apps_names()
        self.monitor_thread = QThread()
        self.monitor_worker = GlobalMonitorWorker(watched_list)
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.run)
        
        # 连接退出信号：Worker结束 -> 线程退出
        self.monitor_worker.finished.connect(self.monitor_thread.quit)
        
        self.monitor_worker.finished.connect(self.monitor_worker.deleteLater)
        self.monitor_thread.finished.connect(self.monitor_thread.deleteLater)
        self.monitor_worker.status_updated.connect(self.update_table_status)
        self.monitor_thread.start()

    def get_watched_apps_names(self):
        db = SessionLocal()
        apps = db.query(WatchedApplication).all()
        names = [app.executable_name for app in apps]
        db.close()
        return names

    def refresh_table_from_db(self):
        db = SessionLocal()
        apps = db.query(WatchedApplication).all()
        self.tableWidget.setRowCount(0)
        for app in apps:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            
            self.tableWidget.setItem(row, 0, self.create_status_item("#cbd5e0"))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(app.executable_name))
            self.tableWidget.setItem(row, 2, QTableWidgetItem("-"))
            self.tableWidget.setItem(row, 3, QTableWidgetItem("-"))
            self.tableWidget.setItem(row, 4, QTableWidgetItem("-"))
            
            base_focus = app.summary.total_focus_time_seconds
            item_focus = QTableWidgetItem(format_seconds_to_text(base_focus))
            item_focus.setData(Qt.UserRole, base_focus)
            self.tableWidget.setItem(row, 5, item_focus)

            base_life = app.summary.total_lifetime_seconds
            item_life = QTableWidgetItem(format_seconds_to_text(base_life))
            item_life.setData(Qt.UserRole, base_life)
            self.tableWidget.setItem(row, 6, item_life)
            
        db.close()

    @Slot(dict)
    def update_table_status(self, status_data: dict):
        for row in range(self.tableWidget.rowCount()):
            exe_name = self.tableWidget.item(row, 1).text()
            current_status_item = self.tableWidget.item(row, 0)
            
            item_total_focus = self.tableWidget.item(row, 5)
            item_total_life = self.tableWidget.item(row, 6)
            
            base_focus = item_total_focus.data(Qt.UserRole) or 0
            base_life = item_total_life.data(Qt.UserRole) or 0

            if exe_name in status_data:
                data = status_data[exe_name]
                status_color = "#48bb78" if data['is_focused'] else "#4299e1"
                
                self.tableWidget.setItem(row, 0, self.create_status_item(status_color))
                self.tableWidget.setItem(row, 2, QTableWidgetItem(format_seconds_to_text(data['focus'])))
                self.tableWidget.setItem(row, 3, QTableWidgetItem(format_seconds_to_text(data['runtime_seconds'])))
                self.tableWidget.setItem(row, 4, QTableWidgetItem(data['start_str']))
                current_total_focus = base_focus + data['focus']
                item_total_focus.setText(format_seconds_to_text(current_total_focus))
                
                current_total_life = base_life + data['runtime_seconds']
                item_total_life.setText(format_seconds_to_text(current_total_life))
            else:
                if current_status_item.foreground().color().name() != "#cbd5e0":
                    self.tableWidget.setItem(row, 0, self.create_status_item("#cbd5e0"))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem("-"))
                    self.tableWidget.setItem(row, 3, QTableWidgetItem("-"))
                    self.tableWidget.setItem(row, 4, QTableWidgetItem("-"))
                    # 离线时重置为基数显示
                    item_total_focus.setText(format_seconds_to_text(base_focus))
                    item_total_life.setText(format_seconds_to_text(base_life))

    def open_add_app_dialog(self):
        dialog = DialogWindow(self)
        if dialog.exec() == QDialog.Accepted:
            selected_name = dialog.get_selected_proc_name()
            if selected_name:
                exe_name = selected_name
                db = SessionLocal()
                existing = db.query(WatchedApplication).filter_by(executable_name=exe_name).first()
                if not existing:
                    add_or_get_watched_app(db, exe_name)
                    self.statusBar().showMessage(f"已添加: {exe_name}", 3000)
                    self.refresh_table_from_db()
                    if self.monitor_worker:
                        self.monitor_worker.update_watch_list(self.get_watched_apps_names())
                else:
                    self.statusBar().showMessage("该应用已在监控列表中", 3000)
                db.close()

    def open_detail_dialog(self, index):
        row = index.row()
        exe_name = self.tableWidget.item(row, 1).text()
        db = SessionLocal()
        app_data = db.query(WatchedApplication).filter_by(executable_name=exe_name).first()
        if app_data:
            dialog = AppDetailDialog(app_data, self)
            dialog.exec()
        db.close()

    def show_context_menu(self, pos):
        menu = QMenu()
        detail_action = menu.addAction("查看详细信息")
        delete_action = menu.addAction("不再监控此应用")
        action = menu.exec(self.tableWidget.mapToGlobal(pos))
        
        if action == detail_action:
            idx = self.tableWidget.currentIndex()
            if idx.isValid(): self.open_detail_dialog(idx)
        elif action == delete_action:
            row = self.tableWidget.currentRow()
            if row >= 0:
                exe_name = self.tableWidget.item(row, 1).text()
                reply = QMessageBox.question(self, "确认", f"确定移除 {exe_name} 吗？\n历史数据会保留。", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    db = SessionLocal()
                    db.query(WatchedApplication).filter_by(executable_name=exe_name).delete()
                    db.commit()
                    db.close()
                    self.refresh_table_from_db()
                    if self.monitor_worker:
                        self.monitor_worker.update_watch_list(self.get_watched_apps_names())

    def open_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.token = dialog.token
            self.username = dialog.username
            self.user_show.setText(self.username)
            self.run_immediate_sync()

    def start_api_sync_service(self):
        if self.sync_thread and self.sync_thread.isRunning(): return
        self.sync_thread = QThread(self)
        self.sync_worker = ApiSyncWorker(parent_window=self)
        self.sync_worker.moveToThread(self.sync_thread)
        self.sync_thread.started.connect(self.sync_worker.start_service)
        self.request_stop_sync.connect(self.sync_worker.stop, Qt.QueuedConnection)
        self.sync_worker.status_updated.connect(self.update_status_bar, Qt.QueuedConnection)
        
        
        # 【关键修复】确保 Timer 停止后，Worker 发出 finished，Thread 才会退出
        self.sync_worker.finished.connect(self.sync_thread.quit)
        
        self.sync_thread.finished.connect(self._on_sync_thread_finished)
        
        self.sync_thread.start()

    # 新增的清理方法
    def _on_sync_thread_finished(self):
        """同步线程完全停止后的清理工作"""
        print("[MainWindow] 同步线程已安全停止")
        if self.sync_worker:
            self.sync_worker.deleteLater()
            self.sync_worker = None
        if self.sync_thread:
            self.sync_thread.deleteLater()
            self.sync_thread = None
    
    def run_immediate_sync(self):
        if not self.token: return
        data, marks = get_and_prepare_sync_data()
        if data and send_data_to_api(data, "/sync/sessions/", self.token):
            mark_activities_as_synced(marks)
            self.update_status_bar("同步成功")

    def update_status_bar(self, msg: str):
        self.statusBar().showMessage(msg, 5000)

    # --- 核心修复：优雅退出逻辑 ---
    def closeEvent(self, event):
    # 先停止监控线程
        if self.monitor_worker and self.monitor_thread:
            self.monitor_worker.stop()
            self.monitor_thread.quit()
            if not self.monitor_thread.wait(1000):  # 等待1秒
                print("监控线程停止超时，但继续关闭")
        
        # 优雅停止同步线程
        if self.sync_worker and self.sync_thread:
            # 1. 发出停止信号，但不强制退出
            self.request_stop_sync.emit()
            
            # 2. 给予合理时间让同步线程完成当前操作
            if not self.sync_thread.wait(3000):  # 等待3秒让同步完成
                print("同步线程正在完成最后操作，稍后自动退出")
                
            # 3. 不再强制退出，让线程自然结束
            # 系统关闭时会自动清理资源
        
        # 4. 继续关闭主窗口
        super().closeEvent(event)
# --- DialogWindow (保留你的全功能版本) ---
class DialogWindow(QDialog, Ui_ProcList):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.proc_pid = None

        self.lineEdit_search.textChanged.connect(self.populate_process_list)
        self.list_brush.clicked.connect(self.populate_process_list) 
        
        header = self.procTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # PID 自适应
        header.setSectionResizeMode(1, QHeaderView.Interactive)      # 名字可拖动
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # 路径自动拉伸
        
        self.procTable.setSortingEnabled(True)
        self.procTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.procTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.procTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.pushButton_accept.clicked.connect(self.accept)
        self.pushButton_reject.clicked.connect(self.reject)

        self.populate_process_list()

    def get_selected_proc_name(self): 
        selected_rows_indexes = self.procTable.selectionModel().selectedRows()
        if not selected_rows_indexes:
            return None
        row = selected_rows_indexes[0].row()
        return self.procTable.item(row, 1).text()

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
                path_str = proc['exe'].lower() if proc['exe'] else ""
                
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
            
            path_str = proc_info['exe'] or "N/A"
            path_item = QTableWidgetItem(path_str)
            path_item.setToolTip(path_str)
            
            self.procTable.setItem(row, 0, pid_item)
            self.procTable.setItem(row, 1, name_item)
            self.procTable.setItem(row, 2, path_item)
            
        self.procTable.setSortingEnabled(True)