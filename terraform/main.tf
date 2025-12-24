terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "0.95.0"
    }
  }
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

# Service Account и права доступа
resource "yandex_iam_service_account" "sa" {
  name        = "${var.prefix}-sa"
}

# Роли для сервисного аккаунта в папке
resource "yandex_resourcemanager_folder_iam_member" "editor" {
  folder_id = var.folder_id
  role      = "editor"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_viewer" {
  folder_id = var.folder_id
  role      = "lockbox.payloadViewer"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_admin" {
  folder_id = var.folder_id
  role      = "ydb.admin"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_editor" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "speechkit" {
  folder_id = var.folder_id
  role      = "ai.speechkit-stt.user"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "yandexgpt" {
  folder_id = var.folder_id
  role      = "ai.languageModels.user"
  member    = "serviceAccount:${yandex_iam_service_account.sa.id}"
}

resource "yandex_container_registry_iam_binding" "sa_container" {
  registry_id = yandex_container_registry.registry.id
  role        = "container-registry.images.puller"
  members = [
    "serviceAccount:${yandex_iam_service_account.sa.id}",
  ]
}

resource "yandex_serverless_container_iam_binding" "sa_invoker" {
  container_id = yandex_serverless_container.web.id
  role         = "serverless.containers.invoker"
  members      = [
    "serviceAccount:${yandex_iam_service_account.sa.id}",
    "system:allUsers"
  ]
}

# Статические ключи доступа для сервисного аккаунта
resource "yandex_iam_service_account_static_access_key" "sa_static_key" {
  service_account_id = yandex_iam_service_account.sa.id
}

# Хранение секретов
resource "yandex_lockbox_secret" "secret" {
  name        = "${var.prefix}-secrets"
  description = "Application secrets"
}

resource "yandex_lockbox_secret_version" "secret_version" {
  secret_id = yandex_lockbox_secret.secret.id

  entries {
    key        = "AWS_ACCESS_KEY_ID"
    text_value = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  }

  entries {
    key        = "AWS_SECRET_ACCESS_KEY"
    text_value = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
  }
}

# Ожидание применения прав доступа
resource "time_sleep" "wait_for_sa_permissions" {
  create_duration = "10s"

  depends_on = [
    yandex_resourcemanager_folder_iam_member.sa_editor,
    yandex_iam_service_account_static_access_key.sa_static_key
  ]
}

# YDB Database
resource "yandex_ydb_database_serverless" "database" {
  name = "${var.prefix}-db"
}

# Object Storage
resource "yandex_storage_bucket" "bucket" {
  access_key = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
  bucket     = "${var.prefix}-bucket"
  acl        = "private"
  force_destroy = true

  depends_on = [time_sleep.wait_for_sa_permissions]

  lifecycle_rule {
    id      = "cleanup-temp-audio"
    enabled = true
    prefix  = "temp_audio/"
    expiration {
      days = 1
    }
  }

  lifecycle_rule {
    id      = "cleanup-summaries"
    enabled = true
    prefix  = "summaries/"
    expiration {
      days = 1
    }
  }
}

# Message Queue
resource "yandex_message_queue" "queue" {
  access_key = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
  name       = "${var.prefix}-queue"
  depends_on = [time_sleep.wait_for_sa_permissions]
}

# Container Registry
resource "yandex_container_registry" "registry" {
  name = "${var.prefix}-registry"
}

# Web Application Container
resource "yandex_serverless_container" "web" {
  name               = "${var.prefix}-container"
  memory             = 1024
  cores              = 1
  core_fraction      = 100
  service_account_id = yandex_iam_service_account.sa.id

  execution_timeout = "300s"

  image {
    url         = "cr.yandex/${yandex_container_registry.registry.id}/hw2-web:latest"
    environment = {
      YDB_ENDPOINT     = yandex_ydb_database_serverless.database.document_api_endpoint
      YDB_DATABASE     = yandex_ydb_database_serverless.database.database_path
      MQ_ENDPOINT      = "https://message-queue.api.cloud.yandex.net"
      MQ_QUEUE_NAME    = yandex_message_queue.queue.name
      BUCKET_NAME      = yandex_storage_bucket.bucket.bucket
      LOCKBOX_SECRET_ID = yandex_lockbox_secret.secret.id
    }
  }

  secrets {
    id                   = yandex_lockbox_secret.secret.id
    version_id           = yandex_lockbox_secret_version.secret_version.id
    key                  = "AWS_ACCESS_KEY_ID"
    environment_variable = "AWS_ACCESS_KEY_ID"
  }

  secrets {
    id                   = yandex_lockbox_secret.secret.id
    version_id           = yandex_lockbox_secret_version.secret_version.id
    key                  = "AWS_SECRET_ACCESS_KEY"
    environment_variable = "AWS_SECRET_ACCESS_KEY"
  }

  depends_on = [
    yandex_container_registry_iam_binding.sa_container
  ]
}

# Generator Container
resource "yandex_serverless_container" "generator" {
  name               = "${var.prefix}-generator"
  memory             = 1024
  core_fraction      = 100
  service_account_id = yandex_iam_service_account.sa.id

  execution_timeout = "300s"
  image {
    url = "cr.yandex/${yandex_container_registry.registry.id}/hw2-generator:latest"

    environment = {
      YDB_ENDPOINT      = yandex_ydb_database_serverless.database.document_api_endpoint
      YDB_DATABASE      = yandex_ydb_database_serverless.database.database_path
      BUCKET_NAME       = yandex_storage_bucket.bucket.bucket
      YC_FOLDER_ID      = var.folder_id
      LOCKBOX_SECRET_ID = yandex_lockbox_secret.secret.id
    }
  }

  secrets {
    id                   = yandex_lockbox_secret.secret.id
    version_id           = yandex_lockbox_secret_version.secret_version.id
    key                  = "AWS_ACCESS_KEY_ID"
    environment_variable = "AWS_ACCESS_KEY_ID"
  }

  secrets {
    id                   = yandex_lockbox_secret.secret.id
    version_id           = yandex_lockbox_secret_version.secret_version.id
    key                  = "AWS_SECRET_ACCESS_KEY"
    environment_variable = "AWS_SECRET_ACCESS_KEY"
  }
}

resource "yandex_serverless_container_iam_binding" "trigger_invoker" {
  container_id = yandex_serverless_container.generator.id
  role         = "serverless.containers.invoker"
  members      = [
    "serviceAccount:${yandex_iam_service_account.sa.id}",
  ]
}

# Trigger
resource "yandex_function_trigger" "queue_trigger" {
  name = "${var.prefix}-trigger"

  container {
    id                 = yandex_serverless_container.generator.id
    service_account_id = yandex_iam_service_account.sa.id
    path               = "/"
  }

  message_queue {
    queue_id           = yandex_message_queue.queue.arn
    service_account_id = yandex_iam_service_account.sa.id
    batch_size         = 1
    batch_cutoff       = 10
  }
}


# API Gateway 
resource "yandex_api_gateway" "gateway" {
  name = "${var.prefix}-gateway"

  spec = <<-EOT
openapi: 3.0.0
info:
  title: Lecture Generator API
  version: 1.0.0
paths:
  /:
    get:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: "${yandex_serverless_container.web.id}"
        service_account_id: "${yandex_iam_service_account.sa.id}"

  /create/task:
    post:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: "${yandex_serverless_container.web.id}"
        service_account_id: "${yandex_iam_service_account.sa.id}"

  /tasks:
    get:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: "${yandex_serverless_container.web.id}"
        service_account_id: "${yandex_iam_service_account.sa.id}"
EOT
}

