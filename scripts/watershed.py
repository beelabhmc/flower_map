#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(
    description="Run the watershed algorithm to produce segmented regions in an orthomosaic. Or run watershed with multiple overlapping segmented regions."
)
parser.add_argument(
    "ortho", help="the path to the orthomosaic image"
)
parser.add_argument(
    "high", help="the path to the file that contain the coordinates of each extracted high confidence object (or a glob path if there are multiple such files)"
)
parser.add_argument(
    "low", help="the path to the file that contain the coordinates of each extracted low confidence object (or a glob path if there are multiple such files)"
)
parser.add_argument(
    "-g", "--glob", action='store_true', help="whether to interpret the 'high' and 'low' file paths as globs that match multiple files instead of just one"
)
parser.add_argument(
    "out", help="the path to the final segmented regions produced by running the watershed algorithm"
)
# parser.add_argument(
#     "out_high", help="the path to the final segmented regions produced by running the watershed algorithm"
# )
# parser.add_argument(
#     "out_low", help="the path to the final segmented regions produced by running the watershed algorithm"
# )
args = parser.parse_args()
if not (
    (args.high.endswith('.json') or args.high.endswith('.npy')) and
    (args.low.endswith('.json') or args.low.endswith('.npy')) and
    (args.out.endswith('.json') or args.out.endswith('.npy'))
):
    parser.error('Unsupported segments input or output file type. The files must have a .json or .npy ending.')

import cv2 as cv
import numpy as np
import import_labelme
from imantics import Polygons
#from test_util import * # uncomment for testing
# import matplotlib.pyplot as plt # uncomment for testing
# plt.ion() # uncomment for testing


def import_segments(file, img_shape=cv.imread(args.ortho)[-2::-1], pts=True):
    """
        import the segments in whatever format they're in as a bool mask
        provide img_shape if you want to ignore the coordinates of segments that lie outside of the img
    """
    # if the data is from labelme, import it using the labelme importer
    if file.endswith('.json'):
        labels = Polygons(import_labelme.main(file, False, img_shape))
        if pts:
            pts = {
                tuple(np.around(labels.points[i].mean(axis=0)).astype(np.uint))[::-1] : i
                for i in range(len(labels.points))
            }
        segments = labels.mask(*img_shape).array
    elif file.endswith('.npy'):
        if pts:
            # todo: implement pts here
            pts = {}
        segments = np.load(file) != 0
    else:
        raise Exception('Unsupported input file format.')
    return (pts, segments) if pts else segments

def load_segments(high, low, high_all=None, low_all=None, img_shape=cv.imread(args.ortho)[:2]):
    """ load the segments and merge them with a cumulative OR of the segments """
    # first, load the segments as boolean masks
    pts, high_segs = import_segments(high, img_shape[::-1])
    low_segs = import_segments(low, img_shape[::-1], False)
    # create the high and low cumulative arrays if they don't exist yet
    if high_all is None:
        high_all = np.zeros(img_shape, dtype=bool)
    if low_all is None:
        low_all = np.zeros(img_shape, dtype=bool)
    # now merge the segments with the cumulative high and low masks
    return pts, np.logical_or(high_all, high_segs), np.logical_or(low_all, low_segs)


print('loading orthomosaic')
img = cv.imread(args.ortho)

print('loading segments')
high, low = None, None
pts = {'ortho':None}
for cam in pts:
    pts[cam], high, low = load_segments(args.high, args.low, high, low, img.shape[:2])
# convert to uint8
high, low = high.astype(np.uint8), low.astype(np.uint8)

# Finding unknown region
print('identifying unknown regions (those not classified as either foreground or background)')
# subtract low (1st argument) from high (2nd argument) since high confidence
# regions are contained within low confidence ones
unknown = cv.subtract(low, high)

# Marker labelling
print('marking connected components')
ret, markers = cv.connectedComponents(high)
# Add one to all labels so that sure background is not 0, but 1
markers = markers+1
# Now, mark the region of unknown with zero
markers[unknown==255] = 0

print('running the watershed algorithm')
markers = cv.watershed(img,markers)
# clean up the indices
# merge background with old background
markers[markers == -1] = 1
markers -= 1

# data structure for mapping orthomosaic segments to drone image segments:
# list:
#   key: orthomosaic segment ID
#   value: a set of tuples: drone image segment ID
#
# algorithm to construct this data structure:
# 1) keep a running dictionary mapping an arbitrary point in a drone image segment to its tuple
# 2) after you've collected all of the points, go through each ortho connected component and
#   1) isolate the points that are contained within it
#   2) add their tuples to the dictionary set
#   3) delete the points that you added (from the pts dictionary)
# 3) raise an error if there are any points left
ortho_to_drone = [set() for i in range(ret-1)]
for i in range(1, ret):
    for cam in pts:
        for pt in list(pts[cam].keys()):
            if markers[pt] == i:
                ortho_to_drone[i-1].add((cam, pts[cam][pt]))
                del pts[cam][pt]

# should we save the segments as a mask or as bounding boxes?
if args.out.name.endswith('.npy'):
    np.save(args.out.name, markers)
elif args.out.name.endswith('.json'):
    # import extra required modules
    from imantics import Mask
    import import_labelme
    segments = [
        (int(i), Mask(markers == i).polygons().points[0].tolist())
        for i in filter(lambda x: x, np.unique(markers))
    ]
    import_labelme.write(args.out.name, segments, args.image)
else:
    sys.exit("Unsupported output file format.")
