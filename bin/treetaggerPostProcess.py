#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, re

# Open text input, find and apply rules
sentHasAux = False
verbForms = []
lastTag = None
for tokenLine in sys.stdin.readlines():
	tokenLine = tokenLine.strip('\r\n\t ')
	tokenParts = tokenLine.split('\t')
	if len(tokenParts) == 3 and tokenParts[1].startswith('VER'):
		verbPos = tokenParts[1]
		verbLemma = tokenParts[2]
		if not len(verbForms) and not sentHasAux and verbPos == 'VER:pper':
			print(tokenParts[0]+'\tADJ\t'+verbLemma)
		else:
			if not sentHasAux and verbLemma in ['être', 'avoir']:
				sentHasAux = True
			verbForms.append(tokenParts[0])
	else:
		if len(tokenParts) == 3:
			lastTag = tokenParts[1]

			if tokenParts[1] not in ['ADV', 'PRO:PER']:
				sentHasAux = False
		if len(verbForms):
			print(' '.join(verbForms)+'\t'+verbPos+'\t'+verbLemma)
			verbForms = []
		print(tokenLine)
if len(verbForms):
	print(' '.join(verbForms)+'\t'+verbPos+'\t'+verbLemma)
if not lastTag in ['SENT', 'PUN']:
	print('.\tSENT\t.')
	print('<_fs_> ')
