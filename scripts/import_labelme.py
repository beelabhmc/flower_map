#!/usr/bin/env python3
import json


def main(labels, labeled=False, dims=tuple()):
    """
        import the labels and extract the coordinates to a list
        if dimensions are specified, labels that don't exist inside the dims will be ignored
    """
    with open(labels) as json_file:
        # initialize input and output
        labels = json.load(json_file)['shapes']
        segments = {}
        # for each segment, grab its pt and store it in the output
        for i in range(len(labels)):
            pts = labels[i]['points']
            if dims:
                pts = list(
                    filter(
                        lambda pt: (0 <= pt[0] < dims[0]) and (0 <= pt[1] < dims[1]),
                        pts
                    )
                )
            # add to the segments dict
            label = labels[i]['label']
            if type(label) != int:
                # convert the label to an integer, ignoring any chars in the string
                label = int("".join([s for s in labels[i]['label'] if s.isdigit()]))
            segments[label] = pts
            # replace in the labels array
            labels[i] = pts
    return segments if labeled else labels

if __name__ == '__main__':
    # if this script is being called but not imported:
    import argparse
    parser = argparse.ArgumentParser(description='Import the labelme labels as a simple python list.')
    parser.add_argument(
        "labels", help="the path to the json file containing the labelme labels"
    )
    parser.add_argument(
        "dims", nargs='?', default='', help="specify the width and height (separated by a single comma) in pixels of the image if labels that are outside that range should be ignored"
    )
    args = parser.parse_args()
    args.dims = tuple(filter(lambda i: i, args.dims.split(",")))
    print(main(args.labels, False, args.dims))
