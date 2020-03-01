#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, os, joblib, numpy, math
from scipy import sparse
from sklearn import linear_model, tree, svm, ensemble
import sequence_classifier

# Parameters
modeDebug = True
modeLoadMarkersModel = False
modeAdjustWeights = True
modeAdjustCosts = True
learnAlgo = 'LogisticRegression' # LogisticRegression, SVM, DecisionTreeClassifier, RandomForestClassifier, ExtraTreesClassifier
infosFilename = sys.argv[1]
corpusModel = os.environ.get('CORPUS_MODEL')
learnSequencesSteps = int(os.environ.get('LEARN_SEQ_STEPS', 0))
annotationFormat = os.environ.get('ANNOTATION_FORMAT')

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
markerCount = 0
markerTargetsSet = numpy.zeros(nbMarkers, dtype=numpy.int)
markerClassFrequencies = numpy.zeros(nbMarkerClasses)
markerFeaturesSet = sparse.lil_matrix((nbMarkers, nbFeatures), dtype=numpy.bool)
sequenceCount = 0
sequenceTargetsSet = numpy.zeros(nbSequences, dtype=numpy.int)
sequenceClassFrequencies = numpy.zeros(nbSequenceClasses)
sequenceFeaturesSet = sparse.lil_matrix((nbSequences, nbFeatures), dtype=numpy.bool)
sequenceMarkerIds = numpy.zeros((nbSequenceClasses, nbMarkerClasses), dtype=numpy.float)
for line in sys.stdin:
	lineParts = line.strip().split('\t')
	featureIds = [int(lineParts[i]) - 1 for i in range (2, len(lineParts))]
	sequenceId = int(lineParts[0]) - 1
	sequenceTargetsSet[sequenceCount] = sequenceId
	sequenceClassFrequencies[sequenceId] += 1
	for featureId in featureIds:
		sequenceFeaturesSet[sequenceCount, featureId] = True
	sequenceCount += 1
	for markerId in lineParts[1].split(','):
		markerId = int(markerId) - 1
		markerClassFrequencies[markerId] += 1
		markerTargetsSet[markerCount] = markerId
		for featureId in featureIds:
			markerFeaturesSet[markerCount, featureId] = True
		markerCount += 1
		sequenceMarkerIds[sequenceId, markerId] += 1
	if modeDebug and not sequenceCount%10000:
		print(' >', sequenceCount)

# Learning markers model
if modeLoadMarkersModel:
	markersClassifier = joblib.load(corpusModel + '/model_markers.txt', 'rb')
else:
	print('Learning markers')
	print(' - parametrizing weights')
	classWeights = None # None, auto
	if modeAdjustWeights and annotationFormat == 'Ester2' and not classWeights:
		classWeights = {}
		for line in open(infosFilename):
			lineParts = line.strip().split('\t')
			if lineParts[0] == 'mark':
				shortMarker = lineParts[1]
				targetId = int(lineParts[2]) - 1
				if shortMarker == '=':
					classWeights[targetId] = 1
				elif shortMarker[1:] in ['loc', 'org']:
					classWeights[targetId] = 30
				else:
					classWeights[targetId] = 20
	elif modeAdjustWeights and annotationFormat == 'Etape' and not classWeights:
		classWeights = {}
		for line in open(infosFilename):
			lineParts = line.strip().split('\t')
			if lineParts[0] == 'mark':
				shortMarker = lineParts[1]
				targetId = int(lineParts[2]) - 1
				if shortMarker == '=':
					classWeights[targetId] = 1
				elif shortMarker[1:] in ['kind', 'qualifier', 'time-modifier']:
					classWeights[targetId] = 30
				elif shortMarker[1:] in ['amount', 'time.date.abs', 'time.date.rel', 'time.hour.abs', 'time.hour.rel', 'func.ind', 'func.coll', 'org.ent', 'org.adm']:
					classWeights[targetId] = 10
				else:
					classWeights[targetId] = 5
	print(' - prepare classifier for', learnAlgo)
	markersClassifier = None
	if learnAlgo == 'LogisticRegression':
		#markersClassifier = linear_model.LogisticRegression(C=nbMarkers, penalty='l1', class_weight=classWeights)
		markersClassifier = linear_model.LogisticRegression(max_iter=10000)
		markerFeaturesSet = markerFeaturesSet.tocsr()
	elif learnAlgo == 'SVM':
		markersClassifier = svm.SVC(probability=True, C=nbMarkers, class_weight=classWeights)
		markerFeaturesSet = markerFeaturesSet.tocsr()
	elif learnAlgo == 'DecisionTreeClassifier':
		markersClassifier = tree.DecisionTreeClassifier(min_samples_split=10, min_density=1)
		markerFeaturesSet = markerFeaturesSet.toarray()
	elif learnAlgo == 'RandomForestClassifier':
		markersClassifier = ensemble.RandomForestClassifier(min_samples_split=10, min_density=1)
		markerFeaturesSet = markerFeaturesSet.toarray()
	elif learnAlgo == 'ExtraTreesClassifier':
		markersClassifier = ensemble.ExtraTreesClassifier(min_samples_split=10, min_density=1)
		markerFeaturesSet = markerFeaturesSet.toarray()
	print(' - fit dataset')
	markersClassifier.fit(markerFeaturesSet, markerTargetsSet)
	print(' - save model to file')
	joblib.dump(markersClassifier, corpusModel + '/model_markers.txt')

