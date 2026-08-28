import csv
import importlib
import os
import re
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import dlp_utils
from employee import send_document


STYLE = """
QMainWindow, QDialog { background: #11161C; }
QLabel#brand { color: #55C2A3; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F3F6F8; font-size: 26px; font-weight: 700; }
QLabel#subtitle, QLabel#fieldLabel, QLabel#status { color: #95A4B2; }
QLabel#success { color: #55C2A3; }
QLabel#error { color: #E68181; }
QLineEdit, QComboBox, QTextEdit, QListWidget { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 6px; padding: 8px 10px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QListWidget:focus { border: 2px solid #55C2A3; }
QPushButton { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 7px; padding: 8px 14px; min-height: 34px; }
QPushButton:hover { background: #31404D; }
QPushButton#primary { background: #55C2A3; color: #10211D; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #43A98E; }
QPushButton#danger { background: #E68181; color: #10211D; border: none; font-weight: 600; }
QPushButton#danger:hover { background: #C76666; }
"""


def get_conn():
    return sqlite3.connect("logs.db", timeout=10)


def open_admin_gui(uid, on_logout=None):
    window = AdminWindow(uid, on_logout)
    window.show()
    window.raise_()
    window.activateWindow()
    return window


class AdminDialog(QDialog):
    def __init__(self, parent, title, subtitle=None, width=700, height=520):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(width, height)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 24, 28, 24)
        self.layout.setSpacing(12)
        heading = QLabel(title)
        heading.setObjectName("title")
        self.layout.addWidget(heading)
        if subtitle:
            description = QLabel(subtitle)
            description.setObjectName("subtitle")
            self.layout.addWidget(description)


