#!/usr/bin/env python3
import json

if __name__ == '__main__':
    # if this script is being called but not imported:
    import argparse
    parser = argparse.ArgumentParser(description='Import the labelme labels as a simple python list.')
    parser.add_argument(
        "labels", help="the path to the json file containing the labelme labels"
    )
    args = parser.parse_args()
    labels = args.labels
elif labels is None:
    # otherwise, if it is being imported and the labels var isn't set
    raise Exception("you must set the labels var to the path to the json file containing the labelme labels before importing this module")

# import the labels and extract the coordinates to a list
with open(labels) as json_file:
    labels = json.load(json_file)['shapes']
    for i in range(len(labels)):
        labels[i] = labels[i]['points']

# if this script is being called but not imported, print the data to stdout
if __name__ == '__main__':
    print(labels)
