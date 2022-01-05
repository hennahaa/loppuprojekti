# Terraform Kortinjulkaisualusta

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.2.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "4.3.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_file)
  project = var.project
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  credentials = file(var.credentials_file)
  project = var.project
  region  = var.region
  zone    = var.zone
}

## Google Cloud Source Repository ##

resource "google_sourcerepo_repository" "repo" {
  name = "kekkoslovakia"
}

## Cloud Storage ##

resource "google_storage_bucket" "bucket" {
  provider = google
  name     = "kekkoslovakia-ky"
  location = "EU"
}

## CLOUD RUN ##

#Placeholder Cloud Run
resource "google_cloud_run_service" "default" {
  name     = "cloudrun-srv"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

## TIETOKANTA ##

#Placeholder DB (tilaukset? tarvitaanko me tilauksille tietokantaa??)
resource "google_sql_database_instance" "instance" {
  name             = "cloudrun-sql"
  database_version = "POSTGRES_11"
  settings {
    tier = "db-f1-micro"
  }

  deletion_protection  = "true"
}

## CLOUD FUNCTIONS ##

# DELETEFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "deletefunktio" {
  provider  = google
  name      = "deletefunktio"
  bucket    = google_storage_bucket.bucket.name
  source    = "../deletefunktio/deletefunktio.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function1" {
  provider    = google
  name        = "deletefunktio"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.deletefunktio.name
  trigger_http          = true
  entry_point           = "poistatoken"
}

# Funktio julkisesti saataville
resource "google_cloudfunctions_function_iam_member" "invoker1" {
  provider       = google
  cloud_function = google_cloudfunctions_function.function1.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# TOKENINLUOJAFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "tokeninluojafunktio" {
  provider  = google
  name      = "tokeninluojafunktio"
  bucket    = google_storage_bucket.bucket.name
  source    = "../tokeninluojafunktio/tokeninluojafunktio.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function2" {
  provider    = google
  name        = "tokeninluojafunktio"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.tokeninluojafunktio.name
  trigger_http          = true
  entry_point           = "event_tietokantaan"
}

# Funktio julkisesti saataville
resource "google_cloudfunctions_function_iam_member" "invoker2" {
  provider       = google
  cloud_function = google_cloudfunctions_function.function2.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}


## API GATEWAY ##

#API
resource "google_api_gateway_api" "kekkos-api" {
  provider = google-beta
  api_id = "kekkos-api"
}

#API CONFIG
resource "google_api_gateway_api_config" "kekkos-config" {
  provider = google-beta
  api = google_api_gateway_api.kekkos-api.api_id
  api_config_id = "config"

  openapi_documents {
    document {
      path = "spec.yaml"
      contents = filebase64("../api-gateway/api-config.yaml")
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

#API GATEWAY
resource "google_api_gateway_gateway" "kekkos-gw" {
  provider = google-beta
  api_config = google_api_gateway_api_config.kekkos-config.id
  gateway_id = "kekkos-gw"
}

