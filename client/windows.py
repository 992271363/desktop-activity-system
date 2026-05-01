import time

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QMessageBox, QPushButton, QLabel,
    QWidget, QVBoxLayout, QHBoxLayout
)

# 业务引用
from services import GlobalMonitorWorker
from local_database import SessionLocal
from local_models import WatchedApplication
from tracking_service import add_or_get_watched_app

# 窗口引用
from login_dialog import LoginDialog
from sync_service import ApiSyncWorker, get_and_prepare_sync_data, mark_activities_as_synced
from client_api import send_data_to_api

# 拆分出的模块
from utils import format_seconds_to_text
from dialogs import AppDetailDialog, ClosingDialog
from proc_dialog import ProcSelectDialog


class Mywindow(QMainWindow):
    request_stop_sync = Signal()

    def __init__(self):
        super().__init__()

        # ---- 纯代码 UI 初始化（响应式布局）----
        self.setWindowTitle("desktopActivitySystem")
        self.resize(925, 382)

        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.tableWidget = QTableWidget()
        main_layout.addWidget(self.tableWidget, stretch=1)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.pushButton_procs = QPushButton("添加进程")
        self.login_button = QPushButton("登录")
        self.user_label = QLabel("账号：")
        self.user_show = QLabel("N/A")

        bottom_layout.addWidget(self.pushButton_procs)
        bottom_layout.addWidget(self.login_button)
        bottom_layout.addWidget(self.user_label)
        bottom_layout.addWidget(self.user_show)
        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout)
        # ----------------------------------------

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
        self.tableWidget.setAlternatingRowColors(True)

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
        self.start_api_sync_service()

    def create_status_label(self, color_hex: str):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        dot = QLabel()
        dot.setFixedSize(14, 14)
        dot.setStyleSheet(f"background-color: {color_hex}; border-radius: 7px;")
        layout.addWidget(dot)
        container.setProperty("status_color", color_hex)
        return container

    def start_global_monitor(self):
        watched_info = self.get_watched_apps_info()
        self.monitor_thread = QThread()
        self.monitor_worker = GlobalMonitorWorker(watched_info)
        self.monitor_worker.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor_worker.run)

        # 连接退出信号：Worker结束 -> 线程退出
        self.monitor_worker.finished.connect(self.monitor_thread.quit)

        self.monitor_worker.finished.connect(self.monitor_worker.deleteLater)
        self.monitor_thread.finished.connect(self.monitor_thread.deleteLater)
        self.monitor_worker.status_updated.connect(self.update_table_status)
        self.monitor_thread.start()

    def get_watched_apps_info(self):
        db = SessionLocal()
        apps = db.query(WatchedApplication).all()
        infos = [(app.executable_path, app.executable_name) for app in apps]
        db.close()
        return infos

    def refresh_table_from_db(self):
        db = SessionLocal()
        apps = db.query(WatchedApplication).all()
        self.tableWidget.setRowCount(0)
        for app in apps:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)

            self.tableWidget.setCellWidget(row, 0, self.create_status_label("#cbd5e0"))

            name_item = QTableWidgetItem(app.executable_name)
            name_item.setData(Qt.UserRole, app.executable_path)
            self.tableWidget.setItem(row, 1, name_item)

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
            exe_name_item = self.tableWidget.item(row, 1)
            exe_path = exe_name_item.data(Qt.UserRole)
            current_status_widget = self.tableWidget.cellWidget(row, 0)

            item_total_focus = self.tableWidget.item(row, 5)
            item_total_life = self.tableWidget.item(row, 6)

            base_focus = item_total_focus.data(Qt.UserRole) or 0
            base_life = item_total_life.data(Qt.UserRole) or 0

            if exe_path in status_data:
                data = status_data[exe_path]
                status_color = "#48bb78" if data['is_focused'] else "#4299e1"

                self.tableWidget.setCellWidget(row, 0, self.create_status_label(status_color))
                self.tableWidget.setItem(row, 2, QTableWidgetItem(format_seconds_to_text(data['focus'])))
                self.tableWidget.setItem(row, 3, QTableWidgetItem(format_seconds_to_text(data['runtime_seconds'])))
                self.tableWidget.setItem(row, 4, QTableWidgetItem(data['start_str']))
                current_total_focus = base_focus + data['focus']
                item_total_focus.setText(format_seconds_to_text(current_total_focus))

                current_total_life = base_life + data['runtime_seconds']
                item_total_life.setText(format_seconds_to_text(current_total_life))
            else:
                if current_status_widget and current_status_widget.property("status_color") != "#cbd5e0":
                    self.tableWidget.setCellWidget(row, 0, self.create_status_label("#cbd5e0"))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem("-"))
                    self.tableWidget.setItem(row, 3, QTableWidgetItem("-"))
                    self.tableWidget.setItem(row, 4, QTableWidgetItem("-"))
                    # 离线时重置为基数显示
                    item_total_focus.setText(format_seconds_to_text(base_focus))
                    item_total_life.setText(format_seconds_to_text(base_life))

    def open_add_app_dialog(self):
        dialog = ProcSelectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            selected_info = dialog.get_selected_proc_info()
            if selected_info:
                exe_path, exe_name = selected_info
                db = SessionLocal()
                existing = db.query(WatchedApplication).filter_by(executable_path=exe_path).first()
                if not existing:
                    add_or_get_watched_app(db, exe_path, exe_name)
                    self.statusBar().showMessage(f"已添加: {exe_name}", 3000)
                    self.refresh_table_from_db()
                    if self.monitor_worker:
                        self.monitor_worker.update_watch_list(self.get_watched_apps_info())
                else:
                    self.statusBar().showMessage("该应用已在监控列表中", 3000)
                db.close()

    def open_detail_dialog(self, index):
        row = index.row()
        exe_path = self.tableWidget.item(row, 1).data(Qt.UserRole)
        db = SessionLocal()
        app_data = db.query(WatchedApplication).filter_by(executable_path=exe_path).first()
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
            if idx.isValid():
                self.open_detail_dialog(idx)
        elif action == delete_action:
            row = self.tableWidget.currentRow()
            if row >= 0:
                exe_name = self.tableWidget.item(row, 1).text()
                exe_path = self.tableWidget.item(row, 1).data(Qt.UserRole)
                reply = QMessageBox.question(
                    self, "确认",
                    f"确定移除 {exe_name} 吗？\n历史数据会保留。",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    db = SessionLocal()
                    db.query(WatchedApplication).filter_by(executable_path=exe_path).delete()
                    db.commit()
                    db.close()
                    self.refresh_table_from_db()
                    if self.monitor_worker:
                        self.monitor_worker.update_watch_list(self.get_watched_apps_info())

    def open_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.token = dialog.token
            self.username = dialog.username
            self.user_show.setText(self.username)
            self.run_immediate_sync()

    def start_api_sync_service(self):
        if self.sync_thread and self.sync_thread.isRunning():
            return
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
        if not self.token:
            return
        data, marks = get_and_prepare_sync_data()
        if data and send_data_to_api(data, "/sync/sessions/", self.token):
            mark_activities_as_synced(marks)
            self.update_status_bar("同步成功")

    def update_status_bar(self, msg: str):
        self.statusBar().showMessage(msg, 5000)

    # --- 核心修复：优雅退出逻辑 ---
    def closeEvent(self, event):
        # 1. 立即显示关闭提示对话框
        self._closing_dialog = ClosingDialog(self)
        self._closing_dialog.show()
        # 强制立即处理事件，确保对话框完全渲染显示出来
        for _ in range(5):  # 多处理几次，确保对话框已显示
            QApplication.processEvents()
            time.sleep(0.01)  # 10ms，让UI线程有机会渲染

        # 2. 停止监控线程（非阻塞轮询，保持UI响应）
        print("[Close] 开始处理监控线程...")
        if self.monitor_worker and self.monitor_thread:
            print(f"[Close] 监控线程存在，isRunning={self.monitor_thread.isRunning()}")
            self._closing_dialog.set_status("正在停止进程监控...")
            self.monitor_worker.stop()
            self.monitor_thread.quit()
            # 非阻塞等待，保持进度条动画
            self._wait_for_thread(self.monitor_thread, 1500, self._closing_dialog, "正在停止进程监控")

        # 3. 优雅停止同步线程
        print(f"[Close Debug] sync_worker: {self.sync_worker}, sync_thread: {self.sync_thread}")
        if self.sync_worker and self.sync_thread:
            print(f"[Close Debug] 同步线程运行状态: {self.sync_thread.isRunning()}")
            self._closing_dialog.set_status("正在停止同步服务...")
            print("[Close Debug] 发送停止信号...")
            self.request_stop_sync.emit()
            print("[Close Debug] 开始等待同步线程结束...")
            # 非阻塞等待，保持进度条动画
            self._wait_for_thread(self.sync_thread, 3000, self._closing_dialog, "正在停止同步服务")
            print("[Close Debug] 同步线程等待完成")
        else:
            print("[Close Debug] 同步组件不存在，跳过")

        # 4. 最后提示并关闭对话框
        self._closing_dialog.set_status("保存完成，正在关闭...")
        QApplication.processEvents()
        # 短暂延时让用户看到最终提示
        QTimer.singleShot(300, self._finish_close_event)

        # 暂时忽略关闭事件，等定时器完成后再真正关闭
        event.ignore()

    def _wait_for_thread(self, thread, timeout_ms, dialog=None, status_text=""):
        """非阻塞等待线程结束，保持UI更新和进度条动画"""
        start_time = time.time() * 1000
        check_count = 0

        while thread.isRunning():
            check_count += 1
            # 每500ms更新一次对话框文字，让用户知道还在运行
            if dialog and check_count % 25 == 0:  # 25 * 20ms = 500ms
                elapsed = int((time.time() * 1000 - start_time) / 100) / 10
                dialog.set_status(f"{status_text} (已等待{elapsed}秒)...")

            # 处理事件，保持进度条动画
            QApplication.processEvents()

            # 检查超时
            if (time.time() * 1000 - start_time) > timeout_ms:
                print(f"线程停止超时({timeout_ms}ms)，线程仍在运行: {thread.isRunning()}")
                break

            # 短暂休眠，避免CPU空转
            time.sleep(0.02)  # 20ms

        print(f"线程等待结束，总共检查{check_count}次，最终状态: {thread.isRunning()}")

    def _finish_close_event(self):
        """完成最终的关闭操作"""
        if self._closing_dialog:
            self._closing_dialog.close()
            self._closing_dialog = None
        # 真正关闭窗口
        self.close()

    def closeEvent_real(self, event):
        """实际的关闭处理（备用，防止循环调用）"""
        super().closeEvent(event)
