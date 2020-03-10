#!/usr/bin/env python3
#_*_coding:utf8_*_

import os, json, re, codecs, sys, collections, math, wikiapi, string

dicospath = os.environ.get('DICOS_PATH')
json_data = {}
wiki = wikiapi.WikiApi({'locale': 'fr'})

def cut_word(content):
    text = re.sub("[^a-zA-Z]", " ", content)
    words = text.lower().split()
    # stops = set(stopwords.words('french'))
    tags = [w for w in words]
    return (tags)

def merge_tag(tag1=None, tag2=None):
    v1 = []
    v2 = []
    tag_dict1 = collections.Counter(tag1)
    tag_dict2 = collections.Counter(tag2)
    merged_tag = set()
    for it in tag_dict1.keys():
        merged_tag.add(it)
    for item in tag_dict2.keys():
        merged_tag.add(item)
    for i in merged_tag:
        if i in tag_dict1:
            v1.append(tag_dict1[i])
        else:
            v1.append(0)
        if i in tag_dict2:
            v2.append(tag_dict2[i])
        else:
            v2.append(0)
    return v1, v2

def dot_product(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))

def magnitude(vector):
    return math.sqrt(dot_product(vector, vector))

def similarity(v1, v2):
    return dot_product(v1, v2) / (magnitude(v1) * magnitude(v2) + .00000000001)

def approxMatch(s1, s2, l):
	if s1 == s2:
		return True
	elif l > 0:
		excludes = string.punctuation+' \t\n'
		s1 = ''.join(c for c in s1 if c not in excludes)
		s2 = ''.join(c for c in s2 if c not in excludes)
		# print(s1, s2)
		if s1 == s2:
			return True
		elif l > 1:
			s1 = ''.join(c for c in s1 if c in string.ascii_letters).lower()
			s2 = ''.join(c for c in s2 if c in string.ascii_letters).lower()
			if s1 == s2:
				return True
			elif l > 2:
				s1 = ''.join(c for c in s1 if c not in string.digits)
				s2 = ''.join(c for c in s2 if c not in string.digits)
				if s1 == s2:
					return True
				elif l > 3:
					if s1 in s2 or s2 in s1:
						return True
					elif l > 4:
						return True

def nameBestMatches(entity, titles):
	matches = []
	l = 0
	while not len(matches):
		for title in titles:
			if approxMatch(entity, title, l):
				matches.append(title)
		l += 1
	return matches

def get_wikilinks(entity, content):
	url = None
	# results = wiki.find(n.strip())
	results = wiki.find(entity)
	if results and len(results):
		results = nameBestMatches(entity, results)
		if len(results) > 1:
			dico_simi = {}
			for title in results:
				article = wiki.get_article(title)
				summary = article.content
				tag1, tag2 = cut_word(summary), cut_word(content)
				v1, v2 = merge_tag(tag1, tag2)
				simi = similarity(v1, v2)
				dico_simi[article] = simi
			return max(dico_simi, key=lambda k: dico_simi[k]).url
		else:
			return wiki.get_article(results[0]).url

def extract_data():
    data = dicospath+"/links.json"
    dico = {}
    lines = [line for line in codecs.open(data)]
    js = [json.loads(line) for line in lines]
    for person in js:
        if "fullName" and "wikipediaUrl" in person:
            fullName = person["fullName"]
            wikiUrl = person["wikipediaUrl"]
            dico[fullName] = wikiUrl
            if "lastName" in person:
                lastName = person["lastName"]
                dico[lastName] = wikiUrl
    return(dico)

def identifier_NEs(content):
    data_reference = extract_data()
    names = re.findall(r'<pers.*?>.*?</pers.*?>', content)
    if names:
        for name in names:
            link = None
            entity = re.search(r'<pers.*?>(.*?)</pers.*?>', name).group(1).strip()
            entity = re.sub('  +', ' ', re.sub('<[^>]*>', '', entity).strip())
            if entity in data_reference:
                link = '"' + data_reference[entity] + '"'
            else:
                url = get_wikilinks(entity, content)
                if url != None:
                    link = '"' + url + '"'
            try:
                old = re.compile(name)
            except:
                pass
            if link:
                new = "<pers link={}>{}</pers>".format(link, entity)
                content = old.sub(new, content)
    return content

print(identifier_NEs(sys.stdin.read()))
