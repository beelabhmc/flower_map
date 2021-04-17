#!/usr/bin/env python3

# a file to extract images from label numbers to make it easier to form subsets of images

import sys
import argparse

parser = argparse.ArgumentParser(description='Extract source images for specific list of segment labels.')
parser.add_argument(
    "sourceDir", help="the path to the directory containing the current sample's rev_transform jsons", type=str
)
parser.add_argument(
    "configFile", help="the path to a directory containing (for each image in the orthomosaic) the coordinates of each segmented region"
)
parser.add_argument(
    "out", help="the text file containing all the image file names associated with the current segment label list"
)

args = parser.parse_args()

import os
import re
import json
import yaml

def extractAllImages(sourceDir, targetLabels, out):
    """extract images used to form certain labels in the segment map stitch"""
    outputImages = []
    outputImageDict = {}
    print(targetLabels)
    print("WHATS GOING ON??")
    for filename in os.listdir(sourceDir):
        if filename.endswith(".json"):
            # json_reader = open(filename, "rt")
            print(filename)
            json_reader = open(sourceDir+"/"+filename,)
            json_data = json.load(json_reader)
            for line in json_data["shapes"]:
                currentLabel = str(line["label"])
                if currentLabel in targetLabels:
                    imageFilename = filename[:-5]+'.JPG'
                    outputImages.append(imageFilename)
                    if currentLabel not in outputImageDict.keys():
                        outputImageDict.update({currentLabel: [imageFilename]})
                    else:
                        outputImageDict[currentLabel].append(imageFilename)

    uniqueOutputImages = list(set(outputImages))
    # write unique output images to output file
    with open(out, mode="w") as outfile:
        outfile.write("All unique images are:\n")
        for s in outputImages:
            outfile.write("%s\n" % s)
        outfile.write("\n")
    # write images associated with each label to output file
        for s in outputImageDict.keys():
            outfile.write("Current label %s has images: \n" % s)
            outfile.write(str(outputImageDict[s])+"\n")
    return uniqueOutputImages, outputImageDict

# get the list of target labels
with open(args.configFile, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
# clean it
targetLabelsL = [str(item) for item in data_loaded['extracted_labels'].split(',')]
targetLabelsLCleaned = [target.replace(" ", "") for target in targetLabelsL]
extractAllImages(args.sourceDir, targetLabelsLCleaned, args.out)
print("DONEEEE!")

