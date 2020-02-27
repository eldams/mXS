#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys

for trainLine in sys.stdin.readlines():
	trainCols = trainLine.strip().split('\t')
	trainFeats = '\t'.join(trainCols[1:])
	trainLabelO = []
	trainLabelC = []
	for trainLabel in trainCols[0].split(','):
		if trainLabel.startswith('+'):
			trainLabelO.append(trainLabel[1:])
		if trainLabel.startswith('-'):
			trainLabelC.append(trainLabel[1:])
	if len(trainLabelO):
		print('+' + ','.join(trainLabelO) + '\t' + trainFeats)
	else:
		print('+=\t' + trainFeats)
	if len(trainLabelC):
		print('-' + ','.join(trainLabelC) + '\t' + trainFeats)
	else:
		print('-=\t' + trainFeats)
