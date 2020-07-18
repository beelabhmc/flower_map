import os
import warnings
from pathlib import Path
from collections import Counter
from snakemake.utils import min_version

##### set minimum snakemake version #####
min_version("5.18.0")

configfile: "config.yml"


def check_config(value, default=False, place=config):
    """ return true if config value exists and is true """
    return place[value] if (value in place and place[value] is not None) else default

def exp_str():
    """ return the prefix str for the experimental strategy """
    return "-exp" if check_config('parallel') else ""

def read_samples(sample_file):
    """Function to get names and paths from a sample file
    specified in the configuration. Input file is expected to have 2
    columns: <unique_sample_id> <data_path>. Modify
    this function as needed to provide a dictionary of sample_id keys and
    data_paths values"""
    f = open(sample_file, "r")
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
SAMP, SAMP_EXT = read_samples(config['sample_file'])

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

def all_input():
    """
        parse the truth and training config options and determine what
        should be listed as input for the all rule
    """
    outputs = []
    # first, check: are there truth samples?
    if check_config('truth'):
        # get the truth samples
        truth_samps = list(filter(
            lambda samp: samp in config['SAMP_NAMES'],
            config['truth']
        ))
        # check: is there a trained model already?
        if check_config('model'):
            # if so, use all of the truth sets for testing only
            outputs += expand(config['out']+"/{sample}/test"+exp_str()+"/results.pdf", sample=truth_samps)
        else:
            # get the trained models
            outputs += expand(config['out']+"/{sample}/train"+exp_str()+"/model.rda", sample=truth_samps)
            # check: do we also need test results?
            test_samps = filter(
                lambda samp: not check_config('train_all', place=config['truth'][samp]),
                truth_samps
            )
            outputs += expand(config['out']+"/{sample}/test"+exp_str()+"/results.pdf", sample=test_samps)
    if not len(outputs):
        outputs += expand(config['out']+"/{sample}/map"+exp_str()+".tiff", sample=config['SAMP_NAMES'])
    return outputs



rule all:
    input: all_input()

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
    params:
        texture = "--texture-cache " + config['out']+"/{sample}/segments/texture/{image}.npy" if check_config('parallel') else config['out']+"/{sample}/segments/texture.npy"
    output:
        high = config['out']+"/{sample}/segments/high/{image}.json" if check_config('parallel') else config['out']+"/{sample}/segments/high.json",
        low = config['out']+"/{sample}/segments/low/{image}.json" if check_config('parallel') else config['out']+"/{sample}/segments/low.json"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/segments/"+("{image}" if check_config('parallel') else "ortho")+".tsv"
    shell:
        "scripts/segment.py {params} {input} {output}"

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
        segments = config['out']+"/{sample}/segments"+exp_str()+".json"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/watershed"+exp_str()+".tsv"
    shell:
        "scripts/watershed.py {input.ortho} {params.high_dir} {params.low_dir} {output.segments}"

checkpoint rev_transform:
    """ transform the segments from ortho coords to the original image coords """
    input:
        rules.stitch.output,
        rules.watershed.output.segments
    output:
        directory(config['out']+"/{sample}/rev_transforms")
    conda: "envs/default.yml"
    shell:
        "scripts/rev_transform.py {input} {output}"

rule extract_features:
    """ extract feature values for each segment """
    input:
        lambda wildcards: SAMP[wildcards.sample]+"/{image}"+SAMP_EXT[wildcards.sample][0] if check_config('parallel') else rules.export_ortho.output,
        rules.rev_transform.output[0]+"/{image}.json" if check_config('parallel') else rules.watershed.output.segments
    output:
        config['out']+"/{sample}/features"+exp_str()+"/{image}.tsv"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/extract_features"+exp_str()+"/{image}.tsv"
    shell:
        "scripts/extract_features.py {input} {output}"

def image_features(wildcards):
    """ get paths to the classified images """
    return expand(
        rules.extract_features.output[0],
        sample=wildcards.sample,
        image=glob_wildcards(
            os.path.join(
                checkpoints.rev_transform.get(**wildcards).output[0],
                "{image}.json"
            )
        ).image
    )

checkpoint create_truth_data:
    """ create training data that we can feed to the random forest """
    input:
        features = image_features,
        truth = lambda wildcards: config['truth'][wildcards.sample]['path']
    params:
        features = lambda wildcards, input: os.path.dirname(input.features[0]) if check_config('parallel') else input.features[0]
    output:
        directory(config['out']+"/{sample}/truth_data"+exp_str()) \
        if check_config('model') \
        else config['out']+"/{sample}/truth_data"+exp_str()+".tsv"
    conda: "envs/default.yml"
    shell:
        ("mkdir -p {output} && " if check_config('model') else "") + \
        "scripts/create_truth_data.py {params.features} {input.truth} {output}"

checkpoint create_split_truth_data:
    """ create training/testing data that we can feed to the random forest """
    input:
        features = image_features,
        truth = lambda wildcards: config['truth'][wildcards.sample]['path']
    params:
        features = lambda wildcards, input: os.path.dirname(input.features[0]) if check_config('parallel') else input.features[0]
    output:
        train = config['out']+"/{sample}/train"+exp_str()+"/training_data.tsv",
        test = directory(config['out']+"/{sample}/test"+exp_str()+"/testing_data")
    conda: "envs/default.yml"
    shell:
        "mkdir -p {output.test} && " + \
        "scripts/create_truth_data.py {params.features} {input.truth} {output}"

