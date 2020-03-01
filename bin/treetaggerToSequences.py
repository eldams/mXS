#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, re, os

# Parameters
useDictionnaries = os.environ.get('DICO_USE')
useLists = True
splitSentencesPos = os.environ.get('SENTENCEPOS_USE')
modeUncapitalize = os.environ.get('UNCAPITALIZE')
annotationFormat = os.environ.get('ANNOTATION_FORMAT')
useSuffixes = False
useSegmentalsAny = False
useCasenFeatures = False
ignoreCase = False
binOutput = False
if len(sys.argv) == 3:
	binOutput = True

# Class Item
class Item:
	def __init__(self, p, it = False):
		self.parts = p
		self.isToken = it

# Class DictionaryNode
class DictionaryNode:
	def __init__(self):
		self.children = {}
		self.categories = {}
	def __repr__(self):
		return str(self)
	def __str__(self, lexem = ''):
		return self.toStr()
	def toStr(self, lexem = ''):
		str = ''
		if len(self.categories):
			str += lexem + ':' + ' '.join(self.categories.keys()) + '\n'
		if lexem:
			lexem += '|'
		for child in self.children:
			str += self.children[child].toStr(lexem + child)
		return str
	def addNodes(self, t, c):
		if(len(t)):
			token = t.pop(0)
			ambiguousDashTokens = token.split('=')
			for i in range(1, len(ambiguousDashTokens)):
				tokensNoDash = t[:]
				tokensNoDash.insert(0, '='.join(ambiguousDashTokens[i:]))
				tokensNoDash.insert(0, '='.join(ambiguousDashTokens[:i]))
				self.addNodes(tokensNoDash, c)
			token = token.replace('=', '-')
			if ignoreCase or modeUncapitalize:
				token = token.lower()
			if token not in self.children:
				self.children[token] = DictionaryNode()
			self.children[token].addNodes(t, c)
		else:
			for category in c:
				if category not in self.categories:
					self.categories[category] = True
	def applyDictionary(self, s, i, f):
		if i < len(s):
			item = s[i]
			if item.isToken and (modeUncapitalize or item.parts[2] != 'VER'):
				tokens = []
				for itemTokens in [item.parts[-1], item.parts[-2]]:
					for token in itemTokens.split('+'):
						token = token.replace('MXS_SLASH', '/')
						token = token.replace('MXS_PLUS', '+')
						token = token.replace('MXS_DASH', '-')
						token = token.replace('MXS_SPACE', ' ')
						if token not in tokens:
							tokens.append(token)
				categories = {}
				for token in tokens:
					if ignoreCase:
						token = token.lower()
					if token in self.children:
						childrenCategories = self.children[token].applyDictionary(s, i + 1, f)
						for category in childrenCategories:
							categories[category] = True
						for category in self.children[token].categories:
							categories[category] = True
				for category in categories:
					if not i in f:
						f[i] = {}
					f[i][category] = True
				return categories
			else:
				return self.applyDictionary(s, i + 1, f)
		return {}

# Dictionnaries (create dictionnary from Unitex : cat *.dic | iconv -f UTF-16LE -t UTF-8 | sed 's/\xEF\xBB\xBF//' | tr '\r' '\n' | sed -E '/^[ \t]*$/d' | sort | uniq)
dictionnaries = {}
dicospath = os.environ['DICOS_PATH']
def readDictionary(filename, dictionaryCoding, dictionnaryMapping = None):
	rootDictionaryNode = DictionaryNode()
	if dictionaryCoding == 'Unitex' and dictionnaryMapping:
		for dicoLine in open(dicospath+'/'+filename):
			dicoLineParts = re.match(r'(([^,]|\,)*),([^\.]|\.)*\.([^:]*)', dicoLine)
			if dicoLineParts:
				lexem = dicoLineParts.group(1)
				lexem = lexem.strip()
				lexem = lexem.replace('\\', '')
				lexem = lexem.replace('\'', '\' ')
				lexem = lexem.replace('\'', '\' ')
				tokens = lexem.split(' ')
				categories = {}
				dicoCategories = dicoLineParts.group(4).split('+')
				for category in dicoCategories:
					if category in dictionnaryMapping:
						categories[dictionnaryMapping[category]] = True
				if len(tokens) and len(categories):
					rootDictionaryNode.addNodes(tokens, categories)
	if dictionaryCoding == 'mxs':
		for dicoLine in open(dicospath+'/'+filename):
			dicoLineParts = dicoLine.strip().split('\t')
			if len(dicoLineParts) == 2:
				tokens = dicoLineParts[0].split(' ')
				categories = {}
				for category in dicoLineParts[1].split(','):
					categories[category] = True
				rootDictionaryNode.addNodes(tokens, categories)
	return rootDictionaryNode
