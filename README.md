# Busca Jurisprudencial TJRS

Sistema de busca jurisprudencial com recuperação híbrida e refinamento conversacional, desenvolvido como Trabalho de Conclusão de Curso em Ciência da Computação — URI Erechim.

## Sobre o projeto

O sistema permite que profissionais do direito busquem decisões judiciais do TJRS por contexto e similaridade semântica, superando as limitações da busca tradicional por palavras-chave.

**Técnicas utilizadas:**
- Recuperação léxica com FTS5/BM25
- Recuperação semântica com embeddings BERTimbau (768 dimensões)
- Fusão de rankings com Reciprocal Rank Fusion (RRF)
- Refinamento conversacional de consultas via LLM

## Stack

- Python 3.11
- SQLite + sqlite-vec (indexação vetorial)
- BERTimbau (`neuralmind/bert-base-portuguese-cased`)
- FastAPI + Uvicorn
- Anthropic Claude API (refinamento conversacional)

## Estrutura

```
├── main.py                  # API REST (FastAPI)
├── index.html               # Frontend
├── salvar_decisoes.py       # Scraper + geração de embeddings
├── criar_banco.py           # Criação do banco
├── migrar_vec.py            # Migração para tabela vetorial
├── criar_fts.py             # Criação do índice FTS5
├── busca_hibrida.py         # Busca híbrida com RRF
├── busca_semantica.py       # Busca semântica isolada
├── busca_lexica.py          # Busca léxica isolada
├── coletar_massa.py         # Coleta em massa de decisões
└── .env                     # API key (não versionado)
```

## Como rodar

**1. Instalar dependências:**
```bash
pip install fastapi uvicorn sentence-transformers sqlite-vec anthropic python-dotenv torch
```

**2. Configurar API key:**

Cria um arquivo `.env` na raiz:
```
ANTHROPIC_API_KEY=sk-ant-...
```

**3. Iniciar a API:**
```bash
python -m uvicorn main:app --reload
```

**4. Abrir o frontend:**

Abre o arquivo `index.html` no navegador.

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/buscar` | Busca híbrida direta |
| POST | `/refinar` | Gera perguntas de refinamento via LLM |
| POST | `/buscar_refinado` | Busca com consulta reformulada pelo LLM |

## Autor

Gabriel Felipe Martins — URI Erechim, 2025
