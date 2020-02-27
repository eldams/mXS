#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, os, re, math

lexicalFeatures = {}
for sentence in sys.stdin:
	for token in sentence.strip().split():
		tokenParts = token.split('/')
		if len(tokenParts) > 2 and not tokenParts[0].startswith('NE') and tokenParts[2] != '-':
			for lexicalFeature in tokenParts[2].split('+'):
				lexicalFeatures[lexicalFeature] = True
for lexicalFeature in lexicalFeatures:
	print(lexicalFeature)

