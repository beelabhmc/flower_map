#!/usr/bin/env python3
import sys
import argparse

parser = argparse.ArgumentParser(description='Extract the transformation matrices of each image from the project file.')
parser.add_argument(
    "project_file", help="a path to a metashape project file (w/ a psx file ending)"
)
parser.add_argument(
    "out", nargs='?', default=sys.stdout, help="the flattened transformation matrices of each image as a TSV file"
)
args = parser.parse_args()

import ntpath
import Metashape
import numpy as np
import pandas as pd


# open the metashape document
doc = Metashape.Document()
doc.open(args.project_file, read_only=True)

# find the correct chunk
for chunk in doc.chunks:
    if chunk.orthomosaic is not None:
        break

# initialize the output array of transformation matrics
# there should be one row for each camera and columns for each entry in the flattened transformation matrix
transforms = np.ones((len(chunk.cameras), 4*4))
# also retrieve the camera names
names = [None]*len(chunk.cameras)

# extract each camera
for i in range(len(chunk.cameras)):
    names[i] = ntpath.basename(chunk.cameras[i].photo.path)
    transforms[i,:] = np.asarray(chunk.cameras[i].transform)

# convert to a pandas data frame and then write to the file in tsv format
pd.DataFrame(transforms, index=names).to_csv(args.out, sep="\t", header=False)
