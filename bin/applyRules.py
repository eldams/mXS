#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports
import sys, os, re, math, itertools, time

# Parameters
modeDebug = False
modeDebugVerbose = False
modeSegmentals = os.environ.get('SMINER_SEGMENTAL')
corpusTmp = os.environ.get('CORPUS_TMP')
corpusModel = os.environ.get('CORPUS_MODEL')
modeUniqFeatures = True
modeBasicFeaturesBigrams = False
modeSpecificRules = False
hideNamabrFeature = False
hideLemmaFreqMin = False
outputWapitiLexicalFeatures = True
outputWapitiRulesFeatures = False
outputWapitiCasenFeatures = False
outputWapitiBegin = True
restrictCasenFeatures = None # None, 'none' or list of marker categories e.g. ['pers', 'org']
# Ester : ['pers', 'amount', 'time', 'org', 'fonc', 'prod']
# Etape : ['loc.oro', 'loc.add.elec', 'loc.phys.geo', 'prod.object', 'prod.award', 'kind', 'range-mark', 'week', 'month', 'century', 'demonym', 'name.nickname']
forceCasenMarkers = None #['pers'] # None or list of marker categories e.g. ['pers']
probaMode = 'mean' # independance, mean, wmean, hmean, max
labelMode = 'bayesian' # multiple, bayesian
labelModeBayesianMean = 'mean'  # mean, hmean
learnMode = None
learnAlgorithm = None
probaConditionalSmooth = 1
allowRootInSentence = True
forceMarkers = False
probaMinimum = 0.001 # Minimum probability cut-off
nBestSequences = 50 # Keep only n-best sequences for each token
nBestHypothesis = 20 # Keep only n-best hypothesis after each token
depthAllHypothesis = 3 # No n-best cut-off for this level of annotation (1 = root)
discountLength = False

# Argument paramters
arguments = sys.argv[:]
while len(arguments):
	argument = arguments.pop()
	if argument == '-d':
		modeDebug = True
	if argument == '-v':
		modeDebug = True
		modeDebugVerbose = True
	elif argument == '-ct':
		learnAlgorithm = 'Wapiti'
		learnMode = 'train'
	elif argument == '-cl':
		learnAlgorithm = 'Wapiti'
		learnMode = 'label'
	elif argument == '-mt':
		learnAlgorithm = 'MaxEnt'
		learnMode = 'train'
	elif argument == '-mh':
		learnAlgorithm = 'MaxEnt'
		learnMode = 'held'
	elif argument == '-ml':
		learnAlgorithm = 'MaxEnt'
		learnMode = 'label'
	elif argument == '-mbl':
		learnAlgorithm = 'MaxEntBin'
		learnMode = 'label'
	elif argument == '-st':
		learnAlgorithm = 'SciKit'
		learnMode = 'train'
	elif argument == '-sh':
		learnAlgorithm = 'SciKit'
		learnMode = 'held'
	elif argument == '-sl':
		learnAlgorithm = 'SciKit'
		learnMode = 'label'
	elif argument == '-slb':
		learnAlgorithm = 'SciKitBin'
		learnMode = 'label'
	elif argument == '-bl':
		learnAlgorithm = 'Bayes'
		learnMode = 'label'
	elif argument == '-rl':
		learnAlgorithm = 'Rules'
		learnMode = 'label'

# Describle possible nestings for annotations
annotationRoot = 'none'
annotationChildren = None
annotationFormat = os.environ.get('ANNOTATION_FORMAT')
annotationSelect = os.environ.get('SELECT_SCRIPT')
mxsProbaMin = os.environ.get('MXS_PROBAMIN')
if mxsProbaMin:
	probaMinimum = float(mxsProbaMin)
if annotationFormat == 'Etape' and annotationSelect and annotationSelect.endswith('selectOuterPLOP.py'):
	annotationChildren = {annotationRoot: '*'}
	probaMinimum = 0.05
elif annotationFormat == 'Etape':
	annotationEtapeEntites = ['event', 'pers.ind', 'pers.coll', 'time.date.abs', 'time.date.rel', 'time.hour.abs', 'time.hour.rel', 'loc.oro', 'loc.fac', 'loc.unk', 'loc.add.phys', 'loc.add.elec', 'loc.adm.town', 'loc.adm.reg', 'loc.adm.nat', 'loc.adm.sup', 'loc.phys.geo', 'loc.phys.hydro', 'loc.phys.astro', 'prod.object', 'prod.art', 'prod.media', 'prod.fin', 'prod.award', 'prod.serv', 'prod.doctr', 'prod.rule', 'prod.other', 'func.ind', 'func.coll', 'func.unk', 'org.ent', 'org.adm', 'amount']
	annotationEtapeComponentsTransverse = ['name', 'name.nickname', 'kind', 'extractor', 'demonym', 'demonym.nickname', 'qualifier', 'val', 'unit', 'range-mark', 'object']
	annotationEtapeComponentsSpecific = {
		'pers': ['name.last', 'name.first', 'name.middle', 'title'],
		'time.date': ['day', 'week', 'month', 'year', 'century', 'millenium', 'reference-era', 'time-modifier', 'amount'],
		'prod.award': ['award-cat'],
		'func.ind': ['org.adm', 'org.ent'],
		'org.adm': ['loc.adm.nat'],
		'org.ent': ['loc.adm.nat', 'loc.adm.town'],
		'title': ['func.ind'],
		'func.coll': ['org.ent'],
		'object': ['func.coll', 'pers.coll'],
	}
	if annotationSelect and annotationSelect.endswith('selectInner.sh'):
		annotationChildren = {annotationRoot: annotationEtapeComponentsTransverse[:]}
		for entityTypePrefix in annotationEtapeComponentsSpecific:
			annotationChildren[annotationRoot].extend(annotationEtapeComponentsSpecific[entityTypePrefix])
	else:
		annotationChildren = {annotationRoot: annotationEtapeEntites[:]}
		if not annotationSelect or not annotationSelect.endswith('selectOuter.sh'):
			for entity in annotationEtapeEntites:
				annotationChildren[entity] = []
				annotationChildren[entity].extend(annotationEtapeComponentsTransverse)
				for entityTypePrefix in annotationEtapeComponentsSpecific:
					if entity.startswith(entityTypePrefix):
						annotationChildren[entity].extend(annotationEtapeComponentsSpecific[entityTypePrefix])
elif annotationFormat == 'CoNLL2003':
	annotationChildren = {annotationRoot: '*'}

# Load MaxEnt models
maxEntModelMarkersB = None
maxEntModelMarkersE = None
if learnAlgorithm == 'MaxEnt' and learnMode in ['label', 'held']:
	from maxent import MaxentModel
	maxEntModelMarkersB = MaxentModel()
	maxEntModelMarkersB.load(corpusModel+'/model_markers-b.txt')
	maxEntModelMarkersE = MaxentModel()
	maxEntModelMarkersE.load(corpusModel+'/model_markers-e.txt')
maxEntModelMarkers = {}
if learnAlgorithm == 'MaxEntBin' and learnMode in ['label', 'held']:
	from maxent import MaxentModel
	for marker in open(corpusModel + '/markers.lst', 'rb'):
		marker = marker.strip()
		model = MaxentModel()
		model.load(corpusModel+'/model_' + marker + '.txt')
		maxEntModelMarkers[marker] = model

# Load SciKit models
sciKitModelMarkers = None
sciKitModelSequences = None
maxFeatureId = 0
featureIds = {}
shortMarkerIds = {}
idShortMarkers = {}
sequenceMarkerIds = {}
idSequenceMarkers = {}
if learnAlgorithm in ['SciKit', 'SciKitBin'] and learnMode in ['label', 'held']:
	import joblib, numpy
	for line in open(corpusModel + '/model_infos.tsv'):
		line = line.strip()
		lineParts = line.split('\t')
		if lineParts[0] == 'feat':
			featureId = int(lineParts[2])
			if featureId > maxFeatureId:
				maxFeatureId = featureId
			featureIds[lineParts[1]] = featureId
		if lineParts[0] == 'mark':
			idShortMarkers[int(lineParts[2])] = lineParts[1]
		if lineParts[0] == 'seq':
			idSequenceMarkers[int(lineParts[2])] = lineParts[1]
	if learnAlgorithm == 'SciKit':
		from sklearn import linear_model
		sciKitModelMarkers = joblib.load(corpusModel + '/model_markers.txt')
		import sequence_classifier
		sciKitModelSequences = joblib.load(corpusModel + '/model_sequences.txt')
	else:
		from sklearn import linear_model
		sciKitModelMarkers = {}
		for marker in idShortMarkers.values():
			sciKitModelMarkers[marker] = joblib.load(corpusModel + '/model_' + marker + '.txt')

