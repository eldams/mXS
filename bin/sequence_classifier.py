#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import numpy, math, random, gc
from sklearn import svm, linear_model

class MatrixClassifier:
	def predict_proba(self, X):
		scores = numpy.dot(X, self.matrix)
		scores = numpy.maximum(scores, 0)
		for i in range(len(scores)):
			scores[i] /= numpy.sum(scores[i])
		return scores

# Class MatrixClassifierSVM
class MatrixClassifierSVM(MatrixClassifier):
	def __init__(self):
		self.svm = svm.SVC(probability=True)
	def fit(self, X, y):
		self.svm.fit(X, y)
	def predict_proba(self, X):
		return self.svm.predict_proba(X)

# Class MatrixClassifierLogit
class MatrixClassifierLogit(MatrixClassifier):
	def __init__(self):
		self.logit = linear_model.LogisticRegression()
	def fit(self, X, y):
		self.logit.fit(X, y)
	def predict_proba(self, X):
		return self.logit.predict_proba(X)

# Class MatrixClassifierMeanSquaredError
class MatrixClassifierMeanSquaredError(MatrixClassifier):
	def __init__(self, m, v = False, mi = 20, me = 0.001, a = 10):
		self.verbose = v
		self.matrix = m
		self.maxIteration = mi
		self.minError = me
		self.alpha = a
	def fit(self, X, y):
		# Prepare objective target values as a matrix
		yMatrix = numpy.zeros((X.shape[0], self.matrix.shape[1]), dtype=numpy.int)
		for i in range(len(y)):
			yMatrix[i, y[i]] = 1
		# Learn weights to minimize mean squared error
		matrixT = self.matrix.T
		XT = X.T
		yMatrixT = yMatrix.T
		iteration = 1
		errorSquared = self.minError
		while iteration <= self.maxIteration and errorSquared >= self.minError:
			if self.verbose:
				print('Iteration:', iteration)
			iteration += 1
			predictedMatrix = self.predict_proba(X)
			errorMatrix = (yMatrix - predictedMatrix).T
			errorSquared = numpy.sum(numpy.power(errorMatrix, 2))
			if self.verbose:
				print(' > squared error:', errorSquared)
			for i in range(len(matrixT)):
				error = numpy.mean(errorMatrix[i])
				for j in range(len(matrixT[i])):
					cov = numpy.dot(XT[j], yMatrixT[j])/len(X) - numpy.mean(XT[j])*numpy.mean(yMatrixT[j])
					matrixT[i][j] += self.alpha*error*cov

# Class MatrixClassifierPermutationError
class MatrixClassifierPermutationError(MatrixClassifier):
	def __init__(self, m, v = False, mi = 20, mr = 1, a = 1, pc = None):
		self.verbose = v
		self.matrix = m
		self.maxIteration = mi
		self.minRank = mr
		self.alpha = a
		self.permutationCosts = pc
	def fit(self, X, y):
		iterate = self.maxIteration
		if not iterate:
			return
		nbSequences = len(y)
		nbMarkerClasses = self.matrix.shape[0]
		nbSequenceClasses = self.matrix.shape[1]
		matrix = self.matrix
		matrixT = matrix.T
		if self.permutationCosts == None:
			self.permutationCosts = numpy.ones((nbSequenceClasses, nbSequenceClasses), dtype=numpy.float)
		permutationCosts = self.permutationCosts
		bestErrorSum = None
		iteration = 0
		while iterate:
			iteration += 1
			if self.verbose:
				print('Iteration:', iteration)
			predictedMatrix = self.predict_proba(X)
			errorRankSum = 0
			errorProbaSum = 0
			errorPermutationSum = 0
			permutationMarkers = numpy.zeros((nbSequenceClasses, nbSequenceClasses, nbMarkerClasses), dtype=numpy.float)
			for i in range(nbSequences):
				correctSequence = y[i]
				rankedSequences = [[j,  predictedMatrix[i][j]] for j in range(nbSequenceClasses)]
				rankedSequences = sorted(rankedSequences, key=lambda rs:rs[1], reverse=True)
				predictedSequence = rankedSequences[0][0]
				if correctSequence != predictedSequence:
					index = [k for (k, p) in rankedSequences].index(correctSequence)
					errorRankSum += index
					errorProbaSum += rankedSequences[0][1] - rankedSequences[index][1]
					correctPermutationCost = permutationCosts[correctSequence, predictedSequence]
					errorPermutationSum += correctPermutationCost
					maximumPermutationIndex = 0
					maximumPermutationCost = 0
					for j in range(index):
						permutationMarkers[correctSequence, rankedSequences[j][0]] += permutationCosts[correctSequence, rankedSequences[j][0]]*X[i]
			if self.verbose:
				print(' > mean rank:', 1 + float(errorRankSum)/nbSequences)
				print(' > mean proba error:', errorProbaSum/nbSequences)
				print(' > mean permutation error:', errorPermutationSum/nbSequences)
				print(' > l1 weight:', numpy.sum(abs(matrix)))
			if not bestErrorSum or errorPermutationSum < bestErrorSum:
				bestMatrix = matrix.copy()
				gc.collect()
				bestErrorSum = errorPermutationSum
				if self.verbose:
					print(' >> save best matrix')
			iterate = False
			if iteration <= self.maxIteration and errorRankSum > self.minRank:
				iterate = True
				gradientSum = 0
				for i in range(nbSequenceClasses):
					gradientTNMarkers = 0
					gradientFPMarkers = 0
					for j in range(nbSequenceClasses):
						if j != i:
							gradientTNMarkers += permutationMarkers[i, j]
							gradientFPMarkers += permutationMarkers[j, i]
					gradient = self.alpha*(gradientTNMarkers - gradientFPMarkers)/nbSequences
					matrixT[i] += gradient
					gradientSum += numpy.sum(abs(gradient))
				if self.verbose:
					print(' > gradient sum:', gradientSum)
		self.matrix = bestMatrix.copy()
		if self.verbose:
			print('Done')
