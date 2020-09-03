#!/usr/bin/env python3

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("dir", type=Path)
args = parser.parse_args()
args.dir = str(args.dir)+"/benchmark"



import itertools
import pandas as pd

# --FIRST: IMPORT THE DATA--
# initialize dictionaries
default = {}
experimental = {}

# load common steps
default['stitch'] = pd.read_csv(args.dir+"/stitch-lowQual.tsv", sep="\t", header=0)
default['export_ortho'] = pd.read_csv(args.dir+"/export_ortho.tsv", sep="\t", header=0)
for step in default:
    experimental[step] = default[step]

# default strategy
default['segment'] = pd.read_csv(args.dir+"/segments/ortho.tsv", sep="\t", header=0)
default['watershed'] = pd.read_csv(args.dir+"/watershed.tsv", sep="\t", header=0)
default['extract_features'] = pd.read_csv(args.dir+"/extract_features/ortho.tsv", sep="\t", header=0)
default['classify'] = pd.read_csv(args.dir+"/classify/ortho.tsv", sep="\t", header=0)
default['map'] = pd.read_csv(args.dir+"/map.tsv", sep="\t", header=0)

# experimental strategy
experimental['segment'] = pd.DataFrame({'sum':pd.concat((
    pd.read_csv(f, sep="\t", header=0)
    for f in Path(args.dir+"/segments").iterdir()
    if f.stem != 'ortho'
)).max()}).T
experimental['transform'] = pd.DataFrame({'sum':pd.concat((
    pd.read_csv(f, sep="\t", header=0)
    for f in Path(args.dir+"/transform").iterdir()
)).max()}).T
experimental['watershed'] = pd.read_csv(args.dir+"/watershed-exp.tsv", sep="\t", header=0)
experimental['rev_transform'] = pd.read_csv(args.dir+"/rev_transform.tsv", sep="\t", header=0)
experimental['extract_features'] = pd.DataFrame({'sum':pd.concat((
    pd.read_csv(f, sep="\t", header=0)
    for f in Path(args.dir+"/extract_features-exp").iterdir()
)).max()}).T
experimental['classify'] = pd.DataFrame({'sum':pd.concat((
    pd.read_csv(f, sep="\t", header=0)
    for f in Path(args.dir+"/classify-exp").iterdir()
)).max()}).T
experimental['resolve_conflicts'] = pd.read_csv(args.dir+"/resolved_conflicts.tsv", sep="\t", header=0)
experimental['map'] = pd.read_csv(args.dir+"/map-exp.tsv", sep="\t", header=0)

# concatenate the dicts into big pd dfs
default = pd.concat(default, ignore_index=False)
experimental = pd.concat(experimental, ignore_index=False)

# --SECOND: CALCULATE OUR METRICS--
# extract only the metrics we care about:
# running time (in secs) and max memory usage (in MB)
metrics = {}
metrics['default'] = default[['s','max_rss']]
metrics['experimental'] = experimental[['s','max_rss']]

steps = {
    'stitching': (('stitch', 'export_ortho'),),
    'segmentation': (('segment', 'watershed'), ('transform', 'rev_transform')),
    'classification': (('extract_features', 'classify'), ('resolve_conflicts',))
}
print('units (hrs, GB)\n')
strategies = sorted(metrics.keys())
for i in range(len(strategies)):
    strategy = strategies[i]
    print(strategy, 'strategy')
    strat = metrics[strategy].copy()
    print('total', (
        round(strat.sum()['s']/60/60/24, ndigits=5),
        strat.max()['max_rss']/1000)
    )
    for step in sorted(steps.keys(), reverse=True):
        step_names = list(itertools.chain.from_iterable(steps[step][:i+1]))
        time = strat.loc[step_names].sum()['s']/60/60/24
        mem = strat.loc[step_names].max()['max_rss']/1000
        print(step, (round(time, ndigits=5), mem))
    print()

