#!/usr/bin/env python
#_*_coding:utf8_*_
import os
import json
import re
from pprint import pprint
import json
import codecs
import sys
import argparse
import sys

#Mxs_path = os.environ.get('MXS_PATH')


def extract_data():
    data = "/Users/wangyizhe/Desktop/Politiques.json"
    dico = {}
    lines = [line for line in codecs.open(data)]
    js = [json.loads(line) for line in lines]
    for person in js:
        if "fullName" and "wikipediaUrl" in person:
            fullName = person["fullName"]
            wikiUrl = person["wikipediaUrl"]
            dico[fullName] = wikiUrl
    return(dico)


def identifier_NEs():
    data_reference = extract_data()
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('r'))
    args = parser.parse_args()
    content = args.file.read()
    #content = content = sys.argv[1:]
    names = re.findall(r'<pers>.*?</pers>', content)
    if names:
        for name in names:
            link = None
            n = re.search(r'<pers>(.*)</pers>', name).group(1).strip()
            if n in data_reference:
                link = "'" + data_reference[n] + "'"
            try:
                old = re.compile(name)
            except:
                pass
            new = "<pers link={}>{}</pers>".format(link, n)
            content = old.sub(new, content)
        print (content)

identifier_NEs()
