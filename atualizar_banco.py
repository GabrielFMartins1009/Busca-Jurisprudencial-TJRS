import sqlite3, sqlite_vec

conn = sqlite3.connect("jurisprudencia.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM decisoes WHERE embedding IS NOT NULL")
print(f"Decisões com embedding: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM vec_decisoes")
print(f"Vetores na vec_decisoes: {cursor.fetchone()[0]}")

conn.close()