import os
from pathlib import Path
from collections import Counter
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
    samp_exts = {}
    for line in f:
        words = line.strip('\n').split("\t")
        samp_dict[words[0]] = str(Path(words[1]))
        images = [image for image in Path(words[1]).iterdir() if image.is_file()]
        if len(words) != 3:
            words.append(Counter([image.suffix for image in images]).most_common(1)[0][0])
        images = [
            str(image) for image in images if image.suffix == words[2]
        ]
        samp_exts[words[0]] = (words[2], images)
    return samp_dict, samp_exts
SAMP, SAMP_EXT = read_samples()

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
        expand(config['out']+"/{sample}/map"+exp_str()+".tiff", sample=config['SAMP_NAMES'])

rule stitch:
    """ create an orthomosaic from the individual images """
    input:
        lambda wildcards: SAMP[wildcards.sample]
    params:
        low_qual = "--fast" if check_config('low_qual_ortho', check_config('parallel')) else "",
        ext = lambda wildcards: "--ext '"+SAMP_EXT[wildcards.sample][0]+"'"
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
    """ segment plants from an image into high and low confidence regions"""
    input:
        lambda wildcards: SAMP[wildcards.sample]+"/"+wildcards.image+SAMP_EXT[wildcards.sample][0] if check_config('parallel') else rules.export_ortho.output
    output:
        high = config['out']+"/{sample}/segments/high/{image}.json" if check_config('parallel') else config['out']+"/{sample}/segments/high.json",
        low = config['out']+"/{sample}/segments/low/{image}.json" if check_config('parallel') else config['out']+"/{sample}/segments/low.json"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/segments/"+("{image}" if check_config('parallel') else "ortho")+".tsv"
    shell:
        "scripts/segment.py {input} {output}"

rule transform:
    """ transform the segments from the ortho to each image """
    input:
        rules.stitch.output,
        lambda wildcards: rules.segment.output.high if wildcards.confidence == 'high' else rules.segment.output.low
    output:
        config['out']+"/{sample}/transforms/{confidence}/{image}.json"
    wildcard_constraints:
        confidence="(high|low)"
    conda: "envs/default.yml"
    shell:
        "scripts/transform.py {input} {output}"


def transformed_segments(wildcards, confidence='high'):
    """ get paths to the transformed segments """
    # note that the image names must be trimmed of their extension
    return expand(
        rules.transform.output[0],
        sample=wildcards.sample,
        confidence=confidence,
        image=list(
            map(
                lambda i: Path(i).stem,
                SAMP_EXT[wildcards.sample][1]
            )
        )
    ) if check_config('parallel') else (
        rules.segment.output.high
        if confidence == 'high' else rules.segment.output.low
    )


rule watershed:
    """
        use high and low confidence regions to identify separate plants and
        merge segments from drone images if running the experimental strategy
    """
    input:
        ortho = rules.export_ortho.output,
        high = lambda wildcards: transformed_segments(wildcards, 'high'),
        low = lambda wildcards: transformed_segments(wildcards, 'low')
    params:
        high_dir = lambda wildcards, input: Path(input.high[0]).parents[0] if check_config('parallel') else input.high,
        low_dir = lambda wildcards, input: Path(input.low[0]).parents[0] if check_config('parallel') else input.low
    output:
        config['out']+"/{sample}/segments"+exp_str()+".json"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/watershed"+exp_str()+".tsv"
    shell:
        "scripts/watershed.py {input.ortho} {params.high_dir} {params.low_dir} {output}"

checkpoint rev_transform:
    """ transform the segments from ortho coords to the original image coords """
    input:
        rules.stitch.output,
        rules.watershed.output
    output:
        directory(config['out']+"/{sample}/rev_transforms")
    conda: "envs/default.yml"
    shell:
        "scripts/rev_transform.py {input} {output}"

rule extract_features:
    """ extract feature values for each segment """
    input:
        lambda wildcards: SAMP[wildcards.sample]+"/{image}.JPG" if check_config('parallel') else rules.export_ortho.output,
        rules.rev_transform.output[0]+"/{image}.json" if check_config('parallel') else rules.watershed.output
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
                checkpoints.rev_transform.get(**wildcards).output[0],
                "{image}.json"
            )
        ).image
    )


rule resolve_conflicts:
    """ resolve any conflicting classifications from the experimental strategy """
    input:
        img = rules.export_ortho.output,
        labels = rules.rev_transform.output,
        predicts = classified_images
    params:
        predicts = lambda wildcards, input: os.path.dirname(input.predicts[0])
    output:
        config['out']+"/{sample}/resolved_conflicts.tsv"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/resolved_conflicts.tsv"
    shell:
        "scripts/resolve_conflicts.py {input.img} {input.labels} {params.predicts} {output}"

rule map:
    """ overlay each segment and its predicted species back onto the orthomosaic img to create a map """
    input:
        img = rules.export_ortho.output,
        labels = rules.watershed.output,
        predicts = rules.resolve_conflicts.output if check_config('parallel') else rules.classify.output[0].format(sample='{sample}', image='ortho')
    output:
        config['out']+"/{sample}/map"+exp_str()+".tiff"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/map"+exp_str()+".tsv"
    shell:
        "scripts/map.py {input.img} {input.labels} {output} {input.predicts}"

