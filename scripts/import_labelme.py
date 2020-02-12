#!/usr/bin/env python3
import json

def main(data):
    with open(data) as json_file:
        data = json.load(json_file)['shapes']
        for i in range(len(data)):
            data[i] = data[i]['points']
        return data

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Import the labelme data.')
    parser.add_argument(
        "data", nargs="?",
        help="a path to the json file containing the labelme labels"
    )
    args = parser.parse_args()
    print(main(args.data))
