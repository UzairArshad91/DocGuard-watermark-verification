import os
import time
import sqlite3
import requests
from watermarking import add_watermark, get_sig_hash
from encrypt import encrypt_id
from dlp_utils import is_verified_recipient

SERVER = "http://127.0.0.1:5000"

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

    sig = encrypt_id(user_id)
    add_watermark(filepath, name, email, user_id, sig)
    time.sleep(1)
    ext = os.path.splitext(filepath)[1].lower()
    file_hash = get_sig_hash(filepath, ext)

    requests.post(f"{SERVER}/send", json={
        "filename": os.path.abspath(filepath), "owner_id": user_id,
        "hash": file_hash, "signature": sig
    })
    requests.post(f"{SERVER}/log", json={
        "doc_id": user_id, "user_id": user_id,
        "action": "sent", "recipient": recipient
    })
    print("Document sent and logged.")