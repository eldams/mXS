#!/usr/bin/env python
# -*- coding: utf-8 -*-
import fileinput
import re
import sys
import os
# Trouver les entités en sortie de bin/tagEtapeModel qui ont un lien dans dicos/links.lst
# Si lien trouvé ajouter un attribut link à la balise
# <pers>Nicolas Sarkozy</pers>
# <pers link="https://fr.wikipedia.org/wiki/Nicolas_Sarkozy">Nicolas Sarkozy</pers>
MXS_PATH = os.environ.get('MXS_PATH')

def lirelinks():
    with open(MXS_PATH + "/dicos/links.lst") as f:
        content = f.readlines()
        dico = {}
        for entity in content:
            l = entity.split("\t")
            key = (l[1], l[2])
            dico[key] = l[3]
        return dico


def identifier_NEs():
    dico = lirelinks()
    content = sys.stdin.read()
    try:
        ls = content.split('</pers.ind>')
    except:
        print "there is no NEs de type person in text."
    for name in ls:
        entity_persons = re.findall(r'<pers\.ind>.*', name)
        if entity_persons:
            entity_person = entity_persons[0]
            first_name = re.search(
                r'<name\.first>(.*)</name\.first>', entity_person)
            last_name = re.search(
                r'<name\.last>(.*)</name\.last>', entity_person)
            if first_name:
                first_name = first_name.group(1).strip()
            if last_name:
                last_name = last_name.group(1).strip()
            n = (first_name, last_name)
            if n in dico:
                link = dico[n]
            old = re.compile(entity_person)
            new = "<pers.ind link={}><name.first> {} </name.first><name.last> {} </name.last>".format(
                link, first_name, last_name)
            content = old.sub(new, content)
    print (content)
identifier_NEs()
