

#!/usr/bin/env python3
import argparse
from pathlib import Path

# SCRIPT IN PROGRESS
# Goal

# parser = argparse.ArgumentParser(
#     description="Create data that can be used to train a random forest classifier implemented by ranger."
# )
# parser.add_argument(
#     "features", type=Path, help="the path to a file containing tsv files (for each image in the orthomosaic) with the features of each segmented region (or the path to a directory if there are many such files)"
# )
# parser.add_argument(
#     "out", nargs='+', help="the path to a file to write the truth data; we will allow users to write truth table with this script"
# )

# args = parser.parse_args()
# if len(args.out) > 2:
#     parser.error("You can provide at most two outputs.")
# # but if there are two outputs, make sure the first one is a file
# if len(args.out)-1:
#     assert (not Path(args.out[0]).is_dir()), "If you provide two outputs, the first must be a file (for training). The second (for testing) can be either a file or a directory if you want the output split by camera."


import sys
import numpy
from PIL import Image




from create_truth_data import get_features
# get the features files
# check: are we running the experimental strategy or the default one?
if args.features.is_dir():

    # get the features
    features = {
        f.stem: str(f)
        for f in args.features.iterdir()
        if f.suffix == '.tsv'
    }
    features = pd.concat(
        {
            cam: get_features(features[cam])
            for cam in features
        }
    )
    print("______________________")
    print("Here are the features:")
    print(features)


from osgeo import gdal
import numpy as np
from PIL import Image

### HERE: write two things ###
### 1. Match each label with orthomosaic coordinate ###
### 2. Translate orthomosaic coordinates to numpy coordinate ###
### 3. Use the function below to subset image ### 

## a function written to help with understanding how to use gdal package to work with images
def manualVisSubsetImage(tiffFilePath, outputPath, outputName):
    dataset = gdal.Open(tiffFilePath)
    # get rgb frames
    channelR = np.array(dataset.GetRasterBand(1).ReadAsArray())
    channelG = np.array(dataset.GetRasterBand(2).ReadAsArray())
    channelB = np.array(dataset.GetRasterBand(2).ReadAsArray())
    # get shape and show it to user
    print("Current image has dimension (height=" +
          str(channelR.shape[0])+", width="+str(channelR.shape[1])+").")
    print("Please provide dimensions to visualize:")
    hUpperBound = input("Enter upper bound of height (close to 0).")
    hLowerBound = input(
        "Enter lower bound of height (bigger than upper bound).")
    if type(hUpperBound) != int or type(hLowerBound) != int:
        raise Exception("width value(s) entered needs to of the type int.")
    wUpperBound = input("Enter upper bound of height (close to 0).")
    wLowerBound = input(
        "Enter lower bound of height (bigger than upper bound).")
    if type(hUpperBound) != int or type(hLowerBound) != int:
        raise Exception("height value(s) entered needs to of the type int.")
    # get subset
    channelRSub = channelR[wUpperBound:wLowerBound, hUpperBound:hLowerBound]
    channelGSub = channelG[wUpperBound:wLowerBound, hUpperBound:hLowerBound]
    channelBSub = channelB[wUpperBound:wLowerBound, hUpperBound:hLowerBound]
    channelSubSum = np.stack((channelRSub, channelGSub, channelBSub), axis=2)
    # save image
    img = Image.fromarray(channelSubSum, 'RGB')
    img.save(outputPath+"/"+outputName+".png")
    return


# def one_label_per_time(features):
#     """ get one label's images per time to help users write truth.tsv"""
#     for label in featuresdf:
#         for image in all images for this label:
#             get current image path
#             print_image(sys.argv[1]) to see the image in the terminal
#     return

