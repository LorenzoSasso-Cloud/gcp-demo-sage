# Bucket con il file istruzioni.md: Sage lo legge a ogni richiesta e ne aggiunge il contenuto
# al prompt (vedi sources/backend/src/sage/domain/qa/instructions.py). Il file si carica a
# parte: cambiare le istruzioni non richiede né un apply né un nuovo deploy.
resource "google_storage_bucket" "sage_instructions" {
  name     = "${var.resource_prefix}-instructions"
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  force_destroy = true

  depends_on = [google_project_service.apis]
}

# Il backend può solo leggere, e solo da questo bucket (privilegio minimo).
resource "google_storage_bucket_iam_member" "sage_run_instructions_reader" {
  bucket = google_storage_bucket.sage_instructions.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.sage_run.email}"
}
