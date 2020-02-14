#!/usr/bin/env python3
import json


def main(labels):
    # import the labels and extract the coordinates to a list
    with open(labels) as json_file:
        labels = json.load(json_file)['shapes']
        for i in range(len(labels)):
            labels[i] = labels[i]['points']
    return labels

if __name__ == '__main__':
    # if this script is being called but not imported:
    import argparse
    parser = argparse.ArgumentParser(description='Import the labelme labels as a simple python list.')
    parser.add_argument(
        "labels", help="the path to the json file containing the labelme labels"
    )
    args = parser.parse_args()
    main(args.labels)
    print(labels)