# Load Wapiti lexical features
lexicalFeatures = {}
if learnAlgorithm == 'Wapiti':
	for lexicalFeature in open(corpusTmp + '/train_lex.txt'):
		lexicalFeatures[lexicalFeature.strip()] = 0

# Create or append an element inside a dictionnary of sets
def createOrAddDictSet(d, k, e):
	if not k in d:
		d[k] = set()
	d[k].add(e)

# Create or append an element inside a dictionnary of lists
def createOrAppendDictList(d, k, e):
	if not k in d:
		d[k] = []
	d[k].append(e)

# Shorten marker
def shortenMarker(s):
	shortMarkerParts = re.match('NE/<(/?)NE-([^>]*)>$', s)
	if shortMarkerParts:
		shortMarker = '+'
		if shortMarkerParts.group(1) == '/':
			shortMarker = '-'
		shortMarker += shortMarkerParts.group(2)
		return shortMarker

# Expand marker
def expandMarker(s):
	marker = 'NE/<'
	if s[0] == '-':
		marker += '/'
	marker += 'NE-'
	marker += s[1:]
	marker += '>'
	return marker

# Class rule
class Rule:
	def __init__(self, s, i, su, c, f, fw):
		self.string = s.strip()
		self.items = []
		self.markers = {}
		self.proba = 0
		self.probaWithoutTarget = 0
		self.node = None
		self.id = i
		self.support = su
		self.confidence = c
		self.frequency = f
		self.frequencyWithoutTarget = fw
	def __repr__(self):
		return str(self)
	def __str__(self):
		return self.string
	def addMarker(self, i, m):
		if not m.beginMarker:
			for j in self.markers:
				for marker in self.markers[j]:
					if j < i and marker.beginMarker and marker.categoryMarker == m.categoryMarker:
						marker.endingIndexes.append(i - j)
		createOrAddDictSet(self.markers, i, m)
		m.rule = self
		m.ruleIndex = i
	def addItem(self, i):
		self.items.append(i)
	def isMoreSpecificThan(self, r, i):
		rLen = len(r.items)
		selfLen = len(self.items)
		if i < 0 or i + rLen > selfLen:
			return False
		isIdentical = True
		for j in range(rLen):
			if self.items[i + j] != r.items[j]:
				itemCategories = self.items[i + j].split('/')
				rItemCategories = r.items[j].split('/')
				if len(rItemCategories) > len(itemCategories):
					return False
				for k in range(len(rItemCategories)):
					categorySet = itemCategories[k].split('+')
					rCategorySet = rItemCategories[k].split('+')
					for category in rCategorySet:
						if category not in categorySet:
							return False
				isIdentical = False
		return rLen != selfLen or not isIdentical or self.id < r.id

# Class rule node
class RuleNode:
	def __init__(self, item = None):
		self.childrens = {}
		self.rules = set()
		self.id = None
		self.item = item
	def addRule(self, rule):
		self.rules.add(rule)
		rule.node = self
		if not self.id or self.id > rule.id:
			self.id = rule.id
	def getOrCreateChildren(self, children):
		if not children in self.childrens:
			self.childrens[children] = RuleNode(children)
		return self.childrens[children]

# Class rule node match
class RuleNodeMatch:
	def __init__(self, node = None, parent = None):
		self.node = node
		self.parent = parent
		self.length = 1
	def getMarkerPosition(self, i, l):
		p = 0
		if i >= l:
			p += self.length
		if l == 1:
			return p
		else:
			return p + self.parent.getMarkerPosition(i, l - 1)

# Class rule marker
class RuleMarker:
	def __init__(self, i, of = 1, rf = 0):
		self.item = i
		self.frequency = of
		self.rootFrequency = rf
		self.rule = None
		self.ruleIndex = 0
		self.feature = None
		self.shortMarker = shortenMarker(i)
		self.beginMarker = self.shortMarker[0] == '+'
		self.categoryMarker = self.shortMarker[1:]
		self.endingIndexes = []
	def __repr__(self):
		return str(self)
	def __str__(self):
		if self.frequency and self.rule:
			return self.item+','+str(self.frequency)+','+str(self.rule.id)
		else:
			return self.item
	def getProba(self, noRootProba = False):
		if noRootProba:
			return self.noRootProba
		return self.proba

# Class hypothesis
class Hypothesis:
	def __init__(self):
		self.items = {}
		self.lproba = 0
		self.nbMarkers = 0
		self.markerIndexes = []
		self.endingIndexes = []
	def __repr__(self):
		return str(self)
	def __str__(self):
		return str(self.lproba)+','+str(self.items)+','+str(self.markerIndexes)+','+str(self.endingIndexes)
	def clone(self):
		clone = Hypothesis()
		for i in self.items:
			for item in self.items[i]:
				createOrAppendDictList(clone.items, i, item)
		clone.lproba = self.lproba
		clone.markerIndexes = self.markerIndexes[:]
		clone.endingIndexes = self.endingIndexes[:]
		return clone
	def addItem(self, i, k):
		createOrAppendDictList(self.items, k, i)
		self.nbMarkers += 1
	def addNewItem(self, i, k, p):
		self.addItem('NEW/' + i, k)
		self.lproba += math.log(p)
		self.markerIndexes.append(k)
	def addNewItems(self, l, k, p):
		for i in l:
			self.addItem('NEW/' + i, k)
		self.lproba += math.log(p)
		self.markerIndexes.append(k)

# Function to calculate probability from markers
def calculateProbaFromMarkers(priorProba, markers, noRootProba = False):
	if modeDebugVerbose:
		for marker in markers:
			print('Bayes marker:', marker.item, priorProba*marker.getProba(noRootProba)/marker.rule.probaWithoutTarget)
	proba = 0
	if probaMode == 'independance':
		proba = priorProba
		for marker in markers:
			proba *= marker.getProba(noRootProba)/marker.rule.probaWithoutTarget
	elif probaMode == 'mean':
		for marker in markers:
			proba += marker.getProba(noRootProba)/marker.rule.probaWithoutTarget
		proba *= priorProba/len(markers)
	elif probaMode == 'wmean':
		weights = 0
		for marker in markers:
			markerWeight = math.log(marker.rule.proba)
			weights += markerWeight
			proba += markerWeight*marker.getProba(noRootProba)/marker.rule.probaWithoutTarget
		proba *= priorProba/weights
	elif probaMode == 'hmean':
		for marker in markers:
			proba += marker.rule.probaWithoutTarget/marker.getProba(noRootProba)
		proba = priorProba/proba
	elif probaMode == 'max':
		bestFactor = 0
		for marker in markers:
			if marker.getProba(noRootProba)/marker.rule.proba > bestFactor:
				bestFactor = marker.getProba(noRootProba)/marker.rule.probaWithoutTarget
		proba = priorProba*bestFactor
	return proba

# Function to retrieve rule features
previousFeatures = None
dicoFreqs = None
dicoFreqMin = 2
if hideLemmaFreqMin and annotationFormat == 'CoNLL2003':
	dicoFreqs = {}
	for line in open(os.environ['DICOS_PATH']+'/CoNLL-train.freqs'):
		(token, freq) = line.strip().split('\t')
		dicoFreqs[token] = int(freq)
def getBasicFeatures(inc = None, chunk = None, lexical = None, pos = None, lemma = None, token = None, columnFeatures = False):
	global previousFeatures
	posParts = pos.split('/')
	if hideNamabrFeature and posParts[0] in ['NAMABR', 'NNP']:
		lemma = posParts[0]
	if dicoFreqs and (token not in dicoFreqs or dicoFreqs[token] < hideLemmaFreqMin):
		lemma = 'UNK'
	if columnFeatures:
		pos1 = posParts[0]
		pos2 = 'NOPOS'
		pos3 = 'NOPOS'
		if posParts > 1:
			pos2 = '/'.join(posParts[:2])
			if posParts > 2:
				pos3 = '/'.join(posParts[:3])
		currentFeatures = [lemma, pos1, pos2, pos3, lexical]
		if not previousFeatures:
			previousFeatures = ['-', '-', '-', '-', '-']
		returnFeatures = previousFeatures.extend(currentFeatures)
		previousFeatures = currentFeatures
		return returnFeatures
	else:
		features = ['LEM_'+lemma]
		for i in range(0, len(posParts)):
			features.append('POS_'+'/'.join(posParts[:i+1]))
		for lexicalPart in lexical.split('+'):
			if lexicalPart != '-':
				features.append('LEX_'+lexicalPart)
		returnFeatures = []
		if previousFeatures:
			returnFeatures.extend(['P_'+feature for feature in previousFeatures])
			if modeBasicFeaturesBigrams:
				for feature in features:
					for previousFeature in previousFeatures:
						returnFeatures.append('P_'+previousFeature+'_C_'+feature)
		returnFeatures.extend(['C_'+feature for feature in features])
		previousFeatures = features
		return returnFeatures