import joblib
if useDictionnaries:
	dicospathjoblib = dicospath+'/dictionnaries.joblib'
	if os.path.isfile(dicospathjoblib):
		dictionnaries = joblib.load(dicospathjoblib)
	else:
		dictionnaries['CasEN'] = readDictionary('CasEN_en.dic', 'Unitex', {'Ensemble': 'COLL', 'Loi': 'PROD', 'Œuvre': 'PROD', 'ville': 'VILLE', 'Astronyme': 'ASTRO', 'Objet': 'OBJ', 'ToponymeAmbigu': 'TOPOA', 'Radio': 'MEDIA', 'Dynastie': 'DYN', 'Chaine': 'MEDIA', 'SiteInternet': 'MEDIA', 'Animateur': 'IND', 'Journal': 'MEDIA', 'Humour': 'IND', 'Volcan': 'GEO', 'Journaliste': 'IND', 'Produit': 'PROD', 'Surnom': 'SURNOM', 'Sportif': 'IND', 'Institution': 'INST', 'Religion': 'RELIG', 'Edifice': 'BAT', 'Logiciel': 'PROD', 'PartiPolitique': 'COLL', 'Geonyme': 'GEO', 'Marque': 'PROD', 'GroupeMusical': 'COLL', 'Monnaie': 'MON', 'Politique': 'POL', 'Acteur': 'IND', 'Sport': 'SPORT', 'Chanteur': 'IND', 'Oeuvre': 'PROD', 'Histoire': 'EVT', 'Supranational': 'SNAT', 'Ethnonyme': 'ETHNO', 'Pragmonyme': 'EVT', 'Spectacle': 'EVT', 'Animal': 'ANIM', 'Association': 'ASS', 'Entreprise': 'ENT', 'Emission': 'MEDIA', 'TV': 'MEDIA', 'Media': 'MEDIA', 'Commerce': 'COM', 'Organisation': 'ORG', 'Groupement': 'COLL', 'Pays': 'NAT', 'Collectif': 'COLL', 'Ergonyme': 'PROD', 'Hydronyme': 'HYDRO', 'Region': 'REG', 'Territoire': 'TER', 'Celebrite': 'IND', 'Individuel': 'IND', 'Anthroponyme': 'IND', 'Prenom': 'PREN', 'Profession': 'PRO', 'Hum': 'IND', 'Ville': 'VILLE', 'Toponyme': 'TOPO', 'Toponyme': 'TOPO', 'PR': 'NP'})
		if annotationFormat == 'Ester2' and useLists:
			dictionnaries['casen_lists'] = readDictionary('CasEN_lists_Ester2.dic', 'mxs')
		elif annotationFormat == 'Etape' and useLists:
			dictionnaries['casen_lists'] = readDictionary('CasEN_lists_Etape.dic', 'mxs')
		dictionnaries['time'] = readDictionary('time.dic', 'mxs')
		dictionnaries['quantities'] = readDictionary('quantities.dic', 'mxs')
		dictionnaries['jobs'] = readDictionary('jobs.dic', 'mxs')
		dictionnaries['locations'] = readDictionary('locations.dic', 'mxs')
		dictionnaries['organizations'] = readDictionary('organizations.dic', 'mxs')
		dictionnaries['politics'] = readDictionary('politics.dic', 'mxs')
		joblib.dump(dictionnaries, dicospathjoblib)

# Chunking (available tags: </AdP> <AdP> </AP> <AP> </COORD> <COORD> </NP> <NP> </PONCT:S> <PONCT:S> </PP> <PP> </s> <s> </Sint> <Sint> </Srel> <Srel> </Ssub> <Ssub> </VN> <VN> </VPinf> <VPinf> </VPpart> <VPpart>)
chunkingTagsFeatures = {'AdP': 'SA', 'AP': False, 'COORD': False, 'NP': 'SN', 'PONCT:S': False, 'PP': 'SP', 's': False, 'Sint': False, 'Srel': False, 'Ssub': False, 'VN': 'SV', 'VPinf': False, 'VPpart': False}
chunkingTags = []
for chunkingTag in chunkingTagsFeatures:
	chunkingTags.append(chunkingTag)
	chunkingTags.append('/'+chunkingTag)

