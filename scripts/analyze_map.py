#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser(
    description="Calculate various properties of a map (ie the output of the pipeline)."
)

parser.add_argument(
    "out", help="the path to a file in which to write the metrics"
)
args = parser.parse_args()

# THIS SCRIPT IS STILL IN DEVELOPMENT
