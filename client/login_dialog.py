import webbrowser

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import (
    QDialog, QPushButton, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout, QWidget
)

from client_api import api_login, LoginStatus, BASE_URL


class LoginWorker(QObject):
    finished = Signal(LoginStatus, str)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        print("LoginWorker: 开始在后台线程中执行登录...")
        status, token = api_login(self.username, self.password)
        self.finished.emit(status, token)
        print("LoginWorker: 任务完成，已发出 finished 信号。")


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.setFixedSize(300, 170)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 10)
        main_layout.setSpacing(8)

        # 输入区域
        input_layout = QHBoxLayout()
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("账号："))
        label_layout.addWidget(QLabel("密码："))
        input_layout.addLayout(label_layout)

        field_layout = QVBoxLayout()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        field_layout.addWidget(self.user_input)
        field_layout.addWidget(self.pass_input)
        input_layout.addLayout(field_layout)
        main_layout.addLayout(input_layout)

        # 按钮区域：确认 | 取消 | 前往注册
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.login_accept = QPushButton("确认")
        self.login_accept.setFixedWidth(60)
        btn_layout.addWidget(self.login_accept)

        self.login_reject = QPushButton("取消")
        self.login_reject.setProperty("secondary", True)
        self.login_reject.setFixedWidth(60)
        btn_layout.addWidget(self.login_reject)

        btn_layout.addStretch()

        self.register_button = QPushButton("前往注册")
        self.register_button.setProperty("secondary", True)
        self.register_button.setFixedWidth(72)
        btn_layout.addWidget(self.register_button)

        main_layout.addLayout(btn_layout)

        # 提示标签
        self.tips_label = QLabel("")
        main_layout.addWidget(self.tips_label)

        # 状态
        self.token = None
        self.username = None
        self.worker_thread = None

        # 信号连接
        self.login_accept.clicked.connect(self.attempt_login)
        self.login_reject.clicked.connect(self.reject)
        self.register_button.clicked.connect(self._open_register_page)

    def attempt_login(self):
        username_text = self.user_input.text()
        password_text = self.pass_input.text()

        if not username_text or not password_text:
            self.tips_label.setText("用户名和密码不能为空。")
            return

        self.login_accept.setEnabled(False)
        self.tips_label.setText("正在登录中，请稍候...")

        self.worker_thread = QThread()
        self.worker = LoginWorker(username_text, password_text)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_login_result)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def handle_login_result(self, status, token):
        print(f"LoginDialog: 已收到后台结果 -> Status: {status}, Token: {'Yes' if token else 'No'}")
        self.login_accept.setEnabled(True)

        if status == LoginStatus.SUCCESS:
            self.token = token
            self.username = self.user_input.text()
            self.accept()
        elif status == LoginStatus.INVALID_CREDENTIALS:
            self.tips_label.setText("用户名或密码不正确。")
        elif status == LoginStatus.NETWORK_ERROR:
            self.tips_label.setText("网络错误，无法连接到服务器。")
        else:
            self.tips_label.setText("发生未知错误，请稍后重试。")

    def _open_register_page(self):
        register_url = f"{BASE_URL}/register"
        webbrowser.open(register_url)

    def closeEvent(self, event):
        if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
            print("LoginDialog: 用户关闭窗口，正在尝试停止仍在运行的登录线程...")
            self.worker_thread.quit()
            self.worker_thread.wait(200)
        super().closeEvent(event)
