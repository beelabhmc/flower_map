#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='Transform the coordinates of each segment in the original drone images to the orthomosaic.')
parser.add_argument(
    "project_file", help="a path to a metashape project file (w/ a psx file ending) containing an orthomosaic"
)
parser.add_argument(
    "segments", help="a path to the directory containing the json coordinates of the segmented regions in each image"
)
parser.add_argument(
    "out", help="the file in which to store the coordinates of the segmented regions in the orthomosaic"
)
parser.add_argument(
    "--images", default="", help="a path to the directory in which the original drone orthomosaic is stored; this argument must be provided if you plan to open the segment file in labelme"
)
args = parser.parse_args()
args.out += '/' if not args.out.endswith('/') else ''

import Metashape
import numpy as np
import import_labelme


def transform(chunk, camera_idx, points):
    """transform camera pixel coordinates to orthomosaic coordinates"""
    # get the width and height of every pixel in latitude and longitude units
    x = (chunk.orthomosaic.right-chunk.orthomosaic.left)/chunk.orthomosaic.width
    y = (chunk.orthomosaic.top-chunk.orthomosaic.bottom)/chunk.orthomosaic.height
    for point in points:
        # several steps are being taken here:
        # 1) the point is projected from pixel coords to the camera's coordinate system
        # 2) the new point is transformed via matrix multiplcation to geocentric coords
        # 3) the geocentric coords are projected to geographic coords (ie latitude and longitude)
        pt = chunk.crs.project(chunk.transform.matrix.mulp(chunk.cameras[camera_idx].unproject(point)))
        # finally, we convert the pt to pixel coords in the orthomosaic by looking at how far it is from the orthomosaic's top, left corner
        yield [abs((pt[0]-chunk.orthomosaic.left)/x), abs((chunk.orthomosaic.top-pt[1])/y)]


# open the metashape document
doc = Metashape.Document()
doc.open(args.project_file, read_only=True)

# find the correct chunk
for chunk in doc.chunks:
    # ie the one with the orthomosaic in it
    if chunk.orthomosaic is not None:
        break

# import the segments
# if the data is from labelme, import it using the labelme importer
segments = import_labelme.main(args.segments, True)
# prepare a dict of results, containing an array of segments for each camera
results = {camera.label:[] for camera in chunk.cameras}
# convert each segment to coords in the cameras it belongs in
for label in segments:
    segs = transform(chunk, segments[label])
    for cam in segs:
        results[cam].append((label, segs[cam]))
for camera in results:
    import_labelme.write(args.out+camera+'.json', results[camera], args.images+camera+".JPG")
