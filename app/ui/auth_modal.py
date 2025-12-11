"""
AuthModal
----------------------

Handles all user-facing authentication:
- Sign In
- Sign Up
- Password visibility toggles
- Validation
- Modal gating of application startup

This file only handles UI + validation.
Actual authentication calls are delegated to AuthManager.
"""

import os
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from services.auth_manager import auth


ICON = lambda name: os.path.join(os.getcwd(), "assets", "icons", name)


class AuthModal(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup
        self.setObjectName("AuthModal")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(420, 440)

        # Current mode: "signin" or "signup"
        self.mode = "signin"

        # Build UI + initialize behavior
        self._build_ui()
        self._setup_enter_key()
        self.switch_mode("signin")

    # ==================================================================
    # UI Construction
    # ==================================================================
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setObjectName("authCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # ---------------- TITLE + CLOSE BUTTON ----------------
        header = QHBoxLayout()
        self.lbl_title = QLabel("Sign In")
        self.lbl_title.setObjectName("authTitle")

        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon(ICON("close.svg")))
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setProperty("variant", "icon")
        self.btn_close.clicked.connect(self._close_app)

        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(self.btn_close)

        layout.addLayout(header)

        # ---------------- EMAIL ----------------
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email address")
        self.input_email.setObjectName("authField")
        layout.addWidget(self.input_email)

        # ---------------- PASSWORD ----------------
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Password")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setObjectName("authField")

        self.btn_toggle_pw = QPushButton()
        self.btn_toggle_pw.setIcon(QIcon(ICON("not_visible.svg")))
        self.btn_toggle_pw.setFixedSize(32, 32)
        self.btn_toggle_pw.setProperty("variant", "icon")
        self.btn_toggle_pw.clicked.connect(self._toggle_password)

        pw_row = QHBoxLayout()
        pw_row.addWidget(self.input_password)
        pw_row.addWidget(self.btn_toggle_pw)
        layout.addLayout(pw_row)

        # ---------------- CONFIRM PASSWORD (SIGN UP ONLY) ----------------
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setPlaceholderText("Confirm password")
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setObjectName("authField")

        self.btn_toggle_confirm = QPushButton()
        self.btn_toggle_confirm.setIcon(QIcon(ICON("not_visible.svg")))
        self.btn_toggle_confirm.setFixedSize(32, 32)
        self.btn_toggle_confirm.setProperty("variant", "icon")
        self.btn_toggle_confirm.clicked.connect(self._toggle_password_confirm)

        confirm_row = QHBoxLayout()
        confirm_row.addWidget(self.input_password_confirm)
        confirm_row.addWidget(self.btn_toggle_confirm)

        self.confirm_row_widget = QWidget()
        self.confirm_row_widget.setLayout(confirm_row)
        layout.addWidget(self.confirm_row_widget)

        # ---------------- SUBMIT BUTTON ----------------
        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.setProperty("variant", "primary")
        self.btn_submit.clicked.connect(self.submit)
        layout.addWidget(self.btn_submit)

        # ---------------- SWITCH MODE LINK ----------------
        self.btn_switch_mode = QPushButton("Create an account")
        self.btn_switch_mode.setObjectName("authLink")
        self.btn_switch_mode.clicked.connect(self._switch_modes_clicked)
        layout.addWidget(self.btn_switch_mode, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)

    # ==================================================================
    # Enter Key Behavior
    # ==================================================================
    def _setup_enter_key(self):
        """Pressing ENTER submits the form."""
        for w in (self.input_email, self.input_password, self.input_password_confirm):
            w.returnPressed.connect(self.submit)

    # ==================================================================
    # Mode Switching
    # ==================================================================
    def switch_mode(self, mode: str):
        """Switch between Sign In and Sign Up modes."""
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

    def _switch_modes_clicked(self):
        self.switch_mode("signup" if self.mode == "signin" else "signin")

    # ==================================================================
    # Password Toggle Behavior
    # ==================================================================
    def _toggle_password(self):
        mode = self.input_password.echoMode()
        is_hidden = mode == QLineEdit.EchoMode.Password
        self.input_password.setEchoMode(
            QLineEdit.EchoMode.Normal if is_hidden else QLineEdit.EchoMode.Password
        )
        self.btn_toggle_pw.setIcon(
            QIcon(ICON("visible.svg" if is_hidden else "not_visible.svg"))
        )

    def _toggle_password_confirm(self):
        mode = self.input_password_confirm.echoMode()
        is_hidden = mode == QLineEdit.EchoMode.Password
        self.input_password_confirm.setEchoMode(
            QLineEdit.EchoMode.Normal if is_hidden else QLineEdit.EchoMode.Password
        )
        self.btn_toggle_confirm.setIcon(
            QIcon(ICON("visible.svg" if is_hidden else "not_visible.svg"))
        )

    # ==================================================================
    # Close App
    # ==================================================================
    def _close_app(self):
        """User clicked the X button — Exit entire app."""
        QMessageBox.warning(
            self,
            "Exit Application?",
            "Authentication is required to use JobFit Pro.\nClosing this window will exit the app.",
        )
        self.reject()

    # ==================================================================
    # Password Strength Validation
    # ==================================================================
    def validate_password_strength(self, pw: str) -> str | None:
        """Return a string describing the problem, or None if strong."""
        if len(pw) < 8:
            return "Password must be at least 8 characters long."
        if not any(c.islower() for c in pw):
            return "Password must contain at least one lowercase letter."
        if not any(c.isupper() for c in pw):
            return "Password must contain at least one uppercase letter."
        if not any(c.isdigit() for c in pw):
            return "Password must contain at least one number."
        if not any(c in "!@#$%^&*()-_=+[]{};:,<.>/?\\|" for c in pw):
            return "Password must contain at least one symbol."
        return None

    # ==================================================================
    # Submit Logic (Sign In / Sign Up)
    # ==================================================================
    def submit(self):
        email = self.input_email.text().strip()
        pw = self.input_password.text().strip()

        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email.")
            return

        # ---------------- SIGN UP ----------------
        if self.mode == "signup":
            confirm = self.input_password_confirm.text().strip()

            pw_error = self.validate_password_strength(pw)
            if pw_error:
                QMessageBox.warning(self, "Weak Password", pw_error)
                return

            if pw != confirm:
                QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
                return

            user, error = auth.sign_up(email, pw)

            if error:
                QMessageBox.warning(self, "Sign Up Failed", str(error))
                return

            QMessageBox.information(
                self,
                "Account Created",
                "Your account has been created successfully.\nPlease sign in.",
            )

            self.switch_mode("signin")
            return

        # ---------------- SIGN IN ----------------
        user, error = auth.sign_in(email, pw)

        if error or not user:
            QMessageBox.warning(
                self, "Incorrect Credentials", "Email or password is incorrect."
            )
            return

        # Continue into app
        self.accept()
