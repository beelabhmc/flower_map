#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='Transform the coordinates of each segment in the original drone images to the orthomosaic.')
parser.add_argument(
    "project_file", help="a path to a metashape project file (w/ a psx file ending) containing an orthomosaic"
)
parser.add_argument(
    "segments", help="a path to a file containing the json coordinates of the segmented regions in a drone image"
)
parser.add_argument(
    "out", help="the json file in which to store the coordinates of the segmented regions in the orthomosaic"
)
parser.add_argument(
    "--camera", default=None, help="the file name of the original drone image; required only if the segments file is not named the same as the original drone image"
)
parser.add_argument(
    "--image", default="", help="a path to the original drone; this argument must be provided if you plan to open the out file in labelme"
)
args = parser.parse_args()
args.camera = Path(args.segments if args.camera is None else args.camera).stem

import logging
import Metashape
import numpy as np
import import_labelme
import time


# count skipped points to see how much of a problem it is
skipped = 0
def transform(chunk, camera, points):
    """transform camera pixel coordinates to orthomosaic coordinates"""
    global skipped
    # get the width and height of every pixel in latitude and longitude units
    x = (chunk.orthomosaic.right-chunk.orthomosaic.left)/chunk.orthomosaic.width
    y = (chunk.orthomosaic.top-chunk.orthomosaic.bottom)/chunk.orthomosaic.height
    for point in points:
        # several steps are being taken here:
        # 1) the point is projected from pixel coords to the camera's coordinate system
        # 2) the pickPoint() method is used to transform the point to the chunk coord system using the camera's "vector intersection with the (orthomosaic) surface"
        #    (see https://www.agisoft.com/forum/index.php?topic=10513.msg47741#msg47741)
        # 3) if the new point exists, it is transformed via matrix multiplcation to geocentric coords
        # 4) the geocentric coords are projected to geographic coords (ie latitude and longitude)
        pt = chunk.model.pickPoint(camera.center, camera.unproject(Metashape.Vector(point)))
        # print(pt)
        if pt is None:
            # agh I don't know why this happens but we'll just skip it!
            skipped += 1
            continue
        pt = chunk.crs.project(chunk.transform.matrix.mulp(pt))
        # finally, we convert the pt to pixel coords in the orthomosaic by looking at how far it is from the orthomosaic's top, left corner
        yield [(pt[0]-chunk.orthomosaic.left)/x, (chunk.orthomosaic.top-pt[1])/y]


# open the metashape document
doc = Metashape.Document()
doc.open(args.project_file, read_only=True)

# find the correct chunk
for chunk in doc.chunks:
    # ie the one with the orthomosaic in it
    if chunk.orthomosaic is not None:
        break

# now find the camera that matches the name given
for camera in chunk.cameras+[None]:
    if camera is None:
        parser.error("Could not find the specified drone image in the project file. Check the value you provided to the --camera option.")
    if camera.label == args.camera:
        break

# # import the segments
# files = {
#     f.stem: f.stem+f.suffix
#     for f in Path(args.segments).iterdir()
#     if f.is_file() and (f.suffix == '.json' or f.suffix == '.JSON')
# }
# # map each file name (w/o the .json extension) to its index in chunk.cameras
# cams = {
#     chunk.cameras[i].label: chunk.cameras[i]
#     for i in range(len(chunk.cameras))
#     if chunk.cameras[i].label in files
# }

# 1) import the segments using the labelme importer
# 2) transform them
# 3) and then write them to the out file
import_labelme.write(
    args.out,
    [
        list(transform(chunk, camera, seg))
        for seg in import_labelme.main(args.segments)
    ],
    args.image
)
if skipped:
    logging.warning("There were "+str(skipped)+" points that couldn't be transformed")