# Function to get a unique item id
itemIds = {}
itemIdCounts = {}
itemIdHierarchy = {}
def getItemIds(itemParts):
	if not len(itemParts):
		return []
	else:
		parentItemIds = getItemIds(itemParts[:-1])
		itemName = '/'.join(itemParts)
		if itemName not in itemIds:
			itemIds[itemName] = len(itemIds) + 1
		itemId = itemIds[itemName]
		if not itemId in itemIdCounts:
			itemIdCounts[itemId] = 0
			itemIdHierarchy[itemId] = {itemId: True}
		itemIdCounts[itemId] += 1
		for parentItemId in parentItemIds:
			itemIdHierarchy[itemId][parentItemId] = True
		parentItemIds.append(itemId)
		return parentItemIds

# Function to output an item
def getBinTokens(itemParts, itemPrefix = []):
	if not len(itemParts):
		return [getItemIds(itemPrefix)[-1]]
	else:
		binTokens = []
		itemAlts = itemParts.pop(0)
		items = itemAlts.split('+')
		for item in items:
			itemPrefix.append(item)
			binTokens.extend(getBinTokens(itemParts[:], itemPrefix))
			itemPrefix.pop()
		return binTokens

# Function to output a sequence
def outputSequence(sequence):
	sequenceLen = len(sequence)
	if sequenceLen:
		sequenceDictionaryFeatures = {}
		for i in range(0, sequenceLen):
			if sequence[i].isToken:
				for dictionaryName in dictionnaries:
					dictionnaries[dictionaryName].applyDictionary(sequence, i, sequenceDictionaryFeatures)
		for i in range(0, sequenceLen):
			if sequence[i].isToken:
				dictionnaryFeatures = {}
				if useSegmentalsAny:
					dictionnaryFeatures['AD'] = True
				if i in sequenceDictionaryFeatures:
					for feature in sequenceDictionaryFeatures[i]:
						dictionnaryFeatures[feature] = True
				if len(dictionnaryFeatures):
					sequence[i].parts.insert(2, '+'.join(dictionnaryFeatures.keys()))
				else:
					sequence[i].parts.insert(2, '-')
		sequenceItems = []
		for i in range(0, sequenceLen):
			if binOutput:
				# For mining, remove null features
				sequence[i].parts = list(filter(lambda tokenPart: tokenPart != '-', sequence[i].parts))
				# For mining, removes surface form for tokens (but keeps lemma)
				if sequence[i].isToken:
					sequence[i].parts.pop()
				sequenceItems.append(getBinTokens(sequence[i].parts))
			else:
				sequenceItems.append('/'.join(sequence[i].parts))
		return sequenceItems

