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

rule export_ortho:
    """ extract an orthomosaic image from the project file """
    input:
        config['out']+"/{sample}/{step}/stitched.psx"
    output:
        config['out']+"/{sample}/{step}/ortho.tiff"
    conda: "envs/default.yml"
    shell:
        "scripts/export_ortho.py {input} {output}"

rule segment:
    """ segment plants from an image """
    input:
        config['out']+"/{sample}/{step}/ortho.tiff"
    output:
        config['out']+"/{sample}/segment/segmented.pickle"
    conda: "envs/default.yml"
    shell:
        "scripts/segment.py {input} {output}"
