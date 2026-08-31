import os
import subprocess
import sys
import time
import sqlite3
import requests
from watermarking import add_watermark, get_sig_hash
from encrypt import encrypt_id
from dlp_utils import is_verified_recipient

SERVER = "http://127.0.0.1:5000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_server():
    try:
        requests.get(f"{SERVER}/admin/logs", timeout=1).raise_for_status()
        return
    except requests.RequestException:
        subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "main.py")], cwd=BASE_DIR)

    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            requests.get(f"{SERVER}/admin/logs", timeout=1).raise_for_status()
            return
        except requests.RequestException:
            time.sleep(0.2)
    raise ConnectionError("DocGuard server could not be started")

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