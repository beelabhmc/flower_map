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
    help="the path to a python pickle file (with a .pickle extension) in which to store the coordinates of each extracted object"
)
args = parser.parse_args()

print('loading image...')
img = cv2.imread(args.image)

print('creating thresholded matrix...')
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
ret,thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

# noise removal
print('performing morphological opening to remove noise...')
kernel = np.ones((3,3),np.uint8)
opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)

# sure background area
print('identifying background by dilation...')
sure_bg = cv2.dilate(opening,kernel,iterations=3)

# Finding sure foreground area
print('identifying foreground...')
dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
ret, sure_fg = cv2.threshold(dist_transform,0.7*dist_transform.max(),255,0)

# Finding unknown region
print('identifying unknown regions (those not classified as either foreground or background)...')
sure_fg = np.uint8(sure_fg)
unknown = cv2.subtract(sure_bg,sure_fg)

# Marker labelling
print('marking connected components...')
ret, markers = cv2.connectedComponents(sure_fg)
# Add one to all labels so that sure background is not 0, but 1
markers = markers+1
# Now, mark the region of unknown with zero
markers[unknown==255] = 0

print('running the watershed algorithm...')
markers = cv2.watershed(img,markers)
img[markers == -1] = [255,0,0]