# Function to retrieve rule features
def getRuleFeatures(ruleMarkers = None, columnFeatures = False):
	features = []
	ruleMarkerFeatures = {}
	if ruleMarkers:
		for marker in ruleMarkers:
			createOrAddDictSet(ruleMarkerFeatures, marker.feature, marker.shortMarker)
	for markerFeature in ruleMarkerFeatures:
		if markerFeature in ruleMarkerFeatures:
			markerValue = ''
			if columnFeatures:
				markerValue = ':1'
			elif not modeUniqFeatures:
				markerValue = '_'+','.join(sorted(ruleMarkerFeatures[markerFeature]))
			features.append('m' + markerFeature + markerValue)
		elif columnFeatures:
			features.append('m' + markerFeature + ':0')
	return features

# Function to retrieve lexical features
def getLexicalFeatures(lexicalItems):
	features = []
	lexicalItems = lexicalItems.split('+')
	for lexicalFeature in lexicalFeatures:
		if lexicalFeature in lexicalItems:
			features.append('l'+lexicalFeature)
			lexicalFeatures[lexicalFeature] += 1
		else:
			features.append('l'+lexicalFeature+':0')
	return features

# Function to retrieve CasEN features
def getCasenFeatures(casenMarkers = None):
	if restrictCasenFeatures == 'none':
		return []
	casenFeatures = {}
	for casenMarker in casenMarkers:
		if casenMarker[5] == '/':
			casenFeaturePrefix = 'c_-'
			casenMarker = casenMarker[10:-1]
		else:
			casenFeaturePrefix = 'c_+'
			casenMarker = casenMarker[9:-1]
		if restrictCasenFeatures:
			isSelected = False
			casenMarkerFeature = casenMarker
			if 'entity' in casenMarker:
				casenMarkerFeature = casenMarker[casenMarker.index('entity') + 7:]
			for casenFeature in restrictCasenFeatures:
				if casenMarkerFeature.startswith(casenFeature):
					isSelected = True
			if not isSelected:
				casenMarker = None
		if casenMarker:
			casenMarker = casenMarker.replace('n.', '')
			casenMarker = casenMarker.replace('entity.', '')
			casenMarkerParts = casenMarker.split('.')
			casenMarkerPartsLen = len(casenMarkerParts)
			for i in range(casenMarkerPartsLen):
				casenFeatures[casenFeaturePrefix+casenMarkerParts[i]] = True
				casenFeatures[casenFeaturePrefix+'.'.join(casenMarkerParts[0:i+1])] = True
	return casenFeatures.keys()

# Function to retrieve StanfordNER features
def getStanfordNERFeatures(stanfordNERMarkers = None):
	stanfordNERFeatures = {}
	for stanfordNERMarker in stanfordNERMarkers:
		stanfordNERFeatures = {}
		if stanfordNERMarker[5] == '/':
			stanfordNERPrefix = 's_-'
			stanfordNERMarker = stanfordNERMarker[10:-1]
		else:
			stanfordNERPrefix = 's_+'
			stanfordNERMarker = stanfordNERMarker[9:-1]
		stanfordNERFeatures[stanfordNERPrefix+stanfordNERMarker] = True
	return stanfordNERFeatures.keys()

# Function to retrieve CasEN short markers
def getCasenForcedMarkers(casenMarkers = None):
	shortMarkers = {}
	for casenMarker in casenMarkers:
		if casenMarker[5] == '/':
			direction = '-'
			casenMarker = casenMarker[10:-1]
		else:
			direction = '+'
			casenMarker = casenMarker[9:-1]
		casenFeatures = casenMarker.split('.')
		if len(casenFeatures) and 'entity' in casenFeatures:
			entityIndex = casenFeatures.index('entity')
			neCategory = casenFeatures[entityIndex + 1]
			if neCategory and neCategory in forceCasenMarkers:
				shortMarkers[direction + neCategory] = True
	return shortMarkers.keys()

# Function to get or create id for a feature
def getFeatureId(featureName):
	if featureName not in featureIds:
		featureIds[featureName] = str(len(featureIds) + 1)
	return featureIds[featureName]

# Function to get or create id for a marker
def getShortMarkerId(shortMarker):
	if shortMarker not in shortMarkerIds:
		shortMarkerIds[shortMarker] = str(len(shortMarkerIds) + 1)
	return shortMarkerIds[shortMarker]

# Function to get or create id for a markers sequence
def getSequenceMarkerId(sequenceMarker):
	if sequenceMarker not in sequenceMarkerIds:
		sequenceMarkerIds[sequenceMarker] = str(len(sequenceMarkerIds) + 1)
	return sequenceMarkerIds[sequenceMarker]

# Function to calculate parents items from token
def getTokenParents(tokenParts):
	if not len(tokenParts):
		return {}
	tokenPart = tokenParts.pop(0)
	tokenParents = getTokenParents(tokenParts)
	disjunctionTokenParts = tokenPart.split('+')
	newTokenParents = {}
	for disjunctionTokenPart in disjunctionTokenParts:
		for tokenParent in tokenParents:
			newTokenParents[disjunctionTokenPart+'/'+tokenParent] = True
		newTokenParents[disjunctionTokenPart] = True
	return newTokenParents

# Function to retrieve subsequences from a sequence
def getSequenceSubsequences(sequence):
	sequenceItems = sequence.split('/')
	sequenceItemsLen = len(sequenceItems)
	if sequenceItemsLen == 1:
		return {sequence: True}
	subsequences = {}
	for i in range(0, sequenceItemsLen):
		subsequenceItems = []
		if i:
			subsequenceItems = sequenceItems[:i]
		if i < sequenceItemsLen:
			subsequenceItems.extend(sequenceItems[i+1:])
		subsequence = '/'.join(subsequenceItems)
		for subsubsequence in getSequenceSubsequences(subsequence):
			subsequences[subsubsequence] = True
		subsequences[subsequence] = True
	return subsequences

# Function to compute probabilities of sequence from binarized markers
def getSequenceMarkerProbaFromBin(availableMarkers, markers = [], proba = 1):
	sequenceMarkers = {}
	if not len(availableMarkers):
		for sequence in itertools.permutations(markers):
			sequenceMarkers[sequence] = proba
	else:
		(marker, markerProba) = availableMarkers.pop()
		if proba*markerProba > probaMinimum:
			sequenceMarkers.update(getSequenceMarkerProbaFromBin(availableMarkers[:], markers + [marker], proba*markerProba))
		if proba*(1 - markerProba) > probaMinimum:
			sequenceMarkers.update(getSequenceMarkerProbaFromBin(availableMarkers[:], markers[:], proba*(1 - markerProba)))
	return sequenceMarkers

# Function to retrieve sequences from binarized markers
def getSequenceMarkerProbaFromShortMarkers(shortMarkers):
	sequenceMarkers = {}
	sortedMarkersE = sorted([e for e in shortMarkers.items() if e[0][0] == '-'], key = lambda e: max(e[1], 1 - e[1]), reverse = True)
	if not len(sortedMarkersE):
		sortedMarkersE = [('=', 1)]
	for (sequenceE, probaE) in getSequenceMarkerProbaFromBin(sortedMarkersE).items():
		sortedMarkersB = sorted([e for e in shortMarkers.items() if e[0][0] == '+'], key = lambda e: max(e[1], 1 - e[1]), reverse = True)
		if not len(sortedMarkersB):
			sortedMarkersB = [('=', 1)]
		for (sequenceB, probaB) in getSequenceMarkerProbaFromBin(sortedMarkersB).items():
			sequence = [m for m in sequenceE + sequenceB if m != '=']
			if probaE*probaB > probaMinimum:
				sequenceStr = '/'.join(sequence)
				if not sequenceStr:
					sequenceStr = '='
				sequenceMarkers[sequenceStr] = probaE*probaB
	return sequenceMarkers

# Open rules file, retrieve rules and probabilities, build rule nodes
anyFrequency = 0
anyMarkerFrequency = 0
shortMarkerFrequency = {}
shortMarkerSequenceProbas = {}
ruleCount = 0
rules = []
ruleNodeCount = 0
mxsFeatures = {}
rootRuleNode = RuleNode()
minimumSupport = 0
if os.getenv('SMINER_MINIMUM_SUPPORT'):
	minimumSupport = float(os.getenv('SMINER_MINIMUM_SUPPORT'))/100000
minimumConfidence = 0
if os.getenv('SMINER_MINIMUM_CONFIDENCE'):
	minimumConfidence = float(os.getenv('SMINER_MINIMUM_CONFIDENCE'))/100
