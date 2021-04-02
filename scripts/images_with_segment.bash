#!/usr/bin/env bash

# List the original drone images that a segment belongs to.
# arg1: path to the directory of the region in the output folder (ex: out/6617East1)
# arg2: a segment ID (ex: 339)

# ex usage: ./images_with_segment.bash out/6617East1 339
# ex output:
# DJI_0283
# DJI_0284

if [ ! -d "$1"/rev_transforms ]; then
  echo "The directory $1/rev_transforms/ must exist in order to run this script. Check that you are using the experimental strategy of the pipeline and that the 'parallel' config option is set to true."
fi
cd "$1"/rev_transforms
grep -cl '"label": "'$2'"' *.json | sed 's/.json//g'
