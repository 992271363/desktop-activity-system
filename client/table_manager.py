from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject, QCollator
from PySide6.QtGui import QFontMetrics, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QMessageBox, QWidget, QHBoxLayout, QLabel
)

from typing import List
from utils import format_seconds_to_text
from app_repository import AppInfo
from settings import Settings

_collator = QCollator()
_collator.setCaseSensitivity(Qt.CaseInsensitive)

_NOT_RUNNING = -1
_BASE_TOTAL_ROLE = Qt.UserRole + 100


class StyledHeaderView(QHeaderView):
    _ARROW_COLOR = QColor(0x47, 0x55, 0x69)
    _DIVIDER_COLOR = QColor(0x94, 0xa3, 0xb8)
    _GRIP_ZONE = 6

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)
        self.setMouseTracking(True)

    def _is_on_resizable_edge(self, pos):
        col = self.logicalIndexAt(pos)
        if col < 0:
            return False
        edge_x = self.sectionPosition(col) + self.sectionSize(col)
        return abs(pos.x() - edge_x) <= self._GRIP_ZONE

    def paintSection(self, painter, rect, logicalIndex):
        super().paintSection(painter, rect, logicalIndex)

        if logicalIndex == 1:
            painter.save()
            painter.setPen(QPen(self._DIVIDER_COLOR, 2))
            painter.drawLine(rect.right(), rect.top() + 4, rect.right(), rect.bottom() - 4)
            painter.restore()

        if logicalIndex == self.sortIndicatorSection():
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._ARROW_COLOR)
            order = self.sortIndicatorOrder()
            size = 5
            cx = rect.right() - 14
            cy = rect.center().y()
            if order == Qt.AscendingOrder:
                path = QPainterPath()
                path.moveTo(cx - size, cy + 2)
                path.lineTo(cx + size, cy + 2)
                path.lineTo(cx, cy - size + 2)
                path.closeSubpath()
                painter.drawPath(path)
            else:
                path = QPainterPath()
                path.moveTo(cx - size, cy - 2)
                path.lineTo(cx + size, cy - 2)
                path.lineTo(cx, cy + size - 2)
                path.closeSubpath()
                painter.drawPath(path)
            painter.restore()

    def mouseMoveEvent(self, event):
        if self._is_on_resizable_edge(event.pos()):
            self.setCursor(Qt.SplitHCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)


class SortableTableWidgetItem(QTableWidgetItem):
    _ascending = True

    def __lt__(self, other):
        my_val = self.data(Qt.UserRole)
        other_val = other.data(Qt.UserRole)

        if my_val is not None and other_val is not None:
            my_na = (my_val == _NOT_RUNNING)
            other_na = (other_val == _NOT_RUNNING)
            if my_na != other_na:
                if my_na:
                    return not SortableTableWidgetItem._ascending
                return SortableTableWidgetItem._ascending
            if my_na and other_na:
                return False
            try:
                return float(my_val) < float(other_val)
            except (TypeError, ValueError):
                pass
        return _collator.compare(self.text(), other.text()) < 0


