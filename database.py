
import os
import subprocess
import mysql.connector
from mysql.connector import Error
from tkinter import filedialog

from config import DB_CONFIG


# ==================================
# KONFIGURASI MYSQL XAMPP
# ==================================

MYSQL_BIN = r"C:\xampp\mysql\bin"

MYSQLDUMP = os.path.join(MYSQL_BIN, "mysqldump.exe")
MYSQL = os.path.join(MYSQL_BIN, "mysql.exe")


# ==================================
# KONEKSI DATABASE
# ==================================

def get_connection():
    """Membuka koneksi baru ke database MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


def koneksi_database():
    """Alias untuk aplikasi utama."""
    return get_connection()


def fetch_all(sql, params=None):
    conn = get_connection()
    cur = None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()

    finally:
        if cur:
            cur.close()
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    cur = None

    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        conn.close()


def check_connection():
    conn = get_connection()
    conn.close()
    return True


# ==================================
# KONFIGURASI PERINTAH MYSQL
# ==================================

def perintah_mysql(program):
    if not os.path.isfile(program):
        raise FileNotFoundError(
            "File MySQL tidak ditemukan:\n" + program
        )

    perintah = [
        program,
        "--host=" + str(DB_CONFIG.get("host", "localhost")),
        "--user=" + str(DB_CONFIG.get("user", "root"))
    ]

    port = DB_CONFIG.get("port")

    if port:
        perintah.append("--port=" + str(port))

    password = DB_CONFIG.get("password", "")

    if password:
        perintah.append("--password=" + str(password))

    return perintah


# ==================================
# BACKUP DATABASE
# ==================================

def backup_database(output_path=None):

    database = DB_CONFIG.get("database")

    if not database:
        raise ValueError("Nama database belum diatur di config.py")

    if output_path is None:
        output_path = filedialog.asksaveasfilename(
            title="Backup Database",
            defaultextension=".sql",
            filetypes=[("SQL Database", "*.sql")],
            initialfile="backup_db_servis_laptop.sql"
        )

    if not output_path:
        return False

    perintah = perintah_mysql(MYSQLDUMP)
    perintah.append("--result-file=" + output_path)
    perintah.append(database)

    hasil = subprocess.run(
        perintah,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )

    if hasil.returncode != 0:
        raise RuntimeError(
            "Backup gagal:\n" + hasil.stderr
        )

    return output_path


# ==================================
# RESTORE DATABASE
# ==================================

def restore_database(input_path=None):

    database = DB_CONFIG.get("database")

    if not database:
        raise ValueError("Nama database belum diatur di config.py")

    if input_path is None:
        input_path = filedialog.askopenfilename(
            title="Pilih File Backup Database",
            filetypes=[("SQL Database", "*.sql")]
        )

    if not input_path:
        return False

    if not os.path.isfile(input_path):
        raise FileNotFoundError("File backup tidak ditemukan.")

    perintah = perintah_mysql(MYSQL)
    perintah.append(database)

    with open(input_path, "rb") as file_sql:
        hasil = subprocess.run(
            perintah,
            stdin=file_sql,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

    if hasil.returncode != 0:
        pesan = hasil.stderr.decode("utf-8", errors="replace")
        raise RuntimeError("Restore gagal:\n" + pesan)

    return True
