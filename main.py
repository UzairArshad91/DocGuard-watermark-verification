from flask import Flask, request, jsonify
import sqlite3
from smtp import send_email_alert
from datetime import datetime
import os

app = Flask(__name__)

def get_db():
    return sqlite3.connect("logs.db", timeout=10)

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO Documents (filename, owner_id, original_hash, encrypted_signature) VALUES (?,?,?,?)",
                (data["filename"], data["owner_id"], data["hash"], data["signature"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT original_hash FROM Documents WHERE doc_id=?", (data["doc_id"],))
    row = cur.fetchone()
    conn.close()
    match = row and row[0] == data["current_hash"]
    if not match:
        log_alert(data["doc_id"], data["user_id"], "hash mismatch")
    return jsonify({"match": bool(match)})

@app.route("/log", methods=["POST"])
def log():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO Logs (doc_id, user_id, action, recipient, timestamp) VALUES (?,?,?,?,?)",
            (data["doc_id"], data["user_id"], data["action"], data.get("recipient"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/alert", methods=["POST"])
def alert():
    data = request.json
    log_alert(data["doc_id"], data["user_id"], data["reason"])
    return jsonify({"status": "ok"})

def log_alert(doc_id, user_id, reason):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM Documents WHERE doc_id=?", (doc_id,))
    row = cur.fetchone()
    filename = os.path.basename(row[0]) if row else "unknown"
    cur.execute("INSERT INTO Alerts (doc_id, user_id, reason, timestamp) VALUES (?,?,?,?)",
                (doc_id, user_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    send_email_alert(reason, user_id, doc_id, filename)

@app.route("/admin/logs", methods=["GET"])
def admin_logs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Logs")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)