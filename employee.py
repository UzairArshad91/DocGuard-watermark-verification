import os
import socket
import subprocess
import sys
import time
import sqlite3
import requests
from watermarking import add_watermark, get_sig_hash
from encrypt import encrypt_id
from dlp_utils import is_verified_recipient

SERVER_PORTS = (5000, 5001)
SERVER = "http://127.0.0.1:5000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_available_server_port():
    for port in SERVER_PORTS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise ConnectionError("No free DocGuard server port available (5000 or 5001)")


def find_running_server():
    for port in SERVER_PORTS:
        url = f"http://127.0.0.1:{port}"
        try:
            response = requests.get(f"{url}/admin/logs", timeout=1)
            if response.ok:
                return url
        except requests.RequestException:
            pass
    return None


def ensure_server():
    global SERVER

    running = find_running_server()
    if running:
        SERVER = running
        return

    port = get_available_server_port()
    SERVER = f"http://127.0.0.1:{port}"
    startup_timeout = 30

    subprocess.Popen(
        [sys.executable, "-u", os.path.join(BASE_DIR, "main.py")],
        cwd=BASE_DIR,
        env={**os.environ, "DOCGUARD_PORT": str(port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        running = find_running_server()
        if running:
            SERVER = running
            return
        time.sleep(0.5)

    raise ConnectionError(
        f"DocGuard server could not be started within {startup_timeout}s at {SERVER}. "
        "Check that port 5000 or 5001 is free."
    )

def send_document(filepath, user_id, name, email, recipient, pin):
    if not filepath or not filepath.strip():
        raise ValueError("File path is required")
    if not os.path.isfile(filepath):
        raise FileNotFoundError("File path is invalid or file does not exist")
    if not recipient or not recipient.strip():
        raise ValueError("Recipient is required")
    if not pin or not pin.strip():
        raise ValueError("PIN is required")

    conn = sqlite3.connect("logs.db", timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT pin FROM Users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise ValueError("User record not found")
    if str(row[0]).strip() != str(pin).strip():
        raise ValueError("Invalid PIN")

    if not is_verified_recipient(recipient):
        raise ValueError("Blocked: recipient not verified")

    ensure_server()
    sig = encrypt_id(user_id)
    add_watermark(filepath, name, email, user_id, sig)
    time.sleep(1)
    ext = os.path.splitext(filepath)[1].lower()
    file_hash = get_sig_hash(filepath, ext)

    requests.post(f"{SERVER}/send", timeout=10, json={
        "filename": os.path.abspath(filepath), "owner_id": user_id,
        "hash": file_hash, "signature": sig
    })
    requests.post(f"{SERVER}/log", timeout=10, json={
        "doc_id": user_id, "user_id": user_id,
        "action": "sent", "recipient": recipient
    })
    print("Document sent and logged.")