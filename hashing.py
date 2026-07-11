import hashlib

def get_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def verify_hash(filepath, stored_hash):
    return get_file_hash(filepath) == stored_hash