locals {
  # example local variable
  gcs_bucket_name = "proj_ny_citibike"
}

variable "project" {
  description = "full, unique id of GCP project"
  default = "zoomcamp-project-385518"
  type = string
}

## Comment out if using local var for "gcs_bucket_name"
# variable "gcs_bucket_name" {
#   description = "Bucket name for Data Lake"
#   type = string
#   default = "proj_ny_citybike"
# }

variable "region" {
  default = "us-central1"
  type = string
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "bq_dataset" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "ny_citibike_trips"
}


##
#Artifact registry
##
variable "registry_repo_name" {
  description = "Docker registry"
  type = string
  default = "citibike-rides"
} 

variable "repo_description" {
  description =  "Docker registry for prefect "
  type = string
  default = "prefect-registry"
} 

variable "repo_format" {
  description = "Format, usually 'DOCKER'" 
  type = string
  default  = "DOCKER"
}

##
# Compute Engine Resource/Schedule
# Comment out here, in main.tf, and in terraform.tfvars if not using
##

variable gce_policy_name {
  description = ""
  type = string
  default = "citibike_gce_sched_run_monthly"
}

variable gce_policy_sched_start {
  description = "Cron schedule for starting time"
  type = string
  default = "45 2 10 * *"
}

variable gce_policy_sched_start_stop {
  description = "Cron schedule for stop time"
  type = string
  default = "15 3 10 * *"
}


##
# Compute Engine
##
variable "gce_image" {
  description = "Image, eg the OS, from google image registry to use"
  type = string
  default = "ubuntu-2004-focal-v20230302"
}

variable gce_inst_name {
  description = ""
  type = string
  default = "prefect-citibike-compute-instance"
}

variable gce_machine_type {
  description = "Machine type for GCE"
  type = string
  default =  "e1-micro"
}

variable gce_sa_email {
  description = "service account email to use in creating GCE instance"
  type = string
  default = "run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com"
}

variable gce_preemptible {
  description = "Whether the VM can be stopped by GCE to allocate capacity to other VMs. They are cheaper. These are being phased out for 'Spot' VMs, which have  more features."
  type = bool
  default = False
}

variable gce_auto_restart {
  description = ""
  type = bool
  default = True
}