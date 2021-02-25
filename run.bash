#!/usr/bin/env bash
#$ -t 1
#$ -V
#$ -S /bin/bash
#$ -j y
#$ -cwd
#$ -o /dev/null
#$ -e /dev/null

# An example bash script demonstrating how to run the entire snakemake pipeline
# on an SGE cluster
# This script creates two separate log files in the output dir:
# 	1) log - the basic snakemake log of completed rules
# 	2) qlog - a more detailed log of the progress of each rule and any errors

# Before running this snakemake pipeline, remember to complete the config file
# with the required input info. In particular, make sure that you have created
# a samples.tsv file specifying paths to your drone imagery.
# Also, make sure that this script is executed from the directory that it lives in!

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

# handle some weird behavior where sge passes the noclobber argument to the script
# this only applies if the script is being executed from qsub on our cluster (like: qsub run.bash)
test "$1" = "noclobber" && shift

# try to find and activate the snakemake conda env if we need it
# changed 2/13/2021 deleted snakemake detection conditional because snakmake 5.5.3 is installed on purves globally
if command -v 'conda' &>/dev/null && \
   [ "$CONDA_DEFAULT_ENV" != "snakemake" ] && \
   conda info --envs | grep "$CONDA_ROOT/snakemake" &>/dev/null; then
        echo "Snakemake not detected. Attempting to switch to snakemake environment." >> "$out_path/log"
        eval "$(conda shell.bash hook)"
        conda activate snakemake
fi

# check: are we being executed from within qsub?
if [ "$ENVIRONMENT" = "BATCH" ]; then
	snakemake \
	--cluster "qsub -t 1 -V -S /bin/bash -j y -cwd -o $out_path/qlog" \
	--config out="$out_path" \
	--latency-wait 60 \
	--use-conda \
	-k \
	-j 12 \
	"$@" &>"$out_path/log"
else
	snakemake \
	--config out="$out_path" \
	--latency-wait 60 \
	--use-conda \
	-k \
	-j 12 \
	"$@" 2>>"$out_path/log" >>"$out_path/qlog"
fi

# message the user on slack if possible
exit_code="$?"
if command -v 'slack' &>/dev/null; then
    if [ "$exit_code" -eq 0 ]; then
        slack "flower-mapping pipeline finished successfully" &>/dev/null
    else
        slack "flower-mapping pipeline exited with error code $exit_code"
    fi
fi
exit "$exit_code"
