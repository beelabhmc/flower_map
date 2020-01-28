import cv2
import argparse
import numpy as np
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser(description='Segment the image into objects.')
parser.add_argument(
    "image",
    help="a path to the image to segment"
)
parser.add_argument(
    "out", type=argparse.FileType('w', encoding='UTF-8'),
    default=sys.stdout, help="the path to a python pickle file (with a .pickle extension) in which to store the coordinates of each extracted object"
)
args = parser.parse_args()

img = cv2.imread(args.image)
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
ret,thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

