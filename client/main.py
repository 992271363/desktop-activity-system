import sys # 提供命令行参数与退出状态码
from PySide6.QtWidgets import QApplication # Qt应用入口类
from main_window import Mywindow # 自定义主窗口
from local_database import create_db_and_tables # 数据库初始化工具
from styles import MODERN_LIGHT_QSS # 全局QSS样式表
import autostart

if __name__ == "__main__": # 程序主入口
    print("正在初始化数据库...") # 状态提示
    create_db_and_tables() # 若数据库或表不存在则创建
    print("数据库初始化完成。") # 完成提示

    if autostart.is_available():
        autostart.fix_path()

    app = QApplication(sys.argv) # 创建Qt应用实例
    app.setStyle("Fusion") # 设置跨平台统一风格
    app.setStyleSheet(MODERN_LIGHT_QSS) # 应用自定义样式
    window = Mywindow() # 实例化主窗口
    window.show() # 显示窗口
    sys.exit(app.exec()) # 进入事件循环并返回退出码