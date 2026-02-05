#!/bin/bash

module load slurm python3

srun --job-name=parallel_reset_srun \
     --cpus-per-task=8 \
     --time=1-12:00:00 \
     --partition=general-cpu \
     --pty /bin/bash
