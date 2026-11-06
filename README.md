# Busca Jurisprudencial TJRS

Sistema de busca de jurisprudência do TJRS com recuperação híbrida e refinamento conversacional de consultas. Desenvolvido como Trabalho de Conclusão de Curso em Ciência da Computação, URI Erechim (2026).

O sistema recebe uma consulta em linguagem natural e retorna decisões ranqueadas pela fusão (RRF) de uma busca léxica (FTS5/BM25) com uma busca semântica (embeddings BERTimbau). Opcionalmente, um modelo de linguagem faz duas perguntas de esclarecimento ao usuário e reformula a consulta antes da busca.

## Como funciona

1. **Coleta (offline):** `coletar_massa.py` busca decisões no portal do TJRS, vetoriza cada ementa com o BERTimbau (vetores normalizados) e grava tudo em um único arquivo SQLite.
2. **Busca (online):** a API vetoriza a consulta, consulta o índice vetorial (20 mais próximos) e o índice léxico (20 melhores por BM25), e funde os dois rankings por Reciprocal Rank Fusion (k = 60). Retorna as 5 melhores decisões.
3. **Refinamento (opcional):** `/refinar` gera 2 perguntas via Claude; `/buscar_refinado` recebe a consulta e as duas respostas, gera uma consulta reformulada e a usa nas duas buscas.

## Requisitos

- Python 3.11
- Placa de vídeo NVIDIA com CUDA é opcional (sem ela, a vetorização roda na CPU, mais lenta)
- Uma chave da API da Anthropic para o refinamento conversacional (serviço pago; a busca direta funciona sem ela)
- Conexão com a internet para a coleta e o download do modelo BERTimbau (na primeira execução)

## Instalação

Com GPU NVIDIA, instale primeiro o PyTorch com CUDA (opcional, mas recomendado):

```bash
py -3.11 -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

Depois, as demais dependências:

```bash
py -3.11 -m pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto, copiando o `.env.example`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

O `.env` e o banco de dados (`*.db`) não são versionados.

## Banco de dados

O arquivo `jurisprudencia.db` **não está neste repositório** (tem cerca de 80 MB). Há duas opções:

- **Receber o arquivo pronto** do autor e colocá-lo na raiz do projeto. É a base usada no artigo (9.478 decisões).
- **Gerar uma base nova:**
  ```bash
  py -3.11 criar_banco.py
  py -3.11 coletar_massa.py
  ```
  A coleta consulta o portal do TJRS (15 termos, 25 páginas por termo) e leva bastante tempo. Como o portal devolve as decisões mais recentes primeiro, a base gerada hoje **não será idêntica** à usada no artigo.

## Executando

**1. Iniciar a API** (porta 8000), na raiz do projeto:

```bash
py -3.11 -m uvicorn main:app --port 8000
```

Aguarde a mensagem `Application startup complete`: o modelo BERTimbau é carregado na inicialização. Não use `--reload` (ele recarrega o modelo a cada alteração de arquivo e atrapalha a demonstração).

**2. Abrir o frontend:** abra o `index.html` no navegador (ou sirva a pasta com o Live Server do VS Code, porta 5500). O frontend espera a API em `http://127.0.0.1:8000`.

A API e o frontend foram feitos para uso local: o CORS está liberado para qualquer origem e não há autenticação.

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/buscar` | Busca híbrida direta |
| POST | `/refinar` | Gera as duas perguntas de refinamento (LLM) |
| POST | `/buscar_refinado` | Busca com a consulta reformulada a partir das respostas (LLM) |

## Arquivos

| Arquivo | Função |
|---------|--------|
| `main.py` | API REST (FastAPI): busca semântica, busca léxica, fusão RRF e refinamento |
| `index.html` | Interface web (HTML, CSS e JavaScript, sem frameworks) |
| `criar_banco.py` | Cria o banco com as três estruturas: `decisoes`, `vec_decisoes` (sqlite-vec) e `fts_decisoes` (FTS5) |
| `coletar_massa.py` | Coleta em massa do portal do TJRS e gera os embeddings |
| `salvar_decisoes.py` | Coleta de um único termo (versão simples da coleta) |
| `regerar_embeddings.py` | Regera todos os embeddings com vetores normalizados (rodar com a API parada) |
| `verificar_banco.py` | Conferência rápida do banco (contagem e distribuição por período) |
| `medir_tokens.py` | Mede o tamanho das ementas em tokens do BERTimbau (truncamento em 512) |
| `medir_tempos.py` | Mede os tempos de busca e de refinamento |
| `Figuras/` | Figuras usadas no artigo |

## Limitações conhecidas

- A avaliação do sistema é qualitativa e de pequena escala; não há métricas formais de recuperação.
- 80,5% das ementas excedem o limite de 512 tokens do modelo e são truncadas na vetorização.
- A base é predominantemente cível e concentrada em decisões de 2026.
- O refinamento depende de uma API paga e é mais lento que a busca direta.

## Autor

Gabriel Felipe Martins, URI Erechim, 2026.
