
# Final Projekti / team 2 / Terraform-template for database
# -----------------------------------------------
# Templaten variables are in file "variables.tf"

# Provider-info:
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.2.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.14.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_file)
  project     = var.project
  region      = var.region
  zone        = var.zone
}

# create SQL database instance gaved info
# Whether to deploy a Cloud SQL database or not. false = do not create, true = create

resource "google_sql_database_instance" "Postgreskanta" {
  count            = var.deploy_db ? 1 : 0
  name             = "postgreskanta"
  database_version = "POSTGRES_13"
  deletion_protection = false
  region           = var.region

  settings {
    tier = "db-f1-micro" # postgresql tukee vain shared core machineja! tämä shared-core löytyy haminasta
    maintenance_window {
      day = "1"
      hour = "3"
    }
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "04:30"
      transaction_log_retention_days = "2"
    }
    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
  }
}

resource "google_sql_database" "henkilosto" {
  count = var.deploy_db ? 1 : 0

  name     = "henkilosto"
  project  = var.project
  instance = google_sql_database_instance.Postgreskanta[0].name

  depends_on = [google_sql_database_instance.Postgreskanta]
}

resource "google_sql_user" "default" {
  count = var.deploy_db ? 1 : 0

  project  = var.project
  name     = var.sql_name
  instance = google_sql_database_instance.Postgreskanta[0].name
  password = var.sql_password

  depends_on = [google_sql_database.henkilosto]
}


