#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, os

# Load MaxEnt models
corpusPath = os.environ.get('CORPUS_PATH')
from maxent import MaxentModel
maxEntModel = MaxentModel()
maxEntModel.load(corpusPath+'/model_markers.txt')

for trainLine in sys.stdin.readlines():
	trainCols = trainLine.split('\t')
	modelMarkerProbas = maxEntModel.eval_all(trainCols[1:])
	probaFeats = []
	for modelMarkerProba in modelMarkerProbas:
		if modelMarkerProba[1] > 0.00001:
			probaFeats.append(modelMarkerProba[0] + ':' + str(modelMarkerProba[1]))
	print(trainCols[0] + '\t' + '\t'.join(probaFeats))

