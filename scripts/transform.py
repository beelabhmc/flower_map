#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='Transform the coordinates of each segment in the orthomosaic to the original drone images.')
parser.add_argument(
    "project_file", help="a path to a metashape project file (w/ a psx file ending) containing an orthomosaic"
)
parser.add_argument(
    "segments", help="a path to the coordinates of the segmented regions in the orthomosaic"
)
parser.add_argument(
    "out", help="a path to a directory in which to store the coordinates of the segmented regions in each image"
)
parser.add_argument(
    "--images", default="", help="a path to the directory in which the original drone images are stored; this argument must be provided if you plan to open the segment files in labelme"
)
args = parser.parse_args()
args.out += '/' if not args.out.endswith('/') else ''

import Metashape
import numpy as np


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

def rev_transform(chunk, points):
    """transform orthomosaic pixel coordinates to camera coordinates"""
    # get the width and height of the orthomosaic in latitute and longitude units
    x = chunk.orthomosaic.right-chunk.orthomosaic.left
    y = chunk.orthomosaic.top-chunk.orthomosaic.bottom
    # create a new Metashape "Shape"
    chunk.shapes = Metashape.Shapes()
    chunk.shapes.crs = chunk.crs
    shape = chunk.shapes.addShape()
    shape.type = Metashape.Shape.Polygon
    shape.has_z = False
    # convert our points to geographic coords and then add them to the "Shape"
    shape.vertices = [
        Metashape.Vector([
            chunk.orthomosaic.left+(point[0]/chunk.orthomosaic.width)*x,
            chunk.orthomosaic.top-(point[1]/chunk.orthomosaic.height)*y
        ])
        for point in points
    ]
    # add z coords to every x/y point
    chunk.shapes.updateAltitudes(chunk.shapes)
    # check: did this actually work?
    # sometimes updateAltitudes won't work. I suspect that this happens when the points are outside our digital elevation model
    if not shape.has_z:
        # just ignore this segment
        return []
    # prepare results: a dictionary keyed by a camera label, containing the coords in that camera
    results = {}
    for camera in chunk.cameras:
        vertices = []
        vertex_count = 0
        for point in shape.vertices:
            # several steps are being taken here:
            # 1) the point is unprojected from geographic coords to geocentric coords
            # 2) the new point is transformed via matrix multiplication to the chunk's projected coordinate system
            # 3) the coords are projected onto the camera to retrieve their pixel coords on the camera
            # TODO: rewrite these for loops so that we aren't redoing steps 1 and 2 for every camera?
            pt = camera.project(chunk.transform.matrix.inv().mulp(chunk.crs.unproject(point)))
            # check: did it work?
            # sometimes it won't work. I have no idea why. But I'm just going to skip this pt then
            if pt is None:
                continue
            vertices.append(list(pt))
            # count the pixels that actually exist in the photo
            if (0 <= pt[0] < camera.sensor.width) and (0 <= pt[1] < camera.sensor.height):
                vertex_count += 1
        # only add to the results if a polygon can be formed from the remaining vertices
        if vertex_count >= 3:
            results[camera.label] = vertices
    return results


# open the metashape document
doc = Metashape.Document()
doc.open(args.project_file, read_only=True)

# find the correct chunk
for chunk in doc.chunks:
    # ie the one with the orthomosaic in it
    if chunk.orthomosaic is not None:
        break

# create the dir if it doesn't already exist
Path(args.out).mkdir(exist_ok=True)

# import the segments
# if the data is from labelme, import it using the labelme importer
if args.segments.endswith('.json'):
    import import_labelme
    segments = import_labelme.main(args.segments, True)
    # prepare a dict of results, containing an array of segments for each camera
    results = {camera.label:[] for camera in chunk.cameras}
    # convert each segment to coords in the cameras it belongs in
    for label in segments:
        segs = rev_transform(chunk, segments[label])
        for cam in segs:
            results[cam].append((label, segs[cam]))
    for camera in results:
        import_labelme.write(args.out+camera+'.json', results[camera], args.images+camera+".JPG")
# # else its a np mask
# elif args.segments.endswith('.npy'):
#     segments = np.load(args.segments)
else:
    sys.exit("Unsupported segments file format.")
