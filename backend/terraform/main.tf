# Alustetaan Terraform
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.2.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_file)
  project = var.project
  region  = var.region
  zone    = var.zone
}


#VPC-verkko
resource "google_compute_network" "kekkoslovakia-vpc" {
  name                    = "kekkos-vpc"
  auto_create_subnetworks = "false"
}

#VPC-subnet
resource "google_compute_subnetwork" "kekkoslovakia-subnetwork" {
  name          = "subnet-1"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.kekkoslovakia-vpc.name
  private_ip_google_access = true
}

#router
resource "google_compute_router" "router" {
  name    = "kekkos-router"
  region  = google_compute_subnetwork.kekkoslovakia-subnetwork.region
  network = google_compute_network.kekkoslovakia-vpc.id

  bgp {
    asn = 64514
  }
}

#NAT
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

#Luodaan SSH-firewall-sääntö
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

#Luodaan HTTP-sääntö
resource "google_compute_firewall" "http-firewall" {
  name    = "http-rule"
  network = google_compute_network.kekkoslovakia-vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["http-rule"]
}

#Luodaan Bastion-sääntö
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

#Luodaan instanssi
resource "google_compute_instance" "bastion" {
  name         = "kekkoslovakia-bastion"
  machine_type = "f1-micro"
  tags         = ["ssh-rule", "http-rule"]

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

  #tämä on nyt täysillä scopeilla, riittäisi varmaan 
  #service_account {
  #  email  = var.service_acco
  #  scopes = ["storage-full"]
  #}

  #startup.sh:n lataa APACHEn instanssiin
  #metadata_startup_script = file("startup.sh")
}

#Luodaan henkiloston instanssi (ei external ip:tä)
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

  #tämä on nyt täysillä scopeilla, riittäisi varmaan 
  #service_account {
  #  email  = var.service_acco
  #  scopes = ["storage-full"]
  #}

  #startup.sh:n lataa APACHEn instanssiin
  #metadata_startup_script = file("startup.sh")
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
      hours = 0
      minutes = 30
      seconds = 30
      nanos = 20
    }

    monthly {
      week_day_of_month {
        week_ordinal = -1
        day_of_week  = "TUESDAY"
      }
    }
  }
}