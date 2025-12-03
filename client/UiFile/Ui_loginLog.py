# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'loginLog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_LoginLog(object):
    def setupUi(self, LoginLog):
        if not LoginLog.objectName():
            LoginLog.setObjectName(u"LoginLog")
        LoginLog.resize(296, 168)
        self.login_reject = QPushButton(LoginLog)
        self.login_reject.setObjectName(u"login_reject")
        self.login_reject.setGeometry(QRect(151, 90, 75, 24))
        self.login_accept = QPushButton(LoginLog)
        self.login_accept.setObjectName(u"login_accept")
        self.login_accept.setGeometry(QRect(70, 90, 75, 24))
        self.tips_label = QLabel(LoginLog)
        self.tips_label.setObjectName(u"tips_label")
        self.tips_label.setGeometry(QRect(30, 130, 241, 16))
        self.widget = QWidget(LoginLog)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(33, 22, 231, 52))
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.user_label = QLabel(self.widget)
        self.user_label.setObjectName(u"user_label")

        self.verticalLayout.addWidget(self.user_label)

        self.pass_label = QLabel(self.widget)
        self.pass_label.setObjectName(u"pass_label")

        self.verticalLayout.addWidget(self.pass_label)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.user_input = QLineEdit(self.widget)
        self.user_input.setObjectName(u"user_input")

        self.verticalLayout_2.addWidget(self.user_input)

        self.pass_input = QLineEdit(self.widget)
        self.pass_input.setObjectName(u"pass_input")
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.verticalLayout_2.addWidget(self.pass_input)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.retranslateUi(LoginLog)

        QMetaObject.connectSlotsByName(LoginLog)
    # setupUi

    def retranslateUi(self, LoginLog):
        LoginLog.setWindowTitle(QCoreApplication.translate("LoginLog", u"Dialog", None))
        self.login_reject.setText(QCoreApplication.translate("LoginLog", u"\u53d6\u6d88", None))
        self.login_accept.setText(QCoreApplication.translate("LoginLog", u"\u786e\u8ba4", None))
        self.tips_label.setText("")
        self.user_label.setText(QCoreApplication.translate("LoginLog", u"\u8d26\u53f7\uff1a", None))
        self.pass_label.setText(QCoreApplication.translate("LoginLog", u"\u5bc6\u7801\uff1a", None))
        self.pass_input.setText("")
    # retranslateUi

