import sys  # 提供命令行参数与退出状态码
import os  # 提供路径拼接等系统相关功能
import tempfile  # 获取系统临时目录，用于存放锁文件

from PySide6.QtWidgets import QApplication  # Qt 应用入口类
from PySide6.QtCore import QLockFile  # Qt 提供的跨平台文件锁工具

from main_window import Mywindow  # 自定义主窗口
from local_database import create_db_and_tables  # 数据库初始化工具
from settings import Settings  # 配置读取工具
from theme import apply_theme  # 主题应用工具
import autostart  # 开机自启动相关工具


# ============================================================
# 程序唯一性锁文件名
#
# 注意：
# 1. 这个名字应该尽量唯一，避免和其他软件冲突
# 2. 建议使用你的软件英文名，例如 "my_app.lock"
# 3. 不要每次启动都随机生成，否则就无法判断是否重复启动
# ============================================================
APP_LOCK_NAME = "my_unique_app.lock"


def check_single_instance():
    """
    检测当前程序是否已经有实例正在运行。

    返回值：
        QLockFile 对象：
            表示加锁成功，当前程序可以继续运行。

        None：
            表示加锁失败，说明程序可能已经在运行。

    重要说明：
        返回的 lock_file 对象必须一直被变量保存着。
        如果这个对象被销毁，锁也会被释放，唯一性检测就会失效。
    """

    # 获取系统临时目录
    #
    # Windows 示例：
    #   C:\\Users\\用户名\\AppData\\Local\\Temp
    #
    # macOS / Linux 示例：
    #   /tmp
    temp_dir = tempfile.gettempdir()

    # 拼接锁文件完整路径
    #
    # 例如：
    #   C:\\Users\\用户名\\AppData\\Local\\Temp\\my_unique_app.lock
    lock_path = os.path.join(temp_dir, APP_LOCK_NAME)

    # 创建 Qt 文件锁对象
    lock_file = QLockFile(lock_path)

    # 设置锁文件的过期时间，单位是毫秒
    #
    # 这里设置为 0，表示不自动认为旧锁过期。
    #
    # 如果你的程序异常崩溃后无法再次启动，
    # 可以改成 30000，也就是 30 秒后认为旧锁失效。
    #
    # 示例：
    #   lock_file.setStaleLockTime(30000)
    lock_file.setStaleLockTime(0)

    # 尝试加锁
    #
    # tryLock(100) 表示最多等待 100 毫秒。
    #
    # 如果返回 True：
    #   说明当前没有其他实例运行，当前程序获得锁。
    #
    # 如果返回 False：
    #   说明锁已被其他进程占用，程序已经在运行。
    if not lock_file.tryLock(100):
        return None

    # 加锁成功，返回锁对象
    return lock_file


if __name__ == "__main__":
    # ========================================================
    # 第一步：检测程序是否已经启动
    #
    # 这一步建议放在最前面。
    # 这样可以避免重复启动时再次初始化数据库、创建窗口等。
    # ========================================================
    single_instance_lock = check_single_instance()

    if single_instance_lock is None:
        print("程序已经在运行，禁止重复启动。")
        sys.exit(0)

    # ========================================================
    # 第二步：初始化数据库
    #
    # 如果数据库或表不存在，则创建。
    # 因为前面已经做过唯一性检测，所以不会有多个实例同时初始化数据库。
    # ========================================================
    print("正在初始化数据库...")
    create_db_and_tables()
    print("数据库初始化完成。")

    # ========================================================
    # 第三步：修复开机自启动路径
    #
    # 如果当前系统支持开机自启动，则检查并修复启动路径。
    # ========================================================
    if autostart.is_available():
        autostart.fix_path()

    # ========================================================
    # 第四步：创建 Qt 应用实例
    #
    # sys.argv 用于接收命令行参数。
    # QApplication 是所有 Qt Widgets 程序的入口。
    # ========================================================
    app = QApplication(sys.argv)

    # 设置 Qt 内置 Fusion 风格
    #
    # Fusion 是 Qt 提供的跨平台统一风格，
    # 可以让 Windows / macOS / Linux 上的界面观感更一致。
    app.setStyle("Fusion")

    # ========================================================
    # 第五步：应用主题
    #
    # 从 Settings 中读取 themeMode。
    #
    # 如果用户没有设置主题，则默认使用 "system"，
    # 也就是跟随系统主题。
    # ========================================================
    apply_theme(Settings().get("themeMode", "system"))

    # ========================================================
    # 第六步：创建并显示主窗口
    # ========================================================
    window = Mywindow()
    window.show()

    # ========================================================
    # 第七步：进入 Qt 事件循环
    #
    # app.exec() 会阻塞在这里，直到用户关闭程序。
    # sys.exit() 会把 Qt 程序退出码返回给系统。
    #
    # 注意：
    # single_instance_lock 变量必须一直存在到程序结束。
    # 只要这个变量还在，程序唯一性锁就不会被释放。
    # ========================================================
    sys.exit(app.exec())