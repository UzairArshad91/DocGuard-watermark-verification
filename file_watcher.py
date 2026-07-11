from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests, sqlite3, os, time
from watermarking import get_sig_hash
from session_utils import get_current_user



class Handler(FileSystemEventHandler):
    last_fired = {}
    def on_modified(self, event):
        now = time.time()
        if event.src_path in self.last_fired and now - self.last_fired[event.src_path] < 3:
            return
        self.last_fired[event.src_path] = now
        time.sleep(2)
        print("Modified:", event.src_path)
        try:
            conn = sqlite3.connect("logs.db", timeout=10)
            cur = conn.cursor()
            cur.execute("SELECT doc_id FROM Documents WHERE filename=? COLLATE NOCASE ORDER BY doc_id DESC LIMIT 1", (os.path.abspath(event.src_path),))
            row = cur.fetchone()
            conn.close()
            if row:
                doc_id = row[0]
                uid = get_current_user()
                ext = os.path.splitext(event.src_path)[1].lower()
                h = get_sig_hash(event.src_path, ext)
                requests.post("http://127.0.0.1:5000/verify", json={"doc_id": doc_id, "user_id": uid, "current_hash": h})
        except Exception as e:
            print("Skipped:", e)

observer = Observer()
handler = Handler()
observer.schedule(handler, path=os.path.dirname(os.path.abspath(__file__)), recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()