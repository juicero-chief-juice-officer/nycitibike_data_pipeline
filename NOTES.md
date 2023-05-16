
f729b34f0040df098e1e88cc12e10e99d0c2cad0

# TO DO
- Clean up SA key storage and naming
- How to update flow script without overwriting prefect yaml
- general naming structure should be more standardized
- maybe rewrite el script to do "if not default, then assume first run and run through all past dates"

NOTES
# Overview

In this project, we set up a basic ELT flow that pulls each monthly citibike ride report, clean it up, and move it to a data warehouse for analysis. 

The basic structure can be applied to any EL needs - though the parts of the core python script that access and transform data will need to be updated. 

It is intended to be easily replicable, and so looks for opportunities to skip over GUIs (especially in GCP) and attempts to leverage one or two schell scripts. However, GUIs can be very helpful to understand the structure of things like Google Cloud Platform. 

It references a few other projects and write-ups, listed at the bottom. 

## Problem Statement
New York's Citibike publishes monthly a file that lists every ride in the citibike system. We want to take these out of the external storage and into our data warehouse in order to run analyses against 



# Process

## 0. Environment/Repo set-up

Notes: 
- https://github.com/github/gitignore/tree/main is a helpful resource for creating your .gitignore.
- If you've recently upgraded from an Intel to an Apple Silicon mac, you may have some issues. Brief discussion [[here]]. 

