[![Snakemake](https://img.shields.io/badge/snakemake-≥5.8.0-brightgreen.svg?style=flat-square)](https://snakemake.bitbucket.io)
[![License](https://img.shields.io/apm/l/vim-mode.svg)](LICENSE)

# flower_map
A pipeline for generating maps of the species of flowers around a bee colony from drone imagery.


# download
Execute the following commands or download the [latest release](https://github.com/beelabhmc/flower_map/releases/latest) manually.
```
wget -O- -q https://github.com/beelabhmc/flower_map/tarball/master | tar mxvzf -
mv beelabhmc-* flower_map
```

# execution
```
# install snakemake via conda (if not already installed)
conda create -c bioconda -c conda-forge -n snakemake 'snakemake>=5.8.0'

# activate the conda env
conda activate snakemake

# execute the pipeline
./run.bash
```

The pipeline is written as a Snakefile, so it must be executed via [Snakemake](https://snakemake.readthedocs.io/en/stable/). See the [`run.bash` script](run.bash) for an example. Make sure to provide required input and options in the [config file](config.yml) before executing.

# dependencies
We highly recommend you install [Snakemake via conda](https://snakemake.readthedocs.io/en/stable/getting_started/installation.html#installation-via-conda) so that you can use the `--use-conda` flag when calling `snakemake` to let it automatically handle all dependencies of the pipelines. Otherwise, you must manually install the dependencies listed in the [env files](envs).

# files and directories

### [Snakefile](Snakefile)
A [Snakefile](https://snakemake.readthedocs.io/en/stable/) for running the entire pipeline. It uses overlapping drone imagery to create a map of the species of flowers surrounding a bee colony.

### [config.yml](config.yml)
A config file that define options and input for the pipeline. You should start by filling this out.

### [scripts/](scripts)
Various scripts used by the pipeline. See the [script README](scripts/README.md) for more information.

### [run.bash](run.bash)
An example bash script for executing the pipeline using `snakemake` and `conda`.
