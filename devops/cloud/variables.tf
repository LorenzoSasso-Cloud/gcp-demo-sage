variable "project_id" {
  description = "ID del progetto GCP"
  type        = string
}

variable "region" {
  description = "Regione GCP in cui creare le risorse"
  type        = string
}

variable "resource_prefix" {
  description = "Prefisso obbligatorio dei nomi delle risorse (es. its-ict-sage-mario-rossi)"
  type        = string

  validation {
    condition     = length(var.resource_prefix) > 0
    error_message = "resource_prefix è obbligatorio: il progetto GCP è condiviso."
  }
}
