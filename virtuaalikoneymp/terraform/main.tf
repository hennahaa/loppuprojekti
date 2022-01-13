#Terraform Backend

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

## VPC ##

# VPC - verkko
resource "google_compute_network" "kekkoslovakia-vpc" {
  name                    = "kekkos-vpc"
  auto_create_subnetworks = "false"
}

# VPC-subnet
resource "google_compute_subnetwork" "kekkoslovakia-subnetwork" {
  name          = "subnet-1"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.kekkoslovakia-vpc.name
  private_ip_google_access = true
}

## CLOUD NAT ##

# Router
resource "google_compute_router" "router" {
  name    = "kekkos-router"
  region  = google_compute_subnetwork.kekkoslovakia-subnetwork.region
  network = google_compute_network.kekkoslovakia-vpc.id

  bgp {
    asn = 64514
  }
}

# NAT
resource "google_compute_router_nat" "nat" {
  name                               = "kekkos-router-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

## FIREWALL RULES ##

# SSH-firewall-sääntö
resource "google_compute_firewall" "ssh-firewall" {
  name    = "ssh-rule"
  network = google_compute_network.kekkoslovakia-vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["ssh-rule"]
}

# Bastion-firewall-sääntö
resource "google_compute_firewall" "bastion-firewall" {
  name    = "bastion-rule"
  network = google_compute_network.kekkoslovakia-vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["10.0.1.0/24"]

  target_tags = ["bastion-rule"]
}

## INSTANSSIT ##

# Bastion-instanssi
resource "google_compute_instance" "bastion" {
  name         = "kekkoslovakia-bastion"
  machine_type = "f1-micro"
  tags         = ["ssh-rule"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
    }
  }

  network_interface {
    network    = google_compute_network.kekkoslovakia-vpc.name
    subnetwork = google_compute_subnetwork.kekkoslovakia-subnetwork.name
    
    access_config {
    }
  
  }

  allow_stopping_for_update = true

  resource_policies = [google_compute_resource_policy.schedule-other.self_link]

    metadata = {
    enable-oslogin = "TRUE"
  }

}

#Service account henkilöstö- ja reskontra-instanssin käyttöä varten
resource "google_service_account" "service_account" {
  account_id = "cloud-sql"
}

resource "google_project_iam_member" "role" {
  project = var.project
  role   = "roles/cloudsql.editor"
  member = "serviceAccount:${google_service_account.service_account.email}"
}

resource "google_service_account_key" "key" {
  service_account_id = google_service_account.service_account.name
}


#Luodaan henkiloston instanssi
resource "google_compute_instance" "henkilosto" {
  name         = "kekkoslovakia-henkilosto"
  machine_type = "f1-micro"
  tags         = ["bastion-rule"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
    }
  }

  network_interface {
    network    = google_compute_network.kekkoslovakia-vpc.name
    subnetwork = google_compute_subnetwork.kekkoslovakia-subnetwork.name
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  resource_policies = [google_compute_resource_policy.schedule-other.self_link]

  allow_stopping_for_update = true

  metadata_startup_script = file("startup_henkilosto.sh")

}

