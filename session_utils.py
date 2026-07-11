import socket

def get_current_user():
    try:
        with open("current_session.txt") as f:
            uid = f.read().strip()
            return uid if uid != "0" else f"unknown ({socket.gethostname()})"
    except FileNotFoundError:
        return f"unknown ({socket.gethostname()})"