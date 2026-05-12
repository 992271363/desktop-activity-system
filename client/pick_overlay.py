import os
import ctypes
import ctypes.wintypes

import win32gui
import win32con
import win32api
import win32process

from PySide6.QtCore import Qt, Signal, QTimer, QRect, QObject
from PySide6.QtGui import QPainter, QPen, QColor, QCursor
from PySide6.QtWidgets import QWidget, QApplication, QPushButton


def enable_dpi_awareness():
    """
    最好在 QApplication 创建之前调用。
    如果你的 main.py 已经更早创建了 QApplication，
    请把这个函数挪到 main.py 最开头执行。
    """
    try:
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )
        return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


enable_dpi_awareness()


class PickButton(QPushButton):
    pick_requested = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFocusPolicy(Qt.NoFocus)
        self.setContextMenuPolicy(Qt.NoContextMenu)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setDown(False)
            self.clearFocus()

            try:
                self.releaseMouse()
            except Exception:
                pass

            event.accept()
            self.pick_requested.emit()
            return

        if event.button() == Qt.RightButton:
            event.accept()
            return

        event.accept()

    def mouseReleaseEvent(self, event):
        self.setDown(False)
        event.accept()

    def contextMenuEvent(self, event):
        event.accept()


class PickOverlayPane(QWidget):
    _BG_COLOR = QColor(0, 0, 0, 40)
    _CROSS_COLOR = QColor(255, 255, 255, 180)
    _HIGHLIGHT_COLOR = QColor(59, 130, 246, 200)
    _HIGHLIGHT_FILL = QColor(59, 130, 246, 30)

    def __init__(self, manager, screen):
        super().__init__(None)

        self.manager = manager
        self.screen = screen

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setContextMenuPolicy(Qt.NoContextMenu)

        self._apply_screen_geometry()

    def _apply_screen_geometry(self):
        self.setGeometry(self.screen.geometry())

    def showEvent(self, event):
        super().showEvent(event)

        self._apply_screen_geometry()

        self.raise_()
        self.activateWindow()
        self.repaint()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.manager.request_cancel_by_right_button()
            event.accept()
            return

        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.manager.request_cancel_by_right_button()
            event.accept()
            return

        event.accept()

    def contextMenuEvent(self, event):
        self.manager.request_cancel_by_right_button()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.manager.cancel()
            return

        event.accept()

    def _monitor_rect_physical(self):
        """
        当前 pane 对应屏幕的物理像素矩形。
        """
        geo = self.screen.geometry()
        center = geo.center()

        ratio = self.screen.devicePixelRatio() or 1.0

        physical_point = (
            int(round(center.x() * ratio)),
            int(round(center.y() * ratio)),
        )

        try:
            monitor = win32api.MonitorFromPoint(
                physical_point,
                win32con.MONITOR_DEFAULTTONEAREST,
            )
            info = win32api.GetMonitorInfo(monitor)
            return info["Monitor"]
        except Exception:
            left = int(round(geo.x() * ratio))
            top = int(round(geo.y() * ratio))
            right = int(round((geo.x() + geo.width()) * ratio))
            bottom = int(round((geo.y() + geo.height()) * ratio))
            return left, top, right, bottom

    def _physical_point_to_local(self, x, y):
        """
        把物理像素坐标转换成当前 pane 内部的 Qt 逻辑坐标。
        """
        ratio = self.screen.devicePixelRatio() or 1.0
        monitor_left, monitor_top, _, _ = self._monitor_rect_physical()

        local_x = int(round((x - monitor_left) / ratio))
        local_y = int(round((y - monitor_top) / ratio))
        return local_x, local_y

    def _physical_rect_to_local(self, rect):
        """
        把物理像素矩形转换成当前 pane 内部的 Qt 逻辑矩形。
        """
        left, top, right, bottom = rect
        ratio = self.screen.devicePixelRatio() or 1.0
        monitor_left, monitor_top, _, _ = self._monitor_rect_physical()

        x = int(round((left - monitor_left) / ratio))
        y = int(round((top - monitor_top) / ratio))
        w = int(round((right - left) / ratio))
        h = int(round((bottom - top) / ratio))
        return x, y, w, h

    @staticmethod
    def _intersect_rect(a, b):
        left = max(a[0], b[0])
        top = max(a[1], b[1])
        right = min(a[2], b[2])
        bottom = min(a[3], b[3])

        if right <= left or bottom <= top:
            return None

        return left, top, right, bottom

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), self._BG_COLOR)

        mouse_x, mouse_y = self.manager.mouse_pos_physical
        monitor_rect = self._monitor_rect_physical()
        monitor_left, monitor_top, monitor_right, monitor_bottom = monitor_rect

        local_mouse_x, local_mouse_y = self._physical_point_to_local(
            mouse_x,
            mouse_y,
        )

        painter.setPen(QPen(self._CROSS_COLOR, 1))

        if monitor_left <= mouse_x < monitor_right:
            painter.drawLine(local_mouse_x, 0, local_mouse_x, self.height())

        if monitor_top <= mouse_y < monitor_bottom:
            painter.drawLine(0, local_mouse_y, self.width(), local_mouse_y)

        target_hwnd = self.manager.target_hwnd

        if target_hwnd:
            try:
                target_rect = self.manager.get_window_frame_rect_physical(
                    target_hwnd
                )
                visible_part = self._intersect_rect(target_rect, monitor_rect)

                if visible_part:
                    x, y, w, h = self._physical_rect_to_local(visible_part)
                    painter.fillRect(x, y, w, h, self._HIGHLIGHT_FILL)
                    painter.setPen(QPen(self._HIGHLIGHT_COLOR, 3))
                    painter.drawRect(x, y, w, h)

            except Exception:
                pass

        painter.end()


