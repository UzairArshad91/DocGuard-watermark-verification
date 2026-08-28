import sys

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from employee import send_document


STYLE = """
QMainWindow { background: #11161C; }
QLabel#brand { color: #55C2A3; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F3F6F8; font-size: 26px; font-weight: 700; }
QLabel#fieldLabel, QLabel#status { color: #95A4B2; }
QLineEdit { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 6px; padding: 8px 10px; }
QLineEdit:focus { border: 2px solid #55C2A3; }
QPushButton { background: #202B36; color: #F3F6F8; border: 1px solid #31404D; border-radius: 7px; padding: 8px 14px; min-height: 34px; }
QPushButton:hover { background: #31404D; }
QPushButton#primary { background: #55C2A3; color: #10211D; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #43A98E; }
"""


class DocumentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocGuard | Send document")
        self.setMinimumSize(620, 420)
        self.resize(700, 480)
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
        title = QLabel("Send document")
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(12)
        self.path = QLineEdit()
        self.path.setPlaceholderText("Choose a document")
        browse = QPushButton("Browse")
        browse.clicked.connect(self.browse)
        file_row = QHBoxLayout()
        file_row.addWidget(self.path)
        file_row.addWidget(browse)
        file_widget = QWidget()
        file_widget.setLayout(file_row)
        form.addRow(self.field_label("File path"), file_widget)

        self.name = QLineEdit()
        form.addRow(self.field_label("Name"), self.name)
        self.email = QLineEdit()
        form.addRow(self.field_label("Email"), self.email)
        self.recipient = QLineEdit()
        form.addRow(self.field_label("Recipient"), self.recipient)
        self.pin = QLineEdit()
        self.pin.setEchoMode(QLineEdit.Password)
        form.addRow(self.field_label("PIN"), self.pin)
        layout.addLayout(form)

        send = QPushButton("Send")
        send.setObjectName("primary")
        send.clicked.connect(self.submit)
        layout.addWidget(send)
        self.status = QLabel("")
        self.status.setObjectName("status")
        layout.addWidget(self.status)
        layout.addStretch()
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

    def submit(self):
        try:
            send_document(self.path.text(), 1, self.name.text(), self.email.text(), self.recipient.text(), self.pin.text())
            self.status.setText("Sent")
        except Exception as exc:
            self.status.setText(f"Send failed: {exc}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DocumentWindow()
    window.show()
    sys.exit(app.exec())
