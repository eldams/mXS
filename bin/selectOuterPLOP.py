#!/usr/bin/python

# Imports
import sys, re

levelIn = 0
levelOut = 0
tags = ['demonym', 'func.coll', 'func.ind', 'loc.add.phys', 'loc.adm.nat', 'loc.adm.reg', 'loc.adm.sup', 'loc.adm.town', 'loc.fac', 'loc.phys.geo', 'loc.phys.hydro', 'org.adm', 'org.ent', 'pers.coll', 'pers.ind', 'prod.art', 'prod.fin', 'prod.media', 'prod.object', 'prod.serv', 'prod.soft']
for line in sys.stdin:
	line = line.strip()
	line = re.sub(r' *(<[^>]*>) *', r' \1 ', line)
	outTokens = []
	for token in line.split(' '):
		if token.startswith('</NE-'):
			if levelIn == levelOut:
				outTokens.append(token)
				levelOut = 0
			levelIn -= 1
		elif token.startswith('<NE-'):
			levelIn +=1
			if levelOut == 0 and token[4:-1] in tags:
				levelOut = levelIn
				outTokens.append(token)
		else:
			outTokens.append(token)
	print re.sub(r'  +', ' ', ' '.join(outTokens))
