#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys

# Reads input and separate sentences to stdout and stderr
sentenceCount = 0
sentenceTokens = ''
for token in sys.stdin:
	tokenParts = token.strip().split('\t')
	sentenceTokens += tokenParts[0]+' '
	if len(tokenParts) > 1 and tokenParts[1] == 'SENT':
		if sentenceCount%3:
			sys.stderr.write(sentenceTokens+'\n')
		else:
			print(sentenceTokens)
		sentenceTokens = ''
		sentenceCount += 1

