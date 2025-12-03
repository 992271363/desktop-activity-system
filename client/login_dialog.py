from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QDialog
from UiFile.Ui_loginLog import Ui_LoginLog
from client_api import api_login, LoginStatus

# 创建一个专门用于执行登录任务的 Worker 类
# 它必须继承自 QObject 才能使用信号与槽机制
class LoginWorker(QObject):
    # 定义一个信号，当登录任务完成时，它会携带结果被发出
    # 参数: (登录状态, token字符串或None)
    finished = Signal(LoginStatus, str)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        """这个函数将在后台线程中执行"""
        print("LoginWorker: 开始在后台线程中执行登录...")
        # 调用已有的、会阻塞的 api_login 函数
        status, token = api_login(self.username, self.password)
        # 任务完成，发出信号，将结果传递回主线程
        self.finished.emit(status, token)
        print("LoginWorker: 任务完成，已发出 finished 信号。")


class LoginDialog(QDialog, Ui_LoginLog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.token = None
        self.username = None
        
        # 用于管理后台线程，防止在对话框关闭后线程仍在运行
        self.worker_thread = None

        self.login_accept.clicked.connect(self.attempt_login)
        self.login_reject.clicked.connect(self.reject)
        self.tips_label.setText("")

    def attempt_login(self):
        """
        当用户点击“确认”时，此方法不再直接执行登录，
        而是设置并启动一个后台线程来完成工作。
        """
        username_text = self.user_input.text()
        password_text = self.pass_input.text()

        if not username_text or not password_text:
            self.tips_label.setText("用户名和密码不能为空。")
            return


        # 立即更新UI，禁用按钮，显示等待提示。
        # 因为这是在主线程中，所以会立刻生效。
        self.login_accept.setEnabled(False)
        self.tips_label.setText("正在登录中，请稍候...")
        
        # 设置并启动后台线程
        self.worker_thread = QThread()
        self.worker = LoginWorker(username_text, password_text)
        
        # 将 worker 移动到新线程中
        self.worker.moveToThread(self.worker_thread)
        
        # 连接信号与槽
        # 1. 当线程启动时，执行 worker 的 run 方法
        self.worker_thread.started.connect(self.worker.run)
        # 2. 当 worker 发出 finished 信号时，调用我们的结果处理函数
        self.worker.finished.connect(self.handle_login_result)
        # 3. 任务完成后，让线程自己退出
        self.worker.finished.connect(self.worker_thread.quit)
        # 4. 线程退出后，清理资源
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        # 启动线程，这将触发上面连接的所有事件
        self.worker_thread.start()

    def handle_login_result(self, status, token):
        """
        这个槽函数在主线程中被调用，用于安全地更新UI。
        """
        print(f"LoginDialog: 已收到后台结果 -> Status: {status}, Token: {'Yes' if token else 'No'}")
        # 无论成功失败，先恢复按钮的可点击状态
        self.login_accept.setEnabled(True)

        if status == LoginStatus.SUCCESS:
            self.token = token
            self.username = self.user_input.text() # 从输入框获取，避免传递
            self.accept() # 登录成功，关闭对话框
        elif status == LoginStatus.INVALID_CREDENTIALS:
            self.tips_label.setText("用户名或密码不正确。")
        elif status == LoginStatus.NETWORK_ERROR:
            self.tips_label.setText("网络错误，无法连接到服务器。")
        else: # LoginStatus.UNKNOWN_ERROR
            self.tips_label.setText("发生未知错误，请稍后重试。")

    def closeEvent(self, event):
        """确保在用户强行关闭对话框时，后台线程也能被妥善停止"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000) # 等待最多1秒让线程结束
        super().closeEvent(event)
