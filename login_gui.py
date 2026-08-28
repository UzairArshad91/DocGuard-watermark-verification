import os
import sqlite3
import subprocess
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

LIGHT_STYLE = """
QMainWindow, QDialog { background: #F3F6F8; }
QLabel#brand { color: #16866C; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #17212B; font-size: 28px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel { color: #60707D; }
QLabel#panelTitle { color: #17212B; font-size: 19px; font-weight: 700; }
QFrame#panel { background: #FFFFFF; border: 1px solid #D5DEE5; border-radius: 12px; }
QLineEdit { background: #EEF2F5; color: #17212B; border: 1px solid #D5DEE5; border-radius: 6px; padding: 0 11px; min-height: 38px; }
QLineEdit:focus { border: 2px solid #16866C; }
QPushButton { border-radius: 7px; padding: 0 16px; min-height: 36px; }
QPushButton#primary { background: #16866C; color: #FFFFFF; font-weight: 600; }
QPushButton#primary:hover { background: #116A56; }
QPushButton#secondary { background: #EEF2F5; color: #17212B; }
QPushButton#secondary:hover { background: #D5DEE5; }
QPushButton#danger { background: #C74747; color: #FFFFFF; font-weight: 600; }
QPushButton#danger:hover { background: #A93636; }
QLabel#error { color: #C74747; }
"""


DARK_STYLE = """
QMainWindow, QDialog { background: #11161C; }
QLabel#brand { color: #55C2A3; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F3F6F8; font-size: 28px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel { color: #95A4B2; }
QLabel#panelTitle { color: #F3F6F8; font-size: 19px; font-weight: 700; }
QFrame#panel { background: #1A222B; border: 1px solid #31404D; border-radius: 12px; }
QLineEdit { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 6px; padding: 0 11px; min-height: 38px; }
QLineEdit:focus { border: 2px solid #55C2A3; }
QPushButton { border-radius: 7px; padding: 0 16px; min-height: 36px; }
QPushButton#primary { background: #55C2A3; color: #10211D; font-weight: 600; }
QPushButton#primary:hover { background: #43A98E; }
QPushButton#secondary { background: #202B36; color: #F3F6F8; }
QPushButton#secondary:hover { background: #31404D; }
QPushButton#danger { background: #E68181; color: #10211D; font-weight: 600; }
QPushButton#danger:hover { background: #C76666; }
QLabel#error { color: #E68181; }
"""


def get_conn():
    return sqlite3.connect("logs.db", timeout=10)


class CloseDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Close application")
        self.setFixedSize(400, 330)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Close application")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        description = QLabel("Administrator verification required")
        description.setObjectName("subtitle")
        layout.addWidget(description)

        form = QFormLayout()
        form.setVerticalSpacing(8)
        name_label = QLabel("Admin name")
        name_label.setObjectName("fieldLabel")
        self.name = QLineEdit()
        pin_label = QLabel("PIN")
        pin_label.setObjectName("fieldLabel")
        self.pin = QLineEdit()
        self.pin.setEchoMode(QLineEdit.Password)
        form.addRow(name_label, self.name)
        form.addRow(pin_label, self.pin)
        layout.addLayout(form)

        self.status = QLabel("")
        self.status.setObjectName("error")
        layout.addWidget(self.status)
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.status.clear)
        layout.addStretch()

        actions = QDialogButtonBox()
        cancel = actions.addButton("Cancel", QDialogButtonBox.RejectRole)
        cancel.setObjectName("secondary")
        confirm = actions.addButton("Close application", QDialogButtonBox.AcceptRole)
        confirm.setObjectName("danger")
        confirm.clicked.connect(self.confirm)
        layout.addWidget(actions)

        self.name.setFocus()
        self.setModal(True)
        self.pin.returnPressed.connect(self.confirm)

    def confirm(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM Users WHERE name=? AND pin=? AND role='admin'",
            (self.name.text(), self.pin.text()),
        )
        valid = cur.fetchone() is not None
        conn.close()
        if valid:
            os.system("taskkill /F /IM python.exe /T & taskkill /F /IM pythonw.exe /T")
        else:
            self.status.setText("Access denied")
            self.status_timer.start(2000)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.child_window = None
        self.setWindowTitle("DocGuard | Secure access")
        self.setMinimumSize(620, 600)
        self.resize(760, 620)
        self.build_ui()
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.status.clear)
        self.apply_theme()

    def build_ui(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(56, 48, 56, 48)
        content_layout.setSpacing(0)

        header = QHBoxLayout()
        brand = QLabel("DOCGUARD")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.theme_button = QPushButton("Light mode")
        self.theme_button.setObjectName("secondary")
        self.theme_button.clicked.connect(self.toggle_theme)
        header.addWidget(self.theme_button)
        content_layout.addLayout(header)

        title = QLabel("Watermark verification system")
        title.setObjectName("title")
        content_layout.addWidget(title)
        subtitle = QLabel("Sign in to manage protected documents securely.")
        subtitle.setObjectName("subtitle")
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(28)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.setSpacing(8)

        panel_title = QLabel("Sign in")
        panel_title.setObjectName("panelTitle")
        panel_layout.addWidget(panel_title)
        panel_layout.addSpacing(10)

        name_label = QLabel("Name")
        name_label.setObjectName("fieldLabel")
        panel_layout.addWidget(name_label)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Enter your name")
        panel_layout.addWidget(self.name)
        panel_layout.addSpacing(6)

        pin_label = QLabel("PIN")
        pin_label.setObjectName("fieldLabel")
        panel_layout.addWidget(pin_label)
        self.pin = QLineEdit()
        self.pin.setPlaceholderText("Enter your PIN")
        self.pin.setEchoMode(QLineEdit.Password)
        self.pin.returnPressed.connect(self.login)
        panel_layout.addWidget(self.pin)

        self.status = QLabel("")
        self.status.setObjectName("error")
        panel_layout.addWidget(self.status)
        panel_layout.addSpacing(4)

        login_button = QPushButton("Continue")
        login_button.setObjectName("primary")
        login_button.clicked.connect(self.login)
        panel_layout.addWidget(login_button)
        content_layout.addWidget(panel)

        content_layout.addStretch()
        close_button = QPushButton("Close app")
        close_button.setObjectName("danger")
        close_button.setFixedWidth(150)
        close_button.clicked.connect(self.admin_close)
        content_layout.addWidget(close_button, alignment=Qt.AlignHCenter)

        self.setCentralWidget(content)
        self.name.setFocus()

    def apply_theme(self):
        self.setStyleSheet(DARK_STYLE if self.dark_mode else LIGHT_STYLE)
        self.theme_button.setText("Dark mode" if self.dark_mode else "Light mode")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def show_login(self):
        self.name.clear()
        self.pin.clear()
        self.status.clear()
        self.child_window = None
        self.show()
        self.raise_()
        self.activateWindow()
        self.name.setFocus()

    def login(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, role FROM Users WHERE name=? AND pin=?", (self.name.text(), self.pin.text()))
        row = cur.fetchone()
        conn.close()
        if not row:
            self.status.setText("Invalid login")
            self.status_timer.start(2000)
            return
        uid, role = row
        with open("current_session.txt", "w") as session_file:
            session_file.write(str(uid))
        uname = self.name.text()
        self.hide()
        if role == "admin":
            from admin_gui import open_admin_gui

            self.child_window = open_admin_gui(uid, on_logout=self.show_login)
        else:
            from employee_gui import open_employee_gui

            self.child_window = open_employee_gui(uid, uname, on_logout=self.show_login)

    def admin_close(self):
        dialog = CloseDialog(self)
        dialog.setStyleSheet(DARK_STYLE if self.dark_mode else LIGHT_STYLE)
        dialog.exec()

    def closeEvent(self, event: QCloseEvent):
        with open("current_session.txt", "w") as session_file:
            session_file.write("0")
        subprocess.Popen(["restart.bat"], shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        event.accept()


if __name__ == "__main__":
    sqlite3.connect("logs.db").execute("PRAGMA journal_mode=WAL;")
    subprocess.Popen([sys.executable, "main.py"])
    subprocess.Popen([sys.executable, "service_watchdog.py"])
    subprocess.Popen([sys.executable, "file_watcher.py"])
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
