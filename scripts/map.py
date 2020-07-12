#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(description='Map the segments (and optionally their predicted class labels) back onto an image.')
parser.add_argument(
    "img", help="the path to the image upon which to create the map"
)
parser.add_argument(
    "segments", help="the path to the file containing the coordinates of each segmented region"
)
parser.add_argument(
    "out", help="a map of the flowering species in the image"
)
parser.add_argument(
    "predicts", nargs="?", const=None, help="the path to the file containing the true and predicted class labels"
)
parser.add_argument(
    "-s", "--spectrum", action='store_true', help=
    """
        if 'predicts' is provided, show predictions on an opacity spectrum where
        opaque segments are those we are more confident about
    """
)
parser.add_argument(
    "-u", "--unique", action='store_true', help="if segments is an npy file, make every segment a different shade of grey"
)
parser.add_argument(
    "-l", "--label", action='store_true', help="label each segment in the map"
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
    if 'label' in predicts.columns:
        predicts = pd.read_csv(args.predicts, sep="\t", header=0, index_col='label')
else:
    predicts = None

img = cv.imread(args.img)
# add alpha channel (ie transparency)
img = cv.cvtColor(img, cv.COLOR_RGB2RGBA)

def handle_label(i):
    """ return the row corresponding with the label"""
    if predicts.index.name == 'label':
        return predicts.loc[i]
    else:
        return predicts.iloc[i]

def get_color(predicts, i, unique = False):
    if predicts is not None and i in predicts.index:
        class_label = int(handle_label(i)["response"])
        return [
            col*255
            for col in plt.cm.Dark2(class_label)[:-1] + (
                0.5*(handle_label(i)["prob."+str(class_label)]+1)
                if args.spectrum else 1.0,
            )
        ]
    else:
        # light gray
        if unique:
            return plt.cm.Greys(i/unique*100)
        else:
            return [211,211,211,255]

def top_right_corner(points, reverse=False):
    """ retrieve the top, right (or bottom, left) point from a list of points """
    # get the topmost and rightmost coordinates
    if reverse:
        top = np.min(points[:,0])
        right = np.max(points[:,1])
    else:
        top = np.max(points[:,0])
        right = np.min(points[:,1])
    # see https://codereview.stackexchange.com/a/28210
    deltas = points - (top, right)
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return tuple(points[np.argmin(dist_2)])

# if the data is from labelme, import it using the labelme importer
if args.segments.endswith('.json'):
    import import_labelme
    if predicts is not None and predicts.index.name == 'label':
        labels = import_labelme.main(args.segments, True, img.shape[-2::-1])
        label_keys = sorted(labels.keys())
        # make sure the segments are in sorted order, according to the keys
        labels = [np.array(labels[i]).astype(np.int32) for i in label_keys]
        # draw each label onto the img
        for i in range(len(labels)):
            cv.drawContours(img, labels, i, get_color(predicts, label_keys[i]), 7)
            if args.label:
                # first, get the top, right corner of the polygon
                # and use it as the bottom left, corner of the text
                bottom_left = top_right_corner(labels[i])
                cv.putText(img, str(label_keys[i]), bottom_left, cv.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 6, cv.LINE_AA)
    else:
        labels = [np.array(segment).astype(np.int32) for segment in import_labelme.main(args.segments, False, img.shape[-2::-1])]
        # draw each label onto the img
        for i in range(len(labels)):
            cv.drawContours(img, labels, i, get_color(predicts, i), 7)
            if args.label:
                # first, get the top, right corner of the polygon
                # and use it as the bottom left, corner of the text
                bottom_left = top_right_corner(labels[i])
                cv.putText(img, str(i), bottom_left, cv.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 6, cv.LINE_AA)
elif args.segments.endswith('.npy'):
    markers = np.load(args.segments)
    assert markers.shape == img.shape[:-1], "The provided img has size "+str(markers.shape)+", while the coordinate mask has size "+str(img.shape[:-1])
    # first, get the marker IDs (ie 0, 1, 2, ...)
    marker_ids = np.unique(markers)
    # next, ignore the marker id for the background (ie 0)
    marker_ids = marker_ids[marker_ids != 0]
    # draw each segment onto the image
    for i in range(len(marker_ids)):
        marker = marker_ids[i]
        color = get_color(predicts, i, max(marker_ids) if args.unique else False)
        # get a colored mask with which to overlay the segmented region
        overlay = np.ones(img.shape, dtype=np.float32)*color
        # also construct a regular mask containing the transparency values
        mask = np.zeros(img.shape, dtype=np.float32)
        mask[markers == marker] = (1-TRANSPARENCY,)*4
        # put the colored mask on top of the image
        img = overlay*mask + img*(1-mask)
        if args.label:
            # first, get the top, right corner of the mask
            # and use it as the bottom left, corner of the text
            bottom_left = top_right_corner(np.argwhere(markers == marker), True)
            cv.putText(img, str(marker), bottom_left[::-1], cv.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 6, cv.LINE_AA)
else:
    raise Exception('label format not supported yet')

cv.imwrite(args.out, img.astype(np.uint8))
