import os
import time
import requests
from watermarking import add_watermark, get_sig_hash
from encrypt import encrypt_id
from dlp_utils import is_verified_recipient

SERVER = "http://127.0.0.1:5000"

def send_document(filepath, user_id, name, email, recipient, pin):
    if not is_verified_recipient(recipient):
        print("Blocked: recipient not verified")
        return

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