#!/usr/bin/env python3
import sys
import argparse

parser = argparse.ArgumentParser(description='Extract the coordinates of each point in the orthomosaic.')
parser.add_argument(
    "orthomosaic",
    help="a path to the orthomosaic"
)
parser.add_argument(
    "out", nargs='?', type=argparse.FileType('w', encoding='UTF-8'), default=sys.stdout,
    help="the path to a tsv file in which to store the coordinates of each extracted object"
)
args = parser.parse_args()

import Metashape

doc = Metashape.Document()
doc.open(args.orthomosaic, read_only=True)

for chunk in doc.chunks:
    if chunk.orthomosaic is not None:
        break

print("Left\tTop\tRight\tBottom", file=args.out)
print("{0}\t{1}\t{2}\t{3}".format(chunk.orthomosaic.left, chunk.orthomosaic.top, chunk.orthomosaic.right, chunk.orthomosaic.bottom), file=args.out)

