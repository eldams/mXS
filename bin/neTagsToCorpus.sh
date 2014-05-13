#!/bin/bash

# Remove new lines
tr '\n' ' ' |
sed -r 's| +| |g' |
# Recover new items
sed -r 's|NEW/(NE/</?NE)|\1m|g' |
# Recover original data format
sed -r 's/(<_n|n_>)//g' |
sed -r 's|<_b|\n|g' |
sed -r 's|<_t|<|g' |
sed -r 's|t_>|>|g' |
sed -r 's|<_c|[|g' |
sed -r 's|c_>|]|g' |
sed -r 's#( |^)[^ \n]*[^<]/([^/ \n]*)#\1\2#g' |
sed -r 's|MXS_SLASH|/|g' |
sed -r 's|MXS_PLUS|+|g' |
sed -r 's|MXS_DASH|-|g' |
sed -r 's|MXS_SPACE| |g' |
sed -r 's|((<[^>]*> +)*)(<_s([^>]*)s_>)|\3 \1|g' |
sed -r 's#( |^)[^ ]+ +((NE/[^ ]* +)*)<_s([^>]*)s_>#\1\4 \2#g' |
sed -r "s| ' |' |g" |
# Finalize
grep -v '^$' |
sed -r 's/^ +//g' |
sed -r 's/  +/ /g'

