import sys
from PySide6.QtWidgets import QApplication
from windows import Mywindow 
from local_database import create_db_and_tables

if __name__ == "__main__":
    print("正在初始化数据库...")
    create_db_and_tables()
    print("数据库初始化完成。")

    app = QApplication(sys.argv)
    window = Mywindow()
    window.show()
    sys.exit(app.exec())
