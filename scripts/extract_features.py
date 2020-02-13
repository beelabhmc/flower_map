#!/usr/bin/env python3
import cv2
import argparse
import features
import numpy as np
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description='Extract the features of each segmented region.')
parser.add_argument(
    "img", help="the path to the original image from which the segmented regions came"
)
parser.add_argument(
    "labels", help="the path to the file containing the coordinates of the polygon of each segmented region"
)
parser.add_argument(
    "out", help="a TSV containing the features (as columns) of each segmented regions (as rows)"
)
args = parser.parse_args()

# if the data is from labelme, import it using the labelme importer
if args.labels.endswith('.json'):
    labels = args.labels
    import import_labelme
    # labels = [np.array(label, dtype=np.int32) for label in labels]
    labels = [tuple(label) for label in labels]
else:
    raise Exception('label format not supported yet')

# load the image
print('loading image...')
img = Image.open(args.img).convert("RGB")
img_array = np.asarray(img)

# initialize a np array to store the output data
out = np.empty((len(labels), 19))

def metrics(region):
    """
        input: region - pixels extracted from each image which correspond with a segmented region
        output: metrics - all of the features we can calculate for that segmented region
    """
    avg = features.colorAvg(region)
    yellow = features.yellowFast(region)
    edges = features.countEdgePixels(region)
    var = features.colorVariance(region)
    texture = features.textureAnalysis(region)
    (contrast, dissim, homog, energy, corr, ASM) = features.glcm(region)
    (Hstd, Sstd, Vstd, Hskew, Sskew, Vskew) = features.colorMoment(region)
    metrics = [avg[0], avg[1], avg[2], yellow, var, edges, texture, contrast, dissim, homog, energy, corr, ASM, Hstd, Sstd, Vstd, Hskew, Sskew, Vskew]
    return metrics

# for each segmented region:
for i in range(len(labels)):

    # calculate a boolean mask of the region contained within the provided contour
    # mask = np.zeros((img.shape[0], img.shape[1])
    mask = Image.new('L', (img_array.shape[1], img_array.shape[0]), 0)
    ImageDraw.Draw(mask).polygon(labels[0], outline=1, fill=1)
    # mask = np.array(mask)
    # use the boolean mask to extract only those pixels of the img
    # assemble new image (uint8: 0-255)
    new_img_array = np.empty(img_array.shape,dtype='uint8')
    # colors (three first columns, RGB)
    new_img_array[:,:,:3] = img_array[:,:,:3]
    new_img = Image.fromarray(new_img_array, "RGB")

    # calculate the features and store them in the np array
    out[i,:] = metrics(new_img)

# write the output to the tsv file
np.savetxt(args.out, out, fmt='%f', delimiter="\t")
# np.savetxt(args.out, out, fmt='%f', delimiter="\t", header=)
