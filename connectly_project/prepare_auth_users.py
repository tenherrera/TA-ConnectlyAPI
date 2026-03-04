import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path(__file__).resolve().parent / 'db.sqlite3'
conn = sqlite3.connect(DB)
cur = conn.cursor()

def ensure_auth_users():
    cur.execute("SELECT id, username, email FROM posts_user")
    posts_users = cur.fetchall()
    for pu in posts_users:
        pu_id, username, email = pu
        cur.execute("SELECT id FROM auth_user WHERE id = ?", (pu_id,))
        if cur.fetchone():
            continue
        now = datetime.utcnow().isoformat(sep=' ')
        cur.execute(
            "INSERT INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (pu_id, '', None, 0, username, '', '', email, 0, 1, now)
        )
        print(f"Inserted auth_user id={pu_id} username={username}")
    conn.commit()

if __name__ == '__main__':
    ensure_auth_users()
    conn.close()
