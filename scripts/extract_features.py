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
    import import_labelme
    # labels = [np.array(label, dtype=np.int32) for label in labels]
    labels = import_labelme.main(args.labels)
else:
    raise Exception('label format not supported yet')

# load the image
print('loading image...')
img = Image.open(args.img).convert("RGB")
img_array = np.asarray(img)

# initialize a np array to store the output data
out = np.empty((len(labels), 19))

def metrics(img, mask):
    """
        input: img - an image from which to grab the pixels in the segmented region given by the boolean mask
               mask - a boolean mask with true values at pixel values contained within the segmented region
        output: metrics - all of the features we can calculate for that segmented region
    """
    avg = features.colorAvg(img, mask)
    yellow = features.yellowFast(img, mask)
    edges = features.countEdgePixels(img, mask)
    var = features.colorVariance(img, mask)
    texture = features.textureAnalysis(img, mask)
    (contrast, dissim, homog, energy, corr, ASM) = features.glcm(img, mask)
    (Hstd, Sstd, Vstd, Hskew, Sskew, Vskew) = features.colorMoment(img, mask)
    metrics = [avg[0], avg[1], avg[2], yellow, var, edges, texture, contrast, dissim, homog, energy, corr, ASM, Hstd, Sstd, Vstd, Hskew, Sskew, Vskew]
    return metrics

# for each segmented region:
for i in range(len(labels)):

    # calculate a boolean mask of the region contained within the provided contour
    # mask = np.zeros((img.shape[0], img.shape[1])
    mask = Image.new('L', (img_array.shape[1], img_array.shape[0]), 0)
    ImageDraw.Draw(mask).polygon(
        [tuple(label) for label in labels[i]],
        outline=1, fill=1
    )

    # bool_mask = np.array(mask)
    # # use the boolean mask to extract only those pixels of the img
    # # assemble new image (uint8: 0-255)
    # new_img_array = np.empty(img_array.shape,dtype='uint8')
    # # colors (three first columns, RGB)
    # new_img_array[:,:,:3] = img_array[:,:,:3]
    # # filtering image by mask
    # new_img_array[:,:,0] = new_img_array[:,:,0] * bool_mask
    # new_img_array[:,:,1] = new_img_array[:,:,1] * bool_mask
    # new_img_array[:,:,2] = new_img_array[:,:,2] * bool_mask
    # new_img = Image.fromarray(new_img_array, "RGB")

    # crop out only the bounding rectangle surrounding the polygon
    new_img = img.crop(mask.getbbox())
    new_mask = mask.crop(mask.getbbox())

    # calculate the features and store them in the np array
    out[i,:] = metrics(new_img, new_mask)

# write the output to the tsv file
np.savetxt(args.out, out, fmt='%f', delimiter="\t")
# np.savetxt(args.out, out, fmt='%f', delimiter="\t", header=)
