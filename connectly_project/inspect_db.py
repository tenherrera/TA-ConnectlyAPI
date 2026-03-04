import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / 'db.sqlite3'
conn = sqlite3.connect(DB)
cur = conn.cursor()

def dump_table(name):
    try:
        cur.execute(f"SELECT * FROM {name} LIMIT 10")
        rows = cur.fetchall()
        print(f"-- {name} ({len(rows)} rows shown max 10):")
        for r in rows:
            print(r)
    except Exception as e:
        print(f"-- {name} ERROR: {e}")

if __name__ == '__main__':
    dump_table('posts_comment')
    dump_table('posts_user')
    dump_table('auth_user')
    conn.close()
