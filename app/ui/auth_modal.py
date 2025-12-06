"""
Authentication Modal (Sign In / Sign Up)
Modern polished UI with password visibility toggle.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QMessageBox,
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

from services.auth_manager import AuthManager

auth = AuthManager()


class AuthModal(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Welcome to JobFit Pro")
        self.setModal(True)
        self.setFixedSize(420, 420)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.mode = "signin"  # "signin" or "signup"

        self.build_ui()
        self.apply_styles()
        self.switch_mode("signin")

    # ------------------------------------------------------------------
    # UI Layout
    # ------------------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # ---------------- Title Row ----------------
        title_row = QHBoxLayout()
        self.lbl_title = QLabel("Sign In")
        self.lbl_title.setObjectName("auth-title")

        # Close button
        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon("app/assets/icons/close.svg"))
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.clicked.connect(self.confirm_exit)

        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        title_row.addWidget(self.btn_close)

        layout.addLayout(title_row)

        # ---------------- Email ----------------
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email address")
        self.input_email.setObjectName("auth-input")

        # ---------------- Password ----------------
        password_row = QHBoxLayout()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Password")
        self.input_password.setObjectName("auth-input")

        self.btn_toggle_pw = QPushButton()
        self.btn_toggle_pw.setIcon(QIcon("app/assets/icons/not_visible.svg"))
        self.btn_toggle_pw.setFixedSize(28, 28)
        self.btn_toggle_pw.clicked.connect(self.toggle_password)

        password_row.addWidget(self.input_password)
        password_row.addWidget(self.btn_toggle_pw)

        # ---------------- Password Confirm (Signup only) ----------------
        confirm_row = QHBoxLayout()
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setPlaceholderText("Confirm password")
        self.input_password_confirm.setObjectName("auth-input")

        self.btn_toggle_confirm = QPushButton()
        self.btn_toggle_confirm.setIcon(QIcon("app/assets/icons/not_visible.svg"))
        self.btn_toggle_confirm.setFixedSize(28, 28)
        self.btn_toggle_confirm.clicked.connect(self.toggle_password_confirm)

        confirm_row.addWidget(self.input_password_confirm)
        confirm_row.addWidget(self.btn_toggle_confirm)

        self.confirm_row_widget = QWidget()
        self.confirm_row_widget.setLayout(confirm_row)

        # ---------------- Submit Button ----------------
        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.clicked.connect(self.submit)

        # ---------------- Switch Mode Link ----------------
        self.btn_switch_mode = QPushButton("Create an account")
        self.btn_switch_mode.setFlat(True)
        self.btn_switch_mode.clicked.connect(self.switch_modes_clicked)

        # Add widgets
        layout.addWidget(self.input_email)
        layout.addLayout(password_row)
        layout.addWidget(self.confirm_row_widget)
        layout.addWidget(self.btn_submit)
        layout.addWidget(self.btn_switch_mode, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------
    # Styling (Modern UI)
    # ------------------------------------------------------------------
    def apply_styles(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #0F172A;
                border-radius: 14px;
            }

            #auth-title {
                font-size: 22px;
                font-weight: 600;
                color: #F1F5F9;
            }

            QLabel {
                color: #E2E8F0;
            }

            #auth-input {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #F8FAFC;
                font-size: 15px;
            }
            #auth-input:focus {
                border: 1px solid #4F46E5;
                background-color: #1E293B;
            }

            QPushButton {
                background-color: #4F46E5;
                color: white;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #6366F1;
            }

            QPushButton:flat {
                background: transparent;
                color: #93C5FD;
                font-size: 14px;
            }
            QPushButton:flat:hover {
                color: #BFDBFE;
                text-decoration: underline;
            }
            """
        )

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------
    def switch_mode(self, mode):
        """Switch between sign-in and sign-up."""
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

    # ------------------------------------------------------------------
    # Password Toggle
    # ------------------------------------------------------------------
    def toggle_password(self):
        if self.input_password.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pw.setIcon(QIcon("app/assets/icons/visible.svg"))
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pw.setIcon(QIcon("app/assets/icons/not_visible.svg"))

    def toggle_password_confirm(self):
        if self.input_password_confirm.echoMode() == QLineEdit.EchoMode.Password:
            self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_confirm.setIcon(QIcon("app/assets/icons/visible.svg"))
        else:
            self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_confirm.setIcon(QIcon("app/assets/icons/not_visible.svg"))

    # ------------------------------------------------------------------
    # Close modal → confirm exit
    # ------------------------------------------------------------------
    def confirm_exit(self):
        reply = QMessageBox.question(
            self,
            "Exit?",
            "Closing this window will exit JobFit Pro. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.reject()

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
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

            resp = auth.sign_up(email, pw)
            QMessageBox.information(
                self,
                "Account Created",
                "Your account has been created.\nYou may now sign in.",
            )
            self.switch_mode("signin")
            return

        # Sign in
        resp = auth.sign_in(email, pw)
        if not resp.user:
            QMessageBox.warning(self, "Error", "Incorrect email or password.")
            return

        self.accept()  # success → close modal
