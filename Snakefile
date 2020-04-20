from snakemake.utils import min_version

##### set minimum snakemake version #####
min_version("5.8.0")

configfile: "config.yml"


def check_config(value):
    """ return true if config value exists and is true """
    return value in config and config[value]

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
        expand(config['out']+"/{sample}/classify/ortho.json", sample=config['SAMP_NAMES']) if not check_config('parallel') else
        expand(config['out']+"/{sample}/features/{image}.tsv", sample=config['SAMP_NAMES'], image=[])

rule stitch:
    """ create an orthomosaic from the individual images """
    input:
        lambda wildcards: SAMP[wildcards.sample]
    output:
        config['out']+"/{sample}/stitch/stitched.psx"
    conda: "envs/default.yml"
    shell:
        "scripts/stitch.py {input} {output}"

rule export_ortho:
    """ extract an orthomosaic image from the project file """
    input:
        rules.stitch.output
    output:
        config['out']+"/{sample}/stitch/ortho.tiff"
    conda: "envs/default.yml"
    shell:
        "scripts/export_ortho.py {input} {output}"

rule segment:
    """ segment plants from an image """
    input:
        rules.export_ortho.output
    output:
        config['out']+"/{sample}/segment/ortho.json"
    conda: "envs/default.yml"
    shell:
        "scripts/segment.py {input} {output}"

rule transform:
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
        lambda wildcards: SAMP[wildcards.sample]+"/{image}.JPG",
        rules.transform.output+"/{image}.json" if check_config('parallel') else rules.segment.output
    output:
        config['out']+"/{sample}/features/"+("{image}.tsv" if check_config('parallel') else "ortho.tsv")
    conda: "envs/default.yml"
    shell:
        "scripts/extract_features.py {input} {output}"

# rule train:
#     """ train the classifier """
#     pass

rule classify:
    """ classify each segment by its species """
    input:
        rules.extract_features.output
    output:
        config['out']+"{sample}/classify/"+("{image}.tsv" if check_config('parallel') else "ortho.tsv")
