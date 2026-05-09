from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QMessageBox, QWidget, QHBoxLayout, QLabel
)

from typing import List
from utils import format_seconds_to_text
from app_repository import AppInfo


class AppTableManager(QObject):
    detail_requested = Signal(str)
    launch_requested = Signal(str)
    delete_requested = Signal(str, str)

    def __init__(self, table_widget: QTableWidget, parent=None):
        super().__init__(parent)
        self.table = table_widget
        self._setup_table()

    def _setup_table(self):
        columns = ["状态", "应用名称", "本次焦点", "本次运行", "最后一次启动", "首次启动", "总焦点时长", "总运行时长"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.doubleClicked.connect(self._on_double_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.setColumnWidth(1, 250)
        self.table.setAlternatingRowColors(True)

    @staticmethod
    def _create_status_label(color_hex: str):
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

    def refresh(self, apps: List[AppInfo]):
        self.table.setRowCount(0)
        for app in apps:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setCellWidget(row, 0, self._create_status_label("#cbd5e0"))

            name_item = QTableWidgetItem(Path(app.exe_name).stem)
            name_item.setData(Qt.UserRole, app.exe_path)
            self.table.setItem(row, 1, name_item)

            self.table.setItem(row, 2, QTableWidgetItem("-"))
            self.table.setItem(row, 3, QTableWidgetItem("-"))
            self.table.setItem(row, 4, QTableWidgetItem(app.last_start_at))
            self.table.setItem(row, 5, QTableWidgetItem(app.first_seen_at))

            item_focus = QTableWidgetItem(format_seconds_to_text(app.total_focus_seconds))
            item_focus.setData(Qt.UserRole, app.total_focus_seconds)
            self.table.setItem(row, 6, item_focus)

            item_life = QTableWidgetItem(format_seconds_to_text(app.total_lifetime_seconds))
            item_life.setData(Qt.UserRole, app.total_lifetime_seconds)
            self.table.setItem(row, 7, item_life)

    def update_status(self, status_data: dict):
        for row in range(self.table.rowCount()):
            exe_name_item = self.table.item(row, 1)
            if not exe_name_item:
                continue
            exe_path = exe_name_item.data(Qt.UserRole)
            current_status_widget = self.table.cellWidget(row, 0)

            item_total_focus = self.table.item(row, 6)
            item_total_life = self.table.item(row, 7)
            if not item_total_focus or not item_total_life:
                continue

            base_focus = item_total_focus.data(Qt.UserRole) or 0
            base_life = item_total_life.data(Qt.UserRole) or 0

            if exe_path in status_data:
                data = status_data[exe_path]
                status_color = "#48bb78" if data['is_focused'] else "#4299e1"

                self.table.setCellWidget(row, 0, self._create_status_label(status_color))
                self.table.setItem(row, 2, QTableWidgetItem(format_seconds_to_text(data['focus'])))
                self.table.setItem(row, 3, QTableWidgetItem(format_seconds_to_text(data['runtime_seconds'])))

                current_total_focus = base_focus + data['focus']
                item_total_focus.setText(format_seconds_to_text(current_total_focus))

                current_total_life = base_life + data['runtime_seconds']
                item_total_life.setText(format_seconds_to_text(current_total_life))
            else:
                if current_status_widget and current_status_widget.property("status_color") != "#cbd5e0":
                    self.table.setCellWidget(row, 0, self._create_status_label("#cbd5e0"))
                    self.table.setItem(row, 2, QTableWidgetItem("-"))
                    self.table.setItem(row, 3, QTableWidgetItem("-"))
                    item_total_focus.setText(format_seconds_to_text(base_focus))
                    item_total_life.setText(format_seconds_to_text(base_life))

    def _on_double_clicked(self, index):
        row = index.row()
        exe_path = self._get_exe_path_by_row(row)
        if exe_path:
            self.detail_requested.emit(exe_path)

    def _on_context_menu(self, pos):
        menu = QMenu()
        detail_action = menu.addAction("查看详细信息")
        launch_action = menu.addAction("启动此应用")
        delete_action = menu.addAction("不再监控此应用")
        action = menu.exec(self.table.mapToGlobal(pos))

        if action == detail_action:
            idx = self.table.currentIndex()
            if idx.isValid():
                exe_path = self._get_exe_path_by_row(idx.row())
                if exe_path:
                    self.detail_requested.emit(exe_path)
        elif action == launch_action:
            row = self.table.currentRow()
            if row >= 0:
                exe_path = self._get_exe_path_by_row(row)
                if exe_path:
                    self.launch_requested.emit(exe_path)
        elif action == delete_action:
            row = self.table.currentRow()
            if row >= 0:
                exe_name = self.table.item(row, 1).text()
                exe_path = self._get_exe_path_by_row(row)
                if exe_path:
                    reply = QMessageBox.question(
                        self.table, "确认",
                        f"确定移除 {exe_name} 吗？\n历史数据会保留。",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.delete_requested.emit(exe_path, exe_name)

    def _get_exe_path_by_row(self, row: int) -> str:
        item = self.table.item(row, 1)
        if item:
            return item.data(Qt.UserRole)
        return ""
