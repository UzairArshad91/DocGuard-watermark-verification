import tkinter as tk
import sqlite3

def get_conn():
    return sqlite3.connect("logs.db")

def main_menu():
    for w in root.winfo_children(): w.destroy()
    tk.Button(root, text="View Users", command=view_users, width=20).pack(pady=10)
    tk.Button(root, text="Add User", command=add_user_screen, width=20).pack(pady=10)
    tk.Button(root, text="Delete User", command=delete_user_screen, width=20).pack(pady=10)

def view_users():
    for w in root.winfo_children(): w.destroy()
    box = tk.Text(root, width=70, height=25)
    box.pack()
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM Users")
    for row in cur.fetchall():
        box.insert(tk.END, f"{row}\n")
    conn.close()
    tk.Button(root, text="Back", command=main_menu).pack()

def add_user_screen():
    for w in root.winfo_children(): w.destroy()
    tk.Label(root, text="Name").pack(); name = tk.Entry(root); name.pack()
    tk.Label(root, text="Email").pack(); email = tk.Entry(root); email.pack()
    tk.Label(root, text="PIN").pack(); pin = tk.Entry(root); pin.pack()
    tk.Label(root, text="Role").pack()
    role = tk.StringVar(value="employee")
    tk.Radiobutton(root, text="Admin", variable=role, value="admin").pack()
    tk.Radiobutton(root, text="Employee", variable=role, value="employee").pack()
    status = tk.Label(root, text=""); status.pack()

    def submit():
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO Users (name, email, pin, role) VALUES (?,?,?,?)",
                    (name.get(), email.get(), pin.get(), role.get()))
        conn.commit(); conn.close()
        status.config(text="User added")

    tk.Button(root, text="Add", command=submit).pack(pady=5)
    tk.Button(root, text="Back", command=main_menu).pack()

def delete_user_screen():
    for w in root.winfo_children(): w.destroy()
    tk.Label(root, text="User ID to delete").pack()
    uid = tk.Entry(root); uid.pack()
    status = tk.Label(root, text=""); status.pack()

    def submit():
        conn = get_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM Users WHERE user_id=?", (uid.get(),))
        conn.commit(); conn.close()
        status.config(text="User deleted")

    tk.Button(root, text="Delete", command=submit).pack(pady=5)
    tk.Button(root, text="Back", command=main_menu).pack()

root = tk.Tk()
root.geometry("600x600")
main_menu()
root.mainloop()