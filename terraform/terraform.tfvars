#GCP settings
project = "zoomcamp-project-385518" 
region = "us-central1"

#Data Lake Cloud Storage Bucket
# gcs_bucket_name "proj_ny_citibike"
gcs_storage_class = "STANDARD"

#Data Warehouse BigQuery
bq_dataset = "dwh_ny_citibike_trips"

#Artifact registry
registry_repo_name  = "dl_citibike_rides"
repo_description = "For docker image which will run prefect extract-load"
repo_format = "DOCKER"

# GCE Schedule (Policy)
gce_policy_name = "sched_ny_citibike_run_monthly"
gce_policy_sched_start = "45 2 10 * *"
gce_policy_sched_start_stop = "15 3 10 * *"
# gce_policy_timezone = 'Americas/New_York'

#Compute Engine
gce_inst_name = "compute_instance_ny_citibike_prefect"
gce_machine_type  = "e1-micro"
gce_sa_email = "run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com"
gce_image = "ubuntu-2004-focal-v20230302"
gce_preemptible = True
gce_auto_restart = False