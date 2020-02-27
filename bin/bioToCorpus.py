#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys

corpusTokens = []
tokenLabelPrevious = 'null'
for tokenLine in sys.stdin.readlines():
	tokenLine = tokenLine.strip()
	tokenParts = tokenLine.split(' ')
	token = tokenParts[0]
	tokenLabel = tokenParts[-1]
	if not tokenLabel:
		if tokenLabelPrevious and tokenLabelPrevious not in ['O', 'null']:
			corpusTokens.append('</NE-'+tokenLabelPrevious[:-2]+'>')
		corpusTokens.append('<sent/>\n')
	else:
		if tokenLabel[-1] != 'I' and tokenLabelPrevious and tokenLabelPrevious not in ['O', 'null']:
			corpusTokens.append('</NE-'+tokenLabelPrevious[:-2]+'>')
		if tokenLabel[-1] == 'B':
			corpusTokens.append('<NE-'+tokenLabel[:-2]+'>')
		if tokenLabel[-1] == 'I' and tokenLabel[:-2] != tokenLabelPrevious[:-2]:
			if tokenLabelPrevious and tokenLabelPrevious not in ['O', 'null']:
				corpusTokens.append('</NE-'+tokenLabelPrevious[:-2]+'>')
			corpusTokens.append('<NE-'+tokenLabel[:-2]+'>')
	if token:
		corpusTokens.append(token)
	tokenLabelPrevious = tokenLabel
print(' '.join(corpusTokens))

