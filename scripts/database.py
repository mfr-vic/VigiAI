from pathlib import Path
import sqlite3

def init_db(path: str):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE IF NOT EXISTS predictions (path TEXT, prob REAL, pred INTEGER)")
    con.commit(); con.close()
