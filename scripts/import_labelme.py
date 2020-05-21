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
        new_labels = []
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
            if len(pts) < 3:
                continue
            # add to the segments dict
            label = labels[i]['label']
            if type(label) != int:
                # convert the label to an integer, ignoring any chars in the string
                label = int("".join([s for s in labels[i]['label'] if s.isdigit()]))
            segments[label] = pts
            # add to the new labels array
            new_labels.append(pts)
    return segments if labeled else new_labels

def write(file, segments, image_path=None):
    """
        write the segments (belonging to image_path) to the file in JSON format
        segments can be either a list of tuples (label, pts) or a simple list of pts
        if image_path is provided, the file will be in valid labelme format
    """
    import os.path
    image_path = os.path.relpath(image_path, file)
    with open(file, 'w') as out:
        json.dump(
            {
                'flags': {},
                'shapes': [
                    {
                        'label': str(segment[0]),
                        'line_color': None,
                        'fill_color': None,
                        'points': segment[1],
                        'shape_type': "polygon",
                        'flags': {} if len(segment) == 2 else segment[2]
                    }
                    if type(segment) is tuple else
                    {
                        'label': str(idx),
                        'line_color': None,
                        'fill_color': None,
                        'points': segment,
                        'shape_type': "polygon",
                        'flags': {}
                    }
                    for idx, segment in enumerate(segments)
                ],
                "lineColor": [0,255,0,128],
                "fillColor": [255,0,0,128],
                "imagePath": image_path,
                "imageData": None
            },
            out
        )

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
