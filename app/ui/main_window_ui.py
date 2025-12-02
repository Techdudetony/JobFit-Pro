# main_window_ui.py
from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 700)

        # ------------------------------------------------------
        # MENU BAR
        # ------------------------------------------------------
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1100, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        # Tools menu placeholder (real items added in main_window.py)
        self.menuTools = QtWidgets.QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menubar.addMenu(self.menuTools)

        # ------------------------------------------------------
        # CENTRAL WIDGET
        # ------------------------------------------------------
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # IMPORTANT: layout needed or Qt covers menu bar
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)

        # This placeholder is where your real UI gets inserted
        # Your Python-generated UI will populate this area
        self.container = QtWidgets.QWidget(self.centralwidget)
        self.container.setObjectName("container")
        self.verticalLayout.addWidget(self.container)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "JobFit Pro"))
        self.menuTools.setTitle(_translate("MainWindow", "Tools"))
