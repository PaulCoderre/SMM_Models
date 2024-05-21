#!/bin/bash
#SBATCH --account=rpp-kshook
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-1:30:00
#SBATCH --mem=96G
#SBATCH --job-name=scenarios
#SBATCH --error=slurm_logs/slurm_%j.err
#SBATCH --output=slurm_logs/slurm_%j.out

module restore scimods
source ~/virtual-envs/scienv/bin/activate

run_number=$SLURM_ARRAY_TASK_ID

python elegant_run_ensemble.py $run_number





