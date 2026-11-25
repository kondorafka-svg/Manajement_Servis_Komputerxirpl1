import hashlib
from database import fetch_all, execute

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def login_user(username, password):
    rows = fetch_all(
        "SELECT id_user, username, nama, role FROM users WHERE username=%s AND password_hash=%s",
        (username, hash_password(password))
    )
    return rows[0] if rows else None

def create_default_admin():
    rows = fetch_all("SELECT id_user FROM users WHERE username=%s", ("admin",))
    if not rows:
        execute(
            "INSERT INTO users (username, password_hash, nama, role) VALUES (%s,%s,%s,%s)",
            ("admin", hash_password("admin123"), "Administrator", "admin")
        )
