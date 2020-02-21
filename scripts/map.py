#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(description='Stitch the drone imagery together.')
parser.add_argument(
    "ortho", help="the path to the stitched orthomosaic"
)
parser.add_argument(
    "labels", help="the path to the file containing the coordinates of the polygon of each segmented region"
)
parser.add_argument(
    "predicts", help="the path to the file containing the coordinates of the polygon of each segmented region"
)
parser.add_argument(
    "out", help="a map of the flowering species in the stitched orthomosaic"
)
args = parser.parse_args()

import cv2 as cv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# if the data is from labelme, import it using the labelme importer
if args.labels.endswith('.json'):
    import import_labelme
    # labels = [np.array(label, dtype=np.int32) for label in labels]
    labels = import_labelme.main(args.labels)
else:
    raise Exception('label format not supported yet')
labels = [np.array(label).astype(np.int32) for label in labels]

# import predictions
predicts = pd.read_csv(args.predicts, sep="\t", header=0, index_col=False)

img = cv.imread(args.ortho)

for i in range(len(labels)):
    class_label = int(predicts.iloc[i]["response"])
    # set transparecy according to prediction p-value
    color = [
        col*255
        for col in plt.cm.Dark2(class_label)[:-1] + (
            predicts.iloc[i]["prob."+str(class_label)],
        )
    ]
    cv.drawContours(img, labels, i, color, 5)

cv.imwrite(args.out, img)