class AppTableManager(QObject):
    detail_requested = Signal(str)
    launch_requested = Signal(str)
    delete_requested = Signal(str, str)
    table_width_hint = Signal(int)

    def __init__(self, table_widget: QTableWidget, parent=None, settings: Settings = None):
        super().__init__(parent)
        self.table = table_widget
        self._settings = settings
        self._setup_table()

    def _setup_table(self):
        columns = ["状态", "应用名称", "本次焦点", "本次运行", "最后一次启动", "首次启动", "总焦点时长", "总运行时长"]
        self.table.setColumnCount(len(columns))

        header = StyledHeaderView(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(header)
        self.table.setHorizontalHeaderLabels(columns)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
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

        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().sortIndicatorChanged.connect(self._on_sort_indicator_changed)
        self.table.horizontalHeader().sortIndicatorChanged.connect(self._save_sort_preference)
        

    @staticmethod
    def _create_status_label(color_hex: str):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
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
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for app in apps:
            row = self.table.rowCount()
            self.table.insertRow(row)

            status_item = SortableTableWidgetItem("")
            status_item.setData(Qt.UserRole, 0)
            self.table.setItem(row, 0, status_item)
            self.table.setCellWidget(row, 0, self._create_status_label("#cbd5e0"))

            name_item = SortableTableWidgetItem(Path(app.exe_name).stem)
            name_item.setData(Qt.UserRole, app.exe_path)
            self.table.setItem(row, 1, name_item)

            item_cur_focus = SortableTableWidgetItem("-")
            item_cur_focus.setData(Qt.UserRole, _NOT_RUNNING)
            self.table.setItem(row, 2, item_cur_focus)

            item_cur_run = SortableTableWidgetItem("-")
            item_cur_run.setData(Qt.UserRole, _NOT_RUNNING)
            self.table.setItem(row, 3, item_cur_run)

            item_last_start = SortableTableWidgetItem(app.last_start_at)
            item_last_start.setData(Qt.UserRole, app.last_start_at_ts or 0)
            self.table.setItem(row, 4, item_last_start)

            item_first_seen = SortableTableWidgetItem(app.first_seen_at)
            item_first_seen.setData(Qt.UserRole, app.first_seen_at_ts or 0)
            self.table.setItem(row, 5, item_first_seen)

            item_focus = SortableTableWidgetItem(format_seconds_to_text(app.total_focus_seconds))
            item_focus.setData(Qt.UserRole, app.total_focus_seconds)
            item_focus.setData(_BASE_TOTAL_ROLE, app.total_focus_seconds)
            self.table.setItem(row, 6, item_focus)

            item_life = SortableTableWidgetItem(format_seconds_to_text(app.total_lifetime_seconds))
            item_life.setData(Qt.UserRole, app.total_lifetime_seconds)
            item_life.setData(_BASE_TOTAL_ROLE, app.total_lifetime_seconds)
            self.table.setItem(row, 7, item_life)

        self._restore_sort()
        self._adjust_name_column_width()
        self._emit_table_width_hint()

    def update_status(self, status_data: dict):
        self.table.setSortingEnabled(False)
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

            base_focus = item_total_focus.data(_BASE_TOTAL_ROLE)
            base_life = item_total_life.data(_BASE_TOTAL_ROLE)

            if base_focus is None:
                base_focus = item_total_focus.data(Qt.UserRole) or 0
            if base_life is None:
                base_life = item_total_life.data(Qt.UserRole) or 0

            if exe_path in status_data:
                data = status_data[exe_path]
                status_color = "#48bb78" if data['is_focused'] else "#4299e1"
                status_val = 2 if data['is_focused'] else 1

                status_item = self.table.item(row, 0)
                if status_item:
                    status_item.setData(Qt.UserRole, status_val)
                self.table.setCellWidget(row, 0, self._create_status_label(status_color))

                item_cur_focus = SortableTableWidgetItem(format_seconds_to_text(data['focus']))
                item_cur_focus.setData(Qt.UserRole, data['focus'])
                self.table.setItem(row, 2, item_cur_focus)

                item_cur_run = SortableTableWidgetItem(format_seconds_to_text(data['runtime_seconds']))
                item_cur_run.setData(Qt.UserRole, data['runtime_seconds'])
                self.table.setItem(row, 3, item_cur_run)

                current_total_focus = base_focus + data['focus']
                item_total_focus.setText(format_seconds_to_text(current_total_focus))
                item_total_focus.setData(Qt.UserRole, current_total_focus)

                current_total_life = base_life + data['runtime_seconds']
                item_total_life.setText(format_seconds_to_text(current_total_life))
                item_total_life.setData(Qt.UserRole, current_total_life)
            else:
                if current_status_widget and current_status_widget.property("status_color") != "#cbd5e0":
                    final_focus = item_total_focus.data(Qt.UserRole)
                    final_life = item_total_life.data(Qt.UserRole)

                    if final_focus is not None:
                        item_total_focus.setData(_BASE_TOTAL_ROLE, final_focus)
                    if final_life is not None:
                        item_total_life.setData(_BASE_TOTAL_ROLE, final_life)

                    status_item = self.table.item(row, 0)
                    if status_item:
                        status_item.setData(Qt.UserRole, 0)
                    self.table.setCellWidget(row, 0, self._create_status_label("#cbd5e0"))

                    item_cur_focus = SortableTableWidgetItem("-")
                    item_cur_focus.setData(Qt.UserRole, _NOT_RUNNING)
                    self.table.setItem(row, 2, item_cur_focus)

                    item_cur_run = SortableTableWidgetItem("-")
                    item_cur_run.setData(Qt.UserRole, _NOT_RUNNING)
                    self.table.setItem(row, 3, item_cur_run)

                    final_focus = item_total_focus.data(_BASE_TOTAL_ROLE) or base_focus
                    final_life = item_total_life.data(_BASE_TOTAL_ROLE) or base_life

                    item_total_focus.setText(format_seconds_to_text(final_focus))
                    item_total_life.setText(format_seconds_to_text(final_life))
                    item_total_focus.setData(Qt.UserRole, final_focus)
                    item_total_life.setData(Qt.UserRole, final_life)
        self.table.setSortingEnabled(True)

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

    def _on_sort_indicator_changed(self, column, order):
        SortableTableWidgetItem._ascending = (order == Qt.AscendingOrder)

    def _save_sort_preference(self, column: int, order):
        if not self._settings:
            return
        self._settings.set("tableSortColumn", column)
        self._settings.set("tableSortOrder", "asc" if order == Qt.AscendingOrder else "desc")

    def _restore_sort(self):
        if not self._settings:
            self.table.setSortingEnabled(True)
            return
        col = self._settings.get("tableSortColumn")
        order_str = self._settings.get("tableSortOrder")
        if col is not None and order_str is not None:
            try:
                col = int(col)
                if 0 <= col < self.table.columnCount():
                    order = Qt.AscendingOrder if order_str == "asc" else Qt.DescendingOrder
                    SortableTableWidgetItem._ascending = (order == Qt.AscendingOrder)
                    self.table.sortItems(col, order)
            except (TypeError, ValueError):
                pass
        self.table.setSortingEnabled(True)

    def _adjust_name_column_width(self):
        name_col = 1

        cell_fm = QFontMetrics(self.table.font())
        header_fm = QFontMetrics(self.table.horizontalHeader().font())

        header_item = self.table.horizontalHeaderItem(name_col)
        header_text = header_item.text() if header_item else "应用名称"

        header_text_width = header_fm.horizontalAdvance(header_text)
        header_min_width = header_text_width + 60

        max_content_width = 0

        for row in range(self.table.rowCount()):
            item = self.table.item(row, name_col)
            if item:
                text_width = cell_fm.horizontalAdvance(item.text())
                max_content_width = max(max_content_width, text_width)

        content_width = max_content_width + 40

        final_width = max(header_min_width, content_width)

        self.table.setColumnWidth(name_col, final_width)

    def _emit_table_width_hint(self):   
        total = 0
        for col in range(self.table.columnCount()):
            total += self.table.columnWidth(col)
        if self.table.verticalScrollBar().isVisible():
            total += self.table.verticalScrollBar().width()
        self.table_width_hint.emit(total+90)