for ruleStr in open(sys.argv[-1]):
	ruleStrParts = re.match(r'(.*) \(freq:([0-9]*)\)$', ruleStr)
	if ruleStrParts:
		frequency = int(ruleStrParts.group(2))
		if ruleStrParts.group(1) == 'ANY':
			anyFrequency = frequency
		elif ruleStrParts.group(1) == 'NE':
			anyMarkerFrequency = frequency
	else:
		ruleStrParts = re.match(r'(.*) \(freq:([0-9]*),freqts:([0-9]*)\)$', ruleStr)
		if ruleStrParts:
			frequency = int(ruleStrParts.group(2))
			frequencyTargetSequence = int(ruleStrParts.group(3))
			markers = ruleStrParts.group(1).split()
			shortMarkersUnique = {}
			shortMarkersSequence = []
			for marker in markers:
				shortMarker = shortenMarker(marker)
				shortMarkersUnique[shortMarker] = True
				shortMarkersSequence.append(shortMarker)
			if len(shortMarkersSequence) == 1:
				shortMarkerFrequency[shortMarker] = frequency
			if frequencyTargetSequence:
				shortMarkersSequenceStr = '/'.join(shortMarkersSequence)
				shortMarkerSequenceProbas[shortMarkersSequenceStr] = {'freq': frequency, 'freqts': frequencyTargetSequence, 'markers': {}}
				for shortMarker in shortMarkersUnique:
					shortMarkerSequenceProbas[shortMarkersSequenceStr]['markers'][shortMarker] = True
		else:
			ruleStrParts = re.search(r'\(supp:(.*),conf:(.*),freq:(.*),nfreq:(.*),id:(.*)\)$', ruleStr)
			support = float(ruleStrParts.group(1))
			confidence = float(ruleStrParts.group(2))
			if ruleStrParts and support > minimumSupport and confidence >= minimumConfidence:
				ruleCount += 1
				rule = Rule(ruleStr, int(ruleStrParts.group(5)), support, confidence, int(ruleStrParts.group(3)), int(ruleStrParts.group(4)))
				ruleNode = rootRuleNode
				itemCount = 0
				previousTagType = None
				ruleIsComplete = True
				for item in ruleStr.split()[:-1]:
					itemParts = re.match(r'(.*)\(ofreq:(.*),rfreq:(.*)\)$', item)
					if itemParts:
						itemTag = itemParts.group(1)
						rule.addMarker(itemCount, RuleMarker(itemTag, int(itemParts.group(2)), int(itemParts.group(3))))
						if ruleIsComplete:
							if not previousTagType and itemTag[4] != '/':
								previousTagType = itemTag[4:-1]
							elif previousTagType and itemTag[4] == '/' and itemTag[5:-1] == previousTagType:
								previousTagType = None
							else:
								ruleIsComplete = False
					else:
						ruleNode = ruleNode.getOrCreateChildren(item)
						if not ruleNode.id:
							ruleNodeCount += 1
						rule.addItem(item)
						itemCount += 1
				if learnMode != 'label' or learnAlgorithm != 'Rules' or (ruleIsComplete and not previousTagType):
					rules.append(rule)
					ruleNode.addRule(rule)

# Set short markers probabilities for models
priorShortMarkerProbas = {}
for shortMarker in shortMarkerFrequency:
	priorShortMarkerProbas[shortMarker] = float(shortMarkerFrequency[shortMarker])/float(anyFrequency)
priorAnyMarkerProba = float(anyMarkerFrequency)/float(anyFrequency)
priorShortMarkerProbas['='] = 1 - priorAnyMarkerProba

# Set rules and markers prior probabilities
for rule in rules:
	rule.proba = float(rule.frequency + probaConditionalSmooth)/float(anyFrequency - len(rule.items) + probaConditionalSmooth)
	rule.probaWithoutTarget = float(rule.frequencyWithoutTarget + probaConditionalSmooth)/float(anyFrequency - len(rule.items) + len (rule.markers) + probaConditionalSmooth)
	for markerIndex in rule.markers:
		for marker in rule.markers[markerIndex]:
			marker.proba = float(marker.frequency + probaConditionalSmooth)/float(shortMarkerFrequency[marker.shortMarker] + probaConditionalSmooth)
			marker.noRootProba = float(rule.frequencyWithoutTarget - marker.rootFrequency + probaConditionalSmooth)/float(anyFrequency - anyMarkerFrequency + probaConditionalSmooth)
			if modeUniqFeatures:
				marker.feature = 'r'+str(rule.node.id)+'.m'+str(markerIndex)
			else:
				marker.feature = 'r'+str(rule.id)+'.m'+str(markerIndex)
			mxsFeatures[marker.feature] = True

# Set prior conditional probabilities for models
for shortMarkerSequence in shortMarkerSequenceProbas:
	for shortMarker in shortMarkerSequenceProbas[shortMarkerSequence]['markers']:
		shortMarkerSequenceProbas[shortMarkerSequence]['markers'][shortMarker] = (float(shortMarkerSequenceProbas[shortMarkerSequence]['freqts']) + probaConditionalSmooth)/(float(shortMarkerFrequency[shortMarker]) + probaConditionalSmooth)

if modeDebug:
	print('Rules:', ruleCount)
	print('Rule nodes:', ruleNodeCount)
	print('Prior markers:')
	for shortMarker in priorShortMarkerProbas:
		print(' >', shortMarker, priorShortMarkerProbas[shortMarker])
	print('Conditional markers:')
	for shortMarkerSequence in shortMarkerSequenceProbas:
		print(' >', shortMarkerSequence, shortMarkerSequenceProbas[shortMarkerSequence])

