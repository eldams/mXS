#!/bin/bash

# Preprocess new lines
tr -d '\r' |
awk '$0=" "$0' |
sed -E 's|$| <_bn_> |g' |
# Removes significant space
sed -E 's|([0-9]) h |\1h |g' |
sed -E 's|([0-9]) m |\1m |g' |
sed -E "s#([^>]) +(,|\.|')#\1\2#g" |
sed -E "s|' +([^<])|'\1|g" |
# Removes special processings (interjections, unknown words, hesitations, etc)
sed -E 's/ /  /g' |
sed -E 's# (\*+|\^+|_+)# <_n\1n_> #g' |
sed -E 's# ((&(amp;)?[^ ]*)|euh|hum) # <_n\1n_> #g' |
sed -E 's# (([A-Za-z]*)\(([A-Za-z]*)\)([A-Za-z]*)) # \2\3\4 <_s\1s_> #g' |
sed -E 's# <_s\(\)s_> # () #g' |
sed -E 's# ([^ <]+) (\1 )+ # \1 <_n\2n_> #g' |
# Removes extra space
sed -E 's|  +| |g'
