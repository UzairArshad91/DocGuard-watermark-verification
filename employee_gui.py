import importlib
import os
import sqlite3

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import dlp_utils
from employee import send_document


DARK_STYLE = """
QMainWindow, QDialog, QWidget { background: #11161C; }
QLabel#brand { color: #55C2A3; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F3F6F8; font-size: 28px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel, QLabel#account, QLabel#status { color: #95A4B2; }
QLabel#success { color: #55C2A3; }
QLabel#error { color: #E68181; }
QFrame#panel { background: #1A222B; border: 1px solid #31404D; border-radius: 12px; }
QLineEdit, QComboBox, QTextEdit, QListWidget { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 6px; padding: 8px 10px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QListWidget:focus { border: 2px solid #55C2A3; }
QPushButton { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 7px; padding: 8px 14px; min-height: 34px; }
QPushButton:hover { background: #31404D; }
QPushButton#primary { background: #55C2A3; color: #10211D; font-weight: 600; border: none; }
QPushButton#primary:hover { background: #43A98E; }
QPushButton#secondary { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; }
QPushButton#secondary:hover { background: #31404D; }
QPushButton#danger { background: #E68181; color: #10211D; font-weight: 600; border: none; }
QPushButton#danger:hover { background: #C76666; }
"""

LIGHT_STYLE = """
QMainWindow, QDialog, QWidget { background: #F3F6F8; }
QLabel#brand { color: #16866C; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #17212B; font-size: 28px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel, QLabel#account, QLabel#status { color: #60707D; }
QLabel#success { color: #16866C; }
QLabel#error { color: #C74747; }
QFrame#panel { background: #FFFFFF; border: 1px solid #D5DEE5; border-radius: 12px; }
QLineEdit, QComboBox, QTextEdit, QListWidget { background: #EEF2F5; color: #17212B; border: 1px solid #D5DEE5; border-radius: 6px; padding: 8px 10px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QListWidget:focus { border: 2px solid #16866C; }
QPushButton { background: #EEF2F5; color: #17212B; border: 1px solid #D5DEE5; border-radius: 7px; padding: 8px 14px; min-height: 34px; }
QPushButton:hover { background: #D5DEE5; }
QPushButton#primary { background: #16866C; color: #FFFFFF; font-weight: 600; border: none; }
QPushButton#primary:hover { background: #116A56; }
QPushButton#secondary { background: #EEF2F5; color: #17212B; border: 1px solid #D5DEE5; }
QPushButton#secondary:hover { background: #D5DEE5; }
QPushButton#danger { background: #C74747; color: #FFFFFF; font-weight: 600; border: none; }
QPushButton#danger:hover { background: #A93636; }
"""

# For backwards compatibility
STYLE = DARK_STYLE


