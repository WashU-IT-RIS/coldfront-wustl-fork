#!/bin/bash

#SBATCH --job-name=parallel_reset_sbatch
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=2
#SBATCH --time=1-12:00:00
#SBATCH --partition=general-cpu
#SBATCH --array=0-6     # Adjust the range based on the number of lines in inputs.csv

module load python3

# Read inputs from a csv file. Read the line corresponding to the SLURM_ARRAY_TASK_ID
# formatted as: wustlkey,storage2_allocation,{storage2_suballocation2,storage2_suballocation2,...}
input_file="./slurm/inputs.csv"
input_line=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" $input_file)
allocation_root=$(echo $input_line | cut -d',' -f2)
sub_allocations=$(echo $input_line | cut -d',' -f3 | tr -d '{}')
storage_suffix=$(echo "$allocation_root" | grep -Po '(?<=storage)\d+')

# Print the parameters for logging
echo "Allocation Root: $allocation_root"
echo "Sub Allocations: $sub_allocations"
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"
echo "Starting parallel reset process..."

# Create task-specific log directory
log_dir="./slurm/logs/$SLURM_JOB_ID/task_${SLURM_ARRAY_TASK_ID}"
mkdir -p $log_dir

# Define walker parameters
num_walkers=4
num_workers_per_walk=10
perform_reset="n"

# Execute the parallel reset command with the parameters read from the input file
if [ ! -z "$sub_allocations" ]; then
    srun python3 ./parallel_acl_controller.py --perform_reset $perform_reset --allocation_root $allocation_root --target_dir ${allocation_root}/Active --sub_allocations $sub_allocations --storage_suffix $storage_suffix --num_walkers $num_walkers --num_workers_per_walk $num_workers_per_walk --log_dir $log_dir
    echo "Parallel reset process complete for SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID, Allocation Root: $allocation_root"
    exit 0
else
    srun python3 ./parallel_acl_controller.py --perform_reset $perform_reset --allocation_root $allocation_root --target_dir ${allocation_root}/Active --storage_suffix $storage_suffix --num_walkers $num_walkers --num_workers_per_walk $num_workers_per_walk --log_dir $log_dir
    echo "Parallel reset process complete for SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID, Allocation Root: $allocation_root"
    exit 0
fi

