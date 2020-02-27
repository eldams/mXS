#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Merge tags from CasEN and sminer

import sys, re

applyMergeRules = False

def outputMergedMatches(matchParts):
	neContent = matchParts.group(2)
	nbSubRes = 1
	while nbSubRes:
		subRes = re.subn(r'<NEc-([^>]+)>(.*?)</NEc-\1>', outputMergedMatches, neContent)
		neContent = subRes[0]
		nbSubRes = subRes[1]
	if re.match(r'^( |<[^>]*>)*<NEm-([^>]+)>.*</NEm-\2>( |<[^>]*>)*$', neContent):
		return neContent
	casenFeatures = matchParts.group(1).lower().split('.')
	if not 'entity' in casenFeatures:
		return neContent
	casenEntityIndex = casenFeatures.index('entity')
	if casenEntityIndex == -1 or len(casenFeatures) <= casenEntityIndex + 1:
		return neContent
	casenCategory = casenFeatures[casenEntityIndex + 1]
	if not casenCategory in ['pers', 'org', 'loc', 'fonc', 'amount', 'time', 'prod']:
		return neContent
	if neContent.count('<NEm') != neContent.count('</NEm'):
		return neContent
	if neContent.count('<NEm'):
		neContent = re.sub(r'<NEm([^>]+)>(.*)</NEm\1>', r'<NEm-'+casenCategory+r'>\1</NEm-'+casenCategory+r'>', neContent, 1)
	else:
		neContent = '<NEm-'+casenCategory+'> '+neContent+' </NEm-'+casenCategory+'>'
	return neContent

for line in sys.stdin:
	if applyMergeRules:
		nbSubRes = 1
		while nbSubRes:
			subRes = re.subn(r'(<NE[^>]+>) +(</NE[^>]+>)', r'\2 \1', line)
			line = subRes[0]
			nbSubRes = subRes[1]
		nbSubRes = 1
		while nbSubRes:
			subRes = re.subn(r'(<NEm[^>]+>) +(<NEc[^>]+>)', r'\2 \1', line)
			line = subRes[0]
			nbSubRes = subRes[1]
		nbSubRes = 1
		while nbSubRes:
			subRes = re.subn(r'(</NEc[^>]+>) +(</NEm[^>]+>)', r'\2 \1', line)
			line = subRes[0]
			nbSubRes = subRes[1]
		nbSubRes = 1
		while nbSubRes:
			subRes = re.subn(r'<NEc-([^>]+)>(.*?)</NEc-\1>', outputMergedMatches, line)
			line = subRes[0]
			nbSubRes = subRes[1]
	line = re.sub(r'NEc/</?NEc-([^>]+)>', ' ', line)
	line = re.sub('  +', ' ', line)
	print(line.strip())

