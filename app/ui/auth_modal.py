# app/ui/auth_modal.py
"""
Authentication Modal (Sign In / Sign Up)
----------------------------------------
v2 CHANGES:
- Enter key flow: email → password → confirm/submit
- Remember Me checkbox → passes remember_me=True to auth.sign_in()
"""

import os, sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QWidget, QMessageBox, QApplication,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from services.auth_manager import auth


def _get_icon(name: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", "icons", name)


class AuthModal(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AuthModal")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(420, 460)
        self.mode = "signin"
        self.build_ui()
        self._setup_enter_key()
        self.switch_mode("signin")

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("authCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        self.lbl_title = QLabel("Sign In")
        self.lbl_title.setObjectName("authTitle")
        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon(_get_icon("close.svg")))
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setProperty("variant", "icon")
        self.btn_close.clicked.connect(self.confirm_exit)
        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        title_row.addWidget(self.btn_close)
        layout.addLayout(title_row)

        # Email
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email address")
        self.input_email.setObjectName("authField")
        layout.addWidget(self.input_email)

        # Password
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Password")
        self.input_password.setObjectName("authField")
        self.btn_toggle_pw = QPushButton()
        self.btn_toggle_pw.setIcon(QIcon(_get_icon("not_visible.svg")))
        self.btn_toggle_pw.setFixedSize(32, 32)
        self.btn_toggle_pw.setProperty("variant", "icon")
        self.btn_toggle_pw.clicked.connect(self.toggle_password)
        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)
        pw_row.addWidget(self.input_password)
        pw_row.addWidget(self.btn_toggle_pw)
        layout.addLayout(pw_row)

        # Confirm password (sign-up only)
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setPlaceholderText("Confirm password")
        self.input_password_confirm.setObjectName("authField")
        self.btn_toggle_confirm = QPushButton()
        self.btn_toggle_confirm.setIcon(QIcon(_get_icon("not_visible.svg")))
        self.btn_toggle_confirm.setFixedSize(32, 32)
        self.btn_toggle_confirm.setProperty("variant", "icon")
        self.btn_toggle_confirm.clicked.connect(self.toggle_password_confirm)
        confirm_row = QHBoxLayout()
        confirm_row.setSpacing(8)
        confirm_row.addWidget(self.input_password_confirm)
        confirm_row.addWidget(self.btn_toggle_confirm)
        self.confirm_row_widget = QWidget()
        self.confirm_row_widget.setLayout(confirm_row)
        self.confirm_row_widget.setObjectName("confirmRow")
        layout.addWidget(self.confirm_row_widget)

        # Remember Me (sign-in only)
        self.chk_remember_me = QCheckBox("Remember me")
        self.chk_remember_me.setObjectName("rememberMeCheckbox")
        layout.addWidget(self.chk_remember_me)

        # Submit
        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.setProperty("variant", "primary")
        self.btn_submit.clicked.connect(self.submit)
        layout.addWidget(self.btn_submit)

        # Switch mode link
        self.btn_switch_mode = QPushButton("Create an account")
        self.btn_switch_mode.setFlat(True)
        self.btn_switch_mode.setObjectName("authLink")
        self.btn_switch_mode.clicked.connect(self.switch_modes_clicked)
        layout.addWidget(self.btn_switch_mode, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)

    def _setup_enter_key(self):
        self.input_email.returnPressed.connect(lambda: self.input_password.setFocus())
        self.input_password.returnPressed.connect(self._password_enter)
        self.input_password_confirm.returnPressed.connect(self.submit)

    def _password_enter(self):
        if self.mode == "signup":
            self.input_password_confirm.setFocus()
        else:
            self.submit()

    def switch_mode(self, mode: str):
        self.mode = mode
        if mode == "signin":
            self.lbl_title.setText("Sign In")
            self.btn_submit.setText("Sign In")
            self.btn_switch_mode.setText("Create an account")
            self.confirm_row_widget.hide()
            self.chk_remember_me.show()
        else:
            self.lbl_title.setText("Create Account")
            self.btn_submit.setText("Sign Up")
            self.btn_switch_mode.setText("Already have an account? Sign In")
            self.confirm_row_widget.show()
            self.chk_remember_me.hide()

    def switch_modes_clicked(self):
        self.switch_mode("signup" if self.mode == "signin" else "signin")

    def toggle_password(self):
        if self.input_password.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pw.setIcon(QIcon(_get_icon("visible.svg")))
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pw.setIcon(QIcon(_get_icon("not_visible.svg")))

    def toggle_password_confirm(self):
        if self.input_password_confirm.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_confirm.setIcon(QIcon(_get_icon("visible.svg")))
        else:
            self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_confirm.setIcon(QIcon(_get_icon("not_visible.svg")))

    def confirm_exit(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit Application?")
        msg.setText("Closing authentication will exit JobFit Pro.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.reject()
            app = QApplication.instance()
            if app:
                app.quit()

    def submit(self):
        email = self.input_email.text().strip()
        pw = self.input_password.text().strip()

        if not email or not pw:
            QMessageBox.warning(self, "Error", "Email and password are required.")
            return

        if self.mode == "signup":
            confirm = self.input_password_confirm.text().strip()
            if pw != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
            try:
                auth.sign_up(email, pw)
            except Exception as e:
                QMessageBox.critical(self, "Sign Up Failed", str(e))
                return
            QMessageBox.information(
                self, "Account Created",
                "Your account has been created.\n"
                "If email verification is required, please check your inbox.",
            )
            self.switch_mode("signin")
            return

        # Sign-in — pass remember_me to auth manager
        remember_me = self.chk_remember_me.isChecked()
        try:
            auth.sign_in(email, pw, remember_me=remember_me)
        except Exception as e:
            QMessageBox.critical(self, "Sign In Failed", str(e))
            return

        if not auth.get_user():
            QMessageBox.warning(self, "Error", "Incorrect email or password.")
            return

        self.accept()