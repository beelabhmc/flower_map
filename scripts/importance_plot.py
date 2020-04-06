#!/usr/bin/env python3

import sys
import argparse
import matplotlib
import pandas as pd
matplotlib.use('Agg')
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument(
    "table", default=sys.stdin,
    help="a two column (variable/importance) table of importances w/ a header"
)
parser.add_argument(
    "out", nargs='?', default=sys.stdout, help="the filename to save the data to"
)
args = parser.parse_args()


# import the data and create the plot
plot = pd.read_csv(
    args.table, sep="\t", header=0
).sort_values(by="importance", ascending=False).plot.bar(x='variable')

plot.legend().remove()
plt.xlabel('Feature')
plt.ylabel('Importance')

plt.savefig(args.out, bbox_inches='tight', pad_inches=0.02)