# Open text input, find and apply rules
sequenceLines = 0
markerLines = 0
heldStats = {'items' : 0, 'detect-cr' : 0, 'reco-c' : 0, 'reco-r' : 0, 'reco-cr' : 0, 'disamb-c' : 0, 'disamb-r' : 0, 'disamb-cr' : 0, 'reco-sr': 0, 'disamb-sr': 0, 'disamb-sra': 0}
for sentence in sys.stdin:
	sentence = sentence.strip()
	if modeDebug:
		print('\nSentence:', sentence)
	sentenceItems = []
	sentenceInfos = {}
	sentenceInc = {}
	sentenceChunk = {}
	sentenceLexical = {}
	sentencePOS = {}
	sentenceLemmas = {}
	sentenceTokens = {}
	tokenParents = {}
	ruleNodeMatches = {}
	sentenceMarkers = {}
	sentenceRuleMarkers = {}
	sentenceCasenMarkers = {}
	sentenceStanfordNERMarkers = {}
	sentenceShortMarkerProbas = {}
	sentenceSequenceMarkerProbas = {}
	shortMarkerProbas = {}
	sentenceEscaping = False
	sentenceEscapes = {}
	existingMarkers = {}
	bestAnnotationMarker = None
	ri = 0 # Current resolved index
	annotationHypothesis = {annotationRoot: Hypothesis()}
	# For each index in sentence
	tokens = sentence.split()
	tokensLen = len(tokens)
	for tokenIndex in range(tokensLen):
		if True or tokenIndex < tokensLen:
			# Examines current token
			token = tokens[tokenIndex]
			if modeDebug:
				print('-------------------------------')
				print('Search rules for token', tokenIndex, token, ':')
			itemIndex = len(sentenceItems)
			# If escape token, just store it
			if sentenceEscaping or re.match(r'<_', token):
				sentenceEscaping = True
				if re.search(r'_>$', token):
					sentenceEscaping = False
				createOrAppendDictList(sentenceEscapes, itemIndex, token)
			# If marker token, just store it
			elif shortenMarker(token):
				createOrAppendDictList(existingMarkers, itemIndex, RuleMarker(token))
			# If CasEN marker token, store it as a feature
			elif re.match('NEc/</?NEc-[^>]*>', token):
				createOrAppendDictList(sentenceCasenMarkers, itemIndex, token)
			# If StanfordNER marker token, store it as a feature
			elif re.match('NEs/</?NEs-[^>]*>', token):
				createOrAppendDictList(sentenceStanfordNERMarkers, itemIndex, token)
			# If other token, select corresponding rules
			else:
				# Stores token, POS
				sentenceItems.append(token)
				sentenceInfos[itemIndex] = token
				tokenParts = []
				while token:
					tokenMatches = re.match('(([^/]|</|/>)*)/(.*)', token)
					if tokenMatches:
						tokenParts.append(tokenMatches.group(1))
						token = tokenMatches.group(3)
					else:
						tokenParts.append(token)
						token = False
				if annotationFormat == 'CoNLL2003':
					sentenceChunk[itemIndex] = tokenParts[0]
					sentenceInc[itemIndex] = '-'
					sentenceLexical[itemIndex] = tokenParts[1]
					sentenceLemmas[itemIndex] = tokenParts[-1]
					sentenceTokens[itemIndex] = tokenParts[-1]
					sentencePOS[itemIndex] = '/'.join(tokenParts[2:-1])
				else:
					sentenceChunk[itemIndex] = tokenParts[0]
					sentenceInc[itemIndex] = tokenParts[1]
					sentenceLexical[itemIndex] = tokenParts[2]
					sentenceLemmas[itemIndex] = tokenParts[-2]
					sentenceTokens[itemIndex] = tokenParts[-1]
					sentencePOS[itemIndex] = '/'.join(tokenParts[3:-2])
				# Search rules
				newRuleNodeMatches = {}
				tokenParts = list(filter(lambda tokenPart: tokenPart != '-', tokenParts))
				previousTokenParents = tokenParents
				tokenParents = getTokenParents(tokenParts)
				if modeDebugVerbose:
					print('Token categories:', tokenParents)
				for tokenParent in tokenParents:
					for startingIndex in ruleNodeMatches:
						for ruleMatch in ruleNodeMatches[startingIndex]:
							checkSegments = True
							previousTokenParent = ruleMatch.node.item
							if modeSegmentals and previousTokenParent and tokenParent == ruleMatch.node.item:
								ruleMatch.length += 1
								createOrAddDictSet(newRuleNodeMatches, startingIndex + 1, ruleMatch)
								checkSegments = False
							if modeSegmentals and checkSegments and previousTokenParent:
								if checkSegments:
									tokenParentParts = tokenParent.split('/')
									for i in range(0, len(tokenParentParts)):
										tokenParentParent = '/'.join(tokenParentParts[0:i + 1])
										if not previousTokenParent.startswith(tokenParentParent) and tokenParentParent in previousTokenParents:
											checkSegments = False
								if checkSegments:
									previousTokenParentParts = previousTokenParent.split('/')
									for i in range(0, len(previousTokenParentParts)):
										previousTokenParentParent = '/'.join(previousTokenParentParts[0:i + 1])
										if not tokenParent.startswith(previousTokenParentParent) and previousTokenParentParent in tokenParents:
											checkSegments = False
							if checkSegments:
								if tokenParent in ruleMatch.node.childrens:
									createOrAddDictSet(newRuleNodeMatches, startingIndex + 1, RuleNodeMatch(ruleMatch.node.childrens[tokenParent], ruleMatch))
							elif modeDebugVerbose:
								print('Avoid continuing segmental rule (', tokenParent, ' vs ', previousTokenParent, ')')
					if tokenParent in rootRuleNode.childrens:
						if not modeSegmentals or tokenParent not in previousTokenParents:
							createOrAddDictSet(newRuleNodeMatches, 0, RuleNodeMatch(rootRuleNode.childrens[tokenParent]))
						elif modeDebugVerbose:
							print('Avoid starting segmental rule (', tokenParent, ')')
				ruleNodeMatches = newRuleNodeMatches
				# Records markers for applying rules
				for j in ruleNodeMatches:
					for ruleNodeMatch in ruleNodeMatches[j]:
						for rule in ruleNodeMatch.node.rules:
							for k in rule.markers:
								mi = ruleNodeMatch.getMarkerPosition(k, len(rule.items))
								if modeSegmentals and modeDebugVerbose:
									print('Segmental rule:', rule, k, mi)
								for marker in rule.markers[k]:
									markerIndex = itemIndex - j + mi
									if modeSegmentals and markerIndex - 1 in sentenceMarkers and marker in sentenceMarkers[markerIndex - 1]:
										if modeDebugVerbose:
											print('Remove previous marker:', marker, markerIndex - 1)
										sentenceMarkers[markerIndex - 1].remove(marker)
									createOrAddDictSet(sentenceMarkers, markerIndex, marker)
									if modeDebugVerbose:
										print('Added rule', rule, markerIndex, marker)
		# Tries to resolve markers for fully determined local context
		maxRuleNodeMatchesIndex = 0
		if tokenIndex == tokensLen - 1:
			maxRuleNodeMatchesIndex = -2
		elif ruleNodeMatches:
			maxRuleNodeMatchesIndex = max(ruleNodeMatches.keys())
		while ri < itemIndex - maxRuleNodeMatchesIndex:
			# Finds markers for current resolved index
			if modeDebug:
				print('-------------------------------')
				print('Resolve token', ri, ':',)
				if ri in sentenceTokens:
					print(sentenceTokens[ri], '(', sentenceInfos[ri], ')')
				else:
					print('(end sentence)')
				if ri in sentenceMarkers:
					print('Proposed markers:')
					proposedMarkers = {}
					for marker in sentenceMarkers[ri]:
						proposedMarkers[marker.shortMarker] = True
					print('Rule triggered markers:' + ','.join(proposedMarkers))
					if modeDebugVerbose:
						for marker in sentenceMarkers[ri]:
							print('Rule triggered:', marker.rule)
			# Retrieve and append existing markers to all hypothesis
			if ri in existingMarkers:
				if modeDebug:
					print('Existing markers:', existingMarkers[ri])
				for marker in existingMarkers[ri]:
					for categoryPath in annotationHypothesis:
						annotationHypothesis[categoryPath].addItem(marker.item, ri)
			# Calculate or retrieve markers proba
			markers = {}
			shortMarkerProbas = {}
			if ri in sentenceMarkers:
				for marker in sentenceMarkers[ri]:
					createOrAddDictSet(markers, marker.shortMarker, marker)
			if modeDebugVerbose:
				print('Rule markers:')
				for shortMarker in markers:
					print('Marker', shortMarker, ':')
					for marker in markers[shortMarker]:
						print('- rule:', marker.rule.string)
			# Discard non-specific rules
			if modeSpecificRules:
				specificMarkers = {}
				for shortMarker in markers:
					for marker in markers[shortMarker]:
						markerIsSpecificAll = True
						markerIsSpecificShortMarker = True
						for otherShortMarker in markers:
							for otherMarker in markers[otherShortMarker]:
								if otherMarker.rule.isMoreSpecificThan(marker.rule, otherMarker.ruleIndex - marker.ruleIndex):
									markerIsSpecificAll = False
									if otherShortMarker == shortMarker:
										markerIsSpecificShortMarker = False
									if modeDebugVerbose:
										print('Rule discarded:', marker.rule.string, '(vs: ', otherMarker.rule.string, ', for short marker:',markerIsSpecificShortMarker ,')')
									if not markerIsSpecificShortMarker:
										break
						if markerIsSpecificShortMarker:
							createOrAddDictSet(specificMarkers, shortMarker, marker)
							if markerIsSpecificAll:
								createOrAddDictSet(specificMarkers, '=', marker)
				markers = specificMarkers
			# List rules
			if learnMode:
				for shortMarker in markers:
					for marker in markers[shortMarker]:
						if modeDebugVerbose and ri in sentenceTokens:
							print('Add:', sentenceTokens[ri], marker, marker.rule)
						createOrAddDictSet(sentenceRuleMarkers, ri, marker)
			# Prediction part
			if not learnMode or learnAlgorithm in ['MaxEnt', 'MaxEntBin', 'SciKit', 'SciKitBin', 'Bayes'] and learnMode in ['label', 'held']:
				# MaxEnt features for labelling or heldout file
				learnFeatures = None
				modelMarkerProbaLevel = []
				if learnMode:
					learnFeatures = []
					if ri in sentenceTokens:
						learnFeatures = getBasicFeatures(sentenceInc[ri], sentenceChunk[ri], sentenceLexical[ri], sentencePOS[ri], sentenceLemmas[ri], sentenceTokens[ri])
					if ri in sentenceRuleMarkers:
						learnFeatures.extend(getRuleFeatures(sentenceRuleMarkers[ri]))
					if ri in sentenceCasenMarkers:
						learnFeatures.extend(getCasenFeatures(sentenceCasenMarkers[ri]))
					if ri in sentenceStanfordNERMarkers:
						learnFeatures.extend(getStanfordNERFeatures(sentenceStanfordNERMarkers[ri]))
					if modeDebugVerbose:
						print('Local features:', learnFeatures)
				# Dynamic programming for prediction
				if not learnMode or learnMode in ['label', 'held']:
					# Retrieve learned probabilities
					unavoidableMarkers = {}
					for categoryPath in annotationHypothesis:
						for shortMarkerCategory in categoryPath.split('/')[1:]:
							unavoidableMarkers['-'+shortMarkerCategory] = True
					unavoidableMarkers = unavoidableMarkers.keys()
					shortMarkerProbas = {}
					sequenceMarkerProbas = {}
					if learnMode and learnAlgorithm == 'Bayes':
						allMarkers = []
						sumProbas = 0
						for shortMarker in markers:
							sequenceMarkerProbas[shortMarker] = calculateProbaFromMarkers(priorShortMarkerProbas[shortMarker], markers[shortMarker])
							allMarkers.extend(markers[shortMarker])
							sumProbas += sequenceMarkerProbas[shortMarker]
						if len(allMarkers):
							sequenceMarkerProbas['='] = calculateProbaFromMarkers(priorShortMarkerProbas['='], allMarkers, True)
							sumProbas += sequenceMarkerProbas['=']
							for shortMarker in sequenceMarkerProbas:
								sequenceMarkerProbas[shortMarker] /= sumProbas
						else:
							sequenceMarkerProbas['='] = 1
						sequenceMarkerProbaSum = sum(sequenceMarkerProbas.values())
						for sequenceMarker in sequenceMarkerProbas:
							sequenceMarkerProbas[sequenceMarker] /= sequenceMarkerProbaSum
					if learnMode and learnAlgorithm == 'MaxEnt':
						sequenceMarkerProbas = {}
						modelMarkerProbasE = maxEntModelMarkersE.eval_all(learnFeatures)
						modelMarkerProbasB = maxEntModelMarkersB.eval_all(learnFeatures)
						for modelMarkerProbaE in modelMarkerProbasE:
							shortMarkerE = modelMarkerProbaE[0]
							probaE = modelMarkerProbaE[1]
							if probaE > probaMinimum:
								sequenceMarkerE = ''
								shortMarkerProbas[shortMarkerE] = probaE
								if shortMarkerE != '-=':
									sequenceMarkerE = '-' + '/-'.join(shortMarkerE[1:].split(','))
								for modelMarkerProbaB in modelMarkerProbasB:
									shortMarkerB = modelMarkerProbaB[0]
									probaB = modelMarkerProbaB[1]
									if probaB > probaMinimum:
										sequenceMarker = sequenceMarkerE
										shortMarkerProbas[shortMarkerB] = probaB
										if shortMarkerB != '+=':
											if len(sequenceMarker):
												sequenceMarker += '/'
											sequenceMarker += '+' + '/+'.join(shortMarkerB[1:].split(','))
										if len(sequenceMarker):
											sequenceMarkerProbas[sequenceMarker] = probaE*probaB
						if '-=' in shortMarkerProbas and '+=' in shortMarkerProbas:
							sequenceMarkerProbas['='] = shortMarkerProbas['-=']*shortMarkerProbas['+=']
						else:
							sequenceMarkerProbas['='] =  probaMinimum
						sequenceMarkerProbaSum = sum(sequenceMarkerProbas.values())
						for sequenceMarker in sequenceMarkerProbas:
							sequenceMarkerProbas[sequenceMarker] /= sequenceMarkerProbaSum
					sciKitDataLine = None
					if learnMode and learnAlgorithm in ['SciKit', 'SciKitBin']:
						sciKitDataLine = numpy.zeros(maxFeatureId)
						for featureName in learnFeatures:
							if featureName in featureIds:
								sciKitDataLine[featureIds[featureName] - 1] = 1
					if learnMode and learnAlgorithm == 'SciKit':
						modelMarkerProbas = sciKitModelMarkers.predict_proba([sciKitDataLine])[0]
						for i in range(len(modelMarkerProbas)):
							shortMarkerProbas[idShortMarkers[i + 1]] = modelMarkerProbas[i]
						modelSequenceProbas = sciKitModelSequences.predict_proba([modelMarkerProbas])[0]
						for i in range(len(modelSequenceProbas)):
							sequence = idSequenceMarkers[i + 1]
							proba = modelSequenceProbas[i]
							if sequence == '=' or proba > probaMinimum:
								sequenceMarkerProbas[sequence] = proba
					if learnMode and learnAlgorithm in ['MaxEntBin', 'SciKitBin']:
						if learnAlgorithm == 'MaxEntBin':
							for marker in maxEntModelMarkers:
								modelMarkerProbas = maxEntModelMarkers[marker].eval_all(learnFeatures)
								proba = dict(modelMarkerProbas)['1']
								if proba > probaMinimum:
									shortMarkerProbas[marker] = min(proba, 1 - probaMinimum)
						if learnAlgorithm == 'SciKitBin':
							for marker in idShortMarkers.values():
								modelMarkerProbas = sciKitModelMarkers[marker].predict_proba([sciKitDataLine])[0]
								proba = modelMarkerProbas[1]
								if proba > probaMinimum:
									shortMarkerProbas[marker] = min(proba, 1 - probaMinimum)
						sequenceMarkerProbas = getSequenceMarkerProbaFromShortMarkers(shortMarkerProbas)
					newShortMarkerProbas = {}
					if learnMode and (not '=' in sequenceMarkerProbas or not sequenceMarkerProbas['=']):
						sequenceMarkerProbas['='] = probaMinimum
					if modeDebug:
						print('Markers probabilities:', sorted(shortMarkerProbas.items(), key=lambda pair:pair[1], reverse=True))
						print('Sequence probabilities:', sorted(sequenceMarkerProbas.items(), key=lambda pair:pair[1], reverse=True)[:10])
					# Records markers probabilities for held-out file
					if learnMode == 'held':
						sentenceShortMarkerProbas[ri] = shortMarkerProbas
						sentenceSequenceMarkerProbas[ri] = sequenceMarkerProbas
					# Creates or replace hypothesis for solutions using closing and opening markers
					elif labelMode == 'bayesian':
						if not allowRootInSentence and len(annotationHypothesis) > 1 and annotationRoot in annotationHypothesis:
							del annotationHypothesis[annotationRoot]
						# Examines probable markers sequences
						newAnnotationHypothesis = {}
						newAnnotationHypothesisLProbas = {}
						noMarkerLproba = math.log(sequenceMarkerProbas['='])
						del sequenceMarkerProbas['=']
						if not forceMarkers:
							for categoryPath in annotationHypothesis:
								newAnnotationHypothesisLProbas[categoryPath] = annotationHypothesis[categoryPath].lproba + noMarkerLproba
						sequenceMarkerProbasSorted = sorted(sequenceMarkerProbas.items(), key=lambda pair:pair[1])
						reverseCategoryPathTree = {}
						for categoryPath in annotationHypothesis:
							reverseCategoryPathNode = reverseCategoryPathTree
							categoryPathParents = categoryPath.split('/')
							while categoryPathParents:
								categoryPathParent = categoryPathParents.pop()
								if not categoryPathParent in reverseCategoryPathNode:
									reverseCategoryPathNode[categoryPathParent] = {}
								reverseCategoryPathNode = reverseCategoryPathNode[categoryPathParent]
						bestHypothesisSearch = True
						rootHypothesisSearch = True
						while len(sequenceMarkerProbasSorted) and sequenceMarkerProbasSorted[-1][1] and (bestHypothesisSearch or rootHypothesisSearch):
							sequenceMarker, sequenceMarkerProba = sequenceMarkerProbasSorted.pop()
							sequenceMarkerLProba = math.log(sequenceMarkerProba)
							shortMarkers = sequenceMarker.split('/')
							shortMarkers.reverse()
							categoryPathNode = reverseCategoryPathTree
							removedCategories = []
							while categoryPathNode and shortMarkers and shortMarkers[-1][0] == '-':
								shortMarker = shortMarkers.pop()
								shortMarkerCategory = shortMarker[1:]
								if shortMarkerCategory in categoryPathNode:
									removedCategories.append(shortMarkerCategory)
									categoryPathNode = categoryPathNode[shortMarkerCategory]
								else:
									categoryPathNode = None
							categoryPathChildren = []
							if categoryPathNode:
								if bestHypothesisSearch:
									categoryPathChildren = [[[], categoryPathNode]]
								elif rootHypothesisSearch and not len(shortMarkers) and annotationRoot in categoryPathNode:
									categoryPathChildren = [[[], {annotationRoot: {}}]]
								removedCategoryPath = None
								if len(removedCategories):
									removedCategories.reverse()
									removedCategoryPath = '/'.join(removedCategories)
							while len(categoryPathChildren):
								newCategoryPathChildren = []
								for baseCategories, categoryPathNode in categoryPathChildren:
									baseCategoryShortMarkers = shortMarkers[:]
									for category in categoryPathNode:
										newBaseCategories = baseCategories[:]
										newBaseCategories.insert(0, category)
										newCategoryPathChildren.append([newBaseCategories, categoryPathNode[category]])
									if len(baseCategories) and baseCategories[0] == annotationRoot:
										newCategoryPathParents =  baseCategories[:]
										while newCategoryPathParents and baseCategoryShortMarkers:
											shortMarker = baseCategoryShortMarkers.pop()
											shortMarkerCategory = shortMarker[1:]
											newCategoryPathParent = newCategoryPathParents[-1]
											if not annotationChildren or newCategoryPathParent in annotationChildren and annotationChildren[newCategoryPathParent] and ('*' in annotationChildren[newCategoryPathParent] or shortMarkerCategory in annotationChildren[newCategoryPathParent]):
												newCategoryPathParents.append(shortMarkerCategory)
											else:
												newCategoryPathParents = None
										if newCategoryPathParents:
											oldCategoryPath = baseCategories[:]
											if removedCategoryPath:
												oldCategoryPath.append(removedCategoryPath)
											oldCategoryPath = '/'.join(oldCategoryPath)
											newCategoryPath = '/'.join(newCategoryPathParents)
											newCategoryPathLproba = None
											if newCategoryPath in newAnnotationHypothesisLProbas:
												newCategoryPathLproba = newAnnotationHypothesisLProbas[newCategoryPath]
											updatedAnnotationPathLproba = annotationHypothesis[oldCategoryPath].lproba + sequenceMarkerLProba
											if modeDebug:
												print('Test annotation path', oldCategoryPath, sequenceMarker, newCategoryPath, newCategoryPathLproba, updatedAnnotationPathLproba)
											if not newCategoryPathLproba or updatedAnnotationPathLproba > newCategoryPathLproba:
												markers = []
												for shortMarker in sequenceMarker.split('/'):
													markers.append(expandMarker(shortMarker))
												newAnnotationHypothesis[newCategoryPath] = annotationHypothesis[oldCategoryPath].clone()
												newAnnotationHypothesis[newCategoryPath].addNewItems(markers, ri, sequenceMarkerProba)
												newAnnotationHypothesisLProbas[newCategoryPath] = updatedAnnotationPathLproba
												if modeDebug:
													print('Updates', newCategoryPath, markers, newAnnotationHypothesis[newCategoryPath].lproba, sequenceMarkerProba)
								categoryPathChildren = newCategoryPathChildren
							if len(sequenceMarkerProbasSorted):
								bestHypothesisSearch = sequenceMarkerProbasSorted[-1][1] > probaMinimum or len(newAnnotationHypothesis) < nBestHypothesis
								rootHypothesisSearch = annotationRoot in newAnnotationHypothesis
						# Store hypothesis that have not been updated
						if not forceMarkers:
							for categoryPath in annotationHypothesis:
								if categoryPath not in newAnnotationHypothesis:
									newAnnotationHypothesis[categoryPath] = annotationHypothesis[categoryPath]
									newAnnotationHypothesis[categoryPath].lproba += noMarkerLproba
									if modeDebugVerbose:
										print('No update for', categoryPath, newAnnotationHypothesis[categoryPath].lproba)
						annotationHypothesis = newAnnotationHypothesis
						if modeDebugVerbose:
							print('Hypothesis after updates:')
							for categoryPath in annotationHypothesis:
								print('-', categoryPath, ':', annotationHypothesis[categoryPath])
					# If threshold to keep best hypothesis apply
					if discountLength:
						for categoryPath, hypothesis in annotationHypothesis.items():
							if categoryPath != '/' and len(hypothesis.markerIndexes):
								lastMarkerIndex = max(hypothesis.markerIndexes)
								if ri > lastMarkerIndex:
									hypothesis.lproba += math.log(10.0/(10 + ri - lastMarkerIndex))
					# If threshold to keep best hypothesis apply
					if nBestHypothesis and len(annotationHypothesis) > nBestHypothesis:
						newAnnotationHypothesis = {}
						nHypothesis = 0
						for categoryPath, hypothesis in sorted(annotationHypothesis.items(), key=lambda h: h[1].lproba, reverse = True):
							if nHypothesis <= nBestHypothesis or len(categoryPath.split('/')) <= depthAllHypothesis:
								newAnnotationHypothesis[categoryPath] = hypothesis
							nHypothesis += 1
						annotationHypothesis = newAnnotationHypothesis
						if modeDebug:
							print('Only keep best and depth:')
							for categoryPath in annotationHypothesis:
								print('-', categoryPath, ':', annotationHypothesis[categoryPath])
			if learnAlgorithm == 'Rules' and learnMode == 'label':
				for shortMarker in markers:
					for marker in markers[shortMarker]:
						if not marker.beginMarker and bestAnnotationMarker and marker.rule == bestAnnotationMarker.rule:
							annotationHypothesis[annotationRoot].addNewItems([bestAnnotationMarker.item], bestAnnotationIndex, marker.rule.proba)
							annotationHypothesis[annotationRoot].addNewItems([marker.item], ri, marker.rule.proba)
							bestAnnotationMarker = None
							if modeDebug:
								print('End best annotation rule:', marker.categoryMarker)
				for shortMarker in markers:
					for marker in markers[shortMarker]:
						if marker.beginMarker and (not bestAnnotationMarker or marker.rule.proba > bestAnnotationMarker.rule.proba):
							bestAnnotationMarker = marker
							bestAnnotationIndex = ri
							if modeDebug:
								print('Begin best annotation rule:', marker.categoryMarker, marker.rule.proba)
			# Moves to next resolution index
			ri += 1
	# Create output sentence with escapes and markers
	output = []
	sentenceItemsLen = len(sentenceItems)
	if not learnMode or learnAlgorithm in ['MaxEnt', 'MaxEntBin', 'SciKit', 'SciKitBin', 'Bayes', 'Rules'] and learnMode == 'label':
		if not annotationRoot in annotationHypothesis:
			annotationRootHypothesis = None
			annotationRootProba = None
			anyMarkerLProba = math.log(probaMinimum)
			for categoryPath in annotationHypothesis:
				categories = categoryPath.split('/')
				if not annotationRootProba or annotationHypothesis[categoryPath].lproba + (len(categories) - 1)*anyMarkerLProba > annotationRootProba:
					annotationRootHypothesis = annotationHypothesis[categoryPath].clone()
					categories.reverse()
					categories.pop()
					for category in categories:
						annotationRootHypothesis.addNewItem(expandMarker('-'+category), sentenceItemsLen, probaMinimum)
					annotationRootProba = annotationRootHypothesis.lproba
					if modeDebug:
						print('Find forced root:', categoryPath, len(categories), annotationRootProba)
			annotationHypothesis[annotationRoot] = annotationRootHypothesis
		for i in range(sentenceItemsLen + 1):
			closingMarkers = []
			openingMarkers = []
			if i in annotationHypothesis[annotationRoot].items:
				for marker in annotationHypothesis[annotationRoot].items[i]:
					if '</' in marker:
						closingMarkers.append(marker)
					else:
						openingMarkers.append(marker)
			output.append(' '.join(closingMarkers))
			if i in sentenceCasenMarkers:
				output.append(' '.join(sentenceCasenMarkers[i]))
			if i in sentenceStanfordNERMarkers:
				output.append(' '.join(sentenceStanfordNERMarkers[i]))
			if i in sentenceEscapes:
				output.append(' '.join(sentenceEscapes[i]))
			output.append(' '.join(openingMarkers))
			if i < sentenceItemsLen:
				output.append(sentenceItems[i])
		if len(output):
			if modeDebug:
				print('Output:')
			print(' '.join(output))
	elif learnAlgorithm in ['MaxEnt', 'MaxEntBin', 'SciKit', 'SciKitBin'] and learnMode == 'held':
		for i in range(sentenceItemsLen + 1):
			existingShortMarkers = []
			existingSequenceMarker = '='
			heldStats['items'] += 1
			if i in existingMarkers:
				existingSequenceMarker = []
				for marker in existingMarkers[i]:
					existingSequenceMarker.append(marker.shortMarker)
					if not marker.shortMarker in existingShortMarkers:
						existingShortMarkers.append(marker.shortMarker)
				existingSequenceMarker = '/'.join(existingSequenceMarker)
			if i in sentenceSequenceMarkerProbas:
				sequenceMarkerRank = len(idSequenceMarkers)
				sentenceSequenceMarkerProbasSorted = None
				if i in sentenceSequenceMarkerProbas:
					sentenceSequenceMarkerProbasSorted = sorted(sentenceSequenceMarkerProbas[i].items(), key=lambda pair:pair[1], reverse=True)
					sentenceSequenceMarkerProbasSorted = [sentenceSequenceMarkerProba[0] for sentenceSequenceMarkerProba in sentenceSequenceMarkerProbasSorted]
					if existingSequenceMarker in sentenceSequenceMarkerProbasSorted:
						sequenceMarkerRank = sentenceSequenceMarkerProbasSorted.index(existingSequenceMarker) + 1
				heldStats['reco-sr'] += sequenceMarkerRank
				if existingSequenceMarker != '=' or sentenceSequenceMarkerProbasSorted and sentenceSequenceMarkerProbasSorted[0] != '=':
					heldStats['disamb-sr'] += sequenceMarkerRank
					heldStats['disamb-sra'] += 1
			predictedShortMarkers = []
			if i in sentenceShortMarkerProbas:
				for predictedShortMarker in sorted(sentenceShortMarkerProbas[i].items(), key=lambda pair:pair[1], reverse=True):
					predictedShortMarkers.append(predictedShortMarker[0])
			existingShortMarkersLen = len(existingShortMarkers)
			predictedShortMarkersLen = len(predictedShortMarkers)
			if not existingShortMarkersLen:
				heldStats['reco-c'] += 1
				heldStats['reco-r'] += 1
				if not predictedShortMarkersLen or predictedShortMarkers[0] == '=':
					heldStats['detect-cr'] += 1
					heldStats['reco-cr'] += 1
			else:
				heldStats['reco-c'] += existingShortMarkersLen
				heldStats['reco-r'] += min(existingShortMarkersLen, predictedShortMarkersLen)
				heldStats['disamb-c'] += existingShortMarkersLen
				heldStats['disamb-r'] += min(existingShortMarkersLen, predictedShortMarkersLen)
				if predictedShortMarkersLen:
					if predictedShortMarkers[0] != '=':
						heldStats['detect-cr'] += 1
					for predictedShortMarker in predictedShortMarkers[0:existingShortMarkersLen]:
						if predictedShortMarker in existingShortMarkers:
							heldStats['reco-cr'] += 1
							heldStats['disamb-cr'] += 1
	elif learnMode == 'train' or learnAlgorithm == 'Wapiti':
		currentCategories = []
		currentCasenEntities = ['O']
		currentMarkerLevel = 0
		for i in range(sentenceItemsLen + 1):
			if learnMode == 'label':
				standOffs = []
				if i in sentenceEscapes:
					standOffs.extend(sentenceEscapes[i])
				sys.stderr.write(' '.join(standOffs)+'\n')
			if learnAlgorithm == 'Wapiti':
				if i == sentenceItemsLen:
					print('')
				else:
					features = [sentenceItems[i]]
					features.extend(getBasicFeatures(sentenceInc[i], sentenceChunk[i], sentenceLexical[i], sentencePOS[i], sentenceLemmas[i], sentenceTokens[i], True))
					if outputWapitiLexicalFeatures:
						features.extend(getLexicalFeatures(sentenceLexical[i]))
					if outputWapitiRulesFeatures:
						ruleMarkers = []
						if i in sentenceRuleMarkers:
							ruleMarkers = sentenceRuleMarkers[i]
						features.extend(getRuleFeatures(ruleMarkers, True))
					if outputWapitiCasenFeatures:
						if i in sentenceCasenMarkers:
							for sentenceCasenMarker in sentenceCasenMarkers[i]:
								sentenceCasenMarker = sentenceCasenMarker[4:]
								if sentenceCasenMarker[1] == '/' and len(currentCasenEntities) > 1:
									currentCasenEntities.pop()
								else:
									currentCasenEntities.append(sentenceCasenMarker[5:-1])
						if modeDebug:
							print('CasEN feature:', '/'.join(currentCasenEntities))
						features.append('/'.join(currentCasenEntities))
					if learnMode == 'train':
						for j in range(len(currentCategories)):
							currentCategories[j] = currentCategories[j].replace('-B', '-I')
						if i in existingMarkers:
							for marker in existingMarkers[i]:
								if not marker.beginMarker and len(currentCategories):
									currentCategories.pop()
							for marker in existingMarkers[i]:
								if marker.beginMarker:
									bioTag = '-I'
									if outputWapitiBegin:
										bioTag = '-B'
									currentCategories.append(marker.categoryMarker+bioTag)
					if len(currentCategories):
						features.append('/'.join(currentCategories))
					else:
						features.append('O')
					print('\t'.join(features))
			elif learnAlgorithm in ['MaxEnt', 'MaxEntBin', 'SciKit', 'SciKitBin']:
				features = []
				if i < sentenceItemsLen:
					features = getBasicFeatures(sentenceInc[i], sentenceChunk[i], sentenceLexical[i], sentencePOS[i], sentenceLemmas[i], sentenceTokens[i])
				if i in sentenceRuleMarkers:
					features.extend(getRuleFeatures(sentenceRuleMarkers[i]))
				if i in sentenceCasenMarkers:
					features.extend(getCasenFeatures(sentenceCasenMarkers[i]))
				transitionMarkers = ['=']
				if learnMode == 'train' and i in existingMarkers:
					transitionMarkers = []
					for marker in existingMarkers[i]:
						transitionMarkers.append(marker.shortMarker)
				if len(features):
					if learnAlgorithm in ['MaxEnt', 'MaxEntBin']:
						print(','.join(transitionMarkers) + '\t' + '\t'.join(features))
					elif learnAlgorithm == 'SciKit':
						sequenceLines += 1
						markerLines += len(transitionMarkers)
						transitionMarkerIds = []
						for transitionMarker in transitionMarkers:
							transitionMarkerIds.append(getShortMarkerId(transitionMarker))
						if modeDebug:
							print('\t'.join(['/'.join(transitionMarkers), '\t'.join(features)]))
						print('\t'.join([getSequenceMarkerId('/'.join(transitionMarkers)), ','.join(transitionMarkerIds), '\t'.join([str(getFeatureId(feature)) for feature in features])]))
