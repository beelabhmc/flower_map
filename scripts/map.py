#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(description='Stitch the drone imagery together.')
parser.add_argument(
    "ortho", help="the path to the stitched orthomosaic"
)
parser.add_argument(
    "labels", help="the path to the file containing the coordinates of each segmented region"
)
parser.add_argument(
    "out", help="a map of the flowering species in the stitched orthomosaic"
)
parser.add_argument(
    "predicts", nargs="?", const=None, help="the path to the file containing the true and predicted class labels"
)
args = parser.parse_args()

import cv2 as cv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


TRANSPARENCY = 0.65


# import predictions if they've been given
if args.predicts is not None:
    predicts = pd.read_csv(args.predicts, sep="\t", header=0, index_col=False)
else:
    predicts = None

img = cv.imread(args.ortho)
# add alpha channel (ie transparency)
img = cv.cvtColor(img, cv.COLOR_RGB2RGBA)

def get_color(predicts, i, unique = False):
    if predicts is not None:
        class_label = int(predicts.iloc[i]["response"])
        return [
            col*255
            for col in plt.cm.Dark2(class_label)[:-1] + (
                predicts.iloc[i]["prob."+str(class_label)],
            )
        ]
    else:
        # light gray
        if unique:
            return plt.cm.Greys(i/unique)
        else:
            return [211,211,211,255]

# if the data is from labelme, import it using the labelme importer
if args.labels.endswith('.json'):
    import import_labelme
    labels = [np.array(label).astype(np.int32) for label in import_labelme.main(args.labels)]
    # draw each label onto the img
    for i in range(len(labels)):
        cv.drawContours(img, labels, i, get_color(predicts, i), 7)
elif args.labels.endswith('.npy'):
    markers = np.load(args.labels)
    # first, get the marker IDs (ie 0, 1, 2, ...)
    marker_ids = np.unique(markers)
    # next, ignore the marker id for the background (ie 0)
    marker_ids = marker_ids[marker_ids != 0]
    # draw each segment onto the image
    for i in range(len(marker_ids)):
        marker = marker_ids[i]
        color = get_color(predicts, i, max(marker_ids))
        # get a colored mask with which to overlay the segmented region
        overlay = np.ones(img.shape, dtype=np.float32)*color
        # also construct a regular mask containing the transparency values
        mask = np.zeros(img.shape, dtype=np.float32)
        mask[markers == marker] = (1-TRANSPARENCY,)*4
        # put the colored mask on top of the image
        img = overlay*mask + img*(1-mask)
else:
    raise Exception('label format not supported yet')

cv.imwrite(args.out, img.astype(np.uint8))
