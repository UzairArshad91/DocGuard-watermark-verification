import requests
import sqlite3

SERVER_PORTS = (8000, 8080, 8888, 9000, 5555)

def find_running_server():
    for port in SERVER_PORTS:
        url = f"http://127.0.0.1:{port}"
        try:
            r = requests.get(f"{url}/admin/logs", timeout=1)
            if r.ok:
                return url
        except requests.RequestException:
            pass
    return None

SERVER = find_running_server() or "http://127.0.0.1:8000"

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