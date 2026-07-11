import pyperclip, time
from smtp import send_email_alert

def monitor_clipboard(doc_signature, doc_id, user_id):
    last = ""
    while True:
        current = pyperclip.paste()
        if current != last:
            if doc_signature in current:
                send_email_alert("clipboard copy detected", user_id, doc_id)
            last = current
        time.sleep(1)