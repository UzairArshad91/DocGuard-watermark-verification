from cryptography.fernet import Fernet

key = Fernet.generate_key()  # store this securely, reuse across app
f = Fernet(key)

def encrypt_id(user_id):
    return f.encrypt(str(user_id).encode()).decode()

def decrypt_id(token):
    return f.decrypt(token.encode()).decode()