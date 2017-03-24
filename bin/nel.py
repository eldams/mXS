#!/usr/bin/env python
#_*_coding:utf8_*_
import os,json,re, codecs, sys, argparse, collections
from pprint import pprint
from wikiapi import WikiApi
from nltk.corpus import stopwords
from math import sqrt


json_data ={} 
project = os.environ.get('project')
n = 0
list_path = []
mxsfolder = project + "/result_mXS"
list_dirs = os.walk(mxsfolder)

wiki = WikiApi()
wiki = WikiApi({'locale': 'fr'})


def cut_word(content):
    text = re.sub("[^a-zA-Z]", " ", content)
    words = text.lower().split()
    stops = set(stopwords.words('french'))
    tags = [w for w in words if not w in stops]
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
    return sqrt(dot_product(vector, vector))


def similarity(v1, v2):
    return dot_product(v1, v2) / (magnitude(v1) * magnitude(v2) + .00000000001)


def get_wikilinks(n, content):
    url = None
    print (n)
    # results = wiki.find(n.strip())
    results = wiki.find(n)
    if results:
        if len(results) == 0:
            return("no page wikipedia")
        else:
            dico_simi = {}
            for text in results:
                article = wiki.get_article(text)
                summary = article.content
                tag1, tag2 = cut_word(summary), cut_word(content)
                v1, v2 = merge_tag(tag1, tag2)
                simi = similarity(v1, v2)
                dico_simi[article] = simi
            max_key = max(dico_simi, key=lambda k: dico_simi[k])
            url = max_key.url
            return url


def extract_data():
    data = "/Users/wangyizhe/Desktop/StageNEL/Politiques.json"
    dico = {}
    lines = [line for line in codecs.open(data)]
    js = [json.loads(line) for line in lines]
    for person in js:
        if "fullName" and "wikipediaUrl" in person:
            fullName = person["fullName"]
            wikiUrl = person["wikipediaUrl"]
            dico[fullName] = wikiUrl
    return(dico)


def identifier_NEs(content):
    data_reference = extract_data()
    """for root, dirs, files in list_dirs:
        for f in files[:3]:
            if f != '.DS_Store':
                with open(mxsfolder + '/' + f, 'r') as fo:
                    content = fo.read()"""
    names = re.findall(r'<pers.*?>.*?</pers>', content)
    if names:
        for name in names:
            link = None
            n = re.search(r'<pers.*?>(.*)</pers>', name).group(1).strip()
            if n in data_reference:
                link = "'" + data_reference[n] + "'"
            else:
                url = get_wikilinks(n, content)
                if url != None:
                    link = "'" + url + "'"
            try:
                old = re.compile(name)
            except:
                pass
            new = "<pers link={}>{}</pers>".format(link, n)
            content = old.sub(new, content)
        print (content)
data = sys.stdin.read()
identifier_NEs(data)
