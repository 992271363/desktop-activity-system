# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Main.ui'
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
from PySide6.QtWidgets import (QApplication, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QWidget)

class Ui_desktopActivitySystem(object):
    def setupUi(self, desktopActivitySystem):
        if not desktopActivitySystem.objectName():
            desktopActivitySystem.setObjectName(u"desktopActivitySystem")
        desktopActivitySystem.resize(925, 382)
        self.pushButton_procs = QPushButton(desktopActivitySystem)
        self.pushButton_procs.setObjectName(u"pushButton_procs")
        self.pushButton_procs.setGeometry(QRect(10, 330, 121, 41))
        self.login_button = QPushButton(desktopActivitySystem)
        self.login_button.setObjectName(u"login_button")
        self.login_button.setGeometry(QRect(140, 330, 51, 41))
        self.user_label = QLabel(desktopActivitySystem)
        self.user_label.setObjectName(u"user_label")
        self.user_label.setGeometry(QRect(200, 340, 31, 21))
        self.user_show = QLabel(desktopActivitySystem)
        self.user_show.setObjectName(u"user_show")
        self.user_show.setGeometry(QRect(240, 340, 101, 21))
        self.tableWidget = QTableWidget(desktopActivitySystem)
        if (self.tableWidget.columnCount() < 10):
            self.tableWidget.setColumnCount(10)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(8, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(9, __qtablewidgetitem9)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setGeometry(QRect(10, 10, 901, 311))

        self.retranslateUi(desktopActivitySystem)

        QMetaObject.connectSlotsByName(desktopActivitySystem)
    # setupUi

    def retranslateUi(self, desktopActivitySystem):
        desktopActivitySystem.setWindowTitle(QCoreApplication.translate("desktopActivitySystem", u"desktopActivitySystem", None))
        self.pushButton_procs.setText(QCoreApplication.translate("desktopActivitySystem", u"\u6dfb\u52a0\u8fdb\u7a0b", None))
        self.login_button.setText(QCoreApplication.translate("desktopActivitySystem", u"\u767b\u5f55", None))
        self.user_label.setText(QCoreApplication.translate("desktopActivitySystem", u"\u8d26\u53f7\uff1a", None))
        self.user_show.setText(QCoreApplication.translate("desktopActivitySystem", u"N/A", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("desktopActivitySystem", u"\u540d\u5b57", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("desktopActivitySystem", u"\u8fdb\u7a0b", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("desktopActivitySystem", u"\u603b\u8fd0\u884c\u65f6\u957f", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("desktopActivitySystem", u"\u603b\u7126\u70b9\u65f6\u957f", None));
        ___qtablewidgetitem4 = self.tableWidget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("desktopActivitySystem", u"\u672c\u6b21\u8fd0\u884c\u65f6\u957f", None));
        ___qtablewidgetitem5 = self.tableWidget.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("desktopActivitySystem", u"\u672c\u6b21\u7126\u70b9\u65f6\u957f", None));
        ___qtablewidgetitem6 = self.tableWidget.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("desktopActivitySystem", u"\u6700\u540e\u4e00\u6b21\u542f\u52a8", None));
        ___qtablewidgetitem7 = self.tableWidget.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("desktopActivitySystem", u"\u6700\u540e\u4e00\u6b21\u7ed3\u675f", None));
        ___qtablewidgetitem8 = self.tableWidget.horizontalHeaderItem(8)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("desktopActivitySystem", u"\u9996\u6b21\u542f\u52a8", None));
    # retranslateUi

