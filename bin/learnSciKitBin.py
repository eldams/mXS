#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, os, joblib, numpy, math
from scipy import sparse
from sklearn import linear_model, svm

# Parameters
modeDebug = True
learnAlgo = 'LogisticRegression' # LogisticRegression, SVM, SGD
infosFilename = sys.argv[1]
corpusModel = os.environ.get('CORPUS_MODEL')

# Load infos about data
nbSequences = 0
nbFeatures = 0
nbMarkerClasses = 0
nbSequenceClasses = 0
sequenceClassesLen = {}
markerIds = {}
sequenceLabels = {}
for line in open(infosFilename):
	lineParts = line.strip().split('\t')
	if lineParts[0] == 'shape':
		nbMarkers = int(lineParts[1])
		nbSequences = int(lineParts[2])
		nbFeatures = int(lineParts[3])
	elif lineParts[0] == 'mark':
		nbMarkerClasses += 1
		markerId = int(lineParts[2]) - 1
		markerIds[lineParts[1]] = markerId
	elif lineParts[0] == 'seq':
		nbSequenceClasses += 1
		sequenceId = int(lineParts[2]) - 1
		sequenceLabels[sequenceId] = lineParts[1]
		if lineParts[1] == '=':
			voidSequenceId = sequenceId
		sequenceClassesLen[sequenceId] = len(lineParts[1].split('/'))

# Loads data
print('Loading data:', nbSequences, 'sequences (', nbSequenceClasses,'distincts),', nbMarkers, 'markers (', nbMarkerClasses,'distincts)', nbFeatures, 'features')
sequenceCount = 0
sequenceTargetsSet = []
sequenceFeaturesSet = sparse.lil_matrix((nbSequences, nbFeatures), dtype=numpy.bool)
for line in sys.stdin:
	lineParts = line.strip().split('\t')
	featureIds = [int(lineParts[i]) - 1 for i in range (2, len(lineParts))]
	for featureId in featureIds:
		sequenceFeaturesSet[sequenceCount, featureId] = True
	sequenceTargetsSet.append([int(markerId) for markerId in lineParts[1].split(',')])
	sequenceCount += 1
	if modeDebug and not sequenceCount%10000:
		print(' >', sequenceCount)

# Learning markers model
for marker in markerIds:
	print('Learning marker ' + marker)
	markerId = markerIds[marker]
	classWeights = None # None, auto
	sequencesClassifier = None
	markerTargetsSet = numpy.zeros(nbSequences, dtype=numpy.int)
	for i in range(nbSequences):
		if markerId + 1 in sequenceTargetsSet[i]:
			markerTargetsSet[i] = 1
	if learnAlgo == 'LogisticRegression':
		sequencesClassifier = linear_model.LogisticRegression(max_iter=10000)
		sequenceFeaturesSet = sequenceFeaturesSet.tocsr()
	elif learnAlgo == 'SVM':
		sequencesClassifier = svm.SVC(probability=True)
		sequenceFeaturesSet = sequenceFeaturesSet.tocsr()
	elif learnAlgo == 'SGD':
		sequencesClassifier = linear_model.SGDClassifier(loss = 'log')
		sequenceFeaturesSet = sequenceFeaturesSet.tocsr()
	sequencesClassifier.fit(sequenceFeaturesSet, markerTargetsSet)
	joblib.dump(sequencesClassifier, corpusModel + '/model_' + marker + '.txt')
print('Done')

