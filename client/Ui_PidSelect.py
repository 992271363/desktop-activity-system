# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PidSelect.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_desktopActivitySystem(object):
    def setupUi(self, desktopActivitySystem):
        if not desktopActivitySystem.objectName():
            desktopActivitySystem.setObjectName(u"desktopActivitySystem")
        desktopActivitySystem.resize(377, 189)
        self.pushButton_procs = QPushButton(desktopActivitySystem)
        self.pushButton_procs.setObjectName(u"pushButton_procs")
        self.pushButton_procs.setGeometry(QRect(10, 140, 121, 41))
        self.layoutWidget = QWidget(desktopActivitySystem)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(100, 20, 261, 106))
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.proc_name_show = QLabel(self.layoutWidget)
        self.proc_name_show.setObjectName(u"proc_name_show")

        self.verticalLayout.addWidget(self.proc_name_show)

        self.proc_path_show = QLabel(self.layoutWidget)
        self.proc_path_show.setObjectName(u"proc_path_show")

        self.verticalLayout.addWidget(self.proc_path_show)

        self.proc_start_time_show = QLabel(self.layoutWidget)
        self.proc_start_time_show.setObjectName(u"proc_start_time_show")

        self.verticalLayout.addWidget(self.proc_start_time_show)

        self.proc_end_time_show = QLabel(self.layoutWidget)
        self.proc_end_time_show.setObjectName(u"proc_end_time_show")

        self.verticalLayout.addWidget(self.proc_end_time_show)

        self.label_focus_time_show = QLabel(self.layoutWidget)
        self.label_focus_time_show.setObjectName(u"label_focus_time_show")

        self.verticalLayout.addWidget(self.label_focus_time_show)

        self.layoutWidget1 = QWidget(desktopActivitySystem)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(10, 20, 86, 106))
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.proc_name_label = QLabel(self.layoutWidget1)
        self.proc_name_label.setObjectName(u"proc_name_label")
        self.proc_name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_2.addWidget(self.proc_name_label)

        self.proc_path_label = QLabel(self.layoutWidget1)
        self.proc_path_label.setObjectName(u"proc_path_label")
        self.proc_path_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_2.addWidget(self.proc_path_label)

        self.start_time_label = QLabel(self.layoutWidget1)
        self.start_time_label.setObjectName(u"start_time_label")
        self.start_time_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_2.addWidget(self.start_time_label)

        self.end_time_label = QLabel(self.layoutWidget1)
        self.end_time_label.setObjectName(u"end_time_label")
        self.end_time_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_2.addWidget(self.end_time_label)

        self.focus_time_label = QLabel(self.layoutWidget1)
        self.focus_time_label.setObjectName(u"focus_time_label")
        self.focus_time_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_2.addWidget(self.focus_time_label)

        self.login_button = QPushButton(desktopActivitySystem)
        self.login_button.setObjectName(u"login_button")
        self.login_button.setGeometry(QRect(310, 140, 51, 41))
        self.user_label = QLabel(desktopActivitySystem)
        self.user_label.setObjectName(u"user_label")
        self.user_label.setGeometry(QRect(150, 150, 31, 21))
        self.user_show = QLabel(desktopActivitySystem)
        self.user_show.setObjectName(u"user_show")
        self.user_show.setGeometry(QRect(190, 150, 101, 21))

        self.retranslateUi(desktopActivitySystem)

        QMetaObject.connectSlotsByName(desktopActivitySystem)
    # setupUi

    def retranslateUi(self, desktopActivitySystem):
        desktopActivitySystem.setWindowTitle(QCoreApplication.translate("desktopActivitySystem", u"desktopActivitySystem", None))
        self.pushButton_procs.setText(QCoreApplication.translate("desktopActivitySystem", u"\u9009\u62e9\u8fdb\u7a0b", None))
        self.proc_name_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
        self.proc_path_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
        self.proc_start_time_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
        self.proc_end_time_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
        self.label_focus_time_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
        self.proc_name_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u8fdb\u7a0b\u540d\uff1a", None))
        self.proc_path_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u8def\u5f84\uff1a", None))
        self.start_time_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u542f\u52a8\u65f6\u95f4\uff1a", None))
        self.end_time_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u7ed3\u675f\u65f6\u95f4\uff1a", None))
        self.focus_time_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u7a97\u53e3\u505c\u7559\u65f6\u957f\uff1a", None))
        self.login_button.setText(QCoreApplication.translate("desktopActivitySystem", u"\u767b\u5f55", None))
        self.user_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u8d26\u53f7\uff1a", None))
        self.user_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
    # retranslateUi

