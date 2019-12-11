from snakemake.utils import min_version

##### set minimum snakemake version #####
min_version("5.8.0")

configfile: "configs/"
