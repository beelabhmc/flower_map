[![Snakemake](https://img.shields.io/badge/snakemake-≥5.18.0-brightgreen.svg?style=flat-square)](https://snakemake.bitbucket.io)
[![License](https://img.shields.io/apm/l/vim-mode.svg)](LICENSE)

# flower_map
A pipeline for generating maps of the species of flowers around a bee colony using drone imagery. The pipeline uses Agisoft Metashape to stitch the drone images together into an orthomosaic, various computer vision algorithms to segment each plant from its background, and a pre-trained random forest classifier to label each plant by its species.

# download
Execute the following commands or download the [latest release](https://github.com/beelabhmc/flower_map/releases/latest) manually.
```
git clone https://github.com/beelabhmc/flower_map.git
```

# setup
## dependencies
The pipeline is written as a Snakefile which can be executed via [Snakemake](https://snakemake.readthedocs.io). We recommend using at least version 5.20.1:
```
conda create -n snakemake -c bioconda -c conda-forge --no-channel-priority 'snakemake>=5.20.1'
```
We highly recommend you install [Snakemake via conda](https://snakemake.readthedocs.io/en/stable/getting_started/installation.html#installation-via-conda) like this so that you can use the `--use-conda` flag when calling `snakemake` to let it [automatically handle all dependencies](https://snakemake.readthedocs.io/en/stable/snakefiles/deployment.html#integrated-package-management) of the pipeline. Otherwise, you must manually install the dependencies listed in the [env files](envs).

## Agisoft Metashape
Our Snakefile assumes that there is a `metashape.lic` file containing the Metashape License in the same directory as the `run.bash` script. Without this file, the pipeline will attempt to run Metashape unlicensed, which usually fails on import. To create the file, run the following command after activating your `snakemake` conda environment:
```
metashape_LICENSE="your-25-digit-license-key-goes-here" ./run.bash -U create_license
```

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
    qsub run.bash
    ```

#### Executing the pipeline on your own data
You must modify [the config.yaml file](config.yml) to specify paths to your data. See [our wiki](https://github.com/beelabhmc/flower_map/wiki) for more information.

### If this is your first time using Snakemake
We recommend that you run `snakemake --help` to read about Snakemake's options. For example, to check that the pipeline will be executed correctly before you run it, you can call Snakemake with the `-n -p -r` flags. This is also a good way to familiarize yourself with the steps of the pipeline and their inputs and outputs (the latter of which are inputs to the first rule in the pipeline -- ie the `all` rule).

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
