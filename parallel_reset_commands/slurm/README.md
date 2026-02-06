### Quick Start

1. Connect to Compute2 Login node
1. `cd` to the `parallel_reset_commands` directory
    ```bash
    cd ./parallel_reset_commands
    ```
1. `sudo bash` to become root in the current working directory

#### Interactive
1. As `root` launch an interactive job
    ```bash
    ./slurm/srun.sh
    ```
1. Perform your work interactively using the `parallel_acl_controller.py` like you would on any host.

#### Batch
1. Create an `inputs.csv` file within the `slurm` directory.
    * Please see `inputs-template.csv` for the format requirements.
    * Only single digit storage suffix supported at this time.
1. Get the total line count of your `inputs.csv`
    ```bash
    wc -l ./slurm/inputs.csv
    ```
    ```bash
    ❯ wc -l ./slurm/inputs.csv 
           7 ./slurm/inputs.csv # results in array of 0-6
    ```
1. Use the line count value to set the array size used by `./slurm/sbatch.sh`
    ```bash
    vi ./slurm/sbatch.sh
    ```
    ```bash
    ❯ grep array ./slurm/sbatch.sh 
    #SBATCH --array=0-6     # Adjust the range based on the number of lines in inputs.csv
    ```
1. As `root` launch the slurm batch job
    ```bash
    sbatch ./slurm/sbatch.sh
    ```

