#!/usr/bin/env python3

# a file to extract images from label numbers to make it easier to form subsets of images

import sys
import argparse

parser = argparse.ArgumentParser(description='Extract source images for specific list of segment labels.')
parser.add_argument(
    "sourceDir", help="the path to the directory containing the current sample's rev_transform jsons", type=str
)
parser.add_argument(
    "labels", nargs='+', help='either the path to a yaml file containing a list of segment IDs keyed by the entry "extracted_labels" OR each segment ID as a list of arguments'
)
parser.add_argument(
    "out", help="the text file containing all the image file names associated with the current segment label list"
)

args = parser.parse_args()

import os
import re
import json
import yaml
import import_labelme


def extractAllImages(sourceDir, targetLabels, out):
    """extract images used to form certain labels in the segment map stitch"""
    outputImages = []
    outputImageDict = {}
    for filename in os.listdir(sourceDir):
        if filename.endswith(".json"):
            segments = import_labelme.main(sourceDir+"/"+filename, labeled=True)
            if segments != {}:
                currentLabels = list(segments.keys())
                currentLabels = [str(label) for label in currentLabels]
            for currentLabel in currentLabels:
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

targetLabelsL = args.labels

try:
    with open(targetLabelsL[0], 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    # clean it
    targetLabelsLCleaned = data_loaded['extracted_labels']
    targetLabelsLCleaned = [str(target) for target in targetLabelsLCleaned]
except:
    targetLabelsLCleaned = targetLabelsL[0].split(',')


extractAllImages(args.sourceDir, targetLabelsLCleaned, args.out)


