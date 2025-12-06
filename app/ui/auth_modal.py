# app/ui/auth_modal.py
"""
Authentication Modal (Sign In / Sign Up)
----------------------------------------

Modern framed auth dialog that:
- Uses the shared `auth` singleton for Supabase sign-up / sign-in
- Blocks the main app until the user successfully signs in
"""

import os

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

# IMPORTANT: import the global singleton, not the class
from services.auth_manager import auth

ICON = lambda name: os.path.join(os.getcwd(), "assets", "icons", name)


class AuthModal(QDialog):
    """
    Frameless, centered authentication modal.
    - Requires user identity before the app can open.
    - Uses `auth` singleton under the hood.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("AuthModal")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(420, 430)

        # Current mode: "signin" or "signup"
        self.mode = "signin"

        # Build widget tree and start in sign-in mode
        self.build_ui()
        self.switch_mode("signin")

    # ==================================================================
    # UI CONSTRUCTION
    # ==================================================================
    def build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card-like container in the center
        card = QWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # ---------------- Title Row ----------------
        title_row = QHBoxLayout()
        self.lbl_title = QLabel("Sign In")
        self.lbl_title.setObjectName("auth-title")

        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon(ICON("close.svg")))
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setProperty("authIcon", True)
        self.btn_close.clicked.connect(self.confirm_exit)

        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        title_row.addWidget(self.btn_close)
        layout.addLayout(title_row)

        # ---------------- Email ----------------
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email address")
        self.input_email.setProperty("authField", True)
        layout.addWidget(self.input_email)

        # ---------------- Password ----------------
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Password")
        self.input_password.setProperty("authField", True)

        self.btn_toggle_pw = QPushButton()
        self.btn_toggle_pw.setIcon(QIcon(ICON("not_visible.svg")))
        self.btn_toggle_pw.setFixedSize(32, 32)
        self.btn_toggle_pw.setProperty("authIcon", True)
        self.btn_toggle_pw.clicked.connect(self.toggle_password)

        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)
        pw_row.addWidget(self.input_password)
        pw_row.addWidget(self.btn_toggle_pw)
        layout.addLayout(pw_row)

        # ---------------- Confirm Password (signup only) ----------------
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setPlaceholderText("Confirm password")
        self.input_password_confirm.setProperty("authField", True)

        self.btn_toggle_confirm = QPushButton()
        self.btn_toggle_confirm.setIcon(QIcon(ICON("not_visible.svg")))
        self.btn_toggle_confirm.setFixedSize(32, 32)
        self.btn_toggle_confirm.setProperty("authIcon", True)
        self.btn_toggle_confirm.clicked.connect(self.toggle_password_confirm)

        confirm_row = QHBoxLayout()
        confirm_row.setSpacing(8)
        confirm_row.addWidget(self.input_password_confirm)
        confirm_row.addWidget(self.btn_toggle_confirm)

        self.confirm_row_widget = QWidget()
        self.confirm_row_widget.setLayout(confirm_row)
        layout.addWidget(self.confirm_row_widget)

        # ---------------- Submit Button ----------------
        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.setProperty("authPrimary", True)
        self.btn_submit.clicked.connect(self.submit)
        layout.addWidget(self.btn_submit)

        # ---------------- Mode Switch Link ----------------
        self.btn_switch_mode = QPushButton("Create an account")
        self.btn_switch_mode.setFlat(True)
        self.btn_switch_mode.setProperty("authLink", True)
        self.btn_switch_mode.clicked.connect(self.switch_modes_clicked)
        layout.addWidget(self.btn_switch_mode, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)

    # ==================================================================
    # MODE SWITCHING
    # ==================================================================
    def switch_mode(self, mode: str) -> None:
        """
        Switches between 'signin' and 'signup' modes and updates the UI.
        """
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

    def switch_modes_clicked(self) -> None:
        self.switch_mode("signup" if self.mode == "signin" else "signin")

    # ==================================================================
    # PASSWORD VISIBILITY TOGGLES
    # ==================================================================
    def toggle_password(self) -> None:
        """
        Show/hide the main password field.
        """
        if self.input_password.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pw.setIcon(QIcon(ICON("visible.svg")))
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pw.setIcon(QIcon(ICON("not_visible.svg")))

    def toggle_password_confirm(self) -> None:
        """
        Show/hide the confirm password field.
        """
        if self.input_password_confirm.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_confirm.setIcon(QIcon(ICON("visible.svg")))
        else:
            self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_confirm.setIcon(QIcon(ICON("not_visible.svg")))

    # ==================================================================
    # EXIT BEHAVIOR
    # ==================================================================
    def confirm_exit(self) -> None:
        """
        Prompt before closing the modal.

        NOTE:
        - If the user closes this without signing in, the main window
          will detect that (result != Accepted) and exit the app.
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit Application?")
        msg.setText("Closing authentication will exit JobFit Pro.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Reject dialog to indicate "no login"
            self.reject()
            # Also signal app exit if event loop is running
            app = QApplication.instance()
            if app is not None:
                app.quit()

    # ==================================================================
    # SUPABASE AUTH HANDLING
    # ==================================================================
    def submit(self) -> None:
        """
        Handles both Sign In and Sign Up flows, based on current mode.
        """
        email = self.input_email.text().strip()
        pw = self.input_password.text().strip()

        if not email or not pw:
            QMessageBox.warning(self, "Error", "Email and password are required.")
            return

        # ---------- SIGN UP ----------
        if self.mode == "signup":
            confirm = self.input_password_confirm.text().strip()
            if pw != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return

            try:
                resp = auth.sign_up(email, pw)
            except Exception as e:
                QMessageBox.critical(self, "Sign Up Failed", str(e))
                return

            QMessageBox.information(
                self,
                "Account Created",
                "Your account has been created.\n"
                "If email verification is required, please verify before signing in.",
            )
            # After sign-up, go back to sign-in mode
            self.switch_mode("signin")
            return

        # ---------- SIGN IN ----------
        try:
            resp = auth.sign_in(email, pw)
            # debug prints already in AuthManager, but we can log here too if needed
        except Exception as e:
            QMessageBox.critical(self, "Sign In Failed", str(e))
            return

        # Make sure a user exists on the response
        if not auth.get_user():
            QMessageBox.warning(self, "Error", "Incorrect email or password.")
            return

        # Tell caller (MainWindow) that auth succeeded
        self.accept()