# Compute permutation cost as edit distance adapted to sequences
def getSequenceDistance(s1, s2):
	s1Len = len(s1)
	s2Len = len(s2)
	if not s1Len or not s2Len:
		return s1Len + s2Len
	sequenceDistance = 0
	# insertion
	insertionDistance = 1 + getSequenceDistance(s1[1:], s2)
	# deletion
	deletionDistance = 1 + getSequenceDistance(s1, s2[1:])
	# substitution
	if s1[0][0] != s2[0][0]:
		substitutionDistance = 2
	else:
		s1Cats = set(s1[0][1:].split('.'))
		s2Cats = set(s2[0][1:].split('.'))
		substitutionDistance = 1 - 2*float(len(s1Cats.intersection(s2Cats)))/(len(s1Cats) + len(s2Cats))
	substitutionDistance += getSequenceDistance(s1[1:], s2[1:])
	return min(insertionDistance, deletionDistance, substitutionDistance)

# Learning sequences model
print('Learning sequences')
print(' - prepare sequences classifier')
sequenceFeaturesSet = sequenceFeaturesSet.tocsr()
sequenceMarkerProbas = markersClassifier.predict_proba(sequenceFeaturesSet)
print(' - initializes markers to sequence matrix')
sequenceMarkerIds /= markerClassFrequencies
for sequenceId in sequenceClassesLen:
	sequenceMarkerIds[sequenceId] /= sequenceClassesLen[sequenceId]
print(' - fit dataset')
# sequence_classifierclasses: MatrixClassifierMeanSquaredError, MatrixClassifierPermutationError, MatrixClassifierSVM
permutationCosts = None
if modeAdjustCosts and annotationFormat in ['Ester2', 'Etape']:
	permutationCosts = numpy.ones((nbSequenceClasses, nbSequenceClasses), dtype=numpy.float)
	for i in range(nbSequenceClasses):
		if annotationFormat == 'Ester2' and (sequenceLabels[i].count('+') > 1 or sequenceLabels[i].count('-') > 1):
			permutationCosts[i] = 0
			permutationCosts.T[i] = 0
		permutationCosts[i][i] = 0
	for i in range(nbSequenceClasses):
		for j in range(i + 1, nbSequenceClasses):
			if permutationCosts[i, j]:
				sequenceItemsI = [ m for m in sequenceLabels[i].split('/') if m != '=' ]
				sequenceItemsJ = [ m for m in sequenceLabels[j].split('/') if m != '=' ]
				permutationCosts[i, j] = permutationCosts[j, i] = getSequenceDistance(sequenceItemsI, sequenceItemsJ)
#sequenceClassifier = sequence_classifier.MatrixClassifierPermutationError(sequenceMarkerIds.T, v= modeDebug, mi = learnSequencesSteps, pc = permutationCosts)
#sequenceClassifier = sequence_classifier.MatrixClassifierSVM()
sequenceClassifier = sequence_classifier.MatrixClassifierLogit()
sequenceClassifier.fit(sequenceMarkerProbas, sequenceTargetsSet)
print(' - save model to file')
joblib.dump(sequenceClassifier, corpusModel + '/model_sequences.txt')
