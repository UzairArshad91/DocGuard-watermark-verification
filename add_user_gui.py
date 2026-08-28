import sqlite3
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


STYLE = """
QMainWindow { background: #11161C; }
QLabel#brand { color: #55C2A3; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F3F6F8; font-size: 26px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel, QLabel#status { color: #95A4B2; }
QLabel#success { color: #55C2A3; }
QLabel#error { color: #E68181; }
QLineEdit, QListWidget { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 6px; padding: 8px 10px; }
QLineEdit:focus, QListWidget:focus { border: 2px solid #55C2A3; }
QPushButton { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 7px; padding: 8px 14px; min-height: 34px; }
QPushButton:hover { background: #31404D; }
QPushButton#primary { background: #55C2A3; color: #10211D; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #43A98E; }
QPushButton#danger { background: #E68181; color: #10211D; border: none; font-weight: 600; }
QPushButton#danger:hover { background: #C76666; }
QRadioButton { color: #F3F6F8; spacing: 8px; }
"""


def get_conn():
    return sqlite3.connect("logs.db", timeout=10)


def main_menu():
    window.show_main_menu()


def view_users():
    window.show_view_users()


def add_user_screen():
    window.show_add_user()


def delete_user_screen():
    window.show_delete_user()


class UserManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocGuard | User management")
        self.setMinimumSize(620, 560)
        self.resize(700, 620)
        self.setStyleSheet(STYLE)
        self.content = QWidget()
        self.layout = QVBoxLayout(self.content)
        self.layout.setContentsMargins(48, 36, 48, 36)
        self.layout.setSpacing(12)
        self.setCentralWidget(self.content)
        self.show_main_menu()

    def clear_content(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

    def add_header(self, title, subtitle):
        brand = QLabel("DOCGUARD")
        brand.setObjectName("brand")
        self.layout.addWidget(brand)
        heading = QLabel(title)
        heading.setObjectName("title")
        self.layout.addWidget(heading)
        description = QLabel(subtitle)
        description.setObjectName("subtitle")
        self.layout.addWidget(description)
        self.layout.addSpacing(12)

    def add_back_button(self):
        back = QPushButton("Back to menu")
        back.clicked.connect(self.show_main_menu)
        self.layout.addWidget(back, alignment=Qt.AlignLeft)

    def show_main_menu(self):
        self.clear_content()
        self.add_header("User management", "Review and maintain DocGuard user accounts.")
        for text, handler in (
            ("View users", self.show_view_users),
            ("Add user", self.show_add_user),
            ("Delete user", self.show_delete_user),
        ):
            button = QPushButton(text)
            button.clicked.connect(handler)
            self.layout.addWidget(button)
        self.layout.addStretch()

    def show_view_users(self):
        self.clear_content()
        self.add_header("View users", "All registered DocGuard accounts.")
        users = QListWidget()
        self.layout.addWidget(users, stretch=1)
        conn = get_conn()
        rows = conn.execute("SELECT * FROM Users").fetchall()
        conn.close()
        users.addItems([str(row) for row in rows])
        self.add_back_button()

    def show_add_user(self):
        self.clear_content()
        self.add_header("Add user", "Create an administrator or employee account.")
        form = QFormLayout()
        form.setVerticalSpacing(12)
        name = QLineEdit()
        email = QLineEdit()
        pin = QLineEdit()
        form.addRow(self.field_label("Name"), name)
        form.addRow(self.field_label("Email"), email)
        form.addRow(self.field_label("PIN"), pin)
        self.layout.addLayout(form)

        role_row = QHBoxLayout()
        role_group = QButtonGroup(self)
        employee = QRadioButton("Employee")
        admin = QRadioButton("Admin")
        employee.setChecked(True)
        role_group.addButton(employee)
        role_group.addButton(admin)
        role_row.addWidget(employee)
        role_row.addWidget(admin)
        role_row.addStretch()
        self.layout.addLayout(role_row)

        status = QLabel("")
        status.setObjectName("status")
        self.layout.addWidget(status)
        add = QPushButton("Add user")
        add.setObjectName("primary")
        self.layout.addWidget(add)
        self.layout.addStretch()
        self.add_back_button()

        def submit():
            if not name.text() or not email.text() or not pin.text():
                status.setText("All fields required")
                return
            role = "admin" if admin.isChecked() else "employee"
            conn = get_conn()
            conn.execute("INSERT INTO Users (name, email, pin, role) VALUES (?,?,?,?)", (name.text(), email.text(), pin.text(), role))
            conn.commit()
            conn.close()
            status.setObjectName("success")
            status.setText("User added")
            name.clear()
            email.clear()
            pin.clear()

        add.clicked.connect(submit)

    def show_delete_user(self):
        self.clear_content()
        self.add_header("Delete user", "Remove an account by its user ID.")
        form = QFormLayout()
        user_id = QLineEdit()
        form.addRow(self.field_label("User ID"), user_id)
        self.layout.addLayout(form)
        status = QLabel("")
        status.setObjectName("status")
        self.layout.addWidget(status)
        delete = QPushButton("Delete user")
        delete.setObjectName("danger")
        self.layout.addWidget(delete)
        self.layout.addStretch()
        self.add_back_button()

        def submit():
            if not user_id.text().strip():
                status.setText("User ID is required")
                return
            conn = get_conn()
            conn.execute("DELETE FROM Users WHERE user_id=?", (user_id.text().strip(),))
            conn.commit()
            conn.close()
            status.setObjectName("success")
            status.setText("User deleted")

        delete.clicked.connect(submit)

    @staticmethod
    def field_label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label


window = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = UserManagerWindow()
    window.show()
    sys.exit(app.exec())
