#!/usr/bin/env python3
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Run the watershed algorithm to produce segmented regions in an orthomosaic. Or run watershed with multiple overlapping segmented regions."
)
parser.add_argument(
    "ortho", help="the path to the orthomosaic image"
)
parser.add_argument(
    "high", type=Path, help="the path to the file that contain the coordinates of each extracted high confidence object (or a directory if there are multiple such files)"
)
parser.add_argument(
    "low", type=Path, help="the path to the file that contain the coordinates of each extracted low confidence object (or a directory if there are multiple such files)"
)
parser.add_argument(
    "-m", "--map", default=None, help="a json file in which to store a dictionary mapping the labels of the original segmented regions to their corresponding merged labels in the orthomosaic; the original segments are labeled by their file name"
)
parser.add_argument(
    "--high-out", default=None, help="a file in which to write the new, merged high segments; default is not to do so"
)
parser.add_argument(
    "--low-out", default=None, help="a file in which to write the new, merged low segments; default is not to do so"
)
parser.add_argument(
    "out", help="the path to the final segmented regions produced by running the watershed algorithm"
)
args = parser.parse_args()
# validate the input
if args.high.is_dir() ^ args.low.is_dir():
    parser.error('Either the high and low args must both be directories, or they must both be files. One cannot be a file while the other is a directory.')
if args.high.is_dir():
    args.high = [f for f in sorted(args.high.iterdir()) if f.is_file() and f.suffix == '.json']
    args.low = [f for f in sorted(args.low.iterdir()) if f.is_file() and f.suffix == '.json']
else:
    args.high = [args.high] if args.high.suffix == '.json' else []
    args.low = [args.low] if args.low.suffix == '.json' else []
if not (len(args.high) == len(args.low) and len(args.high) and args.out.endswith('.json')):
    # TODO: support .npy files so that this error message becomes correct
    parser.error('Unsupported segments input (high and low args) or output (out arg) file type. The files must have a .json ending.')

import json
import cv2 as cv
import numpy as np
import scipy.ndimage
import import_labelme
from imantics import Polygons

# uncomment this stuff for testing
from test_util import *
import matplotlib.pyplot as plt
plt.ion()


def import_segments(file, img_shape=cv.imread(args.ortho)[-2::-1], pts=True):
    """
        import the segments in whatever format they're in as a bool mask
        provide img_shape if you want to ignore the coordinates of segments that lie outside of the img
    """
    # if the data is from labelme, import it using the labelme importer
    if file.endswith('.json'):
        labels = import_labelme.main(file, True, img_shape)
        label_keys = sorted(labels.keys())
        # make sure the segments are in sorted order, according to the keys
        labels = Polygons([labels[i] for i in label_keys])
        if pts:
            pts = {
                label_keys[i] : tuple(np.around(labels.points[i].mean(axis=0)).astype(np.uint))[::-1]
                for i in range(len(labels.points))
            }
        segments = labels.mask(*img_shape).array
    elif file.endswith('.npy'):
        segments = np.load(file) != 0
        if pts:
            # todo: implement pts here
            pts = {}
    else:
        raise Exception('Unsupported input file format.')
    return (pts, segments) if type(pts) is dict else segments

def load_segments(high, low, high_all=None, low_all=None, img_shape=cv.imread(args.ortho)[:2]):
    """ load the segments and merge them with a cumulative OR of the segments """
    # first, load the segments as boolean masks
    pts, high_segs = import_segments(high, img_shape[::-1])
    low_segs = import_segments(low, img_shape[::-1], False)
    # create the high and low cumulative arrays if they don't exist yet
    if high_all is None:
        high_all = np.zeros(img_shape, dtype=np.uint8)
    if low_all is None:
        low_all = np.zeros(img_shape, dtype=np.uint8)
    # now merge the segments with the cumulative high and low masks
    return pts, np.add(high_all, high_segs), np.add(low_all, low_segs)

def largest_polygon(polygons):
    """ get the largest polygon among the polygons """
    # we should probably use a complicated formula to do this
    # but for now, it probably suffices to notice that the last one is usually
    # the largest
    return polygons.points[-1]

def export_results(ret, markers, out):
    """ write the resulting mask to a file """
    # should we save the segments as a mask or as bounding boxes?
    if out.endswith('.npy'):
        np.save(out, markers)
    elif out.endswith('.json'):
        # import extra required modules
        from imantics import Mask
        import import_labelme
        segments = [
            (int(i), largest_polygon(Mask(markers == i).polygons()).tolist())
            for i in (range(1, ret) if ret is not None else np.unique(markers).astype(int))
        ]
        import_labelme.write(out, segments, args.ortho)
    else:
        raise Exception("Unsupported output file format.")


print('loading orthomosaic')
img = cv.imread(args.ortho)

print('loading segments')
high, low = None, None
pts = {cam.stem:None for cam in args.high}
# load each segment and add its values to the values we already have
for high_file, low_file in zip(args.high, args.low):
    pts[high_file.stem], high, low = load_segments(str(high_file), str(low_file), high, low, img.shape[:2])
    # convert the merged high and low matrices into the appropriate datatypes
high = high.astype(np.float32)
low = np.uint8(low != 0)

print('processing segments')
# the high-confidence segments that we have right now are arrays of integers
# high integers represent pixels that we are highly confident contain plants
# we use the following algorithm to convert this array to a boolean mask:
# 1) first, extract the connected components of the largest possible segments
high_ret, high_mask = cv.connectedComponents(np.uint8(high != 0))
# 2) normalize the values within each segment by their mean
for seg in range(1, high_ret):
    high[high_mask == seg] /= np.mean(high[high_mask == seg])
# 3) threshold the high confidence regions to convert them to a bool mask
high = np.uint8(high >= 1)

# write to temporary output files, if desired
if args.high_out is not None:
    export_results(*cv.connectedComponents(high), args.high_out)
if args.low_out is not None:
    export_results(*cv.connectedComponents(low), args.low_out)

# Finding unknown region
print('identifying unknown regions (those not classified as either foreground or background)')
# subtract low (1st argument) from high (2nd argument) since high confidence
# regions are contained within low confidence ones
unknown = cv.subtract(low, high)

# Marker labeling
print('marking connected components')
ret, markers = cv.connectedComponents(high)

# Add one to all labels so that sure background is not 0, but 1
markers = markers+1
# Now, mark the region of unknown with zero
markers[unknown==1] = 0

print('running the watershed algorithm')
markers = cv.watershed(img,markers)
# clean up the indices
# merge background with old background
markers[markers == -1] = 1
markers -= 1

if args.map is not None:
    # a data structure for mapping drone image segments to orthomosaic segments
    # dictionary:
    #   key: a camera name
    #   value:
    #       another dictionary:
    #           key: the drone image segment label
    #           value: the orthomosaic segment id
    #
    # algorithm to construct this data structure:
    # 1) keep a running dictionary mapping a drone image segment to an arbitrary
    #    point in that segment (ex: its centroid)
    # 2) after you've collected all of the points, go through each point and find
    #    the id of the orthomosaic segment it belongs in
    # 3) replace the point with the newfound id
    for cam in pts:
        for label in pts[cam]:
            pts[cam][label] = str(markers[pts[cam][label]])

print('writing to desired output files')
export_results(ret, markers, args.out)

# also create the map file if the user requested it
if args.map is not None:
    json.dump(pts, open(args.map, 'w'))
