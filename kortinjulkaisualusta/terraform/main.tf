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

## ARTIFACT REGISTRY ## 

resource "google_artifact_registry_repository" "kekkosrepo" {
  provider = google-beta

  location = var.region
  repository_id = "kekkosrepo"
  description = "kekkos-testi"
  format = "DOCKER"
}


## CLOUD STORAGE ##

resource "google_storage_bucket" "bucket_1" {
  provider = google
  name     = "kekkoslovakia-bucket-prod"
  location = "EU"
}

resource "google_storage_bucket" "bucket_2" {
  provider = google
  name     = "kekkoslovakia-cards-prod"
  location = "EU"
}

## CLOUD RUN ##

#Placeholder Cloud Run
resource "google_cloud_run_service" "kekkoslovakia" {
  name     = "kekkoslovakia-front-prod"
  location = var.region

  template {
    spec {
      containers {
        image = "europe-north1-docker.pkg.dev/final-project-2-337107/cloud-run-source-deploy/kekkoslovakia-front-dev"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

}

resource "google_cloud_run_service_iam_member" "member" {
  location = google_cloud_run_service.kekkoslovakia.location
  project  = google_cloud_run_service.kekkoslovakia.project
  service  = google_cloud_run_service.kekkoslovakia.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

## LOAD BALANCER ##

# Reserve IP
resource "google_compute_global_address" "default" {
  name = "${var.name}-address"
}

resource "google_compute_ssl_policy" "default" {
  name    = "production-ssl-policy"
  profile = "RESTRICTED"
  min_tls_version = "TLS_1_2"
}

# SSL CERT
resource "google_compute_ssl_certificate" "default" {
  name_prefix = "sertti"
  description = "Tämä on SSL-sertificaatti"
  private_key = file("../api/salaisuudet/privatekey.pem")
  certificate = file("../api/salaisuudet/cert1.pem")

  lifecycle {
    create_before_destroy = true
  }
}

# NEG
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  provider              = google-beta
  name                  = "${var.name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_service.kekkoslovakia.name
  }
}

#Backend service
resource "google_compute_backend_service" "default" {
  name      = "${var.name}-backend"

  protocol  = "HTTP"
  port_name = "http"
  timeout_sec = 30

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }
}

# Empty URL map
resource "google_compute_url_map" "default" {
  name            = "${var.name}-urlmap"

  default_service = google_compute_backend_service.default.id
}

# HTTPS PROXY
resource "google_compute_target_https_proxy" "default" {
  name   = "${var.name}-https-proxy"

  url_map          = google_compute_url_map.default.id
  ssl_certificates = [
    google_compute_ssl_certificate.default.id
  ]
  ssl_policy      =  google_compute_ssl_policy.default.id
}

# FORWARDING RULE
resource "google_compute_global_forwarding_rule" "default" {
  name            = "${var.name}-lb"

  target          = google_compute_target_https_proxy.default.id
  port_range      = "443"
  ip_address      = google_compute_global_address.default.address
}

## TIETOKANTA ##

#Tilaukset DB
resource "google_sql_database_instance" "instance" {
  name             = "tilaukset-sql-test"
  database_version = "POSTGRES_13"
  settings {
    tier = "db-f1-micro"
  }

  deletion_protection  = "false"
}

#Kekkoslovakia henkilöstö DB
resource "google_sql_database" "tilaukset_database" {
  provider = google-beta

  name     = "kekkoslovakia-db-srv-tilaukset"
  instance = google_sql_database_instance.instance.name
}


#Luodaan DB-instanssille käyttäjä
resource "google_sql_user" "users" {
  name     = var.db_user
  instance = google_sql_database_instance.instance.name
  password = var.db_pass
}

## SECRETS ##

#salainen sana
resource "google_secret_manager_secret" "secret-pw" {
  secret_id = "secret-pw-prod"

  labels = {
    label = "salasana-kanta"
  }

  replication {
    automatic = true
  }
}


resource "google_secret_manager_secret_version" "secret-version-pw" {
  secret = google_secret_manager_secret.secret-pw.id

  secret_data = var.db_pass
}

#db käyttäjänimi
resource "google_secret_manager_secret" "secret-user" {
  secret_id = "secret-user-prod"

  labels = {
    label = "käyttäjä-kanta"
  }

  replication {
    automatic = true
  }
}


resource "google_secret_manager_secret_version" "secret-version-user" {
  secret = google_secret_manager_secret.secret-user.id

  secret_data = var.db_user
}

#db
resource "google_secret_manager_secret" "secret-kanta" {
  secret_id = "secret-kanta-prod"

  labels = {
    label = "kanta"
  }

  replication {
    automatic = true
  }
}


resource "google_secret_manager_secret_version" "secret-version-kanta" {
  secret = google_secret_manager_secret.secret-kanta.id

  secret_data = google_sql_database_instance.instance.name
}

#db
resource "google_secret_manager_secret" "secret-host" {
  secret_id = "secret-host-prod"

  labels = {
    label = "host"
  }

  replication {
    automatic = true
  }
}


resource "google_secret_manager_secret_version" "secret-version-host" {
  secret = google_secret_manager_secret.secret-host.id

  secret_data = var.db_ip
}

## CLOUD FUNCTIONS ##

# DELETEFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "poistatoken" {
  provider  = google
  name      = "poistatoken"
  bucket    = google_storage_bucket.bucket_1.name
  source    = "../api/functions/poistatoken/poistatoken.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function_poistatoken" {
  provider    = google
  name        = "poistatoken"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket_1.name
  source_archive_object = google_storage_bucket_object.poistatoken.name
  trigger_http          = true
  entry_point           = "poistatoken"

  environment_variables = {
    PROJECTID = var.project
  }
}

# Funktio julkisesti saataville
resource "google_cloudfunctions_function_iam_member" "invoker1" {
  provider       = google
  cloud_function = google_cloudfunctions_function.function_poistatoken.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# TOKENINLUOJAFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "lisaatoken" {
  provider  = google
  name      = "lisaatoken"
  bucket    = google_storage_bucket.bucket_1.name
  source    = "../api/functions/lisaatoken/lisaatoken.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function_lisaatoken" {
  provider    = google
  name        = "lisaatoken"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket_1.name
  source_archive_object = google_storage_bucket_object.lisaatoken.name
  trigger_http          = true
  entry_point           = "event_tietokantaan"

  environment_variables = {
    PROJECTID = var.project
  }

}

# Funktio julkisesti saataville
resource "google_cloudfunctions_function_iam_member" "invoker2" {
  provider       = google
  cloud_function = google_cloudfunctions_function.function_lisaatoken.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# KORTTIEN HAKIJAFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "haekaikki" {
  provider  = google
  name      = "haekaikki"
  bucket    = google_storage_bucket.bucket_1.name
  source    = "../api/functions/haekaikki/haekaikki.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function_haekaikki" {
  provider    = google
  name        = "haekaikki"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket_1.name
  source_archive_object = google_storage_bucket_object.haekaikki.name
  trigger_http          = true
  entry_point           = "hae_kaikki_kortit"

  environment_variables = {
    PROJECTID = var.project
  }

}

# Funktio julkisesti saataville
resource "google_cloudfunctions_function_iam_member" "invoker3" {
  provider       = google
  cloud_function = google_cloudfunctions_function.function_haekaikki.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# YHDEN KORTIN HAKIJAFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "haekortti" {
  provider  = google
  name      = "haekortti"
  bucket    = google_storage_bucket.bucket_1.name
  source    = "../api/functions/haekortti/haekortti.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function_haekortti" {
  provider    = google
  name        = "haekortti"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket_1.name
  source_archive_object = google_storage_bucket_object.haekortti.name
  trigger_http          = true
  entry_point           = "hae_kortti"

  environment_variables = {
    PROJECTID = var.project
  }

}

# KORTIN LISÄÄJÄFUNKTIO

# Luodaan Storage Object funktion zipistä #
resource "google_storage_bucket_object" "lisaakortti" {
  provider  = google
  name      = "lisaakortti"
  bucket    = google_storage_bucket.bucket_1.name
  source    = "../api/functions/lisaakortti/lisaakortti.zip"
}

# Luo funktion zipistä
resource "google_cloudfunctions_function" "function_lisaakortti" {
  provider    = google
  name        = "lisaakortti"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket_1.name
  source_archive_object = google_storage_bucket_object.lisaakortti.name
  trigger_http          = true
  entry_point           = "lisaa_kortti"

  environment_variables = {
    PROJECTID = var.project
  }

}

# Funktio julkisesti saataville
resource "google_cloudfunctions_function_iam_member" "invoker5" {
  provider       = google
  cloud_function = google_cloudfunctions_function.function_lisaakortti.name

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
  api_config_id = "kekkoslovakia-api-config-prod"

  openapi_documents {
    document {
      path = "spec.yaml"
      contents = filebase64("../api/api-gateway/api-config.yaml")
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