class AdminWindow(QMainWindow):
    def __init__(self, uid, on_logout=None):
        super().__init__()
        self.uid = uid
        self.on_logout = on_logout
        self.logout_handled = False
        self.setWindowTitle("DocGuard | Admin workspace")
        self.setMinimumSize(760, 700)
        self.resize(860, 780)
        self.setStyleSheet(STYLE)
        self.build_ui()

    def build_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(12)

        brand = QLabel("DOCGUARD")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        title = QLabel("Admin workspace")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("Manage users, document activity, recipients, and system records.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(14)

        menu = QVBoxLayout()
        menu.setSpacing(8)
        buttons = (
            ("Manage users", self.manage_db),
            ("View all logs", self.view_logs),
            ("View alerts", self.view_alerts),
            ("Search logs by employee", self.search_logs),
            ("Change user PIN", self.change_pin),
            ("Manage verified recipients", self.manage_recipients),
            ("Export logs to CSV", self.export_logs),
            ("Send document", self.send_mail),
        )
        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            menu.addWidget(button)
        layout.addLayout(menu)
        layout.addStretch()

        self.export_status = QLabel("")
        self.export_status.setObjectName("success")
        layout.addWidget(self.export_status, alignment=Qt.AlignHCenter)
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

    def text_view(self, title, query, transform=None, clear_table=None):
        dialog = AdminDialog(self, title, width=760, height=600)
        box = QTextEdit()
        box.setReadOnly(True)
        dialog.layout.addWidget(box, stretch=1)

        def refresh():
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()
            values = []
            for row in rows:
                values.append(str(transform(row) if transform else row))
            box.setPlainText("\n".join(values))

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(refresh)
        dialog.layout.addWidget(refresh_button)
        if clear_table:
            clear_button = QPushButton("Clear records")
            clear_button.setObjectName("danger")
            clear_button.clicked.connect(lambda: self.clear_records(dialog, box, clear_table, query))
            dialog.layout.addWidget(clear_button)
        refresh()
        dialog.exec()

    def clear_records(self, dialog, box, table, query):
        confirm = QMessageBox.question(dialog, "Confirm clear", f"Delete all records from {table}?")
        if confirm != QMessageBox.Yes:
            return
        conn = get_conn()
        conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        box.clear()

    def manage_db(self):
        dialog = AdminDialog(self, "Manage users", width=760, height=600)
        tabs = QHBoxLayout()
        view_button = QPushButton("View users")
        add_button = QPushButton("Add user")
        delete_button = QPushButton("Delete user")
        tabs.addWidget(view_button)
        tabs.addWidget(add_button)
        tabs.addWidget(delete_button)
        dialog.layout.addLayout(tabs)
        content = QWidget()
        dialog.layout.addWidget(content, stretch=1)

        def clear_content():
            old_layout = content.layout()
            if old_layout:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            else:
                content.setLayout(QVBoxLayout())
            return content.layout()

        def show_view():
            form = clear_content()
            box = QTextEdit()
            box.setReadOnly(True)
            form.addWidget(box)
            conn = get_conn()
            rows = conn.execute("SELECT * FROM Users").fetchall()
            conn.close()
            box.setPlainText("\n".join(str(row) for row in rows))

        def show_add():
            form = clear_content()
            fields = QFormLayout()
            name = QLineEdit()
            email = QLineEdit()
            pin = QLineEdit()
            role = QComboBox()
            role.addItems(["employee", "admin"])
            fields.addRow(self.field_label("Name"), name)
            fields.addRow(self.field_label("Email"), email)
            fields.addRow(self.field_label("PIN"), pin)
            fields.addRow(self.field_label("Role"), role)
            form.addLayout(fields)
            status = QLabel("")
            status.setObjectName("status")
            form.addWidget(status)
            submit = QPushButton("Add user")
            submit.setObjectName("primary")
            form.addWidget(submit)

            def add_user():
                if not name.text() or not email.text() or not pin.text():
                    status.setText("All fields required")
                    return
                conn = get_conn()
                conn.execute("INSERT INTO Users (name, email, pin, role) VALUES (?,?,?,?)", (name.text(), email.text(), pin.text(), role.currentText()))
                conn.commit()
                conn.close()
                status.setText("User added")
                name.clear(); email.clear(); pin.clear()

            submit.clicked.connect(add_user)

        def show_delete():
            form = clear_content()
            fields = QFormLayout()
            user_id = QLineEdit()
            fields.addRow(self.field_label("User ID"), user_id)
            form.addLayout(fields)
            status = QLabel("")
            status.setObjectName("status")
            form.addWidget(status)
            submit = QPushButton("Delete user")
            submit.setObjectName("danger")
            form.addWidget(submit)

            def delete_user():
                if not user_id.text().strip():
                    status.setText("User ID is required")
                    return
                conn = get_conn()
                admin_count = conn.execute("SELECT COUNT(*) FROM Users WHERE role='admin'").fetchone()[0]
                target = conn.execute("SELECT role FROM Users WHERE user_id=?", (user_id.text().strip(),)).fetchone()
                if not target:
                    status.setText("User not found")
                elif target[0] == "admin" and admin_count <= 1:
                    status.setText("Cannot delete last admin")
                else:
                    conn.execute("DELETE FROM Users WHERE user_id=?", (user_id.text().strip(),))
                    conn.commit()
                    status.setText("User deleted")
                conn.close()

            submit.clicked.connect(delete_user)

        view_button.clicked.connect(show_view)
        add_button.clicked.connect(show_add)
        delete_button.clicked.connect(show_delete)
        show_view()
        dialog.exec()

    def view_logs(self):
        self.text_view("All logs", "SELECT Logs.log_id, Documents.filename, Logs.user_id, Logs.action, Logs.recipient, Logs.timestamp FROM Logs JOIN Documents ON Logs.doc_id = Documents.doc_id", lambda row: (*row[:1], os.path.basename(row[1]), *row[2:]), "Logs")

    def view_alerts(self):
        self.text_view("All alerts", "SELECT Alerts.alert_id, Documents.filename, Alerts.user_id, Alerts.reason, Alerts.timestamp FROM Alerts JOIN Documents ON Alerts.doc_id = Documents.doc_id", lambda row: (*row[:1], os.path.basename(row[1]), *row[2:]), "Alerts")

    def search_logs(self):
        dialog = AdminDialog(self, "Search logs by employee", width=760, height=600)
        controls = QHBoxLayout()
        user_id = QLineEdit()
        user_id.setPlaceholderText("User ID")
        search_button = QPushButton("Search")
        controls.addWidget(user_id)
        controls.addWidget(search_button)
        dialog.layout.addLayout(controls)
        box = QTextEdit()
        box.setReadOnly(True)
        dialog.layout.addWidget(box, stretch=1)

        def search():
            conn = get_conn()
            rows = conn.execute("SELECT * FROM Logs WHERE user_id=?", (user_id.text(),)).fetchall()
            conn.close()
            box.setPlainText("\n".join(str(row) for row in rows))

        search_button.clicked.connect(search)
        user_id.returnPressed.connect(search)
        dialog.exec()

    def change_pin(self):
        dialog = AdminDialog(self, "Change user PIN", width=520, height=360)
        form = QFormLayout()
        user_id = QLineEdit()
        new_pin = QLineEdit()
        form.addRow(self.field_label("User ID"), user_id)
        form.addRow(self.field_label("New PIN"), new_pin)
        dialog.layout.addLayout(form)
        status = QLabel("")
        status.setObjectName("status")
        dialog.layout.addWidget(status)
        update = QPushButton("Update PIN")
        update.setObjectName("primary")
        dialog.layout.addWidget(update)

        def submit():
            if not user_id.text().strip():
                status.setText("User ID is required")
                return
            if not new_pin.text().strip():
                status.setText("New PIN is required")
                return
            conn = get_conn()
            target = conn.execute("SELECT 1 FROM Users WHERE user_id=?", (user_id.text().strip(),)).fetchone()
            if not target:
                status.setText("User not found")
            else:
                conn.execute("UPDATE Users SET pin=? WHERE user_id=?", (new_pin.text(), user_id.text().strip()))
                conn.commit()
                status.setText("PIN updated")
            conn.close()

        update.clicked.connect(submit)
        dialog.exec()

    def send_mail(self):
        importlib.reload(dlp_utils)
        dialog = AdminDialog(self, "Send document", width=760, height=520)
        form = QFormLayout()
        path = QLineEdit()
        browse = QPushButton("Browse")
        browse.clicked.connect(lambda: path.setText(QFileDialog.getOpenFileName(dialog, "Choose document")[0]))
        file_row = QHBoxLayout()
        file_row.addWidget(path)
        file_row.addWidget(browse)
        file_widget = QWidget()
        file_widget.setLayout(file_row)
        form.addRow(self.field_label("Document"), file_widget)
        recipient = QComboBox()
        recipient.addItems(dlp_utils.VERIFIED_RECIPIENTS)
        form.addRow(self.field_label("Recipient"), recipient)
        pin = QLineEdit()
        pin.setEchoMode(QLineEdit.Password)
        form.addRow(self.field_label("PIN"), pin)
        dialog.layout.addLayout(form)
        status = QLabel("")
        status.setObjectName("status")
        dialog.layout.addWidget(status)
        send_button = QPushButton("Send document")
        send_button.setObjectName("primary")
        dialog.layout.addWidget(send_button)

        def send():
            file_path = path.text().strip()
            recipient_value = recipient.currentText().strip()
            pin_value = pin.text().strip()
            if not file_path or not os.path.isfile(file_path):
                status.setText("Valid file path is required")
                return
            if not recipient_value or recipient_value not in dlp_utils.VERIFIED_RECIPIENTS:
                status.setText("Verified recipient is required")
                return
            if not pin_value:
                status.setText("PIN is required")
                return
            conn = get_conn()
            row = conn.execute("SELECT email, pin FROM Users WHERE user_id=?", (self.uid,)).fetchone()
            conn.close()
            if not row or str(row[1]).strip() != pin_value:
                status.setText("Invalid PIN")
                return
            confirm = QMessageBox.question(dialog, "Confirm send", f"Send {os.path.basename(file_path)} to {recipient_value}?")
            if confirm != QMessageBox.Yes:
                return
            try:
                send_document(file_path, self.uid, "Admin", row[0], recipient_value, pin_value)
                status.setText("Sent")
            except Exception as exc:
                status.setText(f"Send failed: {exc}")

        send_button.clicked.connect(send)
        dialog.exec()

    def manage_recipients(self):
        importlib.reload(dlp_utils)
        dialog = AdminDialog(self, "Manage verified recipients", width=700, height=620)
        box = QListWidget()
        dialog.layout.addWidget(box, stretch=1)
        new_recipient = QLineEdit()
        new_recipient.setPlaceholderText("New recipient email")
        delete_recipient = QLineEdit()
        delete_recipient.setPlaceholderText("Recipient email to delete")
        dialog.layout.addWidget(new_recipient)
        dialog.layout.addWidget(delete_recipient)
        actions = QHBoxLayout()
        add_button = QPushButton("Add recipient")
        delete_button = QPushButton("Delete recipient")
        delete_button.setObjectName("danger")
        actions.addWidget(add_button)
        actions.addWidget(delete_button)
        dialog.layout.addLayout(actions)

        def read_recipients():
            with open("dlp_utils.py") as source:
                content = source.read()
            return re.findall(r'"([^"]+)"', content.split("BLOCKED_SITES")[0])

        def write_recipients(emails):
            with open("dlp_utils.py") as source:
                content = source.read()
            new_line = "VERIFIED_RECIPIENTS = [" + ", ".join(f'"{email}"' for email in emails) + "]"
            content = re.sub(r"VERIFIED_RECIPIENTS = \[.*?\]", new_line, content, flags=re.DOTALL)
            with open("dlp_utils.py", "w") as target:
                target.write(content)

        def refresh():
            importlib.reload(dlp_utils)
            box.clear()
            box.addItems(dlp_utils.VERIFIED_RECIPIENTS)

        def add():
            email = new_recipient.text().strip()
            emails = read_recipients()
            if email and email not in emails:
                emails.append(email)
                write_recipients(emails)
            new_recipient.clear()
            refresh()

        def delete():
            email = delete_recipient.text().strip()
            write_recipients([item for item in read_recipients() if item != email])
            delete_recipient.clear()
            refresh()

        add_button.clicked.connect(add)
        delete_button.clicked.connect(delete)
        refresh()
        dialog.exec()

    def export_logs(self):
        conn = get_conn()
        rows = conn.execute("SELECT * FROM Logs").fetchall()
        conn.close()
        with open("logs_export.csv", "w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(["log_id", "doc_id", "user_id", "action", "recipient", "timestamp"])
            writer.writerows(rows)
        self.export_status.setText("Exported to logs_export.csv")

    def logout(self):
        with open("current_session.txt", "w") as session_file:
            session_file.write("0")
        if self.on_logout is not None and not self.logout_handled:
            self.logout_handled = True
            self.on_logout()
        self.close()

    def closeEvent(self, event):
        with open("current_session.txt", "w") as session_file:
            session_file.write("0")
        if self.on_logout is not None and not self.logout_handled:
            self.logout_handled = True
            self.on_logout()
        event.accept()
