#!/usr/bin/env python3
import sys
import argparse

parser = argparse.ArgumentParser(description='Merge the segmented, classified plants from each overlapping image together.')
parser.add_argument(
    "ortho", help="the path to the orthomosaic"
)
parser.add_argument(
    "segments", help="the path to a directory containing (for each image in the orthomosaic) the coordinates of each segmented region"
)
parser.add_argument(
    "predicts", help="the path to a directory containing tsv files (for each image in the orthomosaic) with the species class of each segmented region"
)
parser.add_argument(
    "--no-labels", action='store_true', help="whether to include the labels of each segment in the output"
)
parser.add_argument(
    "out", help="the classes of each segmented region within the orthomosaic"
)
args = parser.parse_args()
args.segments += '/' if not args.segments.endswith('/') else ''
args.predicts += '/' if not args.predicts.endswith('/') else ''

import os
import numpy as np
import pandas as pd
import import_labelme
from PIL import Image
# from matplotlib import pyplot as plt


THRESHOLD = 0.5
Image.MAX_IMAGE_PIXELS = None # so that PIL doesn't complain when we open large files


def shoelace(coords):
    """ get the area of a polygon, represented as a list of x-y coordinates """
    coords = np.array(coords)
    x, y = coords[:,0], coords[:,1]
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def resolve(segments):
    """ given the predicts of a segment from multiple files (as a pandas Series), return a new class (as a pandas Series) """
    # strategy: weight each probability by the relative size of its area
    # first calculate the relative size of each segment
    segments['area'] = segments['area']/sum(segments['area'])
    segments['prob.1'] = segments['prob.1']*segments['area']
    # first, check: is this testing data? if so, we want to preserve the truth
    if 'truth' in segments:
        return pd.Series([segments['truth'][0], sum(segments['prob.1'])], index=['truth', 'prob.1'])
    else:
        return pd.Series([sum(segments['prob.1'])], index=['prob.1'])

def img_size(ortho=args.ortho):
    # first, load the image as an array, then get its shape
    print('loading orthomosaic')
    # note that this step is extremely memory inefficient!
    # it loads the entire image into memory just so that we can get the image size
    # TODO: improve memory usage here, perhaps by getting the image size from the segments.json file (in the imageData tag) or by using a different library that can determine image size without loading the image into memory
    return np.asarray(Image.open(args.ortho)).shape[-2::-1]
img_shape = img_size()

# next, load the segments coords
print('loading segments')
# first, get a list of the segment files, sorted by their names
# TODO: also support .npy masks, instead of just JSON segments
segments_fnames = sorted([f for f in os.listdir(args.segments) if f.endswith('.json')])
# and then import them using labelme and convert each set of coords to an area
segments = {
    segment[:-len('.json')]: {
        label: shoelace(coords)
        for label, coords in import_labelme.main(args.segments+segment, True, img_shape).items()
    }
    for segment in segments_fnames
}
segments_complete = {
    segment[:-len('.json')]: {
        label: shoelace(coords)
        for label, coords in import_labelme.main(args.segments+segment, True).items()
    }
    for segment in segments_fnames
}
# lastly, flatten the segments to a pandas df multi-indexed by cam and label
areas = pd.DataFrame.from_dict({
    (cam, seg): [segments[cam][seg]]
    for cam in segments for seg in segments[cam]
}).T
areas_complete = pd.DataFrame.from_dict({
    (cam, seg): [segments_complete[cam][seg]]
    for cam in segments_complete
    for seg in segments_complete[cam]
}).T
# we created two different dataframes
# the areas_complete dataframe contains the sizes of each segment in the orthomosaic
# while the areas dataframe contains the sizes within each image
# so now we divide the two to get the fractional area of each segment in each image
areas = areas/areas_complete
areas.columns = ['area']

# also load the predicts
print('loading classification predictions')
# first, get a list of the classification files, sorted by their names
predicts = sorted([f for f in os.listdir(args.predicts) if f.endswith('.tsv')])
# check that there are an equal number of segments and predicts
assert len(segments) >= len(predicts), "There are less camera files in the segments dir than in the predicts dir."
# import them as a single large, multi-indexed pandas dataframe
predicts = pd.concat(
    {
        predict[:-len('.tsv')] : pd.read_csv(args.predicts+predict, sep="\t")
        for predict in predicts
    }
)
# check that the number of segments is kosher before adding the areas
assert len(predicts) <= len(areas), "There are less segments among all of the files than there are classification predictions."
# add the areas of each segment as a column in the predicts df
predicts = predicts.join(areas)
# the dataframe is multi-indexed by camera and label
predicts.index.names = ['camera', 'label']

# now, we can finally group the segments by their label and assign them a new class
print('resolving conflicts')
# get the truth and probs.1 columns
results = predicts.groupby('label').apply(resolve)
# get the prob.0 column and add it before the prob.1 column
results.insert(list(results.columns).index('prob.1'), 'prob.0', (1 - results['prob.1']))
# add the response column back too
results['response'] = (results['prob.1'] >= THRESHOLD).apply(int)

# last step: write the results to the outfile
print('saving results')
# but first, reorder the columns
results.to_csv(args.out, sep="\t", index=(not args.no_labels))