# Adds mined patterns as features for Wapiti
if learnMode == 'train' and learnAlgorithm == 'Wapiti':
	sys.stderr.write('# Corpus mined patterns as unigram and bigram features\n')
	featureColumn = 6
	if outputWapitiLexicalFeatures:
		for lexicalFeature in lexicalFeatures:
			if lexicalFeatures[lexicalFeature] > 1:
				sys.stderr.write('U_LEX_'+lexicalFeature+':%x[0,'+str(featureColumn)+']\n')
			featureColumn += 1
	if outputWapitiRulesFeatures:
		for markerFeature in mxsFeatures:
			sys.stderr.write('U_RUL_'+markerFeature+':%x[0,'+str(featureColumn)+']\n')
			featureColumn += 1
	if outputWapitiCasenFeatures:
		sys.stderr.write('B_CASEN:%x[0,'+str(featureColumn)+']\n')
		featureColumn += 1
# Adds markers and features ids for SciKit
if learnMode == 'train' and learnAlgorithm in ['SciKit', 'SciKitBin']:
	sys.stderr.write('\t'.join(['shape', str(markerLines), str(sequenceLines), str(len(featureIds))]) + '\n')
	for featureName in featureIds:
		sys.stderr.write('feat\t' + featureName + '\t' + str(featureIds[featureName]) + '\n')
	for shortMarker in shortMarkerIds:
		sys.stderr.write('mark\t' + shortMarker + '\t' + shortMarkerIds[shortMarker] + '\n')
	for markerSequence in sequenceMarkerIds:
		sys.stderr.write('seq\t' + markerSequence + '\t' + sequenceMarkerIds[markerSequence] + '\n')
