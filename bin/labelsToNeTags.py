#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys

# Retrieve stand off comments and escapes
lineCount = 0
standOffs = {}
if len(sys.argv) > 1 and sys.argv[1]:
	for line in open(sys.argv[1]):
		line = line.strip()
		if len(line):
			standOffs[lineCount] = line
		lineCount += 1

# Transform labelled output to ne tags output
lineCount = 0
outputTokens = []
currentLabels = []
for line in sys.stdin:
	if lineCount in standOffs:
		outputTokens.append(standOffs[lineCount])
	lineCount += 1
	line = line.strip()
	if line:
		features = line.split('\t')
		labels = features[-1].split('/')
		nextLabels = []
		for label in labels:
			if label.endswith('-B') or label.endswith('-I'):
				nextLabels.append(label[:-2])
		commonLabelsIndex = 0
		for i in range(min(len(currentLabels), len(nextLabels))):
			if nextLabels[i] == currentLabels[i]:
				commonLabelsIndex = i + 1
			else:
				break
		if commonLabelsIndex < len(currentLabels):
			for i in reversed(range(commonLabelsIndex,len(currentLabels))):
				outputTokens.append('NE/</NEm-'+currentLabels[i]+'> ')
		if commonLabelsIndex < len(nextLabels):
			for i in range(commonLabelsIndex, len(nextLabels)):
				outputTokens.append('NE/<NEm-'+nextLabels[i]+'> ')
		currentLabels = nextLabels
		outputTokens.append(features[0])
for i in range(len(currentLabels)):
	outputTokens.append('NE/<NEm-'+nextLabels[i]+'> ')
print(' '.join(outputTokens))

