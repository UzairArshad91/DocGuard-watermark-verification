from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests, sqlite3, os, time
from watermarking import get_sig_hash
from session_utils import get_current_user

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


class Handler(FileSystemEventHandler):
    last_fired = {}
    last_hash = {}

    def on_modified(self, event):
        src_path = os.path.abspath(event.src_path)
        if not os.path.isfile(src_path):
            return

        ext = os.path.splitext(src_path)[1].lower()
        if ext not in {".docx", ".pdf", ".xlsx", ".xls"}:
            return

        now = time.time()
        if src_path in self.last_fired and now - self.last_fired[src_path] < 3:
            return
        self.last_fired[src_path] = now

        try:
            h = get_sig_hash(src_path, ext)
        except Exception:
            return

        if src_path in self.last_hash and self.last_hash[src_path] == h:
            return
        self.last_hash[src_path] = h

        time.sleep(1)
        print("Modified:", src_path)
        try:
            conn = sqlite3.connect("logs.db", timeout=10)
            cur = conn.cursor()
            cur.execute("SELECT doc_id FROM Documents WHERE filename=? COLLATE NOCASE ORDER BY doc_id DESC LIMIT 1", (src_path,))
            row = cur.fetchone()
            conn.close()
            if row:
                doc_id = row[0]
                uid = get_current_user()
                server = find_running_server()
                if server:
                    requests.post(f"{server}/verify", json={"doc_id": doc_id, "user_id": uid, "current_hash": h})
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