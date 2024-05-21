#!/bin/bash
#SBATCH --account=rpp-kshook
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-7:00:00
#SBATCH --mem=48G
#SBATCH --job-name=easymore
#SBATCH --error=slurm_logs/slurm_%j.err
#SBATCH --output=slurm_logs/slurm_%j.out

module restore scimods
source ~/virtual-envs/scienv/bin/activate

directory_index=$SLURM_ARRAY_TASK_ID
ensembles=3
range=$((directory_index * ensembles - ensembles))

for ((i = $range; i < $((range + ensembles)); i++)); do
    python 01_run_easymore.py "$i"
done




