variable "cloud_id" {
  type        = string
  description = "Yandex Cloud ID"
}

variable "folder_id" {
  type        = string
  description = "Yandex Cloud folder ID"
}

variable "zone" {
  type        = string
  default     = "ru-central1-d"
  description = "Default zone"
}

variable "prefix" {
  type        = string
  description = "Prefix for all resources"
  default     = "lecture-notes"
}

variable "yc_token" {
  type        = string
  description = "Yandex Cloud OAuth token"
  sensitive   = true
}