# Prints stats for held
elif learnAlgorithm in ['MaxEnt', 'MaxEntBin', 'SciKit', 'SciKitBin'] and learnMode == 'held':
	print('Detection:', float(heldStats['detect-cr'])/float(heldStats['items']))
	recoPrecision = float(heldStats['reco-cr'])/float(heldStats['reco-c'])
	recoRecall = float(heldStats['reco-cr'])/float(heldStats['reco-r'])
	recoFscore = 0.0
	if recoPrecision + recoRecall:
		recoFscore = 2*recoPrecision*recoRecall/(recoPrecision + recoRecall)
	print('Recognition: fscore', recoFscore, 'precision', recoPrecision, 'recall', recoRecall)
	disambPrecision = 0.0
	if heldStats['disamb-c']:
		disambPrecision = float(heldStats['disamb-cr'])/float(heldStats['disamb-c'])
	disambRecall = 0.0
	if heldStats['disamb-r']:
		disambRecall = float(heldStats['disamb-cr'])/float(heldStats['disamb-r'])
	disambFscore = 0.0
	if disambPrecision + disambRecall:
		disambFscore = 2*disambPrecision*disambRecall/(disambPrecision + disambRecall)
	print('Disambiguation: fscore', disambFscore, 'precision', disambPrecision, 'recall', disambRecall)
	print('Sequences ranking: recognition', float(heldStats['reco-sr'])/float(heldStats['items']), 'disambiguation', float(heldStats['disamb-sr'])/float(heldStats['disamb-sra']))
