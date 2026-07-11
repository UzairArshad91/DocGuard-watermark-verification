import customtkinter as ctk
from employee import send_document
import sqlite3
from tkinter import filedialog
from dlp_utils import VERIFIED_RECIPIENTS
import os
import subprocess, sys
import time


def open_employee_gui(uid, uname):
    root = ctk.CTk()
    root.geometry("700x900")

    conn = sqlite3.connect("logs.db", timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT email FROM Users WHERE user_id=?", (uid,))
    uemail = cur.fetchone()[0]
    conn.close()

    def browse():
        f = filedialog.askopenfilename()
        path.delete(0, "end")
        path.insert(0, f)

    def send():
        send_document(path.get(), uid, uname, uemail, recipient.get(), pin.get())
        status.configure(text="Sent")

    def view_history():
        box.delete("1.0", "end")
        conn = sqlite3.connect("logs.db", timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM Logs WHERE user_id=?", (uid,))
        for row in cur.fetchall():
            box.insert("end", f"{row}\n")
        conn.close()

    def view_alerts():
        box.delete("1.0", "end")
        conn = sqlite3.connect("logs.db", timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT * FROM Alerts WHERE user_id=?", (uid,))
        for row in cur.fetchall():
            box.insert("end", f"{row}\n")
        conn.close()

    def view_recipients():
        box.delete("1.0", "end")
        from dlp_utils import VERIFIED_RECIPIENTS
        for r in VERIFIED_RECIPIENTS:
            box.insert("end", f"{r}\n")

    # centered content frame for responsive layout
    container = ctk.CTkFrame(root)
    container.pack(expand=True, fill="both", padx=30, pady=20)

    # centered container and form for a cleaner layout
    form = ctk.CTkFrame(container)
    form.pack(pady=8, fill="x")
    form.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(form, text="File Path").grid(row=0, column=0, padx=8, pady=8, sticky="e")
    path = ctk.CTkEntry(form, width=420); path.grid(row=0, column=1, padx=8, pady=8)
    ctk.CTkButton(form, text="Browse", command=browse).grid(row=0, column=2, padx=8, pady=8)

    ctk.CTkLabel(form, text=f"Email: {uemail}").grid(row=1, column=0, columnspan=3, pady=8)

    ctk.CTkLabel(form, text="Recipient").grid(row=2, column=0, padx=8, pady=8, sticky="e")
    recipient = ctk.CTkComboBox(form, values=VERIFIED_RECIPIENTS, width=420); recipient.grid(row=2, column=1, columnspan=2, padx=8, pady=8)

    ctk.CTkLabel(form, text="PIN").grid(row=3, column=0, padx=8, pady=8, sticky="e")
    pin = ctk.CTkEntry(form, width=420, show="*"); pin.grid(row=3, column=1, columnspan=2, padx=8, pady=8)

    ctk.CTkButton(container, text="Send Document", command=send).pack(pady=10)
    status = ctk.CTkLabel(container, text=""); status.pack(pady=6)

    # action buttons in a horizontal row
    actions = ctk.CTkFrame(container)
    actions.pack(pady=8)
    ctk.CTkButton(actions, text="View My Alerts", command=view_alerts).pack(side="left", padx=8)
    ctk.CTkButton(actions, text="View My History", command=view_history).pack(side="left", padx=8)
    ctk.CTkButton(actions, text="View Verified Recipients", command=view_recipients).pack(side="left", padx=8)

    box = ctk.CTkTextbox(container, width=640, height=220); box.pack(pady=8)

    def logout():
        with open("current_session.txt", "w") as f:
            f.write("0")
        import subprocess
        subprocess.Popen(["restart.bat"], shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        root.destroy()

    ctk.CTkButton(root, text="Logout", command=logout).pack(pady=10)

    def on_close():
        with open("current_session.txt", "w") as f:
            f.write("0")
        import subprocess
        subprocess.Popen(["restart.bat"], shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()