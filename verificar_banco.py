import sqlite3, sqlite_vec

conn = sqlite3.connect("jurisprudencia.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM decisoes")
print(f"Total: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) FROM decisoes 
    WHERE data_julgamento LIKE '2010%'
    OR data_julgamento LIKE '2011%'
    OR data_julgamento LIKE '2012%'
    OR data_julgamento LIKE '2013%'
    OR data_julgamento LIKE '2014%'
""")
print(f"Decisões 2010-2014: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) FROM decisoes 
    WHERE data_julgamento >= '2015'
""")
print(f"Decisões 2015+: {cursor.fetchone()[0]}")

conn.close()