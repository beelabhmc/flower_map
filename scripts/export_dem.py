#!/usr/bin/env python3
import argparse
import Metashape

parser = argparse.ArgumentParser(description='Extract the elevation of each pixel in a project file.')
parser.add_argument(
    "project_file",
    help="a path to a metashape project file (w/ a psx file ending)"
)
parser.add_argument(
    "out", help="the digital elevation model values"
)
args = parser.parse_args()

# open the metashape document
doc = Metashape.Document()
doc.open(args.project_file, read_only=True)

# find the correct chunk
for chunk in doc.chunks:
    if chunk.orthomosaic is not None:
        break

# export the orthomosaic
chunk.exportDem(args.out)