#Luodaan henkiloston instanssi
resource "google_compute_instance" "reskontra" {
  name         = "kekkoslovakia-reskontra"
  machine_type = "n1-standard-1"
  #machine_type = "f1-micro"
  tags         = ["bastion-rule"]

  boot_disk {
    initialize_params {
      image = "windows-cloud/windows-server-2012-r2-dc-v20211216"
    }
  }

  network_interface {
    network    = google_compute_network.kekkoslovakia-vpc.name
    subnetwork = google_compute_subnetwork.kekkoslovakia-subnetwork.name
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  resource_policies = [google_compute_resource_policy.schedule-bank.self_link]

  allow_stopping_for_update = true

}

#OS config patch manager
resource "google_os_config_patch_deployment" "patch" {
  patch_deployment_id = "monthly-update"

  instance_filter {
    all = true
  }

  recurring_schedule {
    time_zone {
      id = "Europe/Helsinki"
    }

    time_of_day {
      hours   = 0
      minutes = 30
      seconds = 30
      nanos   = 20
    }

    monthly {
      week_day_of_month {
        week_ordinal = -1
        day_of_week  = "TUESDAY"
      }
    }
  }
}

#SNAPSHOT-backup virtuaalikoneista: tarvitaan google_compute_resource_policy -sääntö ja 
#sitten google_compute_disk_resource_policy_attachment millä liitetään sääntö virtuaalikoneeseen

resource "google_compute_resource_policy" "snappolicy" {
  name        = "snappolicy"
  
  snapshot_schedule_policy {
    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "06:00"
      }
    }
    retention_policy {
      max_retention_days    = 10
      on_source_disk_delete = "KEEP_AUTO_SNAPSHOTS"
    }
    snapshot_properties {
      storage_locations = ["EU"]
    }
  }
}


#Kiinnitetään snap policy näihin instansseihin
resource "google_compute_disk_resource_policy_attachment" "snapattachment_1" {
  name = google_compute_resource_policy.snappolicy.name
  disk = google_compute_instance.bastion.name
}

resource "google_compute_disk_resource_policy_attachment" "snapattachment_2" {
  name = google_compute_resource_policy.snappolicy.name
  disk = google_compute_instance.henkilosto.name
}

resource "google_compute_disk_resource_policy_attachment" "snapattachment_3" {
  name = google_compute_resource_policy.snappolicy.name
  disk = google_compute_instance.reskontra.name
}

#Pankkiaikojen mukaan käynnistyvä ja sulkeutuva instanssi
# Aukeaa klo 8 ja sulkeutuu klo 16
resource "google_compute_resource_policy" "schedule-bank" {
  name   = "pankkiaikataulu-policy"
  description = "Käynnistä ja sulje instanssit pankkiaikojen mukaan"
  instance_schedule_policy {
    vm_start_schedule {
      schedule = "0 7 * * *"
    }
    vm_stop_schedule {
      schedule = "0 16 * * *"
    }
    time_zone = "Europe/Helsinki"
  }
}

#Muut instanssit ovat käynnissä kello 6 ja kello 19 välillä.
resource "google_compute_resource_policy" "schedule-other" {
  name   = "aikataulu-policy"
  description = "Käynnistä ja sulje muut instanssit"
  instance_schedule_policy {
    vm_start_schedule {
      schedule = "0 6 * * *"
    }
    vm_stop_schedule {
      schedule = "0 19 * * *"
    }
    time_zone = "Europe/Helsinki"
  }
}

## DATABASE JA IP-SÄÄNNÖT DATABASELLE ##

resource "google_compute_global_address" "private_ip_block" {
  provider = google-beta

  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  ip_version    = "IPV4"
  prefix_length = 24
  network       = google_compute_network.kekkoslovakia-vpc.self_link
}

resource "google_service_networking_connection" "private_vpc_connection" {
  provider = google-beta

  network                 = google_compute_network.kekkoslovakia-vpc.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_block.name]
}

#Tietokanta
resource "google_sql_database_instance" "instance" {
  provider = google-beta

  name             = "kekkoslovakia-db-backend-prod"
  database_version = "POSTGRES_13"

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = "db-f1-micro"
    disk_size = 10
    
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
      ipv4_enabled    = false
      private_network = google_compute_network.kekkoslovakia-vpc.self_link
    }
  }

  deletion_protection  = "false"
}

#Kekkoslovakia henkilöstö DB
resource "google_sql_database" "henkilosto_database" {
  provider = google-beta

  name     = "kekkoslovakia-db-srv-henkilosto"
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_database" "reskontra_database" {
  provider = google-beta

  name     = "kekkoslovakia-db-srv-reskontra"
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "users" {
  name     = var.db_user
  instance = google_sql_database_instance.instance.name
  password = var.db_pass
}

