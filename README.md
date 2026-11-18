# Sage

Sage è l'assistente Q&A del corso ITS ICT — GCP 2026: risponde a domande in linguaggio
naturale su un insieme di documenti, usando il pattern RAG (Retrieval-Augmented
Generation). Ogni domanda è indipendente dalle altre: nessuna memoria di conversazione.

## Architettura

```
Utente ──POST /api/ask──▶ API FastAPI su Cloud Run
                                │
                    1. legge istruzioni.md da Cloud Storage
                    2. calcola l'embedding della domanda (Vertex AI)
                    3. cerca i chunk più simili in Firestore (vector search, find_nearest)
                    4. genera la risposta con Gemini da chunk e istruzioni (Vertex AI)
                    5. logga la domanda (BigQuery: ancora simulato, solo log applicativo)
                                │
                                ▼
                     { answer, sources[] }
```

| Componente | Servizio GCP | Ruolo |
|---|---|---|
| API | Cloud Run | Servizio HTTP stateless, `POST /api/ask` + `GET /health` |
| Base di conoscenza | Firestore (Native mode) | Collection `chunks`: testo + embedding + metadati, interrogata con `find_nearest` |
| LLM ed embedding | Vertex AI | `gemini-3.8-flash` e `gemini-embedding-001`, autenticazione via ADC / service account |
| Istruzioni | Cloud Storage | `gs://<prefisso>-instructions/istruzioni.md`, letto a ogni richiesta |
| Documenti sorgente | Cloud Storage | Bucket `<prefisso>-sage-docs` |
| Immagini container | Artifact Registry | Repository `<prefisso>-sage-backend` |

La pipeline di chunking/embedding **non gira dentro l'API**: è lo script
`sources/backend/utils/ingest_documents.py`, eseguito manualmente per popolare Firestore a
partire dai file Markdown in `sources/backend/data/`.

### Cosa succede se un'integrazione non è disponibile

- **Firestore** non raggiungibile: Sage risponde senza contesto documentale.
- **`istruzioni.md`** mancante o non leggibile: Sage risponde senza istruzioni aggiuntive.
- **Vertex AI** in errore: l'API risponde `502`.

I primi due casi vengono registrati con livello `WARNING` nei log di Cloud Run.

## Struttura del repository

```
sources/backend/    API FastAPI (Python, uv) + script di ingestion + test
  src/sage/          webapp/ (router HTTP) → domain/ (logica RAG) → integrations/ (client GCP)
  utils/              ingest_documents.py — legge data/*.md, calcola gli embedding, popola Firestore
  data/               documenti .md da indicizzare
devops/cloud/        Terraform: tutte le risorse GCP, più istruzioni.md da caricare nel bucket
.github/workflows/    terraform.yml (plan → approvazione → apply) e deploy.yml (build & deploy)
.github/setup/        script e runbook per il bootstrap una tantum del progetto GCP
```

## Prerequisiti

- `gcloud` CLI autenticata (`gcloud auth login` e `gcloud auth application-default login`)
- [`uv`](https://docs.astral.sh/uv/), [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5, Docker

## Messa in funzione

Negli esempi `PROJECT_ID` è il progetto condiviso e `PREFIX` il prefisso personale.

```bash
# 1. Infrastruttura
cd devops/cloud
terraform init -backend-config=backend.hcl
terraform apply -var-file=terraform.tfvars

# 2. Istruzioni
gcloud storage cp istruzioni.md gs://$PREFIX-instructions/istruzioni.md

# 3. Base di conoscenza (sources/backend/.env deve contenere SAGE_PROJECT_ID e SAGE_RESOURCE_PREFIX)
cd ../../sources/backend
uv sync
uv run python utils/ingest_documents.py

# 4. Build e deploy
IMAGE=europe-west6-docker.pkg.dev/$PROJECT_ID/$PREFIX-sage-backend/sage:manual
docker build -t $IMAGE .
docker push $IMAGE
gcloud run deploy $PREFIX-sage-backend --project $PROJECT_ID --region europe-west6 --image $IMAGE
```

Cambiando modello di embedding bisogna rilanciare l'ingestion: domanda e chunk devono usare lo
stesso modello. Rilanciarla è sicuro: i chunk di ogni documento vengono sostituiti solo dopo
aver calcolato tutti i nuovi embedding.

## Test dell'API deployata

```bash
SAGE_URL=$(gcloud run services describe $PREFIX-sage-backend --project $PROJECT_ID \
  --region europe-west6 --format='value(status.url)')

curl -X POST "$SAGE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Perché Sage usa Firestore invece di un database vettoriale separato?"}'
```

In alternativa si può usare l'interfaccia interattiva su `$SAGE_URL/docs`.

## Sviluppo del backend

```bash
cd sources/backend
uv run pytest          # test
uv run ruff check .    # lint
uv run ruff format .   # formattazione
```

La struttura del codice segue tre livelli con dipendenza a senso unico
`webapp → domain → integrations`: `webapp/` è il solo livello che conosce FastAPI, `domain/`
contiene la logica RAG, `integrations/` isola le chiamate a Vertex AI, Firestore, Cloud Storage
e BigQuery.
