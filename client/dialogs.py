from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QFrame, QDialogButtonBox,
    QVBoxLayout, QProgressBar
)
from PySide6.QtGui import QFont

from local_models import WatchedApplication
from utils import format_seconds_to_text


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

        def fmt_time(dt):
            return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "从未"

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


class ClosingDialog(QDialog):
    """关闭时的提示对话框，显示保存进度"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在关闭")
        self.setFixedSize(320, 140)
        # 去掉问号按钮，保留关闭按钮但禁用
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)  # 模态对话框

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        self.status_label = QLabel("正在保存数据，请稍候...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)

        # 无限循环进度条（表示正在处理）
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)  # 0-0 表示无限循环模式
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)

    def set_status(self, text: str):
        """更新状态文字"""
        self.status_label.setText(text)
        # 强制立即重绘，避免卡顿不更新
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
