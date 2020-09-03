[![Snakemake](https://img.shields.io/badge/snakemake-≥5.18.0-brightgreen.svg?style=flat-square)](https://snakemake.bitbucket.io)
[![License](https://img.shields.io/apm/l/vim-mode.svg)](LICENSE)

# flower_map
A pipeline for generating maps of the species of flowers around a bee colony using drone imagery.

# download
Execute the following commands or download the [latest release](https://github.com/beelabhmc/flower_map/releases/latest) manually.
```
wget -O- -q https://github.com/beelabhmc/flower_map/tarball/master | tar mxvzf -
mv beelabhmc-* flower_map
```

# setup
The pipeline is written as a Snakefile which can be executed via [Snakemake](https://snakemake.readthedocs.io). We recommend using at least version 5.18.0:
```
conda create -n snakemake -c bioconda -c conda-forge 'snakemake>=5.18.0'
```
We highly recommend you install [Snakemake via conda](https://snakemake.readthedocs.io/en/stable/getting_started/installation.html#installation-via-conda) like this so that you can use the `--use-conda` flag when calling `snakemake` to let it [automatically handle all dependencies](https://snakemake.readthedocs.io/en/stable/snakefiles/deployment.html#integrated-package-management) of the pipeline. Otherwise, you must manually install the dependencies listed in the [env files](envs).

# execution
1. Activate snakemake via `conda`:
    ```
    conda activate snakemake
    ```
2. Execute the pipeline

    Locally:
    ```
    ./run.bash &
    ```
    __or__ on an SGE cluster:
    ```
    ./run.bash --sge-cluster &
    ```

#### Executing the pipeline on your own data
You must modify [the config.yaml file](config.yml) to specify paths to your data.

### If this is your first time using Snakemake
We recommend that you run `snakemake --help` to learn about Snakemake's options. For example, to check that the pipeline will be executed correctly before you run it, you can call Snakemake with the `-n -p -r` flags. This is also a good way to familiarize yourself with the steps of the pipeline and their inputs and outputs (the latter of which are inputs to the first rule in the pipeline -- ie the `all` rule).

Note that Snakemake will not recreate output that it has already generated, unless you request it. If a job fails or is interrupted, subsequent executions of Snakemake will just pick up where it left off. This can also apply to files that *you* create and provide in place of the files it would have generated.

# files and directories
### [Snakefile](Snakefile)
A [Snakefile](https://snakemake.readthedocs.io/en/stable/) for running the entire pipeline. It uses overlapping drone imagery to create a map of the species of flowers surrounding a bee colony.

### [config.yml](config.yml)
A config file that define options and input for the pipeline. You should start by filling this out.

### [scripts/](scripts)
Various scripts used by the pipeline. See the [script README](scripts/README.md) for more information.

### [run.bash](run.bash)
An example bash script for executing the pipeline using `snakemake` and `conda`. Any arguments to this script are passed directly to `snakemake`.
