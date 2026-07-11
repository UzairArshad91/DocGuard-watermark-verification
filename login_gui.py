import customtkinter as ctk
import sqlite3
import os
import subprocess
from employee_gui import open_employee_gui
from admin_gui import open_admin_gui
import subprocess, sys
sqlite3.connect("logs.db").execute("PRAGMA journal_mode=WAL;")
subprocess.Popen([sys.executable, "main.py"])
subprocess.Popen([sys.executable, "service_watchdog.py"])
subprocess.Popen([sys.executable, "file_watcher.py"])

ctk.set_appearance_mode("dark")

def get_conn():
    return sqlite3.connect("logs.db", timeout=10)

def show_login():
    name.delete(0, "end")
    pin.delete(0, "end")
    status.configure(text="")
    root.deiconify()
    root.lift()
    root.focus_force()


def login():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, role FROM Users WHERE name=? AND pin=?", (name.get(), pin.get()))
    row = cur.fetchone()
    conn.close()
    if not row:
        status.configure(text="Invalid login")
        return
    uid, role = row
    with open("current_session.txt", "w") as f:
        f.write(str(uid))
    uname = name.get()
    root.withdraw()
    if role == "admin":
        open_admin_gui(uid, on_logout=show_login)
    else:
        open_employee_gui(uid, uname, on_logout=show_login)
        

def admin_close():
    os.system("taskkill /F /IM python.exe /T & taskkill /F /IM pythonw.exe /T")

# def admin_close():
#     win = ctk.CTkToplevel(root)
#     win.geometry("300x200")
#     win.attributes("-topmost", True)
#     ctk.CTkLabel(win, text="Admin Name").pack(); n = ctk.CTkEntry(win); n.pack()
#     ctk.CTkLabel(win, text="PIN").pack(); p = ctk.CTkEntry(win, show="*"); p.pack()
#     status = ctk.CTkLabel(win, text=""); status.pack()

#     def confirm():
#         conn = get_conn(); cur = conn.cursor()
#         cur.execute("SELECT * FROM Users WHERE name=? AND pin=? AND role='admin'", (n.get(), p.get()))
#         if cur.fetchone():
#             conn.close()
#             os.system("taskkill /F /IM python.exe /T & taskkill /F /IM pythonw.exe /T")
#         else:
#             status.configure(text="Access denied")
#             conn.close()

#     ctk.CTkButton(win, text="Confirm Close", command=confirm).pack(pady=10)

def on_close():
    with open("current_session.txt", "w") as f:
        f.write("0")
    subprocess.Popen(["restart.bat"], shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    root.destroy()

root = ctk.CTk()
root.geometry("700x500")
# use a centered container so widgets stay centered as window size changes
container = ctk.CTkFrame(root)
container.pack(expand=True, fill="both", padx=40, pady=40)

ctk.CTkLabel(container, text="Name").pack(pady=6)
name = ctk.CTkEntry(container); name.pack(pady=6)
ctk.CTkLabel(container, text="PIN").pack(pady=6)
pin = ctk.CTkEntry(container, show="*"); pin.pack(pady=6)
ctk.CTkButton(container, text="Login", command=login).pack(pady=16)
status = ctk.CTkLabel(container, text=""); status.pack(pady=6)
ctk.CTkButton(container, text="Close App (Admin)", command=admin_close).pack(pady=6)

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()