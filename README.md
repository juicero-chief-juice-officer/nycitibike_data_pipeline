# Overview

In this project, we set up a basic EL flow that pulls a monthly report of NYC's [CitiBike](https://citibike.com) rides, cleans it up, and moves it to a data lake for analysis. A separate project will address the analysis process.

The basic structure can be applied to any EL needs - though the parts of the core python script that access and transform data will need to be updated. 

It is intended to be easily replicable, and so looks for opportunities to skip over GUIs (especially in GCP), uses basic shell scripts, and exclusively free (or effectively free) services. However, GUIs can be very helpful to understand the structure of things like Google Cloud Platform, Prefect, etc.

It references a few other projects and write-ups, listed at the bottom. 

## Problem Statement
New York's Citibike publishes monthly a file that lists every ride in the citibike system. We want to take these out of the external storage and into our data warehouse in order to run analyses against 

# Process

## 0. Project/Environment/Repo set-up

### Naming convention

First, it's helpful to describe a naming convention. I have a bias toward underscores, but the reach of "big hyphen" and their powerful lobby cannot be understated. We thus use hyphens in naming resources. 

The format for GCP Projects is: `[org]-[project]-[component]-[resource/env]`, using  env and resource/family of resources only if resources are split across multiple GCP projects. Else `main`. 

The general format for resources will be:
- [org prefix] - (Optional) I use my initials out of habit. In a business setting, this may be the org or dept name.
- [project] - Broad description of the project
- [component] - The part of the project owned within. For example "pipeline"
- [resource] - 3 letter abbreviation of the resource, plus 3 letter letter if ______
- [description] - 
- [location/zone] - 2 letters for region; 1-2 for cardinal direction; 1 number; 1 letter if zoned
- [env] - 1 letter denoting [d]ev, [s]tage or [p]rod. 
- [version/iteration number]- Terraform has a random_id generator, though for learning/personal development, I find using sequential numbers helpful. Thus the format 
- [resource number]- Only used if multiple identical resources are created.

Yielding: 
- GCP
  - Project: `sbh-nycitibike-pipeline-main`
  - Artifact Repository Repo: `sbh-nycitibike-pipeline-ar-vmrepo-usc1-p01`, 
  - Compute Engine Schedule ("policy"): `sbh-nycitibike-pipeline-gcepol-vmsched-usc1-p01`, 
  - Compute Engine Image: `sbh-nycitibike-pipeline-gceimg-image-usc1-p01`,  
  - Compute Engine Instance: `sbh-nycitibike-pipeline-gceimg-image-usc1-p01-001`,  
  - Cloud Storage Bucket: `sbh-nycitibike-pipeline-gcsdlb-rides-p01`,
  - *Exception:* Service Accounts: `prefect-sa1-[4-character hex]`, (Service accounts are in email form `[sa_name]@[proj_name].iam.gserviceaccount.com` so do not need those descriptors.)
  - *Exception:* BigQuery Dataset: `gbqdwh_rides` (Datasets may be organized in various ways - by department, by source/stage/final, etc. All data sets are quereied within their GCP Project, so there is no need to include project info.) 
- Prefect
  - Workspace: `[org]-[project]-[component]-[env]-pfct-ws` (`sbh-nycitibike-pipeline-p-pfct-ws`)
  - Block: `[org]-[project]-[component]-[env]-pfct-blk-[block-type]` (`sbh-nycitibike-pipeline-p-pfct-blk-gcp-cred`, `sbh-nycitibike-pipeline-p-pfct-blk-gcs-dlb`, etc.)
  - Scripts/Flows 

### Git
https://github.com/github/gitignore/tree/main is a helpful resource for creating your .gitignore.

### Apple Silicon
If you've recently upgraded from an Intel to an Apple Silicon mac, you may have some issues. Brief discussion [here](https://tktktkt.com). 

### Environment setup

We used conda to manage virtual environments and poetry to install packages, but this is not strictly necessary. (pip can install via requirements.txt; conda can install via environment.yml.) For poetry we create the `pyproject.toml` file.

```zsh
conda create --name citibike-pipeline -c conda-forge python=3.11 pip
conda activate citibike-pipeline
conda install poetry
curl -sSL https://install.python-poetry.org | python3 -
poetry install --no-root
```