class PickOverlay(QObject):
    window_picked = Signal(int)
    cancelled = Signal()

    _VK_LBUTTON = 0x01
    _VK_RBUTTON = 0x02
    _VK_ESCAPE = 0x1B

    def __init__(self, parent=None):
        super().__init__(parent)

        self._own_pid = os.getpid()

        self._closed = False
        self._right_cancel_pending = False

        self.target_hwnd = None
        self.mouse_pos_physical = win32api.GetCursorPos()

        self._started_with_left_down = self._is_left_down()
        self._start_pos_qt = QCursor.pos()
        self._drag_mode = False

        self._waiting_for_pick_press = not self._started_with_left_down
        self._pick_press_seen = False

        self._panes = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def show(self):
        self._create_panes()
        self._tick()

        for pane in self._panes:
            pane.show()
            pane.raise_()
            pane.repaint()

    def close(self):
        self._close_panes()

    def _create_panes(self):
        self._close_panes()

        for screen in QApplication.screens():
            pane = PickOverlayPane(self, screen)
            self._panes.append(pane)

    def _close_panes(self):
        for pane in self._panes:
            try:
                pane.close()
                pane.deleteLater()
            except Exception:
                pass

        self._panes = []

    def _is_left_down(self):
        return bool(win32api.GetAsyncKeyState(self._VK_LBUTTON) & 0x8000)

    def _is_right_down(self):
        return bool(win32api.GetAsyncKeyState(self._VK_RBUTTON) & 0x8000)

    def _is_escape_down(self):
        return bool(win32api.GetAsyncKeyState(self._VK_ESCAPE) & 0x8000)

    def _tick(self):
        if self._closed:
            return

        if self._is_escape_down():
            self.cancel()
            return

        self._refresh_target()
        self._poll_mouse_state()

        for pane in self._panes:
            pane.update()

    def _refresh_target(self):
        self.mouse_pos_physical = win32api.GetCursorPos()
        x, y = self.mouse_pos_physical

        hwnd = self._find_window_under_physical_point(x, y)

        if hwnd != self.target_hwnd:
            self.target_hwnd = hwnd

    def _find_window_under_physical_point(self, x, y):
        """
        使用物理像素坐标做命中检测。
        这部分不依赖 Qt 的逻辑坐标，因此不会被混合 DPI 缩放影响。
        """
        own_pid = self._own_pid
        pane_hwnds = {int(pane.winId()) for pane in self._panes}
        found = []

        def enum_proc(hwnd, _):
            if hwnd in pane_hwnds:
                return True

            if not win32gui.IsWindowVisible(hwnd):
                return True

            if self.is_cloaked(hwnd):
                return True

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == own_pid:
                    return True
            except Exception:
                pass

            try:
                rect = self.get_window_frame_rect_physical(hwnd)
            except Exception:
                return True

            left, top, right, bottom = rect

            if right <= left or bottom <= top:
                return True

            if left <= x < right and top <= y < bottom:
                found.append(hwnd)
                return False

            return True

        win32gui.EnumWindows(enum_proc, None)

        if not found:
            return None

        hwnd = found[0]

        root = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
        if root and root not in pane_hwnds:
            try:
                _, root_pid = win32process.GetWindowThreadProcessId(root)
                if root_pid == own_pid:
                    return None
            except Exception:
                pass

            return root

        return hwnd

    def is_cloaked(self, hwnd):
        try:
            DWMWA_CLOAKED = 14
            cloaked = ctypes.c_int(0)

            result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
                hwnd,
                DWMWA_CLOAKED,
                ctypes.byref(cloaked),
                ctypes.sizeof(cloaked),
            )

            return result == 0 and cloaked.value != 0

        except Exception:
            return False

    def get_window_frame_rect_physical(self, hwnd):
        """
        返回窗口可见边界的物理像素坐标。
        """
        try:
            DWMWA_EXTENDED_FRAME_BOUNDS = 9
            rect = ctypes.wintypes.RECT()

            result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
                hwnd,
                DWMWA_EXTENDED_FRAME_BOUNDS,
                ctypes.byref(rect),
                ctypes.sizeof(rect),
            )

            if result == 0:
                return rect.left, rect.top, rect.right, rect.bottom

        except Exception:
            pass

        return win32gui.GetWindowRect(hwnd)

    def request_cancel_by_right_button(self):
        if self._closed:
            return

        self._right_cancel_pending = True
        self.target_hwnd = None

        for pane in self._panes:
            pane.update()

    def _poll_mouse_state(self):
        right_down = self._is_right_down()

        if right_down:
            self.request_cancel_by_right_button()
            return

        if self._right_cancel_pending:
            self.cancel()
            return

        left_down = self._is_left_down()

        if self._started_with_left_down:
            moved = (
                QCursor.pos() - self._start_pos_qt
            ).manhattanLength() >= QApplication.startDragDistance()

            if left_down:
                if moved:
                    self._drag_mode = True
                return

            if self._drag_mode:
                self._finish_pick()
                return

            self._started_with_left_down = False
            self._waiting_for_pick_press = True
            self._pick_press_seen = False
            return

        if self._waiting_for_pick_press:
            if left_down:
                self._pick_press_seen = True
                self._waiting_for_pick_press = False
            return

        if self._pick_press_seen and not left_down:
            self._finish_pick()

    def _finish_pick(self):
        if self._closed:
            return

        self._closed = True
        self._timer.stop()

        hwnd = self.target_hwnd
        self._close_panes()

        if hwnd:
            self.window_picked.emit(int(hwnd))

    def cancel(self):
        if self._closed:
            return

        self._closed = True
        self._timer.stop()

        self._close_panes()
        self.cancelled.emit()
