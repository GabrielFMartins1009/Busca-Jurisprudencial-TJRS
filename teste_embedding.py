from sentence_transformers import SentenceTransformer
import sqlite3
import sqlite_vec
import torch
import numpy as np

# Confirma GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando: {device}\n")

# Carrega o modelo
print("Carregando modelo...")
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased', device=device)
print("Modelo carregado!\n")

# Busca uma ementa do banco
conn = sqlite3.connect("jurisprudencia.db")
cursor = conn.cursor()
cursor.execute("SELECT numero_processo, ementa_completa FROM decisoes LIMIT 1")
row = cursor.fetchone()
conn.close()

numero = row[0]
ementa = row[1]

print(f"Processo: {numero}")
print(f"Ementa (primeiros 200 chars): {ementa[:200]}\n")

# Gera o embedding
print("Gerando embedding...")
embedding = model.encode(ementa)

print(f"Embedding gerado!")
print(f"Dimensões: {embedding.shape}")
print(f"Primeiros 5 números: {embedding[:5]}")