## 1. GCP Set Up
This project runs on Google Cloud Platform, because GCP gives new users $300 in credit to be spent over 90 days. (It seems crazy that AWS doesn't offer the same, but I suppose market dominance has its privileges.) You need to set up a ($300 in free credit for the first 90 days) Google Cloud Account. Directions to do so abound, but googling "GCP", going to the first result, and clicking "get started for free" is a pretty good approach. No credit card is required. 

Install [gcloud CLI](https://cloud.google.com/sdk/docs/install-sdk).

Make sure you are logged in in your browser, with the gmail account you used for the free gcp credit. Then cd to the directory you'd like to use for development and run the following to login:
```gcloud auth login ```

Follow the steps to login with your gmail account. Then run the following to create a GCP project and set it as your default. (A project might be akin to different applications within an organization.)

```
gcloud projects create [[your-project-name]] --name="Descriptive and Customized Project Name"
gcloud config set project [[your-project-name]]
```

Enable billing by opening [billing settings](https://console.cloud.google.com/billing/projects), going to my projects, selecting the kebab and clicking Change Billing. Set the Billing Account (default is okay). 

By default, GCP gives users almost no access to its products. You, the admin, need to turn them on first. You'll need to turn on the following APIs by searching them in the Google Gloud console search , or by running the following:
```zsh 
gcloud services enable artifactregistry.googleapis.com bigquery.googleapis.com bigquerymigration.googleapis.com bigquerystorage.googleapis.com compute.googleapis.com artifactregistry.googleapis.com oslogin.googleapis.com pubsub.googleapis.com run.googleapis.com servicemanagement.googleapis.com serviceusage.googleapis.com storage-api.googleapis.com storage-component.googleapis.com storage.googleapis.com
```

Cconfirm you were successful by running `gcloud services list`.

*Note: The rest of this section can be skipped if you are comfortable building most infrastructure with Terraform.* 

Now, within our project, a "service account" needs to be created, which will hold the permissions to access the products/resources turned on above. Once created, give that service account permissions, and download a service account key. You can do this all with one account (simplest), or you can separate them with more granular access (eg one that can create the infrastructure using terraform, another that can only read/write via Prefect, etc.) Then we need to give that service account permission to access the GCP products we just enabled. 

(A slightly more granular approach to service accounts might look like:)
* Terraform Service Account (Can be used as default/local.): Admin roles on Compute, Storage, BigQuery, and 
* Prefect Service Account: Storage Object Creator, Cloud Run Invoker, etc. 
* And so on.

Again this can be done entirely in the GCP GUI, but running the following ensures replicability by running through CLI (example follows). Adding permissions can also be done by passing a json with the roles (`gcloud projects get-iam-policy my-project --format json > ~/policy.json`). Roles are described [here](https://cloud.google.com/iam/docs/understanding-roles).

If you are following these steps, rather than using Terraform, your Service Account won't necessarily need the 4-char random hex. You will be told if it is not unique.
```zsh
gcloud iam service-accounts create SA_NAME \
    --description="Descriptive name, maybe one that describes the EL process" \
    --display-name="SA_NAME"
```

```zsh
gcloud projects add-iam-policy-binding SA_NAME \
    --member="serviceAccount:SA_NAME@SA_NAME.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding SA_NAME \
    --member="serviceAccount:SA_NAME@SA_NAME.iam.gserviceaccount.com" \
    --role="roles/run.admin"
gcloud projects add-iam-policy-binding SA_NAME \
    --member="serviceAccount:SA_NAME@SA_NAME.iam.gserviceaccount.com" \
    --role="roles/compute.admin"
```

At this point, we'll pause to set up some other pieces outside of GCP. 
```
## 2. Terraform (Infrastructure as Code)
Terraform is used to automate the provisioning (creation) and management of our resources. Terraform could be used for the majority of the GCP work done above, but doing some GCP work via command line or GUI is helpful to understand how GCP works. 

On the other hand, one of the relatively minor, but still helpful, advantages of Terraform is that you can review/manage settings (eg by using a single location for all resources) and naming conventions in a single place. 

Terraform will be used to create the Google Cloud Storage data lake, the Google Big Query data warehouse, the Artifact Registry that will store the Docker Image, and the Virtual Machine that will run the data pipeline.

### Install Terraform
First, install terraform using homebrew:
```zsh
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew update
brew upgrade hashicorp/tap/terraform
```
Finally enable tab completion by running `touch ~/.bashrc` if running bash, or `touch ~/.zshrc` if running zsh.

Confirm successful installation by running `terraform -help`.

### Create bucket for terraform state storage. 
Terraform can store the terraform state locally or in the cloud. We use cloud storage, but the bucket it is stored in must be created by you, Terraform will not create it. 

```
gcloud storage buckets create gs://z_infra_resources
```

### Design Infrastructure via Terraform

Terraform can be leveraged quite simply by creating three docs in ??your repo??: `main.tf`, `variables.tf` and `terraform.tfvars`.

Main will tell Terraform what to do, and how to do it:
  * Terraform Versioning
  * Infrastructure technologies/providers 
  * Infrastructure to create

Variables describes all the variable inputs, including optionally setting defaults.
terraform.tfvars is where the variables are set. 
  * The GCP project
  * Region for creating assets
  * Names, etc. for the assets to be created.

Note that almost all GCP pieces can be created via Terraform. For example, instead of running `gcloud artifacts repositories create ...` to create the repo, a repo can be created with the documentation [here](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository). The same goes for compute instance, as demonstrated in the Terraform files.


### Build using Terraform
You will initialize using the .tfs you built, then run plan to review changes in the local file and align with you on an implementation plan. Finally apply approves that implementation plan and tells GCP to run it. 

```
terraform -chdir=terraform/ init
terraform -chdir=terraform/ plan
terraform -chdir=terraform/ apply
```
*Note: rather than using chdir, you could just cd into the terraform directory.*

One last piece: There is an issue with the terraform main.tf that prevents the Compute instance schedule (aka resource policy) from being added. Pending resolution, that will need to be done through the GUI at https://console.cloud.google.com/iam-admin/iam?authuser=1&project=[[project-name]]. Select the edit icon on `....-compute@developer.gserviceaccount.com` and add the role Compute Admin.

```
gcloud compute instances add-resource-policies sbh-nycitibike-pipeline-gceimg-image-usc1-p01-001 --resource-policies=sbh-nycitibike-pipeline-gcepol-vmsched-usc1-p01
```
### CLI alternatives

To create the Artifact Repo: 
```#
 creates repo, not an image
gcloud artifacts repositories create citibike-docker-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="repo for Docker citibike EL"

#optional and not necessary check of the repo you just built
gcloud artifacts repositories describe citibike-docker-repo \
    --location=us-central1
```


## 3. Prefect
Prefect can be used locally or via Prefect Cloud to manage/orchestrate data pipeline tasks (an alternative to Apache AirFlow ). It will come to tell Cloud Run to run the flow ....

### Prefect Cloud
We need to: 
* Create Prefect Cloud account
* Create Prefect GCP Service Account (done previously)
* Create Prefect Workspace and Blocks
* Build a deployment with the Blocks.

(From the project directory,) get a Service Account key for your Prefect Service Account:
```zsh
#Format: 
gcloud iam service-accounts keys create KEY_FILE.json \
    --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com```

$ gcloud iam service-accounts keys create sa_keys/prefect-el-sa1.json \
    --iam-account=prefect-el-sa1@sbh-nycitibike-pipeline-main.iam.gserviceaccount.com
```

Create the following blocks:
* GCP Credentials: Paste in the text of the service account key json you downloaded.
* Google Cloud Storage (GCS): Paste in the name of the GCS Bucket from your terraform. Link the Credentials Block you just made.
* GitHub: Linking to your GH repo, optionally using a PAT (if private repo). Use the `GitHub`, not the `GitHub Repository` block type.
* GCP Cloud Run Job: Image name in format `[[region]]-docker.pkg.dev/[[project-name]]/[[Artifact Registry Repo Name]]/` (eg `us-central1-docker.pkg.dev/sbh-nycitibike-pipeline-main/sbh-nycitibike-pipeline-ar-vmrepo-usc1-p01/`; note that copying from the GCP Repo will exclude the trailing `/`.)
  * Note this name as it hasn't been assigned yet.

### Build the Prefect deployment for your flow, passing a schedule to the deployment.

At this point, everything is in place, but if you look at Prefect you'll see no Flows (as in, Prefect has the infrastructure it needs but doesn't expect to do any work.) You'll need to build a deployment. If you have any issues identifying blocks, you can use `prefect block ls`. 

```zsh
prefect deployment build prefect/el_from_citibike_to_gcs.py:el_parent_flow \
              --name sbh-nycitibike-prfct-dplmt \
              --cron "0 3 10 * *" \
              --timezone 'America/New_York' \
              --description "Prefect flow via cloud run/docker that will pull from citibike rides monthly and add to cloud storage." \
              -sb github/sbh-nycitibike-pipeline-p-pfct-blk-git-repo  \
              -ib cloud-run-job/sbh-nycitibike-pipeline-p-pfct-blk-gcr-job \
              --output prefect/el_parent_flow-deployment.yaml \
              --apply
```

Alternatively, you can do this in a few steps. 
```zsh
prefect deployment build prefect/el_from_citibike_to_gcs.py:el_parent_flow --name sbh-nycitibike-prfct-dplmt --output prefect/el_parent_flow-deployment.yaml
```
Open the Prefect deployment YAML, in which `schedule: null` and `is_schedule_active...` can be replaced with:
```yaml
  schedule: 
    cron: 0 3 10 * *
    timezone: America/New_York
  is_schedule_active: true
```
Add as well as a description: `"Prefect flow via cloud run/docker that will pull from citibike rides monthly and add to cloud storage."` Then, rebuild using the blocks and updated yaml, and include the --apply tag to register the Deployment with Prefect API.

```zsh
prefect deployment build prefect/el_from_citibike_to_gcs.py:el_parent_flow --name sbh-nycitibike-prfct-dplmt --storage-block github/sbh-nycitibike-pipeline-p-pfct-blk-ghb-rep  --infra-block cloud-run-job/sbh-nycitibike-pipeline-p-pfct-blk-gcr-job --output el_parent_flow-deployment.yaml --apply
```

### Generate an API key.
Finally, generate and save a [Prefect API](https://app.prefect.cloud/my/api-keys) key. 

## 4. Connect Prefect to Google Compute Engine and build VM

If you did not create a compute instance with Terraform, you'll need to do so via CLI (or GUI):

First, create schedule, as these are designed to be always up, but that's expensive. Then create the vm with the schedule you just made.

```zsh
gcloud compute resource-policies create instance-schedule citibike_monthly \
    --description='Run once a month for 30 minutes' \
    --region=us-central1-a \
    --vm-start-schedule='45 2 10 * *' \
    --vm-stop-schedule='15 3 10 * *' \
    --timezone=Americas/New_York 

gcloud compute instances create sbh-nycitibike-pipeline-gceimg-image-usc1-p01-001 \
--resource-policies=[schedulename] \
--image=ubuntu-2004-focal-v20230302 \
--image-project=ubuntu-os-cloud \
--machine-type=e2-micro \
--service-account=SA_NAME@SA_NAME.iam.gserviceaccount.com \
--zone=us-central1-a \
--preemptible
```

## Set up VM
Access that VM via ssh.
```zsh
gcloud compute ssh sbh-nycitibike-pipeline-gceimg-image-usc1-p01-001 --zone=us-central1-a
```

Now, within the VM, you have a "factory" (blank) Llinux install and can run whatever commands you want. In order to run the processes needed for the purposes of this project:
  * Conda needs to be installed. 
  * The machine needs to be told each time it boots up to to start a conda environment and run all commands from within that env.
  * Prefect packages need to be installed


### Create installation shell scripts
This is done in two stages via shell scripts. First Anaconda is set up and saved, then Prefect. (In a future iteration, this may be done by Terraform upon creating the instance.)

Create two shell scripts (`touch` creates, `nano` opens for editing): 
```bash
touch install_pt1.sh install_pt2.sh
nano install_pt1.sh
```

Paste the following into install_pt.sh (hit ctrl+x, then y, then enter to exit and save):
```sh
#!/bin/bash
# Go to home directory
cd ~
# You can change what anaconda version you want on the anaconda site
#!/bin/bash
wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
bash Anaconda3-2023.03-1-Linux-x86_64.sh -b -p ~/anaconda3
rm Anaconda3-2023.03-1-Linux-x86_64.sh
echo 'export PATH="~/anaconda3/bin:$PATH"' >> ~/.bashrc 
# messy workaround for difficulty running source ~/.bashrc from shell script in ubuntu
# sourced from askubuntu question 64387
eval "$(cat ~/.bashrc | tail -n +10)"
conda init
conda update conda
conda --version
```
Note that different guides online recommend different paths to direct the `bash Ananconda...` to /anaconda/... or /anaconda3/... Make sure you are consistent between this line and the `echo` line you use to write to .bashrc.

Then run `nano install_pt2.sh` to open and edit, and paste the following into that file:
```sh
#!/bin/bash
sudo apt-get update -y
sudo apt-get upgrade -y
pip install prefect prefect-gcp
prefect cloud login -k <NSERT_PREFECT_API_KEY>
echo 'prefect agent start -q default' >> ~/.bashrc
```

### Make shell scripts executable
At this point the shell scripts are idle files, rather than executable programs/scripts. You will need to make them both executable by running:
```bash
sudo chmod +x install_pt1.sh install_pt2.sh
```

### Run shell scripts
Run the following commands. The reason there are two separate scripts is that the `source ~/.bashrc` is very hard (for me at least) to replicate within a script (see [this discussion](https://askubuntu.com/a/1041348) for details). Pasting in a simple command is much easier than finding a workaround. This command reloads the shell and allows changes made to it (initializing Anaconda on boot and directing commands to be run via Anaconda) to be accessed.

```bash
./install_pt1.sh
source ~/.bashrc
./install_pt2.sh
source ~/.bashrc
```

You should see the PREFECT AGENT ASCII, as you have added `export prefect agent start -q default` to the startup process (.bashrc) and reloaded the machine.

## 5. Docker
Download and install Docker from https://www.docker.com/.

### Prepare Docker Image
Create your `Dockerfile`, which will tell Docker how to assemble the Docker image.
```Dockerfile
FROM prefecthq/prefect:2.7.7-python3.9

COPY docker-requirements.txt .
COPY prefect/el_from_citibike_to_gcs.py prefect/el_from_citibike_to_gcs.py

RUN pip install -r docker-requirements.txt --trusted-host pypi.python.org

# ENTRYPOINT [ "python", "prefect/[name_of_pipeline_script].py" ]
```

Create the `docker-requirements.txt`, which will become the docker image's requirements.txt. (Note that pyarrow there to assist in parquetizing the input data, which is done less out of necessity than a desire to explore different formats. the orjson requirement may not be necessary, but some later builds of orjson seemed to have issues on Apple Silicon.)
```requirements.txt
pandas==1.5.2
orjson==3.8.10
prefect-gcp[cloud_storage]==0.3.0
protobuf==4.21.11
pyarrow==10.0.1
```

The first document is all that is needed to build a docker image. Dockerfile is the default name, but a different file or path can be passed using the `-f` or `--file`. Within the Dockerfile, docker is told to `pip install` the docker-requirements.txt packages. 

### Build Docker image
First, (authenticate)[https://cloud.google.com/artifact-registry/docs/docker/store-docker-container-images#auth]. 
```zsh
gcloud auth configure-docker us-central1-docker.pkg.dev
```

Note the `.`!, which is the path docker to buildin (`.` is current directory). 
* The `-t` flag sets the name and optional tag (`name:tag`) for the image.
* The tag command tells Docker the specific location it will send the image to, in this case the "google_artifact_registry_repository" created with Terraform. Format is `us-central1-docker.pkg.dev/[project_name]/[repo_name]` (which can be copied from the Artifact Repository GUI).
* The push command sends the image to the GCP Artifact Repository.

```zsh 
docker build -t nycitibike-rides-docker:v0 .
docker tag nycitibike-rides-docker:v0 us-central1-docker.pkg.dev/sbh-nycitibike-pipeline-main/sbh-nycitibike-pipeline-ar-vmrepo-usc1-p01/nycitibike-rides-docker:v0
docker push us-central1-docker.pkg.dev/sbh-nycitibike-pipeline-main/sbh-nycitibike-pipeline-ar-vmrepo-usc1-p01/nycitibike-rides-docker:v0
```


# Complete!
At this point, the data pipeline should be functional. You should be able to manually trigger the flow from within Prefect ("Quick Run") and see data from the most recent month updated in Cloud Storage. 

# Next Steps
The next step will be to trigger and run the analytics processes that turn the raw data into a usable analysis. That can easily be done within Prefect, but will be separated into a separate Project. 


# Notes/Alternatives
Ultimately, the work that happens here is a very simple process that could be done in a variety of different ways. 

While the method developed here is, relatively, overwrought for such an application, doing so affords more opportunities to scale, layer in complexity, manage/implement across a team, reproduce, diagnose issues, etc., myriad more simple and more complex solutions abound.
