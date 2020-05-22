#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(
    description=
    """
        Segment the image into objects and output both 1) contours which we are
        highly confident have plants and 2) contours which we have less
        confidence contain plants (where the contours from #1 are contained
        within the regions outlined by #2). You can run watershed with #1 and
        #2 to get the resulting contours.
    """
)
parser.add_argument(
    "image", help="a path to the image to segment"
)
parser.add_argument(
    "out_high", help="the path to a file in which to store the coordinates of each extracted high confidence object"
)
parser.add_argument(
    "out_low", help="the path to a file in which to store the coordinates of each extracted low confidence object"
)
args = parser.parse_args()
if not (
    (args.out_high.endswith('.json') or args.out_high.endswith('.npy')) and
    (args.out_low.endswith('.json') or args.out_low.endswith('.npy'))
):
    parser.error('Unsupported output file type. The files must have a .json or .npy ending.')

import features
import cv2 as cv
import numpy as np
# from test_util import * # uncomment for testing
# import matplotlib.pyplot as plt # uncomment for testing
# plt.ion() # uncomment for testing


# CONSTANTS
PARAMS = {
    'texture': {
        'window_radius': 2,
        'num_features': 6,
        'inverse_resolution': 30,
        'threshold': 1300,
        'closing': {
            'struct_element_size': 16,
            'iterations': 4
        },
        'opening': {
            'struct_element_size': 31,
            'iterations': 2
        }
    }
}


def sliding_window(img, fnctn, size, num_features=1, skip=0):
    """
        run fnctn over each sliding, square window of width 2*size+1, skipping every skip pixel
        store the result in a np arr of equal size as the img but with depth equal to num_features
    """
    # make a shape x num_features array, since there are num_features features
    new = np.empty(img.shape+(num_features,))
    # run a sliding window over the i and j indices
    for i in range(0, img.shape[0], skip):
        # we adjust for windows that would otherwise go over the edge of the frame
        i1 = max(0, i-size)
        i2 = min(i+size+1, img.shape[0])
        next_i = min(i+skip, img.shape[0])
        for j in range(0, img.shape[1], skip):
            j1 = max(0, j-size)
            j2 = min(j+size+1, img.shape[1])
            next_j = min(j+skip, img.shape[1])
            # call the function
            new[i:next_i,j:next_j,:] = fnctn(img[i1:i2,j1:j2])
    return new

def largest_polygon(polygons):
    """ get the largest polygon among the polygons """
    # we should probably use a complicated formula to do this
    # but for now, it probably suffices to notice that the last one is usually
    # the largest
    return polygons.points[-1]

def export_results(mask, out):
    """ write the resulting mask to a file """
    ret, markers = cv.connectedComponents(mask.astype(np.uint8))
    # should we save the segments as a mask or as bounding boxes?
    if out.endswith('.npy'):
        np.save(out, markers)
    elif out.endswith('.json'):
        # import extra required modules
        from imantics import Mask
        import import_labelme
        segments = [
            (int(i), largest_polygon(Mask(markers == i).polygons()).tolist())
            for i in range(1, ret)
        ]
        import_labelme.write(out, segments, args.image)
    else:
        raise Exception("Unsupported output file format.")

print('loading image')
img = cv.imread(args.image)

print('calculating textures (this may take a while)')
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
if True:
    texture = sliding_window(gray, features.glcm, *tuple([PARAMS['texture'][i] for i in ['window_radius', 'num_features', 'inverse_resolution']]))
else:
    texture = np.load("temp/texture.npy")
thresh_contrast = cv.threshold(texture[:,:,0], PARAMS['texture']['threshold'], 255, cv.THRESH_BINARY)[1]

print('performing morphological operations to remove noise from texture')
thresh_contrast_closing = cv.morphologyEx(thresh_contrast, cv.MORPH_CLOSE, np.ones((PARAMS['texture']['closing']['struct_element_size'],)*2, np.uint8), iterations = PARAMS['texture']['closing']['iterations'])
thresh_contrast_opening = cv.morphologyEx(thresh_contrast_closing, cv.MORPH_OPEN, np.ones((PARAMS['texture']['opening']['struct_element_size'],)*2, np.uint8), iterations = PARAMS['texture']['opening']['iterations'])

# blur image to remove noise from flowers
print('blurring image to remove noise')
blur = cv.GaussianBlur(img,(5,5),60)

print('creating thresholded matrix')
# hsv = cv.cvtColor(img,cv.COLOR_BGR2HSV)
# order of colors is blue, green, red
thresh_green_orig = cv.bitwise_not(cv.inRange(blur, (0, 92, 0), (255, 255, 255)))

thresh_green = np.logical_or(thresh_contrast_opening, thresh_green_orig).astype(np.float)*255

# noise removal
print('performing morphological operations to remove noise from green')
opening1 = cv.morphologyEx(thresh_green,cv.MORPH_OPEN, np.ones((5,5),np.uint8), iterations = 1)
closing1 = cv.morphologyEx(opening1, cv.MORPH_CLOSE, np.ones((5,5),np.uint8), iterations = 5)
confident= cv.morphologyEx(closing1,cv.MORPH_OPEN, np.ones((6,6),np.uint8), iterations = 18)
opening = cv.morphologyEx(closing1, cv.MORPH_OPEN, np.ones((3,3),np.uint8), iterations = 5)
closing = cv.morphologyEx(opening, cv.MORPH_CLOSE, np.ones((5,5),np.uint8), iterations = 20)

# plot_img(create_arr([img, opening1, closing1, confident, opening, closing], 2, 3), close=True)

# save the resulting masks to files
print('writing resulting masks to output files')
export_results(confident, args.out_high)
export_results(closing, args.out_low)