def open_employee_gui(uid, uname, on_logout=None, dark_mode=True, light_style="", dark_style=""):
    importlib.reload(dlp_utils)
    conn = sqlite3.connect("logs.db", timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT email FROM Users WHERE user_id=?", (uid,))
    user_row = cur.fetchone()
    conn.close()
    uemail = user_row[0] if user_row else ""

    window = EmployeeWindow(uid, uname, uemail, on_logout, dark_mode, light_style, dark_style)
    window.show()
    window.raise_()
    window.activateWindow()
    return window


class EmployeeWindow(QMainWindow):
    def __init__(self, uid, uname, uemail, on_logout=None, dark_mode=True, light_style="", dark_style=""):
        super().__init__()
        self.uid = uid
        self.uname = uname
        self.uemail = uemail
        self.on_logout = on_logout
        self.logout_handled = False
        self.dark_mode = dark_mode
        self.light_style = light_style if light_style else LIGHT_STYLE
        self.dark_style = dark_style if dark_style else DARK_STYLE
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.status_clear)
        self.setWindowTitle("DocGuard | Employee workspace")
        self.setMinimumSize(760, 700)
        self.resize(900, 780)
        self.setStyleSheet(self.dark_style if self.dark_mode else self.light_style)
        self.build_ui()

    def build_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(12)

        header = QHBoxLayout()
        brand = QLabel("DOCGUARD")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        theme_button = QPushButton("☀" if self.dark_mode else "🌙")
        theme_button.setMaximumWidth(40)
        theme_button.clicked.connect(self.toggle_theme)
        header.addWidget(theme_button)
        account = QLabel(f"Signed in as {self.uname}")
        account.setObjectName("account")
        header.addWidget(account)
        layout.addLayout(header)

        title = QLabel("Employee workspace")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("Send protected documents and review your activity.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        self.path = QLineEdit()
        self.path.setPlaceholderText("Choose a document")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse)
        file_row = QHBoxLayout()
        file_row.addWidget(self.path)
        file_row.addWidget(browse_button)
        file_widget = QWidget()
        file_widget.setLayout(file_row)
        form.addRow(self.field_label("Document"), file_widget)

        email = QLabel(self.uemail)
        email.setObjectName("account")
        form.addRow(self.field_label("Account email"), email)

        self.recipient = QComboBox()
        self.recipient.addItem("Select a verified recipient")
        self.recipient.addItems(dlp_utils.VERIFIED_RECIPIENTS)
        form.addRow(self.field_label("Recipient"), self.recipient)

        self.pin = QLineEdit()
        self.pin.setEchoMode(QLineEdit.Password)
        self.pin.setPlaceholderText("Enter your PIN")
        form.addRow(self.field_label("PIN"), self.pin)
        layout.addLayout(form)

        send_button = QPushButton("Send document")
        send_button.setObjectName("primary")
        send_button.clicked.connect(self.send)
        layout.addWidget(send_button)
        self.status = QLabel("")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        actions = QHBoxLayout()
        for text, handler in (
            ("My alerts", self.view_alerts),
            ("My history", self.view_history),
            ("Verified recipients", self.view_recipients),
        ):
            button = QPushButton(text)
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout.addLayout(actions)

        self.box = QTextEdit()
        self.box.setReadOnly(True)
        self.box.setMinimumHeight(230)
        layout.addWidget(self.box, stretch=1)

        logout_button = QPushButton("Logout")
        logout_button.setObjectName("danger")
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button, alignment=Qt.AlignHCenter)
        self.setCentralWidget(content)

    @staticmethod
    def field_label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def browse(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose document")
        if file_path:
            self.path.setText(file_path)

    def set_status(self, message, clear_after_ms=2000):
        self.status_timer.stop()
        self.status.setText(message)
        if message:
            self.status_timer.start(clear_after_ms)

    def status_clear(self):
        self.status.clear()

    def send(self):
        file_path = self.path.text().strip()
        if not file_path:
            self.set_status("File path is required", 4000)
            return
        if not os.path.isfile(file_path):
            self.set_status("File path is invalid or file does not exist", 4000)
            return
        recipient_value = self.recipient.currentText().strip()
        if recipient_value == "Select a verified recipient":
            recipient_value = ""
        if not recipient_value:
            self.set_status("Recipient is required", 4000)
            return
        if recipient_value not in dlp_utils.VERIFIED_RECIPIENTS:
            self.set_status("Recipient must be selected from the verified list", 4000)
            return
        if not self.pin.text().strip():
            self.set_status("PIN is required", 4000)
            return

        file_name = os.path.basename(file_path)
        confirm = QMessageBox.question(
            self,
            "Confirm send",
            f"Do you want to send {file_name} to {recipient_value}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            send_document(file_path, self.uid, self.uname, self.uemail, recipient_value, self.pin.text())
        except ValueError as exc:
            self.set_status(str(exc), 4000)
            return
        except Exception as exc:
            self.set_status(f"Send failed: {exc}", 4000)
            return
        self.set_status("Sent")

    def view_history(self):
        self.box.clear()
        conn = sqlite3.connect("logs.db", timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM Logs WHERE user_id=?", (self.uid,))
        self.box.setPlainText("\n".join(str(row) for row in cur.fetchall()))
        conn.close()

    def view_alerts(self):
        self.box.clear()
        conn = sqlite3.connect("logs.db", timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM Alerts WHERE user_id=?", (self.uid,))
        self.box.setPlainText("\n".join(str(row) for row in cur.fetchall()))
        conn.close()

    def view_recipients(self):
        self.box.setPlainText("\n".join(dlp_utils.VERIFIED_RECIPIENTS))

    def logout(self):
        with open("current_session.txt", "w") as session_file:
            session_file.write("0")
        if self.on_logout is not None and not self.logout_handled:
            self.logout_handled = True
            self.on_logout()
        self.close()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(self.dark_style if self.dark_mode else self.light_style)

    def closeEvent(self, event):
        with open("current_session.txt", "w") as session_file:
            session_file.write("0")
        if self.on_logout is not None and not self.logout_handled:
            self.logout_handled = True
            self.on_logout()
        event.accept()
