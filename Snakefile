import os
from pathlib import Path
from snakemake.utils import min_version

##### set minimum snakemake version #####
min_version("5.8.0")

configfile: "config.yml"


def check_config(value, default=False):
    """ return true if config value exists and is true """
    return config[value] if (value in config and config[value] is not None) else default

def exp_str():
    """ return the prefix str for the experimental strategy """
    return "-exp" if check_config('parallel') else ""

def read_samples():
    """Function to get names and paths from a sample file
    specified in the configuration. Input file is expected to have 2
    columns: <unique_sample_id> <data_path>. Modify
    this function as needed to provide a dictionary of sample_id keys and
    data_paths values"""
    f = open(config['sample_file'], "r")
    samp_dict = {}
    for line in f:
        words = line.strip().split("\t")
        samp_dict[words[0]] = words[1]
    return samp_dict
SAMP = read_samples()

# the user can change config['SAMP_NAMES'] here (or define it in the config
# file) to contain whichever sample names they'd like to run the pipeline on
if 'SAMP_NAMES' not in config:
    config['SAMP_NAMES'] = list(SAMP.keys())
else:
    # double check that the user isn't asking for samples they haven't provided
    user_samps = set(config['SAMP_NAMES'])
    config['SAMP_NAMES'] = list(set(SAMP.keys()).intersection(user_samps))
    if len(config['SAMP_NAMES']) != len(user_samps):
        warnings.warn("Not all of the samples requested have provided input. Proceeding with as many samples as is possible...")


rule all:
    input:
        expand(config['out']+"/{sample}/map"+exp_str()+"/ortho.tiff", sample=config['SAMP_NAMES'])

rule stitch:
    """ create an orthomosaic from the individual images """
    input:
        lambda wildcards: SAMP[wildcards.sample]
    params:
        low_qual = "--fast" if check_config('low_qual_ortho', check_config('parallel')) else ""
    output:
        config['out']+"/{sample}/stitch"+("-lowQual" if check_config('low_qual_ortho', check_config('parallel')) else "")+"/stitched.psx"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/stitch"+("-lowQual" if check_config('low_qual_ortho', check_config('parallel')) else "")+".tsv"
    shell:
        "scripts/stitch.py {params} {input} {output}"

rule export_ortho:
    """ extract an orthomosaic image from the project file """
    input:
        rules.stitch.output
    output:
        str(Path(rules.stitch.output[0]).parents[0])+"/ortho.tiff"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/export_ortho.tsv"
    shell:
        "scripts/export_ortho.py {input} {output}"

rule segment:
    """ segment plants from an image """
    input:
        rules.export_ortho.output
    output:
        config['out']+"/{sample}/segment/ortho.json"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/segment/ortho.tsv"
    shell:
        "scripts/segment.py {input} {output}"

checkpoint transform:
    """ transform the segments from the ortho to each image """
    input:
        rules.stitch.output,
        rules.segment.output
    output:
        directory(config['out']+"/{sample}/segments")
    conda: "envs/default.yml"
    shell:
        "scripts/transform.py {input} {output}"

rule extract_features:
    """ extract feature values for each segment """
    input:
        lambda wildcards: SAMP[wildcards.sample]+"/{image}.JPG" if check_config('parallel') else rules.export_ortho.output,
        rules.transform.output[0]+"/{image}.json" if check_config('parallel') else rules.segment.output
    output:
        config['out']+"/{sample}/features"+exp_str()+"/{image}.tsv"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/extract_features"+exp_str()+"/{image}.tsv"
    shell:
        "scripts/extract_features.py {input} {output}"

# rule train:
#     """ train the classifier """
#     pass

rule classify:
    """ classify each segment by its species """
    input:
        rules.extract_features.output,
        config['model'] if check_config('model') else ""
    output:
        config['out']+"/{sample}/classify"+exp_str()+"/{image}.tsv"
    conda: "envs/classify.yml"
    benchmark: config['out']+"/{sample}/benchmark/classify"+exp_str()+"/{image}.tsv"
    shell:
        "scripts/classify_test.R {input} {output}"


def classified_images(wildcards):
    """ get paths to the classified images """
    return expand(
        rules.classify.output,
        sample=wildcards.sample,
        image=glob_wildcards(
            os.path.join(
                checkpoints.transform.get(**wildcards).output[0],
                "{image}.json"
            )
        ).image
    )


rule resolve_conflicts:
    """ resolve any conflicting classifications from the experimental strategy """
    input:
        img = rules.export_ortho.output,
        labels = rules.transform.output,
        predicts = classified_images
    params:
        predicts = lambda wildcards, input: os.path.dirname(input.predicts[0])
    output:
        config['out']+"/{sample}/resolve_conflicts/ortho.tsv"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/resolve_conflicts/ortho.tsv"
    shell:
        "scripts/resolve_conflicts.py {input.img} {input.labels} {params.predicts} {output}"

rule map:
    """ overlay each segment and its predicted species back onto the orthomosaic img to create a map """
    input:
        img = rules.export_ortho.output,
        labels = rules.segment.output,
        predicts = rules.resolve_conflicts.output if check_config('parallel') else rules.classify.output[0].format(sample='{sample}', image='ortho')
    output:
        config['out']+"/{sample}/map"+exp_str()+"/{ortho}.tiff"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/map"+exp_str()+"/{ortho}.tsv"
    shell:
        "scripts/map.py {input.img} {input.labels} {output} {input.predicts}"

