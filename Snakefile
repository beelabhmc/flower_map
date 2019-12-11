from snakemake.utils import min_version

##### set minimum snakemake version #####
min_version("5.8.0")

configfile: "config.yml"


rule all:
    input: config['out']+"/{sample}/stitch/stitched.psx"

rule stitch:
    """ create an orthomosaic from the individual images """
    input:
        lambda wildcards: config['data'][wildcards.sample]['path']
    output:
        config['out']+"/{sample}/stitch/stitched.psx"
    conda: "envs/default.yml"
    shell:
        "scripts/stitch.py {input} {output}"
