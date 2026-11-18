# Infrastruttura di Sage (Terraform)

Un solo ambiente, nel progetto GCP condiviso del corso: ogni risorsa usa `resource_prefix`
per non interferire con quelle degli altri.

## Risorse create

| File | Risorsa | A cosa serve |
|---|---|---|
| `services.tf` | `google_project_service` | Abilita le API GCP usate dal progetto |
| `docs.tf` | `google_storage_bucket` | Bucket `<prefisso>-sage-docs` per i documenti sorgente |
| `instructions.tf` | `google_storage_bucket`, `google_storage_bucket_iam_member` | Bucket `<prefisso>-instructions` con `istruzioni.md`, leggibile dal backend |
| `firestore.tf` | `google_firestore_database`, `google_firestore_index` | Firestore Native + indice vettoriale sul campo `embedding` della collection `chunks` |
| `sage_backend.tf` | Artifact Registry, Cloud Run, service account, IAM | Il servizio che espone `/api/ask` e i suoi permessi |

Niente Secret Manager: Sage chiama Vertex AI con Application Default Credentials, non
servono API key esterne da custodire come segreto.

## Nomi delle risorse

`resource_prefix` è obbligatorio. Con il prefisso `its-ict-sage-mario-rossi`:

- Cloud Run e Artifact Registry: `<prefisso>-sage-backend`
- Bucket: `<prefisso>-sage-docs`, `<prefisso>-instructions` (e `<prefisso>-tfstate` per lo state)
- Firestore: un database chiamato come il prefisso
- Service account: `<prefisso>-sage-backend-run`, accorciato con un hash oltre i 30 caratteri

## Perché l'immagine Cloud Run non è gestita da Terraform

`sage_backend.tf` imposta `container_image` su un placeholder pubblico e poi lo ignora
(`lifecycle.ignore_changes`). L'immagine reale viene pubblicata dalla pipeline applicativa
(`.github/workflows/deploy.yml`), tenuta volutamente separata dalla pipeline Terraform: una
modifica al codice non richiede di rieseguire un piano Terraform, e viceversa.

## Comandi

```bash
cd devops/cloud

terraform init -backend-config=backend.hcl
terraform plan  -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars

# Carica le istruzioni lette da Sage a ogni richiesta
gcloud storage cp istruzioni.md gs://<prefisso>-instructions/istruzioni.md
```

In CI, lo stesso flusso gira nel workflow `terraform.yml`, avviato manualmente (tab
**Actions** del repository → *terraform* → *Run workflow*): `plan`, poi un job `approval` che
attende un'approvazione manuale su una issue GitHub prima di eseguire `apply`.
