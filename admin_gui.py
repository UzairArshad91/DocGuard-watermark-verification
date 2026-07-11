import customtkinter as ctk
import sqlite3, csv
from employee import send_document
from tkinter import filedialog, messagebox
from dlp_utils import is_verified_recipient
import os
import time
import subprocess, sys
from dlp_utils import VERIFIED_RECIPIENTS

def get_conn():
    return sqlite3.connect("logs.db", timeout=10)


def open_admin_gui(uid, on_logout=None):
    root = ctk.CTk()
    root.title("Admin Panel")
    root.geometry("650x650")
    for i in range(2):
        root.grid_columnconfigure(i, weight=1)

    # give top and bottom flexible spacing so content centers vertically
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(7, weight=1)

    def open_window(title, builder, size="800x700"):
        win = ctk.CTkToplevel(root)
        win.title(title)
        win.geometry(size)
        # make the window transient to the admin root and bring it to front
        try:
            win.transient(root)
            win.attributes("-topmost", True)
            win.lift()
            win.focus_force()
        except Exception:
            pass
        builder(win)
        # clear topmost flag so it doesn't stay always on top of other apps
        try:
            win.attributes("-topmost", False)
        except Exception:
            pass

    # ---------- Manage DB ----------
    def manage_db(win):
        # create a simple tab-like area inside the same window
        menu = ctk.CTkFrame(win)
        menu.pack(fill="x", pady=8)

        content = ctk.CTkFrame(win)
        content.pack(expand=True, fill="both", padx=10, pady=10)

        def clear_content():
            for w in content.winfo_children():
                w.destroy()

        def show_view():
            clear_content()
            box = ctk.CTkTextbox(content, width=550, height=300)
            box.pack(pady=10, fill="both", expand=True)
            conn = get_conn(); cur = conn.cursor()
            cur.execute("SELECT * FROM Users")
            for row in cur.fetchall():
                box.insert("end", f"{row}\n")
            conn.close()

        def show_add():
            clear_content()
            frm = ctk.CTkFrame(content)
            frm.pack(pady=8)
            ctk.CTkLabel(frm, text="Name").grid(row=0, column=0, padx=10, pady=5)
            nm = ctk.CTkEntry(frm); nm.grid(row=0, column=1)
            ctk.CTkLabel(frm, text="Email").grid(row=1, column=0, padx=10, pady=5)
            em = ctk.CTkEntry(frm); em.grid(row=1, column=1)
            ctk.CTkLabel(frm, text="PIN").grid(row=2, column=0, padx=10, pady=5)
            pn = ctk.CTkEntry(frm); pn.grid(row=2, column=1)
            role = ctk.StringVar(value="employee")
            ctk.CTkRadioButton(frm, text="Admin", variable=role, value="admin").grid(row=3, column=0)
            ctk.CTkRadioButton(frm, text="Employee", variable=role, value="employee").grid(row=3, column=1)
            status = ctk.CTkLabel(frm, text=""); status.grid(row=5, column=0, columnspan=2)
            status_clear_job = None

            def clear_status():
                nonlocal status_clear_job
                status.configure(text="")
                status_clear_job = None

            def set_status(message):
                nonlocal status_clear_job
                if status_clear_job is not None:
                    frm.after_cancel(status_clear_job)
                status.configure(text=message)
                status_clear_job = frm.after(2000, clear_status)

            def submit_add():
                if not nm.get() or not em.get() or not pn.get():
                    set_status("All fields required")
                    return
                conn = get_conn(); cur = conn.cursor()
                cur.execute("INSERT INTO Users (name, email, pin, role) VALUES (?,?,?,?)",
                            (nm.get(), em.get(), pn.get(), role.get()))
                conn.commit(); conn.close()
                set_status("User added")

            ctk.CTkButton(frm, text="Add", command=submit_add).grid(row=4, column=0, columnspan=2, pady=10)

        def show_delete():
            clear_content()
            frm = ctk.CTkFrame(content)
            frm.pack(pady=8)
            ctk.CTkLabel(frm, text="User ID").grid(row=0, column=0, padx=10, pady=10)
            uid_e = ctk.CTkEntry(frm); uid_e.grid(row=0, column=1)
            status = ctk.CTkLabel(frm, text=""); status.grid(row=2, column=0, columnspan=2)
            status_clear_job = None

            def clear_status():
                nonlocal status_clear_job
                status.configure(text="")
                status_clear_job = None

            def set_status(message):
                nonlocal status_clear_job
                if status_clear_job is not None:
                    frm.after_cancel(status_clear_job)
                status.configure(text=message)
                status_clear_job = frm.after(2000, clear_status)

            def submit_delete():
                user_id = uid_e.get().strip()
                if not user_id:
                    set_status("User ID is required")
                    return
                conn = get_conn(); cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM Users WHERE role='admin'")
                admin_count = cur.fetchone()[0]
                cur.execute("SELECT role FROM Users WHERE user_id=?", (user_id,))
                target = cur.fetchone()
                if not target:
                    set_status("User not found")
                    conn.close()
                    return
                if target[0] == "admin" and admin_count <= 1:
                    set_status("Cannot delete last admin")
                    conn.close()
                    return
                cur.execute("DELETE FROM Users WHERE user_id=?", (user_id,))
                conn.commit(); conn.close()
                set_status("User deleted")

            ctk.CTkButton(frm, text="Delete", command=submit_delete).grid(row=1, column=0, columnspan=2, pady=10)

        ctk.CTkButton(menu, text="View Users", command=show_view).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(menu, text="Add User", command=show_add).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(menu, text="Delete User", command=show_delete).pack(side="left", padx=6, pady=6)

        # default view
        show_view()

    # ---------- View Logs ----------
    
    def view_logs(win):
        box = ctk.CTkTextbox(win, width=550, height=400); box.pack(pady=10)
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""SELECT Logs.log_id, Documents.filename, Logs.user_id, Logs.action, Logs.recipient, Logs.timestamp
               FROM Logs JOIN Documents ON Logs.doc_id = Documents.doc_id""")
        for row in cur.fetchall():
            r = list(row)
            r[1] = os.path.basename(r[1])
            box.insert("end", f"{r}\n")
        conn.close()

        def clear_logs():
            conn = get_conn(); cur = conn.cursor()
            cur.execute("DELETE FROM Logs")
            conn.commit(); conn.close()
            box.delete("1.0", "end")

        ctk.CTkButton(win, text="Clear Logs", command=clear_logs).pack(pady=10)

    # ---------- View Alerts ----------
    
    def view_alerts(win):
        box = ctk.CTkTextbox(win, width=550, height=400); box.pack(pady=10)
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""SELECT Alerts.alert_id, Documents.filename, Alerts.user_id, Alerts.reason, Alerts.timestamp
            FROM Alerts JOIN Documents ON Alerts.doc_id = Documents.doc_id""")
        for row in cur.fetchall():
            r = list(row)
            r[1] = os.path.basename(r[1])
            box.insert("end", f"{r}\n")
        conn.close()

        def clear_alerts():
            conn = get_conn(); cur = conn.cursor()
            cur.execute("DELETE FROM Alerts")
            conn.commit(); conn.close()
            box.delete("1.0", "end")

        ctk.CTkButton(win, text="Clear Alerts", command=clear_alerts).pack(pady=10)

    # ---------- Search Logs by Employee ----------
    def search_logs(win):
        ctk.CTkLabel(win, text="User ID").grid(row=0, column=0, padx=10, pady=10)
        uid_e = ctk.CTkEntry(win); uid_e.grid(row=0, column=1)
        box = ctk.CTkTextbox(win, width=550, height=350)

        def search():
            box.delete("1.0", "end")
            conn = get_conn(); cur = conn.cursor()
            cur.execute("SELECT * FROM Logs WHERE user_id=?", (uid_e.get(),))
            for row in cur.fetchall():
                box.insert("end", f"{row}\n")
            conn.close()

        ctk.CTkButton(win, text="Search", command=search).grid(row=0, column=2, padx=10)
        box.grid(row=1, column=0, columnspan=3, pady=10)

    # ---------- Change PIN ----------
    def change_pin(win):
        ctk.CTkLabel(win, text="User ID").grid(row=0, column=0, padx=10, pady=10)
        uid_e = ctk.CTkEntry(win); uid_e.grid(row=0, column=1)
        ctk.CTkLabel(win, text="New PIN").grid(row=1, column=0, padx=10, pady=10)
        pin_e = ctk.CTkEntry(win); pin_e.grid(row=1, column=1)
        status = ctk.CTkLabel(win, text=""); status.grid(row=3, column=0, columnspan=2)

        def submit():
            user_id = uid_e.get().strip()
            new_pin = pin_e.get().strip()
            if not user_id:
                status.configure(text="User ID is required")
                return
            if not new_pin:
                status.configure(text="New PIN is required")
                return
            conn = get_conn(); cur = conn.cursor()
            cur.execute("SELECT 1 FROM Users WHERE user_id=?", (user_id,))
            target = cur.fetchone()
            if not target:
                conn.close()
                status.configure(text="User not found")
                return
            cur.execute("UPDATE Users SET pin=? WHERE user_id=?", (new_pin, user_id))
            conn.commit(); conn.close()
            status.configure(text="PIN updated")
            win.destroy()

        ctk.CTkButton(win, text="Update", command=submit).grid(row=2, column=0, columnspan=2, pady=10)


    def send_mail(win):
        import importlib, dlp_utils
        importlib.reload(dlp_utils)
        
        def browse():
            f = filedialog.askopenfilename()
            path.delete(0, "end")
            path.insert(0, f)

        def send():
            file_path = path.get().strip()
            if not file_path:
                status.configure(text="File path is required")
                messagebox.showwarning("No file", "Please select a file to send.")
                return
            if not os.path.isfile(file_path):
                status.configure(text="Invalid file path")
                messagebox.showwarning("Invalid file", "File path is invalid or file does not exist.")
                return

            recipient_value = recipient.get().strip()
            if not recipient_value:
                status.configure(text="Recipient is required")
                messagebox.showwarning("No recipient", "Please select a recipient.")
                return
            if recipient_value not in dlp_utils.VERIFIED_RECIPIENTS:
                status.configure(text="Blocked: recipient not verified")
                messagebox.showwarning("Blocked", "Recipient not verified")
                return

            pin_value = pin.get().strip()
            if not pin_value:
                status.configure(text="PIN is required")
                messagebox.showwarning("No PIN", "Please enter your PIN.")
                return

            conn = get_conn(); cur = conn.cursor()
            cur.execute("SELECT pin FROM Users WHERE user_id=?", (uid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                status.configure(text="User record not found")
                messagebox.showerror("Error", "User record not found.")
                return
            if str(row[0]).strip() != pin_value:
                status.configure(text="Invalid PIN")
                messagebox.showwarning("Wrong PIN", "The PIN you entered is incorrect.")
                return

            confirm = messagebox.askyesno("Confirm Send", f"Send:\n{os.path.basename(file_path)}\n to {recipient_value}?")
            if not confirm:
                return
            try:
                send_document(file_path, uid, "Admin", uemail, recipient_value, pin_value)
                status.configure(text="Sent")
                messagebox.showinfo("Sent", "Document sent successfully.")
            except Exception as e:
                status.configure(text="Send failed")
                messagebox.showerror("Error", f"Failed to send: {e}")

        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT email FROM Users WHERE user_id=?", (uid,))
        uemail = cur.fetchone()[0]
        conn.close()

        # centered form container for uniform spacing
        container = ctk.CTkFrame(win)
        container.pack(expand=True, fill="both", padx=24, pady=16)

        form = ctk.CTkFrame(container)
        form.pack(pady=6)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="File Path").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        path = ctk.CTkEntry(form, width=420); path.grid(row=0, column=1, padx=8, pady=8)
        ctk.CTkButton(form, text="Browse", command=browse).grid(row=0, column=2, padx=8, pady=8)

        ctk.CTkLabel(form, text=f"Email: {uemail}").grid(row=1, column=0, columnspan=3, pady=10)

        ctk.CTkLabel(form, text="Recipient").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        recipient = ctk.CTkComboBox(form, values=dlp_utils.VERIFIED_RECIPIENTS, width=420, state="readonly"); recipient.grid(row=2, column=1, columnspan=2, padx=8, pady=8)

        ctk.CTkLabel(form, text="PIN").grid(row=3, column=0, padx=8, pady=8, sticky="e")
        pin = ctk.CTkEntry(form, width=420, show="*"); pin.grid(row=3, column=1, columnspan=2, padx=8, pady=8)

        ctk.CTkButton(container, text="Send Document", command=send).pack(pady=12)
        status = ctk.CTkLabel(container, text=""); status.pack()
    # ---------- Verified Recipients ----------
    def manage_recipients(win):
        from dlp_utils import VERIFIED_RECIPIENTS
        import importlib, dlp_utils

        box = ctk.CTkTextbox(win, width=550, height=300)
        for r in VERIFIED_RECIPIENTS:
            box.insert("end", f"{r}\n")
        box.grid(row=0, column=0, columnspan=2, pady=10)
        def refresh_box():
            importlib.reload(dlp_utils)
            box.delete("1.0", "end")
            for r in dlp_utils.VERIFIED_RECIPIENTS:
                box.insert("end", f"{r}\n")

        ctk.CTkLabel(win, text="New Recipient Email").grid(row=1, column=0, padx=10, pady=10)
        new_r = ctk.CTkEntry(win); new_r.grid(row=1, column=1)
        status = ctk.CTkLabel(win, text=""); status.grid(row=3, column=0, columnspan=2)

        def add():
            import re, dlp_utils
            with open("dlp_utils.py") as f:
                content = f.read()
            emails = re.findall(r'"([^"]+)"', content.split("BLOCKED_SITES")[0])
            if new_r.get() not in emails:
                emails.append(new_r.get())
            new_line = "VERIFIED_RECIPIENTS = [" + ", ".join(f'"{e}"' for e in emails) + "]"
            content = re.sub(r"VERIFIED_RECIPIENTS = \[.*?\]", new_line, content, flags=re.DOTALL)
            with open("dlp_utils.py", "w") as f:
                f.write(content)
            refresh_box()

        def delete_recipient(email):
            import re
            with open("dlp_utils.py") as f:
                content = f.read()
            emails = re.findall(r'"([^"]+)"', content.split("BLOCKED_SITES")[0])
            emails = [e for e in emails if e != email]
            new_line = "VERIFIED_RECIPIENTS = [" + ", ".join(f'"{e}"' for e in emails) + "]"
            content = re.sub(r"VERIFIED_RECIPIENTS = \[.*?\]", new_line, content, flags=re.DOTALL)
            with open("dlp_utils.py", "w") as f:
                f.write(content)

        ctk.CTkButton(win, text="Add Recipient", command=add).grid(row=2, column=0, columnspan=2, pady=10)
        ctk.CTkLabel(win, text="Recipient to Delete").grid(row=4, column=0, padx=10, pady=10)
        del_r = ctk.CTkEntry(win); del_r.grid(row=4, column=1)

        def delete():
            delete_recipient(del_r.get())
            refresh_box()

        ctk.CTkButton(win, text="Delete Recipient", command=delete).grid(row=5, column=0, columnspan=2, pady=10)

    # ---------- Export CSV ----------
    def export_logs():
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM Logs")
        rows = cur.fetchall()
        conn.close()
        with open("logs_export.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["log_id", "doc_id", "user_id", "action", "recipient", "timestamp"])
            writer.writerows(rows)
        export_status.configure(text="Exported to logs_export.csv")

    

    # ---------- Main Menu Layout (grid: 2 columns) ----------
    ctk.CTkLabel(root, text="Admin Panel", font=("Arial", 18, "bold")).grid(row=1, column=0, columnspan=2, pady=15)

    # group buttons in a centered frame for uniform spacing
    menu_frame = ctk.CTkFrame(root)
    menu_frame.grid(row=2, column=0, columnspan=2, pady=8)

    btn_w = 200
    btn_pad = 8
    ctk.CTkButton(menu_frame, text="Manage DB", width=btn_w, command=lambda: open_window("Manage DB", manage_db)).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="View All Logs", width=btn_w, command=lambda: open_window("Logs", view_logs)).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="View Alerts", width=btn_w, command=lambda: open_window("Alerts", view_alerts)).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="Search Logs by Employee", width=btn_w, command=lambda: open_window("Search Logs", search_logs)).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="Change User PIN", width=btn_w, command=lambda: open_window("Change PIN", change_pin)).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="Verified Recipients", width=btn_w, command=lambda: open_window("Recipients", manage_recipients, "600x650")).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="Export Logs (CSV)", width=btn_w, command=export_logs).pack(pady=btn_pad)
    ctk.CTkButton(menu_frame, text="Send Document", width=btn_w, command=lambda: open_window("Send Document", send_mail)).pack(pady=btn_pad)

    export_status = ctk.CTkLabel(root, text=""); export_status.grid(row=3, column=0, columnspan=2)

    def logout():
        with open("current_session.txt", "w") as f:
            f.write("0")
        if on_logout is not None:
            on_logout()
        root.destroy()

    ctk.CTkButton(root, text="Logout", command=logout).grid(row=6, column=0, columnspan=2, pady=10)


    def on_close():
        with open("current_session.txt", "w") as f:
            f.write("0")
        if on_logout is not None:
            on_logout()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()