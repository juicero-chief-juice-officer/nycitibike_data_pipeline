terraform {
  required_version = ">= 1.0"
  backend "gcs" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
                    # storage bucket is infra_resources
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
  // credentials = file(var.credentials)  # Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS
}

# Data Lake Bucket
# no updates needed here; though we removed the _${var.project} as we were confident we wouldn't risk duplicate naming when creating
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${local.data_lake_bucket}"#_${var.project}" # Uses Local variable. Concatenates DL bucket & Project name for unique naming
  location      = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {  
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}

# DWH
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.bq_dataset
  project    = var.project
  location   = var.region
}


resource "google_artifact_registry_repository" "my-repo" {
  location      = var.region
  repository_id = var.repo_name
  description   = var.repo_description
  format        = var.repo_format
}


resource "google_compute_resource_policy" "gce_schedule" {
  name   = var.gce_policy_name
  region = var.gce_policy_region
  description = var.gce_policy_desc
  instance_schedule_policy {
    vm_start_schedule {
      schedule = var.gce_policy_sched_start
    }
    vm_stop_schedule {
      schedule = var.gce_policy_sched_start_stop
    }
    time_zone = var.gce_policy_timezone
  }
}

resource "google_compute_instance" "default" {
  name         = var.gce_inst_name
  machine_type = var.gce_machine_type
  zone         = var.region
  resource_policies = var.gce_policy_name

  boot_disk {
    initialize_params {
      image = var.gce_image
    }
  }

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = vars.gce_sa_email
  }
  
  scheduling {
    preemptible = var.gce_preemptible
    automatic_restart = var.gce_auto_restart

}
}