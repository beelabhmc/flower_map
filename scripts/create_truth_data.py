#!/usr/bin/env python3
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Create data that can be used to train a random forest classifier implemented by ranger."
)
parser.add_argument(
    "features", type=Path, help="the path to a file containing tsv files (for each image in the orthomosaic) with the features of each segmented region (or the path to a directory if there are many such files)"
)
parser.add_argument(
    "truth", help="the path to a tsv file containing true class labels for each segmented region; the tsv must have no header and two columns: 1) the segment ID and 2) the class label"
)
parser.add_argument(
    "out", nargs='+', help="the path to a file (or directory) in which to write the truth data; optionally, provide a file and a directory if you want the truth data split between training and testing sets"
)
parser.add_argument(
    "-d", "--segment-dict", help="the path to a json file containing a dictionary mapping the labels of the original segmented regions to their corresponding merged labels in the orthomosaic; this is output from watershed.py"
)
parser.add_argument(
    "-p", "--test-proportion", default=0.5, help="what proportion of the data should be used for testing? this is only relevant if the truth data is being split between training and testing (see the 'out' argument)"
)
args = parser.parse_args()
if len(args.out) > 2:
    parser.error("You can provide at most two outputs.")
if len(args.out)-1:
    assert (not Path(args.out[0]).is_dir() and Path(args.out[1]).is_dir()), "If you provide two outputs, the first must be a file (for training) and the second a directory (for testing)"

import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


CLASS_LABEL = 'species_label'

def get_features(fname):
    """ get a features table """
    return pd.read_csv(fname, sep="\t", index_col='label')

def get_truth(add_ortho=True):
    """ get the true labels """
    index_col = 'ortho_label' if add_ortho else 'label'
    return pd.read_csv(
        args.truth, sep="\t", header=None,
        names=[index_col, CLASS_LABEL], index_col=index_col
    )

# get the features files
# check: are we running the experimental strategy or the default one?
if args.features.is_dir():

    # get the features
    features = {
        f.stem: str(f)
        for f in args.features.iterdir()
        if f.suffix == '.tsv'
    }
    features = pd.concat(
        {
            cam: get_features(features[cam])
            for cam in features
        }
    )

    # now, get the true labels and add them as a column to the features df
    truth = get_truth()

    # get the segment_dict
    # but first, check that the segment_dict is provided
    if args.segment_dict is None:
        features[CLASS_LABEL] = features.apply(
            lambda row: truth.loc[row.name[1]],
            axis=1
        )
    else:
        with open(args.segment_dict) as json_file:
            # a data structure for mapping drone image segments to orthomosaic segments
            # dictionary:
            #   key: a camera name
            #   value:
            #       another dictionary:
            #           key: the drone image segment label
            #           value: the orthomosaic segment id
            segment_dict = json.load(json_file)
        features[CLASS_LABEL] = features.apply(
            lambda row: truth.loc[segment_dict[row.name[0]][str(int(row.name[1]))]],
            axis=1
        )

else:

    # get the features
    features = get_features(str(args.features))

    # get the true labels and add them as a column to the features df
    features = features.merge(get_truth(add_ortho=False))

# check: do we have to split the output?
if len(args.out)-1:
    # now, split the truth data among the output files
    train, test = train_test_split(
        features, test_size=args.test_proportion, stratify=features[CLASS_LABEL]
    )
    # and write to the files
    # keep only the species labels and the features
    train.to_csv(args.out[0], sep="\t", index=False)
    # and now write the test data to separate files
    for cam in set(test.index.get_level_values(0)):
        test.loc[cam].to_csv(str(Path(args.out[1]))+"/"+cam+".tsv", sep="\t")
else:
    if Path(args.out[0]).is_dir():
        # write the test data to separate files
        for cam in set(features.index.get_level_values(0)):
            features.loc[cam].to_csv(str(Path(args.out[0]))+"/"+cam+".tsv", sep="\t")
    else:
        # write to a file without the segment IDs, keeping only the species labels
        # and the features
        features.to_csv(args.out[0], sep="\t", index=False)
