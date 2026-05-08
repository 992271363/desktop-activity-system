import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QPushButton, QLabel,
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget
)

from app_repository import AppRepository
from table_manager import AppTableManager
from monitor_controller import MonitorController
from sync_controller import SyncController

from dialogs import AppDetailDialog, ClosingDialog
from proc_dialog import ProcSelectDialog
from login_dialog import LoginDialog
from sync_service import get_and_prepare_sync_data, mark_activities_as_synced
from client_api import send_data_to_api


class Mywindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ---- UI 初始化 ----
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

        # ---- 状态 ----
        self.token = None
        self.username = None
        self._is_closing = False

        # ---- 组装子模块 ----
        self.table_manager = AppTableManager(self.tableWidget, self)
        self.table_manager.detail_requested.connect(self._on_detail_requested)
        self.table_manager.delete_requested.connect(self._on_delete_requested)

        self.monitor_controller = MonitorController(self)
        self.monitor_controller.status_updated.connect(self.table_manager.update_status)

        self.sync_controller = SyncController(token_provider=lambda: self.token, parent=self)
        self.sync_controller.status_updated.connect(self.update_status_bar)

        # ---- 信号连接 ----
        self.login_button.clicked.connect(self.open_login_dialog)
        self.pushButton_procs.clicked.connect(self.open_add_app_dialog)

        # ---- 启动 ----
        self.user_show.setText("未登录")
        self.statusBar().showMessage("系统就绪，正在初始化...", 3000)

        self._refresh_table()
        self.monitor_controller.start(AppRepository.get_watched_apps_info())
        self.sync_controller.start()

    def _refresh_table(self):
        apps = AppRepository.get_all_apps()
        self.table_manager.refresh(apps)

    def _refresh_monitor_list(self):
        self.monitor_controller.update_watch_list(AppRepository.get_watched_apps_info())

    def open_add_app_dialog(self):
        dialog = ProcSelectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            selected_info = dialog.get_selected_proc_info()
            if selected_info:
                exe_path, exe_name = selected_info
                if not AppRepository.app_exists(exe_path):
                    AppRepository.add_app(exe_path, exe_name)
                    self.statusBar().showMessage(f"已添加: {exe_name}", 3000)
                    self._refresh_table()
                    self._refresh_monitor_list()
                else:
                    self.statusBar().showMessage("该应用已在监控列表中", 3000)

    def _on_detail_requested(self, exe_path: str):
        app_data = AppRepository.get_app_by_path(exe_path)
        if app_data:
            dialog = AppDetailDialog(app_data, self)
            dialog.exec()

    def _on_delete_requested(self, exe_path: str, exe_name: str):
        AppRepository.delete_app_by_path(exe_path)
        self._refresh_table()
        self._refresh_monitor_list()

    def open_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.token = dialog.token
            self.username = dialog.username
            self.user_show.setText(self.username)
            self.run_immediate_sync()

    def run_immediate_sync(self):
        if not self.token:
            return
        data, marks = get_and_prepare_sync_data()
        if data and send_data_to_api(data, "/sync/sessions/", self.token):
            mark_activities_as_synced(marks)
            self.update_status_bar("同步成功")

    def update_status_bar(self, msg: str):
        self.statusBar().showMessage(msg, 5000)

    # 退出
    def closeEvent(self, event):
        if self._is_closing:
            event.accept()
            return
        self._is_closing = True
        self._closing_dialog = ClosingDialog(self)
        self._closing_dialog.show()
        for _ in range(5):
            QApplication.processEvents()
            time.sleep(0.01)

        self._closing_dialog.set_status("正在停止进程监控...")
        self.monitor_controller.stop(
            timeout_ms=1500, dialog=self._closing_dialog, status_text="正在停止进程监控"
        )

        self._closing_dialog.set_status("正在停止同步服务...")
        self.sync_controller.stop(
            timeout_ms=3000, dialog=self._closing_dialog, status_text="正在停止同步服务"
        )

        self._closing_dialog.set_status("保存完成，正在关闭...")
        QApplication.processEvents()
        QTimer.singleShot(300, self._finish_close_event)
        event.ignore()

    def _finish_close_event(self):
        if self._closing_dialog:
            self._closing_dialog.close()
            self._closing_dialog = None
        self.close()
