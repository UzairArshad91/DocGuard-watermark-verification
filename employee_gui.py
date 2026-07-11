import customtkinter as ctk
from employee import send_document
import sqlite3
from tkinter import filedialog, messagebox
from dlp_utils import VERIFIED_RECIPIENTS
import os
import subprocess, sys
import time


def open_employee_gui(uid, uname, on_logout=None):
    root = ctk.CTk()
    root.geometry("700x900")
    status_clear_job = None

    conn = sqlite3.connect("logs.db", timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT email FROM Users WHERE user_id=?", (uid,))
    uemail = cur.fetchone()[0]
    conn.close()

    def browse():
        f = filedialog.askopenfilename()
        path.delete(0, "end")
        path.insert(0, f)

    def clear_status():
        nonlocal status_clear_job
        status.configure(text="")
        status_clear_job = None

    def set_status(message, clear_after_ms=2000):
        nonlocal status_clear_job
        if status_clear_job is not None:
            root.after_cancel(status_clear_job)
            status_clear_job = None
        status.configure(text=message)
        if message:
            status_clear_job = root.after(clear_after_ms, clear_status)

    def send():
        file_path = path.get().strip()
        if not file_path:
            set_status("File path is required", clear_after_ms=4000)
            return
        if not os.path.isfile(file_path):
            set_status("File path is invalid or file does not exist", clear_after_ms=4000)
            return
        recipient_value = recipient.get().strip()
        if not recipient_value:
            set_status("Recipient is required", clear_after_ms=4000)
            return
        if recipient_value not in VERIFIED_RECIPIENTS:
            set_status("Recipient must be selected from the verified list", clear_after_ms=4000)
            return
        if not pin.get().strip():
            set_status("PIN is required", clear_after_ms=4000)
            return

        file_name = os.path.basename(file_path)
        confirm = messagebox.askyesno(
            "Confirm Send",
            f"Do you want to send {file_name} to {recipient_value}?"
        )
        if not confirm:
            return

        try:
            send_document(file_path, uid, uname, uemail, recipient_value, pin.get())
        except ValueError as exc:
            set_status(str(exc), clear_after_ms=4000)
            return
        except Exception as exc:
            set_status(f"Send failed: {exc}", clear_after_ms=4000)
            return
        set_status("Sent")

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
    recipient = ctk.CTkComboBox(form, values=VERIFIED_RECIPIENTS, width=420, state="readonly"); recipient.grid(row=2, column=1, columnspan=2, padx=8, pady=8)

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
        if on_logout is not None:
            on_logout()
        root.destroy()

    ctk.CTkButton(container, text="Logout", command=logout).pack(pady=(2, 8))

    def on_close():
        with open("current_session.txt", "w") as f:
            f.write("0")
        if on_logout is not None:
            on_logout()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()