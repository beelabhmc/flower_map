#!/usr/bin/env python3

# a file to find images from the output of extract_images.py to subset image and form a new directory

import sys, os
import argparse

parser = argparse.ArgumentParser(description='Subset source images based on input and form a directory.')
parser.add_argument(
    "imageSourceInput", help="directory containing all the images for this week", type=str
)
parser.add_argument(
    "extractImageOutput", help="the text file containing the images identified based on given labels", type=str
)
parser.add_argument(
    "out", help="the address of the directory containing all the images in the subset"
)

args = parser.parse_args()

import shutil

def subsetImages(imageSourceInput, extractImageOutput, out):
    """"""
    source = open(extractImageOutput, "r")
    uniqueStop = False
    imageFileNameL = []
    # extract image file names from the text file
    while uniqueStop == False:
        line = source.readline()
        lineContent = line.split('\t')[0].replace('\n', '')
        print("line", line)
        if lineContent[-4:] == ".JPG":
            print("YESS")
            imageFileNameL.append(lineContent)
            print(imageFileNameL)
        if line == "\n":
            uniqueStop = True
    source.close()

    outputDirL = out.split("/")
    outputDir = '/'.join(outputDirL[:-1])
    # copy image files to output dir
    outLog = open(out, "wt")
    for filename in os.listdir(imageSourceInput):
        if filename in imageFileNameL:
            print("current File", filename)
            print(outputDir)
            newPath = shutil.copy(imageSourceInput+"/"+filename, outputDir)
            print(newPath)
            outLog.write(filename+" copied.\n")
    outLog.close()
    return
subsetImages(args.imageSourceInput, args.extractImageOutput, args.out)
