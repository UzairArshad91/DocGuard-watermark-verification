import requests
import sqlite3

SERVER = "http://127.0.0.1:5000"

def admin_login(username, password):
    conn = sqlite3.connect("logs.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM Users WHERE name=? AND pin=? AND role='admin'", (username, password))
    row = cur.fetchone()
    conn.close()
    return row is not None

def get_logs():
    r = requests.get(f"{SERVER}/admin/logs")
    for row in r.json():
        print(row)

if __name__ == "__main__":
    name = input("Admin username: ")
    pw = input("Admin password: ")
    if admin_login(name, pw):
        get_logs()
    else:
        print("Access denied")