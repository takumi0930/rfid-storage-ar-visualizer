import sqlite3

DB_PATH = "mydatabase.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA foreign_keys = ON;")

cur.execute("""
CREATE TABLE IF NOT EXISTS product_information (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    model_url TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS stored_products (
    uid TEXT PRIMARY KEY,
    product_id INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product_information(product_id)
);
""")

conn.commit()
conn.close() 
