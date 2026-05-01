from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,
    QHeaderView, QAbstractItemView
)

from services import get_process_list


class ProcSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("进程列表")
        self.resize(564, 429)
        self.proc_pid = None

        # ---- 纯代码 UI 初始化（原 Ui_ProcListDialog.py 逻辑内联）----
        self.verticalLayout = QVBoxLayout(self)

        self.procTable = QTableWidget()
        self.procTable.setColumnCount(3)
        self.procTable.setHorizontalHeaderLabels(["PID", "进程名", "进程路径"])
        self.verticalLayout.addWidget(self.procTable)

        self.horizontalLayout_2 = QHBoxLayout()
        self.list_brush = QPushButton("刷新")
        self.horizontalLayout_2.addWidget(self.list_brush)
        self.horizontalLayout_2.addSpacerItem(
            QSpacerItem(34, 14, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.lineEdit_search = QLineEdit()
        self.lineEdit_search.setMaximumSize(155, 16777215)
        self.lineEdit_search.setAlignment(Qt.AlignCenter)
        self.lineEdit_search.setPlaceholderText("搜索")
        self.horizontalLayout_2.addWidget(self.lineEdit_search)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel("过长的值可以悬浮鼠标显示")
        self.horizontalLayout.addWidget(self.label)
        self.horizontalLayout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.pushButton_accept = QPushButton("确认")
        self.pushButton_reject = QPushButton("取消")
        self.pushButton_reject.setProperty("secondary", True)
        self.horizontalLayout.addWidget(self.pushButton_accept)
        self.horizontalLayout.addWidget(self.pushButton_reject)
        self.verticalLayout.addLayout(self.horizontalLayout)
        # ---------------------------------------------------------------

        self.lineEdit_search.textChanged.connect(self.populate_process_list)
        self.list_brush.clicked.connect(self.populate_process_list)

        header = self.procTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # PID 自适应
        header.setSectionResizeMode(1, QHeaderView.Interactive)       # 名字可拖动
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # 路径自动拉伸

        self.procTable.setSortingEnabled(True)
        self.procTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.procTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.procTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.procTable.setAlternatingRowColors(True)

        self.pushButton_accept.clicked.connect(self.accept)
        self.pushButton_reject.clicked.connect(self.reject)

        self.populate_process_list()

    def get_selected_proc_info(self):
        selected_rows_indexes = self.procTable.selectionModel().selectedRows()
        if not selected_rows_indexes:
            return None
        row = selected_rows_indexes[0].row()
        exe_name = self.procTable.item(row, 1).text()
        exe_path = self.procTable.item(row, 2).text()
        return (exe_path, exe_name)

    def populate_process_list(self):
        search_term = self.lineEdit_search.text().lower().strip()

        self.procTable.setSortingEnabled(False)
        self.procTable.setRowCount(0)

        processes = get_process_list()

        if not search_term:
            filtered_processes = processes
        else:
            filtered_processes = []
            for proc in processes:
                pid_str = str(proc['pid'])
                name_str = proc['name'].lower()
                path_str = proc['exe'].lower() if proc['exe'] else ""

                if (search_term in pid_str or
                        search_term in name_str or
                        search_term in path_str):
                    filtered_processes.append(proc)

        self.procTable.setRowCount(len(filtered_processes))
        for row, proc_info in enumerate(filtered_processes):
            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.ItemDataRole.DisplayRole, proc_info['pid'])
            pid_item.setData(Qt.ItemDataRole.UserRole, proc_info['pid'])
            pid_item.setToolTip(str(proc_info['pid']))

            name_item = QTableWidgetItem(proc_info['name'])
            name_item.setToolTip(proc_info['name'])

            path_str = proc_info['exe'] or "N/A"
            path_item = QTableWidgetItem(path_str)
            path_item.setToolTip(path_str)

            self.procTable.setItem(row, 0, pid_item)
            self.procTable.setItem(row, 1, name_item)
            self.procTable.setItem(row, 2, path_item)

        self.procTable.setSortingEnabled(True)
