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


DARK_STYLE = """
QMainWindow { background: #11161C; }
QLabel#brand { color: #55C2A3; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F3F6F8; font-size: 28px; font-weight: 700; }
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

LIGHT_STYLE = """
QMainWindow { background: #F3F6F8; }
QLabel#brand { color: #16866C; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #17212B; font-size: 28px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel, QLabel#status { color: #60707D; }
QLabel#success { color: #16866C; }
QLabel#error { color: #C74747; }
QLineEdit, QListWidget { background: #EEF2F5; color: #17212B; border: 1px solid #D5DEE5; border-radius: 6px; padding: 8px 10px; }
QLineEdit:focus, QListWidget:focus { border: 2px solid #16866C; }
QPushButton { background: #EEF2F5; color: #17212B; border: 1px solid #D5DEE5; border-radius: 7px; padding: 8px 14px; min-height: 34px; }
QPushButton:hover { background: #D5DEE5; }
QPushButton#primary { background: #16866C; color: #FFFFFF; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #116A56; }
QPushButton#danger { background: #C74747; color: #FFFFFF; border: none; font-weight: 600; }
QPushButton#danger:hover { background: #A93636; }
QRadioButton { color: #17212B; spacing: 8px; }
"""

# For backwards compatibility
STYLE = DARK_STYLE


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
        # Remove all items from the layout recursively
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                # Recursively clear nested layouts
                nested_layout = item.layout()
                while nested_layout.count():
                    nested_item = nested_layout.takeAt(0)
                    if nested_item.widget():
                        widget = nested_item.widget()
                        widget.setParent(None)
                        widget.deleteLater()
                nested_layout.deleteLater()

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
            try:
                conn = get_conn()
                conn.execute("INSERT INTO Users (name, email, pin, role) VALUES (?,?,?,?)", (name.text(), email.text(), pin.text(), role))
                conn.commit()
                conn.close()
                status.setObjectName("success")
                status.setText("User added successfully")
                name.clear()
                email.clear()
                pin.clear()
                employee.setChecked(True)
            except Exception as e:
                status.setObjectName("error")
                status.setText(f"Error: {str(e)}")

        add.clicked.connect(submit)

    def show_delete_user(self):
        self.clear_content()
        self.add_header("Remove user account", "Permanently delete a user from the database.")
        
        # Warning panel at top
        warning_panel = QWidget()
        warning_panel.setObjectName("panel")
        warning_layout = QVBoxLayout(warning_panel)
        warning_layout.setContentsMargins(16, 12, 16, 12)
        warning_label = QLabel("⚠️ WARNING: This action is PERMANENT")
        warning_label.setObjectName("error")
        warning_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        warning_layout.addWidget(warning_label)
        warning_desc = QLabel("Once deleted, user data cannot be recovered.")
        warning_desc.setObjectName("subtitle")
        warning_layout.addWidget(warning_desc)
        self.layout.addWidget(warning_panel)
        
        self.layout.addSpacing(8)
        
        # Users scrollable list (center)
        list_title = QLabel("Available users:")
        list_title.setObjectName("fieldLabel")
        self.layout.addWidget(list_title)
        
        users_list = QListWidget()
        users_list.setMinimumHeight(200)
        users_list.setMaximumHeight(300)
        self.layout.addWidget(users_list, stretch=1)
        
        # Load users
        conn = get_conn()
        rows = conn.execute("SELECT user_id, name, role FROM Users ORDER BY user_id").fetchall()
        conn.close()
        
        user_data = {}
        for row in rows:
            user_id, name, role = row
            display_text = f"[{user_id}] {name} - {role.upper()}"
            users_list.addItem(display_text)
            user_data[display_text] = user_id
        
        if not rows:
            users_list.addItem("No users in system")
            users_list.item(0).setFlags(users_list.item(0).flags() & ~Qt.ItemIsSelectable)
        
        # Selection info panel
        info_panel = QWidget()
        info_panel.setObjectName("panel")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_label = QLabel("Selected user information will appear here")
        info_label.setObjectName("subtitle")
        info_layout.addWidget(info_label)
        self.layout.addWidget(info_panel)
        
        # Status message
        status = QLabel("")
        status.setObjectName("status")
        self.layout.addWidget(status)
        
        # Action buttons at bottom
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        delete_btn = QPushButton("🗑️  DELETE SELECTED USER")
        delete_btn.setObjectName("danger")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet("font-weight: bold; font-size: 12px;")
        button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel & Go Back")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.clicked.connect(self.show_main_menu)
        button_layout.addWidget(cancel_btn)
        
        self.layout.addLayout(button_layout)
        
        def update_info():
            if not users_list.currentItem() or users_list.currentItem().text() == "No users in system":
                info_label.setText("No user selected")
                info_label.setObjectName("subtitle")
                return
            selected_text = users_list.currentItem().text()
            user_id = user_data[selected_text]
            conn = get_conn()
            user_info = conn.execute("SELECT name, email, role FROM Users WHERE user_id=?", (user_id,)).fetchone()
            conn.close()
            if user_info:
                name, email, role = user_info
                info_label.setText(f"📋 ID: {user_id} | Name: {name} | Email: {email} | Role: {role.upper()}")
                info_label.setObjectName("fieldLabel")
        
        users_list.itemSelectionChanged.connect(update_info)

        def submit():
            if not users_list.currentItem() or users_list.currentItem().text() == "No users in system":
                status.setText("❌ Please select a user first")
                return
            
            selected_text = users_list.currentItem().text()
            user_id = user_data[selected_text]
            
            from PySide6.QtWidgets import QMessageBox
            confirm = QMessageBox.critical(
                self,
                "⚠️ CONFIRM DELETION",
                f"Are you absolutely sure?\n\nUser ID: {user_id}\n\n"
                "This will permanently delete the user account and cannot be undone!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                try:
                    conn = get_conn()
                    conn.execute("DELETE FROM Users WHERE user_id=?", (user_id,))
                    conn.commit()
                    conn.close()
                    
                    status.setObjectName("success")
                    status.setText("✅ User deleted successfully!")
                    
                    # Refresh list
                    users_list.clear()
                    user_data.clear()
                    conn = get_conn()
                    rows = conn.execute("SELECT user_id, name, role FROM Users ORDER BY user_id").fetchall()
                    conn.close()
                    
                    for row in rows:
                        uid, nm, rl = row
                        display_text = f"[{uid}] {nm} - {rl.upper()}"
                        users_list.addItem(display_text)
                        user_data[display_text] = uid
                    
                    if not rows:
                        users_list.addItem("No users in system")
                        users_list.item(0).setFlags(users_list.item(0).flags() & ~Qt.ItemIsSelectable)
                    
                    info_label.setText("User deleted. Select another user or go back.")
                    
                except Exception as e:
                    status.setObjectName("error")
                    status.setText(f"❌ Error: {str(e)}")

        delete_btn.clicked.connect(submit)

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
