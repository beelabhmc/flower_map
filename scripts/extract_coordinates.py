#!/usr/bin/env python3
import sys
import argparse

parser = argparse.ArgumentParser(description='Extract the coordinates of points in the orthomosaic.')
parser.add_argument(
    "orthomosaic",
    help="a path to the orthomosaic"
)
parser.add_argument(
    "--points", default=None, help=
    """
        a space-separated list of comma-separated x/y coordinate pairs that
        should be converted to geographic coordinates (ex: \"1,3 4,6\");
        defaults to the (left, top) and (right, bottom) corners of the orthomosaic
        OR
        the path to a json segments file, in which case the center of each segment will be used as the points
    """
)
# parser.add_argument(
#     "--only", action='store_true', help="whether to only provide the coordinates of segments whose labels have a 't' suffix"
# )
parser.add_argument(
    "out", nargs='?', type=argparse.FileType('w', encoding='UTF-8'), default=sys.stdout,
    help="the path to a tsv file in which to store the coordinates of each extracted point (default: stdout)"
)
args = parser.parse_args()

import Metashape
from pathlib import Path


doc = Metashape.Document()
doc.open(args.orthomosaic, read_only=True)

for chunk in doc.chunks:
    if chunk.orthomosaic is not None:
        break


# get the width and height of the orthomosaic in latitute and longitude units
WIDTH = chunk.orthomosaic.right-chunk.orthomosaic.left
HEIGHT = chunk.orthomosaic.top-chunk.orthomosaic.bottom
def coord_pt(chunk, point):
    """transform orthomosaic pixel coordinates to geographic coordinates"""
    # get the converted geographic coordinates
    return [
        chunk.orthomosaic.top-(point[1]/chunk.orthomosaic.height)*HEIGHT,
        chunk.orthomosaic.left+(point[0]/chunk.orthomosaic.width)*WIDTH
    ]

def import_segments(file):
    """
        import the segments in whatever format they're in and get their centroids
    """
    img_shape = (WIDTH, HEIGHT)
    # if the data is from labelme, import it using the labelme importer
    if file.endswith('.json'):
        labels = import_labelme.main(file, True, img_shape)
        label_keys = sorted(labels.keys())
        # make sure the segments are in sorted order, according to the keys
        labels = Polygons([labels[i] for i in label_keys])
        pts = {
            label_keys[i] : tuple(np.around(labels.points[i].mean(axis=0)).astype(np.uint))[::-1]
            for i in range(len(labels.points))
        }
    elif file.endswith('.npy'):
        segments = np.load(file) != 0
        # todo: implement pts here
        pts = {}
    else:
        raise Exception('Unsupported input file format.')
    return pts


print("Points\tCoordinates", file=args.out)
if args.points is None:
    print("0,0\t{0},{1}".format(chunk.orthomosaic.top, chunk.orthomosaic.left), file=args.out)
    print("{0},{1}\t{2},{3}".format(chunk.orthomosaic.width, chunk.orthomosaic.height, chunk.orthomosaic.bottom, chunk.orthomosaic.right), file=args.out)
else:
    if Path(args.points).is_file():
        args.points = import_segments(args.points)
    else:
        args.points = [
            tuple(float(i) for i in pt.split(','))
            for pt in args.points.split(' ')
        ]
    for pt in args.points:
        print("{0}\t{1}".format(pt, coord_pt(chunk, pt)), file=args.out)