## 1. GCP Set Up
This project runs on Google Cloud Platform, because GCP gives new users $300 in credit to be spent over 90 days. (It seems crazy that AWS doesn't offer the same, but I suppose market dominance has its privileges.) You need to set up a ($300 in free credit for the first 90 days) Google Cloud Account. Directions to do so abound, but googling "GCP", going to the first result, and clicking "get started for free" is a pretty good approach. No credit card is required. 

Make sure you are logged in in your browser, with the gmail account you used for the free gcp credit. Then cd to the directory you'd like to use for development and run the following to login:
```gcloud auth login ```

Follow the steps to login with your gmail account. Then run the following to create a GCP project and set it as your default. (A project might be akin to different applications within an organization.)

```
gcloud projects create [[your-project-name]] --name="Descriptive and Customized Project Name"
gcloud config set project [[your-project-name]]```

By default, GCP gives users almost no access to its products. You, the admin, need to turn them on first. You'll need to turn on the following APIs by searching them in the Ggoogle Gloud console search , or by running the following:
```zsh 
gcloud services enable artifactregistry.googleapis.com bigquery.googleapis.com bigquerymigration.googleapis.com bigquerystorage.googleapis.com compute.googleapis.com containerregistry.googleapis.com oslogin.googleapis.com pubsub.googleapis.com run.googleapis.com servicemanagemen.googleapis.com serviceusage.googleapis.com storage-api.googleapis.com storage-component.googleapis.com storage.googleapis.com
```

Cconfirm you were successful by running
```gcloud services list```

Now, within our project, a "service account" needs to be created, give that service account permissions, and download a service account key. You can do this all with one account (simplest), or you can separate them with more granular access (eg one that can create the infrastructure using terraform and another that can only read/write via prefect). Then we need to give that service account permission to access the GCP products we just enabled. 

Again this can be done entirely in the GCP GUI, but running the following ensures replicability by running through CLI: 

```zsh
gcloud iam service-accounts create your-service-account-name \
    --description="Descriptive name, maybe one that describes the EL process" \
    --display-name="My EL service account"
```

# Add permissions
# Roles source: https://cloud.google.com/iam/docs/understanding-roles
# this can alternatively be done by passing a json with the roles
# --> $ gcloud projects get-iam-policy my-project --format json > ~/policy.json

```zsh
$ gcloud projects add-iam-policy-binding zoomcamp-project-385518 \
    --member="serviceAccount:run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

$ gcloud projects add-iam-policy-binding zoomcamp-project-385518 \
    --member="serviceAccount:run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com" \
    --role="roles/run.admin"
$ gcloud projects add-iam-policy-binding zoomcamp-project-385518 \
    --member="serviceAccount:run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com" \
    --role="roles/compute.admin"
```

???download key??
```zsh
gcloud iam service-accounts keys create KEY_FILE \
    --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com```

    # Create Service Account KEY
$ gcloud iam service-accounts keys create sa_keys/run-citibike-el1.json \
    --iam-account=run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com
dasd

At this point, we'll pause to set up some other pieces outside of GCP. 
```
## 2. Terraform (Infrastructure as Code)
Terraform is used to automate the provisioning (creation) and management of our resources. Terraform could be used for the majority of the GCP work done above, but doing some GCP work via command line or GUI is helpful to understand how GCP works. 

Terraform will be used to create the Google Cloud Storage data lake, and the Google Big Query data warehouse. 

### Install Terraform
First, install terraform using homebrew:
```zsh
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew update
brew upgrade hashicorp/tap/terraform
```
Finally enable tab completion by running `touch ~/.bashrc` if running bash, or `touch ~/.zshrc` if running zsh.

Confirm successful installation by running `terraform -help`

### Design Infrastructure via Terraform

Terraform can be leveraged quite simply by creating three docs in ??your repo??: `main.tf`, `variables.tf` and `terraform.tfvars`.

Main will tell Terraform what to do, and how to do it:
** Terraform Versioning
** Infrastructure technologies/providers 
** Infrastructure to create

Variables describes all the variable inputs, including optionally setting defaults.
terraform.tfvars is where the variables are set. 
** The GCP project
** Region for creating assets
** Names, etc. for the assets to be created.

Note that almost all GCP pieces can be created via Terraform. For example, instead of running `gcloud artifacts repositories create ...` to create the repo, a repo can be created with the documentation here: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository. The same goes for compute instance. https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance


### Build using Terraform
You will initialize using the .tfs you built, then run plan to review changes in the local file and align with you on an implementation plan. Finally apply approves that implementation plan and tells GCP to run it. 

```
terraform init
terraform plan
terraform apply
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

* Create Prefect Service Account
```zsh

```
* Create Prefect Cloud account
* Create Prefect Workspace

Now, create the following blocks:
* GCP Credentials: Paste in the text of the service account key json you downloaded.
* Google Cloud Storage (GCS): Paste in the name of the GCS Bucket from your terraform. Link the Credentials Block you just made.
* GitHub: Linking to your GH repo, and using a Personal Access Token
* GCP Cloud Run Job: 


## 4. Docker


Download and install Docker from https://www.docker.com/.



# Note the `.`!!!, which is the path you're telling dcker to buildin [`.` is current directory)]
docker build -t citibike-rides:v0 .

docker tag citibike-rides:v0 us-central1-docker.pkg.dev/zoomcamp-project-385518/citibike-docker-repo/citibike-rides:v0
docker push us-central1-docker.pkg.dev/zoomcamp-project-385518/citibike-docker-repo/citibike-rides:v0


- create prefect gcp-credentials, GCS, and google-cloud-run blocks. 
```
Credentials: 
- paste service account json contents

GCP
- bucket path: ny_citibike_live (will be consistent with terraform)
Cloud run:
Type: cloud-run-job
Image name: us-central1-docker.pkg.dev/zoomcamp-project-385518/citibike-docker-repo/
Region: us-central1
Credentials: citibike-creds
```

prefect deployment build prefect/el_from_citibike_to_gcs.py:el_parent_flow --name citibike-deployment
# This generates a prfect deployment YAML
# Update the YAML with your schedule
# ```schedule: 
  cron: 0 3 10 * *
  timezone: America/New_York```
# and description: `description: "Prefect flow via cloud run/docker that will pull from citibike rides monthly and add to cloud storage."`

# GUI: Create GH PAT and GH Prefect Blocks (`gh-block-citibike`)

prefect deployment build prefect/el_from_citibike_to_gcs.py:el_parent_flow --name citibike-deployment --storage-block github/gh-block-citibike  --infra-block cloud-run-job/citibike-cloudrun-block --output el_parent_flow-deployment.yaml --apply



# try same settings as zoomcamp here?? https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-c/instances/zoomcamp-project?authuser=1&project=zoomcamp-project-385518&tab=details

# create schedule, as this process is designed to be always up, but that's expensive
gcloud compute resource-policies create instance-schedule citibike_monthly \
    --description='Run once a month for 30 minutes' \
    --region=us-central1-a \
    --vm-start-schedule='45 2 10 * *' \
    [--vm-stop-schedule='15 3 10 * *'] \
    --timezone=Americas/New_York
    <!-- [--initiation-date=INITIATION_DATE] \ -->
    <!-- [--end-date=END_DATE] -->

# create a vm with that schedule you just made
gcloud compute instances create prefect-citibike-compute-instance \
--resource-policies=[scheudlename]
--image=ubuntu-2004-focal-v20230302 \
--image-project=ubuntu-os-cloud \
--machine-type=e2-micro \
--service-account=run-citibike-el@zoomcamp-project-385518.iam.gserviceaccount.com \
--zone=us-central1-a \
--preemptible

# ssh in 
gcloud compute ssh prefect-citibike-compute-instance --zone=us-central1-a


#################
#################
#SET UP VM
#################
#################

#now within the vm
touch install_script.sh
nano install_script.sh

# Paste in the following, then hit ctrl + x, y, enter
```
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
# make the thing you file created executable
# note - listed on page as chmod+x
sudo chmod +x install_script.sh

# run it
./install_script.sh

# refresh/reload shell
source ~/.bashrc


Section sources: 
https://stackoverflow.com/questions/69981439/activating-conda-during-bash-script-that-installing-anaconda
https://stackoverflow.com/questions/28852841/install-anaconda-on-ubuntu-or-linux-via-command-line
https://askubuntu.com/a/1041348

Note that different guides online recommend different paths to direct the `bash Ananconda...` to (eg /anaconda). Make sure you are consistent between this line and the `echo` line you use to write to .bashrc.

.bashrc is what is run everytime you login, anaconda adds itself to that


adter docker-compose 
add to bashrc export  PATH="${HOME}/bin:${PATH}"
    source .bashrc

# ######
# install script to easily install important packages and optimize start-up process

# ######
#!/bin/bash
# Go to home directory
cd ~

# get list of possible packages
sudo apt-get update -y 
sudo apt-get upgrade -y 
# Install docker
sudo apt-get install -y \
docker.io 

# install docker compose
# not necessary if running via artifact registry and cloudrun
mkdir bin/
wget https://github.com/docker/compose/releases/download/v2.17.3/docker-compose-linux-x86_64 -O bin/docker-compose
sudo chmod +x bin/docker-compose
bash bin/docker-compose
source ~/.bashrc
PATH="${HOME}/bin:$PATH"
export PATH

# Download, install, remove Anaconda installer
wget https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh

bash Anaconda3-2022.10-Linux-x86_64.sh -b -p ~/anaconda
rm Anaconda3-2022.10-Linux-x86_64.sh

# add anaconda path to .bashrc
echo 'export PATH="~/anaconda/bin:$PATH"' >> ~/.bashrc

# Refresh
source ~/.bashrc

# confirm anaconda installed and initiate
conda update conda
conda --version
conda init


docker-compose up -d
prefect cloud login -k pnu_SPGO9Sy9q0ivUxM4bfFFQLIj7XT2NA4aDIMF
prefect agent start -q default



bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/anaconda3


#ALTERNATIVE is 
sudo grouadd docker
sudo gpasswd -a $USER docker
sudo service docker restart

#!/bin/bash
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y \
ca-certificates \
curl \
gnupg \
lsb-release \
software-properties-common \
python3-dateutil
sudo ln-s /usr/bin/python3 /usr/bin/python
wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
PATH="$HOME/.local/bin:$PATH"
exportPATH
pip3 install prefect prefect-gcp
prefect cloud login -k <INSERT_PREFECT_API_KEY>



# Alternatives
This is a very simple process that could be done in a variety of ways. 

However, while the method developed here is, relatively, overwrought for such an application, doing so affords more opportunities to scale, layer in complexity, manage/implement across a team, reproduce, diagnose issues, etc.


# References
https://cloud.google.com/iam/docs/service-accounts-create#iam-service-accounts-create-gcloud