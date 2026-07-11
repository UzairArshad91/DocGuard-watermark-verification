import sqlite3

conn = sqlite3.connect("logs.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    pin TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin','employee')) NOT NULL
)
""")

cur.execute("""
CREATE TABLE Documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    owner_id INTEGER,
    original_hash TEXT,
    encrypted_signature TEXT,
    FOREIGN KEY(owner_id) REFERENCES Users(user_id)
)
""")

cur.execute("""
CREATE TABLE Logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER,
    user_id INTEGER,
    action TEXT,
    recipient TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(doc_id) REFERENCES Documents(doc_id),
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)
""")

cur.execute("""
CREATE TABLE Alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER,
    user_id INTEGER,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(doc_id) REFERENCES Documents(doc_id),
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
)
""")

conn.commit()
conn.close()