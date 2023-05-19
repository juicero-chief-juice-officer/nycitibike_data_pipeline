#RENAME THIS AS `terraform.tfvars`
#GCP settings
project = "sbh-nycitibike-pipeline-main" 
region = "us-central1"

# Service Accounts and roles
# map/dict with key service-account name and values map/dict of description and list of roles to be assigned
# EG :
#       = {"generic-primary-svc-acct" = {
#                         description = "Generic Primary SA with limited view access"
#                         roles=        ["roles/browser"]
#                           }
#          ... }

svc_accts_and_roles = {
            "prefect-el-sa1" = {
                        description = "SA to be used by Prefect to run services and write to cloud storage."
                        roles=        [
                                        "roles/iam.serviceAccountUser"
                                      ,  "roles/storage.objectCreator"
                                      , "roles/run.invoker"
                                    #   , "roles/compute.imageUser"
                                      ]
                          }
            "dbt-trnsfrm-sa1" = {
                        description = "SA to be used by DBT to transform data and update/manage bigquery data warehouse."
                        roles=        [
                                        "roles/iam.serviceAccountUser"
                                      ,  "roles/storage.admin"
                                      , "roles/run.invoker"
                                      , "roles/storage.objectViewer"
                                      ]
                          }
            # "tktktk-analytics-sa1" = {
            #             description = "SA to be used by tktk to perform and render analysis of data "
            #             roles=        [
            #                             "roles/storage.admin"
            #                           , "roles/run.admin"
            #                           , "roles/storage.admin"
            #                           ]
            #               }

                  }



#Data Lake Cloud Storage Bucket
gcs_bucket_name = "sbh-nycitibike-pipeline-gcsdlb-rides-p01"
# gcs_storage_class = "STANDARD"

#Data Warehouse BigQuery
bq_dataset = "gbqdwh_rides"

#Artifact registry
registry_repo_name  = "sbh-nycitibike-pipeline-ar-vmrepo-usc1-p01"
repo_description = "For docker image which will run prefect extract-load"
repo_format = "DOCKER"

# GCE Schedule (Policy)
gce_policy_name = "sbh-nycitibike-pipeline-gcepol-vmsched-usc1-p01"
gce_policy_desc = "Runs from 2:45/3 until 3:15am every month on the 10th of the month."
gce_policy_sched_start = "45 2 10 * *"
gce_policy_sched_stop = "15 3 10 * *"
# gce_policy_timezone = 'America/New_York' (commented out as we will use default set in variables.tf)

#Compute Engine
gce_inst_name = "sbh-nycitibike-pipeline-gceimg-image-usc1-p01-001"
gce_image = "ubuntu-2004-lts"
gce_machine_type  = "e2-micro"
gce_zone  = "us-central1-a"
gce_image_size = 12
gce_preemptible = true
gce_auto_restart = false
# gce_sa_email = "x@y.iam.gserviceaccount.com"