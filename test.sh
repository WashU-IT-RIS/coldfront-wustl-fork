THPC_CONTAINER_OS="linux" \
THPC_BUILD="2023.06" \
LSF_DOCKER_VOLUMES="/home/a.santiago:/home/a.santiago /opt/thpc:/opt/thpc /home/a.santiago/ITSD-37090:/home/a.santiago/ITSD-37090 /storage1/fs1/a.santiago/Active:/storage1/fs1/a.santiago/Active /scratch1/fs1/a.santiago:/scratch1/fs1/a.santiago" \
bsub -q general \
     -a 'docker(ghcr.io/washu-it-ris/ris-thpc:runtime)' \
     -oo sub-.net-1.1.output.log \
     -n 4 \
     -G compute-ris \
     -J HCP_Rotate_Perm_Only \
     -M 4GB \
     -W 60 \
     -u a.santiago@wustl.edu \
     -R select[mem>4GB && tmp>4] -R rusage[mem=4GB, tmp=4] -R span[hosts=1] \
     ./HCP_Rotation_Only_MATLAB_thpc.sh



THPC_CONTAINER_OS="linux" \
THPC_BUILD="2023.06" \
LSF_DOCKER_VOLUMES="/home/a.santiago:/home/a.santiago /opt/thpc:/opt/thpc /home/a.santiago/ITSD-37090:/home/a.santiago/ITSD-37090 /storage1/fs1/a.santiago/Active:/storage1/fs1/a.santiago/Active /scratch1/fs1/a.santiago:/scratch1/fs1/a.santiago" \
bsub -q general \
     -a 'docker(ghcr.io/washu-it-ris/ris-thpc:runtime)' \
     -K \
     -oo sub-.net-1.1.output.log \
     -n 4 \
     -G compute-ris \
     -J HCP_Rotate_Perm_Only \
     -M 4GB \
     -W 60 \
     -N \
     -u a.santiago@wustl.edu \
     -R "select[mem>4GB && tmp>4] rusage[mem=4GB, tmp=4] span[hosts=1]" \
     ./HCP_Rotation_Only_MATLAB_thpc.sh


export ALPHAFOLD_BASE_DIR=/app/alphafold
export RIS_SERVICES=/storage2/fs1/RIS-Services/Active/AlphaFold3
export OUTPUT_DIRECTORY=/storage1/fs1/paul.hime/Active/alphafold3/output
export LSF_DOCKER_VOLUMES="$RIS_SERVICES:$RIS_SERVICES $OUTPUT_DIRECTORY:$OUTPUT_DIRECTORY $HOME:$HOME"
export PATH="/usr/local/cuda/bin/:/opt/conda/bin:/app/alphafold:$PATH"


python3 /app/alphafold/run_alphafold.py --output_dir=/storage1/fs1/a.santiago/Active/alphafold3/output --json_path /storage2/fs1/RIS-Services/Active/AlphaFold3/json/fold_input.json --max_template_date 2021-09-30


#Adjust these paths as needed
export XDG_CONFIG_HOME=/storage1/fs1/a.santiago/Active/podman/
export XDG_DATA_HOME=/storage1/fs1/a.santiago/Active/podman/
export XDG_RUNTIME_DIR=/storage1/fs1/a.santiago/Active/podman/runtime

srun -p general-interactive -A compute2-ris --pty /bin/bash

module load ris
module load podman slurm

# In the container
podman machine init --cpus 2 --memory 4096 --disk-size 200
podman machine start


gcp_project='ris-prod-gke'
gcp_config=${gcp_project}
gcp_region='us-central1-a'
gcp_service_account='prod-kubeadminsa01'
gke_cluster='ris-prod-kube-cluster'
gcloud config configurations list --filter PROJECT=${gcp_project}
gcloud config configurations activate ${gcp_config}
kubectl config get-contexts -o name | grep ${gcp_project}
kubectl config use-context gke_${gcp_project}_${gcp_region}_${gke_cluster}
kubectl exec -it -n coldfront deployment.apps/coldfront-deployment -- coldfront generate_integrated_billing_report --usage-date 2026-01-01 --tier Archive
kubectl exec -it -n coldfront deployment.apps/coldfront-deployment -- coldfront generate_integrated_billing_report --usage-date 2026-01-01 --tier Active
kubectl exec -it -n coldfront deployment.apps/coldfront-deployment -- cat /tmp/RIS-December-storage-archive-billing.csv > RIS-December-storage-archive-billing.csv
kubectl exec -it -n coldfront deployment.apps/coldfront-deployment -- cat /tmp/RIS-December-storage-active-billing.csv > RIS-December-storage-active-billing.csv