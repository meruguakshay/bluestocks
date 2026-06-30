import sqlite3
import pandas as pd

def inspect():
    conn = sqlite3.connect("bluestock_mf.db")
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print("Tables in database:", tables)
    
    # Print row counts and columns
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        cols = [c[1] for c in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        count = cursor.fetchone()[0]
        print(f"- Table: {t:<20} | Rows: {count:<6} | Columns: {cols}")
        
    conn.close()

if __name__ == "__main__":
    inspect()
