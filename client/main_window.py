import time
import psutil
import win32gui
import win32con
import win32process

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QPushButton, QLabel,
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QSystemTrayIcon, QMenu, QStyle
)

from app_repository import AppRepository
from table_manager import AppTableManager
from monitor_controller import MonitorController
from sync_controller import SyncController
from settings import Settings
from settings_dialog import CloseAskDialog, SettingsDialog

from dialogs import AppDetailDialog, ClosingDialog, AddAppDialog
from login_dialog import LoginDialog
from sync_service import get_and_prepare_sync_data, mark_activities_as_synced
from client_api import send_data_to_api


class Mywindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ---- UI 初始化 ----
        self.setWindowTitle("desktopActivitySystem")
        self.resize(1100, 450)

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
        self.btn_crosshair = QPushButton("拾取窗口")
        self.btn_crosshair.setToolTip("按住后拖动到目标窗口上松开，自动添加监控")
        self.btn_crosshair.setProperty("crosshair", True)
        self.settings_button = QPushButton("设置")
        self.login_button = QPushButton("登录")
        self.user_label = QLabel("账号：")
        self.user_show = QLabel("N/A")

        bottom_layout.addWidget(self.pushButton_procs)
        bottom_layout.addWidget(self.btn_crosshair)
        bottom_layout.addWidget(self.settings_button)
        bottom_layout.addWidget(self.login_button)
        bottom_layout.addWidget(self.user_label)
        bottom_layout.addWidget(self.user_show)
        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout)

        # ---- 状态 ----
        self.token = None
        self.username = None
        self._is_closing = False
        self._crosshair_active = False
        self._settings = Settings()

        # ---- 组装子模块 ----
        self.table_manager = AppTableManager(self.tableWidget, self, self._settings)
        self.table_manager.detail_requested.connect(self._on_detail_requested)
        self.table_manager.launch_requested.connect(self._on_launch_requested)
        self.table_manager.delete_requested.connect(self._on_delete_requested)
        self.table_manager.table_width_hint.connect(self._adjust_window_width)

        self.monitor_controller = MonitorController(self)
        self.monitor_controller.status_updated.connect(self.table_manager.update_status)

        self.sync_controller = SyncController(token_provider=lambda: self.token, parent=self)
        self.sync_controller.status_updated.connect(self.update_status_bar)

        # ---- 系统托盘 ----
        self._setup_tray_icon()

        # ---- 信号连接 ----
        self.login_button.clicked.connect(self.open_login_dialog)
        self.pushButton_procs.clicked.connect(self.open_add_app_dialog)
        self.btn_crosshair.pressed.connect(self._on_crosshair_pressed)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # ---- 启动 ----
        self.user_show.setText("未登录")
        self.statusBar().showMessage("系统就绪，正在初始化...", 3000)

        self._refresh_table()
        self.monitor_controller.start(AppRepository.get_watched_apps_info())
        self.sync_controller.start()

    def _setup_tray_icon(self):
        default_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self._tray_icon = QSystemTrayIcon(default_icon, self)

        tray_menu = QMenu()
        action_show = tray_menu.addAction("显示主窗口")
        tray_menu.addSeparator()
        action_settings = tray_menu.addAction("设置...")
        tray_menu.addSeparator()
        action_exit = tray_menu.addAction("退出")

        action_show.triggered.connect(self._tray_show_window)
        action_settings.triggered.connect(self.open_settings_dialog)
        action_exit.triggered.connect(self._tray_exit_app)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._tray_show_window()

    def _tray_show_window(self):
        self.showNormal()
        self.activateWindow()

    def _tray_exit_app(self):
        self._is_closing = True
        self.close()

    def _refresh_table(self):
        apps = AppRepository.get_all_apps()
        self.table_manager.refresh(apps)

    def _adjust_window_width(self, table_content_width: int):
        margins = self.centralWidget().layout().contentsMargins()
        extra = margins.left() + margins.right() + self.centralWidget().layout().spacing()
        self.resize(table_content_width + extra, self.height())

    def _refresh_monitor_list(self):
        self.monitor_controller.update_watch_list(AppRepository.get_watched_apps_info())

    def open_add_app_dialog(self):
        dialog = AddAppDialog(self)
        if dialog.exec() == QDialog.Accepted:
            selected_info = dialog.get_selected_info()
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

    def _on_launch_requested(self, exe_path: str):
        import os
        try:
            os.startfile(exe_path)
        except Exception:
            pass

    def _on_delete_requested(self, exe_path: str, exe_name: str):
        AppRepository.delete_app_by_path(exe_path)
        self._refresh_table()
        self._refresh_monitor_list()

    def _on_crosshair_pressed(self):
        self._crosshair_active = True
        self.grabMouse()
        QApplication.setOverrideCursor(Qt.CrossCursor)
        self.statusBar().showMessage("拖动到目标窗口上松开即可添加…")

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._crosshair_active:
            self._crosshair_active = False
            self.releaseMouse()
            QApplication.restoreOverrideCursor()
            self.statusBar().clearMessage()
            self._pick_window_at(event.globalPosition().toPoint())
            return
        super().mouseReleaseEvent(event)

    def _pick_window_at(self, screen_pos):
        hwnd = win32gui.WindowFromPoint((screen_pos.x(), screen_pos.y()))
        if not hwnd:
            self.statusBar().showMessage("未找到窗口", 3000)
            return

        root = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
        if root:
            hwnd = root

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            self.statusBar().showMessage("无法获取进程信息", 3000)
            return

        if pid in (0, 4):
            self.statusBar().showMessage("系统进程，已跳过", 3000)
            return

        try:
            proc = psutil.Process(pid)
            exe_path = proc.exe()
            exe_name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            self.statusBar().showMessage("无法读取进程路径", 3000)
            return

        if not exe_path:
            self.statusBar().showMessage("无法读取进程路径", 3000)
            return

        if not AppRepository.app_exists(exe_path):
            AppRepository.add_app(exe_path, exe_name)
            self.statusBar().showMessage(f"已添加: {exe_name}", 3000)
            self._refresh_table()
            self._refresh_monitor_list()
        else:
            self.statusBar().showMessage("该应用已在监控列表中", 3000)

    def open_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.token = dialog.token
            self.username = dialog.username
            self.user_show.setText(self.username)
            self.run_immediate_sync()

    def open_settings_dialog(self):
        SettingsDialog(self).exec()

    def run_immediate_sync(self):
        if not self.token:
            return
        data, marks = get_and_prepare_sync_data()
        if data and send_data_to_api(data, "/sync/sessions/", self.token):
            mark_activities_as_synced(marks)
            self.update_status_bar("同步成功")

    def update_status_bar(self, msg: str):
        self.statusBar().showMessage(msg, 5000)

    # ---- 关闭逻辑 ----
    def closeEvent(self, event):
        if self._is_closing:
            event.accept()
            return

        close_behavior = self._settings.get("closeToTray")

        if close_behavior is None:
            event.ignore()
            QTimer.singleShot(0, lambda: self._ask_close_behavior(event))
        elif close_behavior == "tray":
            event.ignore()
            self.hide()
        else:
            event.ignore()
            self._is_closing = True
            self._do_graceful_shutdown()

    def _ask_close_behavior(self, original_event):
        dialog = CloseAskDialog(self)
        dialog.exec()

        if dialog.choice == "tray":
            if dialog.remember_check.isChecked():
                self._settings.set("closeToTray", "tray")
            self.hide()
        elif dialog.choice == "exit":
            if dialog.remember_check.isChecked():
                self._settings.set("closeToTray", "exit")
            self._is_closing = True
            self._do_graceful_shutdown()
        else:
            pass

    def _do_graceful_shutdown(self):
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

    def _finish_close_event(self):
        if self._closing_dialog:
            self._closing_dialog.close()
            self._closing_dialog = None
        self._tray_icon.hide()
        self.close()
