# app/ui/auth_modal.py
"""
Authentication Modal (Sign In / Sign Up)
----------------------------------------

A frameless authentication modal that:
- Connects to Supabase through the global `auth` singleton.
- Provides Sign In and Sign Up modes.
- Exposes QSS objectNames + properties so global styles apply correctly.

v2 CHANGES:
- Enter on email field → moves focus to password (instead of submitting/doing nothing)
- Enter on password field → submits in sign-in mode, moves to confirm in sign-up mode
- Enter on confirm password field → always submits
"""

import os, sys

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QMessageBox,
    QApplication,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

# Import global auth singleton (NOT the class)
from services.auth_manager import auth

def _get_icon(name: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", "icons", name)


class AuthModal(QDialog):
    """
    Modal authentication dialog.
    Blocks access to the main app until user signs in.
    Supports QSS styling through objectNames + dynamic properties.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ---- QSS HOOK ----
        self.setObjectName("AuthModal")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(420, 430)

        self.mode = "signin"
        self.build_ui()
        self._setup_enter_key()   # ← NEW in v2
        self.switch_mode("signin")

    # ==================================================================
    # UI BUILD
    # ==================================================================
    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card wrapper
        card = QWidget()
        card.setObjectName("authCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # ---------------- TITLE ROW ----------------
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

        # ---------------- EMAIL ----------------
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email address")
        self.input_email.setObjectName("authField")
        layout.addWidget(self.input_email)

        # ---------------- PASSWORD ----------------
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

        # ---------------- CONFIRM PASSWORD (SIGN-UP ONLY) ----------------
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

        # ---------------- SUBMIT BUTTON ----------------
        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.setProperty("variant", "primary")
        self.btn_submit.clicked.connect(self.submit)
        layout.addWidget(self.btn_submit)

        # ---------------- SWITCH MODE LINK ----------------
        self.btn_switch_mode = QPushButton("Create an account")
        self.btn_switch_mode.setFlat(True)
        self.btn_switch_mode.setObjectName("authLink")
        self.btn_switch_mode.clicked.connect(self.switch_modes_clicked)
        layout.addWidget(self.btn_switch_mode, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)

    # ==================================================================
    # ENTER KEY HANDLING  ← NEW in v2
    # ==================================================================
    def _setup_enter_key(self):
        """
        Smart Enter key flow:
          Email    → move focus to password field
          Password → submit (sign-in) OR move focus to confirm (sign-up)
          Confirm  → always submit
        """
        # Tab-like: email → password
        self.input_email.returnPressed.connect(
            lambda: self.input_password.setFocus()
        )
        # Password behaviour depends on mode
        self.input_password.returnPressed.connect(self._password_enter)
        # Confirm always submits
        self.input_password_confirm.returnPressed.connect(self.submit)

    def _password_enter(self):
        """Called when Enter is pressed in the password field."""
        if self.mode == "signup":
            # Don't submit yet — move to confirm field first
            self.input_password_confirm.setFocus()
        else:
            self.submit()

    # ==================================================================
    # MODE SWITCHING
    # ==================================================================
    def switch_mode(self, mode: str):
        self.mode = mode

        if mode == "signin":
            self.lbl_title.setText("Sign In")
            self.btn_submit.setText("Sign In")
            self.btn_switch_mode.setText("Create an account")
            self.confirm_row_widget.hide()
        else:
            self.lbl_title.setText("Create Account")
            self.btn_submit.setText("Sign Up")
            self.btn_switch_mode.setText("Already have an account? Sign In")
            self.confirm_row_widget.show()

    def switch_modes_clicked(self):
        self.switch_mode("signup" if self.mode == "signin" else "signin")

    # ==================================================================
    # PASSWORD VISIBILITY
    # ==================================================================
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

    # ==================================================================
    # EXIT BEHAVIOR
    # ==================================================================
    def confirm_exit(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit Application?")
        msg.setText("Closing authentication will exit JobFit Pro.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.reject()
            app = QApplication.instance()
            if app:
                app.quit()

    # ==================================================================
    # SUPABASE AUTH
    # ==================================================================
    def submit(self):
        email = self.input_email.text().strip()
        pw = self.input_password.text().strip()

        if not email or not pw:
            QMessageBox.warning(self, "Error", "Email and password are required.")
            return

        # SIGN-UP FLOW
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
                self,
                "Account Created",
                "Your account has been created.\n"
                "If email verification is required, please check your inbox.",
            )
            self.switch_mode("signin")
            return

        # SIGN-IN FLOW
        try:
            auth.sign_in(email, pw)
        except Exception as e:
            QMessageBox.critical(self, "Sign In Failed", str(e))
            return

        if not auth.get_user():
            QMessageBox.warning(self, "Error", "Incorrect email or password.")
            return

        self.accept()