#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys

tokens = []
overlapSource = False
overlapParts = {}
for diffLine in sys.stdin.readlines():
	diffLine = diffLine.strip()
	if not diffLine:
		diffLine = '\n'
	if not overlapSource and diffLine.startswith('<<<<<<<'):
		overlapSource = 'system'
	elif overlapSource:
		if diffLine.startswith('|||||||'):
			overlapSource = 'common'
		elif diffLine.startswith('======='):
			overlapSource = 'tags'
		elif diffLine.startswith('>>>>>>>'):
			tokens.append(overlapParts['tags'])
			if not 'common' in overlapParts:
				tokens.append(overlapParts['system'])
			overlapSource = False
			overlapParts = {}
		else:
			if overlapSource in overlapParts:
				overlapParts[overlapSource] += ' '+diffLine
			else:
				overlapParts[overlapSource] = diffLine
	else:
		tokens.append(diffLine)
print(' '.join(tokens))

