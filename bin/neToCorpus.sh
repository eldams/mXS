#!/bin/bash

# Preprocess new lines
tr -d '\r' |
sed -r 's|^| |g' |
sed -r 's|$| <_bn_> |g' |
# Removes significant space
sed -r 's|([0-9]) h |\1h |g' |
sed -r 's|([0-9]) m |\1m |g' |
sed -r "s#([^>]) +(,|\.|')#\1\2#g" |
sed -r "s|' +([^<])|'\1|g" |
# Removes special processings (interjections, unknown words, hesitations, etc)
sed -r 's/ /  /g' |
sed -r 's# (\*+|\^+|_+)# <_n\1n_> #g' |
sed -r 's# ((&(amp;)?[^ ]*)|euh|hum) # <_n\1n_> #g' |
sed -r 's# (([a-Z]*)\(([a-Z]*)\)([a-Z]*)) # \2\3\4 <_s\1s_> #g' |
sed -r 's# <_s\(\)s_> # () #g' |
sed -r 's# ([^ <]+) (\1 )+ # \1 <_n\2n_> #g' |
# Removes extra space
sed -r 's|  +| |g'

