MODERN_LIGHT_QSS = """
/* =========================================
   Modern Light Theme for PySide6 Desktop Activity System
   ========================================= */

/* ---- 全局基础 ---- */
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #000000;
    background-color: #f8fafc;
}

/* ---- 主窗口 ---- */
QMainWindow {
    background-color: #f1f5f9;
}

QMainWindow::separator {
    background: #e2e8f0;
    width: 2px;
    height: 2px;
}

/* ---- 对话框 ---- */
QDialog {
    background-color: #ffffff;
    border-radius: 8px;
}

/* ---- 按钮 ---- */
QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2563eb;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #cbd5e1;
    color: #94a3b8;
}

/* 次要按钮（取消、关闭等） */
QPushButton[secondary="true"],
DialogButtonBox QPushButton {
    background-color: #f1f5f9;
    color: #000000;
    border: 1px solid #cbd5e1;
    padding: 6px 16px;
    min-height: 28px;
}

QPushButton[secondary="true"]:hover,
QDialogButtonBox QPushButton:hover {
    background-color: #e2e8f0;
    border-color: #94a3b8;
}

QPushButton[secondary="true"]:pressed,
QDialogButtonBox QPushButton:pressed {
    background-color: #cbd5e1;
}

/* 危险/删除按钮 */
QPushButton[danger="true"] {
    background-color: #ef4444;
}

QPushButton[danger="true"]:hover {
    background-color: #dc2626;
}

/* 拾取窗口按钮 */
QPushButton[crosshair="true"] {
    background-color: #f0fdf4;
    color: #16a34a;
    border: 1.5px dashed #86efac;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
    font-weight: 500;
}

QPushButton[crosshair="true"]:hover {
    background-color: #dcfce7;
    border-color: #4ade80;
}

QPushButton[crosshair="true"]:pressed {
    background-color: #bbf7d0;
    border-color: #22c55e;
    border-style: solid;
}

/* ---- 输入框 ---- */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 22px;
    selection-background-color: #3b82f6;
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
}

QLineEdit::placeholder {
    color: #94a3b8;
}

/* ---- 表格 ---- */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    selection-background-color: #dbeafe;
    selection-color: #000000;
    alternate-background-color: #f8fafc;
    outline: none;
}

QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #f1f5f9;
    color: #000000;
}

QTableWidget::item:selected {
    background-color: #bfdbfe;
    color: #000000;
}

QTableWidget::item:hover {
    background-color: #eff6ff;
}

/* ---- 表头 ---- */
QHeaderView::section {
    background-color: #f1f5f9;
    color: #000000;
    font-weight: 600;
    font-size: 12px;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
}

QHeaderView::section:hover {
    background-color: #e2e8f0;
}

QHeaderView::section:last {
    border-right: none;
}

/* ---- 滚动条 ---- */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ---- 菜单 ---- */
QMenu {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px;
    margin: 2px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #eff6ff;
    color: #2563eb;
}

QMenu::separator {
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 8px;
}

/* ---- 标签 ---- */
QLabel,
QDialog QLabel,
QMainWindow QLabel {
    background: transparent;
    color: #000000 !important;
}

/* ---- 进度条 ---- */
QProgressBar {
    border: none;
    border-radius: 3px;
    background-color: #e2e8f0;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}

/* ---- 工具栏 ---- */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 4px 8px;
    spacing: 6px;
}

QToolBar::separator {
    width: 1px;
    background-color: #e2e8f0;
    margin: 4px 6px;
}

/* 工具栏文字按钮（登录/退出等 QAction） */
QToolBar QToolButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
    font-weight: 500;
}

QToolBar QToolButton:hover {
    background-color: #2563eb;
}

QToolBar QToolButton:pressed {
    background-color: #1d4ed8;
}

/* ---- 消息框 ---- */
QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #000000;
    font-size: 13px;
}

/* ---- 分组框/分割线 ---- */
QFrame {
    color: #e2e8f0;
}

/* ---- 状态栏 ---- */
QStatusBar {
    background-color: #f1f5f9;
    color: #333333;
    font-size: 12px;
    border-top: 1px solid #e2e8f0;
}

QStatusBar::item {
    border: none;
}
"""
