#!/usr/bin/env Rscript

# This R script makes predictions on a dataset using a trained classifier

# param1: The path to a TSV containing the data for which to make predictions.
#         Columns must be named the same as the training data.
# param2: An RDA file containing the trained classifier. This is output by classify_train.R
# param3: The path to a TSV in which to write the predictions. It will be created if it doesn't exist.


args <- commandArgs(trailingOnly = TRUE)
test.data<- args[1]
model <- args[2]
output<- args[3]

# load libraries
library(data.table)
library(plyr)
library(dplyr)
library(mlr)

# load model
print("loading appropriate model")
load(model)

# load test
print("loading and formatting test data")
test<- read.table(test.data, header=TRUE, sep="\t", na.strings=c("NA",".","na","N/A"), skipNul=FALSE, row.names=NULL, nrow=1)
if (names(test)[1] == "label") {
	test<- read.table(test.data, header=TRUE, sep="\t", na.strings=c("NA",".","na","N/A"), skipNul=FALSE, row.names=1)
} else {
	test<- read.table(test.data, header=TRUE, sep="\t", na.strings=c("NA",".","na","N/A"), skipNul=FALSE, row.names=NULL)
}

# first, check: are there any plants in this image?
if (!nrow(test)) {
	# if not, handle it sepcifically
	print(paste("warning:", test.data, "has no segments"))
	if ('species_label' %in% colnames(test)){
		write.table(data.frame('truth'=integer(), 'prob.0'=integer(), 'prob.1'=integer(), 'response'=integer()), sep="\t", quote=FALSE, na=".", output)
	} else {
		write.table(data.frame('prob.0'=integer(), 'prob.1'=integer(), 'response'=integer()), sep="\t", quote=FALSE, na=".", output)
	}
} else {
	# making predictions
	print("making predictions and outputting results")
	pred= predict(fit, newdata= test, type="prob")
	write.table(pred$data, sep='\t', quote=FALSE, na=".", output)
}
