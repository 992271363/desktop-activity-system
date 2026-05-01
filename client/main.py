import sys
from PySide6.QtWidgets import QApplication
from windows import Mywindow
from local_database import create_db_and_tables
from styles import MODERN_LIGHT_QSS

if __name__ == "__main__":
    print("正在初始化数据库...")
    create_db_and_tables()
    print("数据库初始化完成。")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(MODERN_LIGHT_QSS)
    window = Mywindow()
    window.show()
    sys.exit(app.exec())