def train_input(wildcards):
    if check_config('truth') and check_config(wildcards.sample, place=config['truth']):
        if check_config('train_all', place=config['truth'][wildcards.sample]):
            return rules.create_truth_data.output
        return rules.create_split_truth_data.output.train
    else:
        raise Exception("The snakemake pipeline is incorrectly trying to create a trained model. Try moving your model out of the directory it was created in.")

rule train:
    """ train the classifier """
    input: train_input
    output:
        config['out']+"/{sample}/train"+exp_str()+"/model.rda",
        config['out']+"/{sample}/train"+exp_str()+"/variable_importance.tsv"
    conda: "envs/classify.yml"
    shell:
        "Rscript scripts/classify_train.R {input} {output}"

def classify_input(wildcards, return_int=False):
    if check_config('truth') and check_config(wildcards.sample, place=config['truth']):
        if check_config('train_all', place=config['truth'][wildcards.sample]):
            if return_int:
                return 1
            return [rules.create_truth_data.output[0]+"/{image}.tsv", rules.train.output[0]]
        if check_config('model'):
            if return_int:
                return 2
            return [rules.create_truth_data.output[0]+"/{image}.tsv", config['model']]
        else:
            if return_int:
                return 3
            return [rules.create_split_truth_data.output.test+"/{image}.tsv", rules.train.output[0]]
    else:
        if return_int:
            return 0
        if check_config('model'):
            return [rules.extract_features.output[0], config['model']]
        else:
            raise ValueError("If you don't specify any truth sets, you must provide a pre-trained model.")

rule classify:
    """ classify each segment by its species """
    input: classify_input
    output:
        config['out']+"/{sample}/classify"+exp_str()+"/{image}.tsv"
    conda: "envs/classify.yml"
    benchmark: config['out']+"/{sample}/benchmark/classify"+exp_str()+"/{image}.tsv"
    shell:
        "Rscript scripts/classify_test.R {input} {output}"

rule test:
    """ classify each test segment by its species """
    input: classify_input
    output:
        config['out']+"/{sample}/test"+exp_str()+"/classify/{image}.tsv"
    conda: "envs/classify.yml"
    benchmark: config['out']+"/{sample}/benchmark/test"+exp_str()+"/classify/{image}.tsv"
    shell:
        "Rscript scripts/classify_test.R {input} {output}"

def classify_or_test(wildcards, return_int=False):
    """ are we performing testing or just regular classification? """
    classify_rule = rules.classify
    # but check: is there test data?
    i = classify_input(wildcards, return_int=True)
    if i:
        classify_rule = rules.test
    # return tuple if return_int else return classify_rule
    return (classify_rule, i)[:return_int+1]

def classified_images(wildcards):
    """ get paths to the classified images """
    outrule, i = classify_or_test(wildcards, return_int=True)
    if i == 3:
        checkpoint_output = checkpoints.create_split_truth_data.get(**wildcards).output.test
    elif i:
        checkpoint_output = checkpoints.create_truth_data.get(**wildcards).output[0]
    else:
        checkpoint_output = checkpoints.rev_transform.get(**wildcards).output[0]
    return expand(
        outrule.output[0],
        sample=wildcards.sample,
        image=glob_wildcards(
            os.path.join(
                checkpoint_output,
                "{image}"+(".tsv" if i else ".json")
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
        config['out']+"/{sample}/results.tsv"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/resolved_conflicts.tsv"
    shell:
        "scripts/resolve_conflicts.py {input.img} {input.labels} {params.predicts} {output}"

def predictions(wildcards):
    if check_config('parallel'):
        return expand(rules.resolve_conflicts.output[0], sample=wildcards.sample)
    else:
        return expand(classify_or_test(wildcards).output[0], sample=wildcards.sample, image='ortho')

rule prc_pts:
    """ generate single point precision recall metrics """
    input:
        results = predictions
    output: config['out']+"/{sample}/test"+exp_str()+"/metrics.tsv"
    conda: "envs/default.yml"
    shell:
        "tail -n+2 {input} | cut -f 2,3,5 | scripts/metrics.py -o {output}"

rule prc_curves:
    """ generate the points for a precision recall curve """
    input:
        predicts = predictions
    output: config['out']+"/{sample}/test"+exp_str()+"/statistics.tsv"
    conda: "envs/default.yml"
    shell:
        "tail -n+2 {input} | cut -f 2,3 | scripts/statistics.py -o {output}"

rule prc:
    """ create plot containing precision recall curves """
    input:
        pts = rules.prc_pts.output,
        curves = rules.prc_curves.output
    params:
        pts = lambda _, input: ['--buckwheat_pt', input.pts],
        curves = lambda _, input: ['--buckwheat', input.curves]
    output: config['out']+"/{sample}/test"+exp_str()+"/results.pdf"
    conda: "envs/default.yml"
    shell:
        "scripts/prc.py {output} {params.pts} {params.curves}"

rule segments_map:
    """ overlay each segment back onto the orthomosaic img to create a map """
    input:
        img = rules.export_ortho.output,
        labels = rules.watershed.output.segments
    output:
        config['out']+"/{sample}/segments-map"+exp_str()+".tiff"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/segments-map"+exp_str()+".tsv"
    shell:
        "scripts/map.py -l {input.img} {input.labels} {output}"

rule map:
    """ overlay each segment and its predicted species back onto the orthomosaic img to create a map """
    input:
        img = rules.export_ortho.output,
        labels = rules.watershed.output.segments,
        predicts = predictions
    output:
        config['out']+"/{sample}/map"+exp_str()+".tiff"
    conda: "envs/default.yml"
    benchmark: config['out']+"/{sample}/benchmark/map"+exp_str()+".tsv"
    shell:
        "scripts/map.py {input.img} {input.labels} {output} {input.predicts}"

