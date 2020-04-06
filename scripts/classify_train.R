#!/usr/bin/env RScript

# This R script trains a random forest classifier. We recommend using the Snakefile pipeline to run this script.

# param1: The path to a TSV containing the data on which to train the classifier.
#         The last column must contain binarized, true labels. Note that NA's should be removed and numerical columns should be normalized
# param2: The path to an RDA file in which to store the trained classifier. This file is required input to classify_test.R
# param3: The path a TSV in which to store information about how important the random forest deems each column in the data you provided.
# param4 (optional): The path to a TSV in which to store the results of cross validation on the classifier's hyperparameters. If not specified, cross validation will not be performed

args <- commandArgs(trailingOnly = TRUE)
training<- args[1]
model<- args[2]
importance<- args[3] # importance for each of the variables is saved here
tune<- args[4] # if specified, the results of cross validation are saved here

# load libraries
library(plyr)
library(dplyr)
library(mlr)
library(parallelMap)
library(parallel)

# load data.frame
print("loading training data into R")
training_temp<- read.table(training, header=TRUE, sep="\t", na.strings=c("NA",".","na","N/A"), skipNul=FALSE, row.names=NULL, nrow=1)
if (names(training_temp)[1] == "label") {
	training<- read.table(training, header=TRUE, sep="\t", na.strings=c("NA",".","na","N/A"), skipNul=FALSE, row.names=1)
} else {
	training<- read.table(training, header=TRUE, sep="\t", na.strings=c("NA",".","na","N/A"), skipNul=FALSE, row.names=NULL)
}

print("creating training task and making RF learner")

# optimize hyper parameters
# make training task
traintask <- makeClassifTask(data = training, target = colnames(training)[ncol(training)], positive = 1)

# create learner
rf.lrn <- makeLearner("classif.ranger", predict.type = "prob")
rf.lrn$par.vals <- list(importance='impurity', verbose=TRUE)

if (!is.na(tune)) {
	# mtry default: sqrt(number of features)
	# nodesize default: 1
	params <- makeParamSet(makeIntegerParam("mtry",lower = 1,upper = 10),
                           makeIntegerParam("min.node.size",lower = 7,upper = 25))
	# set validation strategy; 4-fold cross validation
	rdesc <- makeResampleDesc("CV",iters=5L)
	# set optimization technique
	ctrl <- makeTuneControlGrid(resolution=c(mtry=10, min.node.size=19))

	# tune hyperparameters
	print("initiating multicore tuning of hyperparameters")
	# but run the hyperparameter tuning in parallel, since it'll take a while
	# number of cores should be detected automatically (but don't use
	# all of the cores because otherwise we'll use too much memory!)
	parallelStartSocket(cpus=trunc(detectCores()/12), level="mlr.tuneParams")
	parallelLibrary("mlr")

	# create a custom F beta measure
	fbeta = makeMeasure(id = "fbeta", minimize = FALSE, best = 1, worst = 0,
		properties = c("classif", "req.pred", "req.truth"),
		name = "Fbeta measure",
		note = "Defined as: (1+beta^2) * tp/ (beta^2 * sum(truth == positive) + sum(response == positive))",
		fun = function(task, model, pred, feats, extra.args) {
			beta = 0.5
			beta = beta^2
			truth = pred$data$truth
			response = pred$data$response
			positive = pred$task.desc$positive
			(1+beta) * measureTP(truth, response, positive) /
				(beta * sum(truth == positive) + sum(response == positive))
		}
	)

	tuned = tuneParams(learner=rf.lrn, task=traintask, resampling=rdesc, measures=list(fbeta), par.set=params, control=ctrl, show.info=T)

	parallelStop()

	print("matrix of classifier performance for each pair of hyperparams")
	data = generateHyperParsEffectData(tuned)
	print(data$data)
	write.table(data$data, sep="\t", file=tune, quote=FALSE, row.names=F)
	print("tuned params are")
	print(tuned$x)
	rf.lrn$par.vals = c(rf.lrn$par.vals, tuned$x)
}
print("training model")
fit = mlr::train(rf.lrn, traintask)

# print out variable importance
print("recording variable importance:")
importance_df = as.data.frame(sort(fit$learner.model$variable.importance, decreasing=TRUE))
print(importance_df)
names(importance_df) <- c("variable\timportance")
write.table(importance_df, sep="\t", file=importance, quote=FALSE)

# save.data
save.image( model )