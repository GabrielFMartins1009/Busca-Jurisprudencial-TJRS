import sqlite3

conn = sqlite3.connect("jurisprudencia.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM decisoes")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM decisoes WHERE embedding IS NOT NULL")
com_embedding = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM decisoes WHERE embedding IS NULL")
sem_embedding = cursor.fetchone()[0]

print(f"Total de decisões: {total}")
print(f"Com embedding: {com_embedding}")
print(f"Sem embedding: {sem_embedding}")

conn.close()