#!/usr/bin/env bash
#$ -t 1
#$ -V
#$ -S /bin/bash
#$ -j y
#$ -cwd
#$ -o /dev/null
#$ -e /dev/null


# first, handle some weird behavior where sge passes the noclobber argument to the script
# this only applies if the script is being executed from qsub on our cluster (like: qsub run.bash)
test "$1" = "noclobber" && shift

# An example bash script demonstrating how to run the entire snakemake pipeline
# on an SGE cluster
# This script creates two separate log files:
# 	1) log - the basic snakemake log of completed rules
# 	2) qlog - a more detailed log of the progress of each rule and any errors

# you can specify a directory for all output here:
out_path="out"
mkdir -p "$out_path"

# clear leftover log files
if [ -f "${out_path}/log" ]; then
	echo ""> "${out_path}/log";
fi
if [ -f "${out_path}/qlog" ]; then
	echo ""> "${out_path}/qlog";
fi

# make sure that this script is executed from the directory that it lives in!

# # also, make sure this script is being executed in the correct snakemake environment!
# if [ "$CONDA_DEFAULT_ENV" != "snakemake" ] && conda info --envs | grep "$CONDA_ROOT/snakemake" &>/dev/null; then
# 	conda activate snakemake
# 	echo "Switched to snakemake environment." > "${out_path}/log"
# fi

# Before running this snakemake pipeline, remember to complete the config file
# with the required input info. In particular, make sure that you have created
# a samples.tsv file specifying paths to your drone imagery.

# check: should we execute via qsub?
if [[ $* == *--sge-cluster* ]]; then
	snakemake \
	--cluster "qsub -t 1 -V -S /bin/bash -j y -cwd -o $out_path/qlog" \
	--config out="$out_path" \
	--latency-wait 60 \
	--use-conda \
	-k \
	-j 12 \
	${@//--sge-cluster/} &>"$out_path/log"
else
	snakemake \
	--config out="$out_path" \
	--latency-wait 60 \
	--use-conda \
	-k \
	-j \
	"$@" 2>"$out_path/log" >"$out_path/qlog"
fi