# Retrieves tabulated lines and builds corpus of sequences
corpus = []
sequence = []
neDataFeatures = {}
chunkingFeatures = {}
casenFeatures = []
for tokenLine in sys.stdin.readlines():
	if tokenLine:
		tokenLine = tokenLine.strip('\r\n\t ')
		if re.match(r'^<_[^>]*_>$', tokenLine):
			if not binOutput:
				sequence.append(Item([tokenLine]))
		elif re.match(r'^<sent/>$', tokenLine):
			corpus.append(outputSequence(sequence))
			chunkingFeatures = {}
			sequence = []
		elif re.match(r'^</?NE-[^>]*>$', tokenLine):
			sequence.append(Item(['NE', tokenLine]))
		elif re.match(r'^</?NEc-[^>]*>$', tokenLine):
			if useCasenFeatures:
				neDataFeatures = {}
				if tokenLine[1] == '/':
					casenFeatures.pop()
				else:
					casenFeatures.append(tokenLine[5:-1].split('.'))
				for casenFeaturesLevel in casenFeatures:
					for casenFeature in casenFeaturesLevel:
						neDataFeatures['CASEN-'+casenFeature] = True
			elif not binOutput:
				sequence.append(Item(['NEc', tokenLine]))
		elif re.match(r'^</?NEm-[^>]*>$', tokenLine):
			neMinedTag = tokenLine[1:-1]
			neMinedTagBegin = True
			if neMinedTag[0] == '/':
				neMinedTagBegin = False
				neMinedTag = neMinedTag[1:]
			if neMinedTagBegin:
				neDataFeatures[neMinedTag] = True
			elif neMinedTag in neDataFeatures:
				del neDataFeatures[neMinedTag]
		elif re.match('^</?[^>]*>$', tokenLine) and tokenLine[1:-1] in chunkingTags:
			chunkingTag = tokenLine[1:-1]
			chunkingTagBegin = True
			if chunkingTag[0] == '/':
				chunkingTagBegin = False
				chunkingTag = chunkingTag[1:]
			if chunkingTag in chunkingTagsFeatures and chunkingTagsFeatures[chunkingTag]:
				chunkingFeature = chunkingTagsFeatures[chunkingTag]
				if chunkingTagBegin:
					chunkingFeatures[chunkingFeature] = True
				elif chunkingFeature in chunkingFeatures:
					del chunkingFeatures[chunkingFeature]
		else:
			tokenLine = tokenLine.replace('/', 'MXS_SLASH')
			tokenLine = tokenLine.replace('+', 'MXS_PLUS')
			tokenLine = tokenLine.replace('-', 'MXS_DASH')
			tokenLine = tokenLine.replace(' ', 'MXS_SPACE')
			tokenLine = tokenLine.replace('|', '+')
			tokenParts = tokenLine.split('\t')
			if len(tokenParts) == 3:
				tokenParts = [tokenParts[1], tokenParts[2], tokenParts[0]]
				while tokenParts.count('<unknown>'):
					tokenParts.remove('<unknown>')
				mainCategory = tokenParts[0].split(':')[0]
				if tokenParts[0] == 'PRP:det':
					tokenParts[0] = 'PRPDET'
				if tokenParts[0].startswith('VER'):
					tokenParts[0] = 'VER'
				tokenParts[:1] = tokenParts[0].split(':')
				if tokenParts[0] == 'DET' and tokenParts[-1] in ['le', 'la', 'les', 'l\'']:
					tokenParts[:1] = ['DET', 'DEF']
				if tokenParts[0] in ['NAM', 'ABR']:
					tokenParts.insert(0, 'NAMABR')
					if binOutput:
						while tokenParts[-1] == tokenParts[-2]:
							tokenParts.pop()
				if tokenParts[0] == 'NUM' and tokenParts[1] == '@card@':
					digitsLen = len(tokenParts[-1])
					if digitsLen > 4:
						tokenParts.insert(2, 'DIGITS:MANY')
					else:
						tokenParts.insert(2, 'DIGITS:'+str(digitsLen))
						if digitsLen == 4:
							tokenParts.insert(3, 'PREF:'+tokenParts[-1][:2])
					tokenParts.append(tokenParts[-1])
				if useSuffixes and tokenParts[0] in ['NAMABR', 'NOM', 'VER']:
					lemmaUnicode = unicode(tokenParts[-2], 'utf-8')
					if len(lemmaUnicode) > 3:
						tokenParts.insert(-2, 'SUFF:'+lemmaUnicode[-3:].encode('utf-8'))
				neFeature = '-'
				if useSegmentalsAny or useCasenFeatures:
					neDataFeatures['AN'] = True
				if len(neDataFeatures):
					neFeature = '+'.join(neDataFeatures)
				tokenParts.insert(0, neFeature)
				chunkingFeature = '-'
				if useSegmentalsAny:
					chunkingFeatures['AC'] = True
				if len(chunkingFeatures):
					chunkingFeature = '+'.join(chunkingFeatures)
				tokenParts.insert(0, chunkingFeature)
				sequence.append(Item(tokenParts, True))
				if splitSentencesPos and mainCategory == 'SENT':
					corpus.append(outputSequence(sequence))
					chunkingFeatures = {}
					sequence = []
corpus.append(outputSequence(sequence))

# Output binary format files
itemSortedIds = {}
if binOutput:
	# Output translations
	itemSortedNb = 0
	for itemSortedId in sorted(itemIdCounts.items(), key=lambda a: a[1], reverse = True):
		itemSortedNb += 1
		itemSortedIds[itemSortedId[0]] = itemSortedNb
	binTranslations = []
	for itemName in itemIds:
		binTranslations.append(str(itemSortedIds[itemIds[itemName]])+' '+itemName)
	open(sys.argv[1], 'w').write('\n'.join(binTranslations)+'\n\n')
	# Output hierarchy
	binHierarchy = []
	for itemId in itemIdHierarchy:
		hierarchyIds = []
		for itemIdParent in itemIdHierarchy[itemId]:
			hierarchyIds.append(itemSortedIds[itemIdParent])
		hierarchyIdStrs = []
		for itemIdParent in sorted(hierarchyIds):
			hierarchyIdStrs.append(str(itemIdParent))
		binHierarchy.append(' '.join(hierarchyIdStrs))
	open(sys.argv[2], 'w').write('\n'.join(binHierarchy)+'\n\n')

# Output corpus
sequences = []
for sequence in corpus:
	if sequence:
		if binOutput:
			binSequence = []
			for item in sequence:
				itemAlt = []
				for itemId in item:
					itemAlt.append(str(itemSortedIds[itemId]))
				binSequence.append('+'.join(itemAlt))
			sequences.append(' '.join(binSequence))
		else:
			sequences.append(' '.join(sequence))
print('\n'.join(sequences)+'\n')

