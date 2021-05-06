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
    "out", nargs='+', help="the path to a file (or directory) in which to write the truth data; optionally, provide another file (or directory) if you want the truth data split between training and testing sets"
)
parser.add_argument(
    "-d", "--segment-dict", help="the path to a json file containing a dictionary mapping the labels of the original segmented regions to their corresponding merged labels in the orthomosaic; this is output from watershed.py"
)
parser.add_argument(
    "-p", "--test-proportion", default=0.5, help="what proportion of the data should be used for testing? this is only relevant if the truth data is being split between training and testing (see the 'out' argument)"
)
parser.add_argument(
    "balance", default=True, help="what proportion of the data should be used for testing? this is only relevant if the truth data is being split between training and testing (see the 'out' argument)"
)
args = parser.parse_args()
if len(args.out) > 2:
    parser.error("You can provide at most two outputs.")
# but if there are two outputs, make sure the first one is a file
if len(args.out)-1:
    assert (not Path(args.out[0]).is_dir()), "If you provide two outputs, the first must be a file (for training). The second (for testing) can be either a file or a directory if you want the output split by camera."

import json
import numpy as np
import pandas as pd
import random
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
    print("______________________")
    print("Here are the features:")
    print(features)

    # now, get the true labels and add them as a column to the features df
    truth = get_truth()

    print("______________________")
    print("Here is the truth data:")
    print(truth)

    # get the segment_dict
    # but first, check that the segment_dict is provided
    if args.segment_dict is None:
        print("______________________")
        print("Here is the new features dataframe")
        features[CLASS_LABEL] = features.apply(
            lambda row: truth.loc[row.name[1]],
            axis=1
        )
        print(features)
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
    features = features.join(get_truth(add_ortho=False))

featureCopy = features.copy()
featureCopy.reset_index(inplace=True)
print("RESETTED FEATURES")
print(features)
# if the balance argument is true, then balance proportion 
# make the number of labels with
# if args.balance:
raw_0_df = features[features[CLASS_LABEL] == 0] 
raw_1_df = features[features[CLASS_LABEL] == 1]

image_label_list_0 = raw_0_df.index.values.tolist()
unique_label_list_0 = list(np.unique([tup[1] for tup in image_label_list_0]))
print(unique_label_list_0)
num_unique_labels_0 = len(unique_label_list_0)

image_label_list_1 = raw_1_df.index.values.tolist()
unique_label_list_1 = np.unique([tup[1] for tup in image_label_list_1])
num_unique_labels_1 = len(unique_label_list_1)
print("nums", num_unique_labels_0, num_unique_labels_1)
# BUG TO FIX HERE: when combining the two dfs back together, index incorrect
if num_unique_labels_0 < num_unique_labels_1:
    raw_1_df.reset_index(inplace=True)
    raw_1_df = raw_1_df.rename(columns = {'level_0':'image_id'})
    new_1_labels = random.sample(unique_label_list_1, num_unique_labels_0)
    new_1_df = raw_1_df[raw_1_df['label'].isin(new_1_labels)]
    new_1_df['label'] = new_1_df['label'].astype(str)
    new_1_df['newIndex'] = new_1_df[['image_id', 'label']].agg(' '.join, axis=1)
    del new_1_df['image_id']
    del new_1_df['label']
    new_0_df = new_0_df.rename(columns = {'newIndex':'label'})
    new_0_df = new_0_df.set_index('label')
    new_0_df = raw_0_df
elif num_unique_labels_0 > num_unique_labels_1:
    raw_0_df.reset_index(inplace=True)
    raw_0_df = raw_0_df.rename(columns = {'level_0':'image_id'})
    new_0_labels = random.sample(unique_label_list_0, num_unique_labels_1)
    new_0_df = raw_0_df[raw_0_df['label'].isin(new_0_labels)]
    new_0_df['label'] = new_0_df['label'].astype(str)
    new_0_df['newIndex'] = new_0_df[['image_id', 'label']].agg(' '.join, axis=1)
    del new_0_df['image_id']
    del new_0_df['label']
    new_0_df = new_0_df.rename(columns = {'newIndex':'label'})
    new_0_df = new_0_df.set_index('label')
    print(new_0_df)
    new_1_df = raw_1_df
    print(new_1_df)

features = new_0_df.append(new_1_df)
print("NEW FEATURES!")
print(features)




def write_dir_output(df, out, *args):
    """ write the test data to multiple files if the output is a directory """
    for cam in set(df.index.get_level_values(0)):
        df.loc[cam].to_csv(str(out)+"/"+cam+".tsv", sep="\t", *args)

def one_label_per_time(features):
    """ get one label's images per time to help readers write truth"""


# check: do we have to split the output?
if len(args.out)-1:
    # now, split the truth data among the output files
    train, test = train_test_split(
        features, test_size=args.test_proportion, stratify=features[CLASS_LABEL]
    )

    # and write to the files
    # keep only the species labels and the features
    train.to_csv(args.out[0], sep="\t", index=False)
    out_file = Path(args.out[1])
    if out_file.is_dir():
        write_dir_output(test, out_file)
    else:
        test.to_csv(args.out[1], sep="\t", index=False)
else:
    out_file = Path(args.out[0])
    if out_file.is_dir():
        write_dir_output(features, out_file)
    else:
        # write to a file without the segment IDs, keeping only the species labels
        # and the features
        features.to_csv(args.out[0], sep="\t", index=False)
