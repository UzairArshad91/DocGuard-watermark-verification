import pyperclip, time

def monitor_clipboard(doc_signature):
    last = ""
    while True:
        current = pyperclip.paste()
        if current != last:
            if doc_signature in current:
                print("ALERT: protected content copied")
            last = current
        time.sleep(1)