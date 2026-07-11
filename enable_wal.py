import sqlite3
conn = sqlite3.connect("logs.db")
conn.execute("PRAGMA journal_mode=WAL;")
conn.close()