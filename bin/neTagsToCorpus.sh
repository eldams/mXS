#!/bin/bash

# Remove new lines
tr '\n' ' ' |
sed -E 's| +| |g' |
# Recover new items
sed -E 's|NEW/(NE/</?NE)|\1m|g' |
# Recover tokens
sed -E 's#( |^)[^ <]*[^<]/([^/ ]*)#\1\2#g' |
# Remove tags
sed -E 's/\. <_fs_>//g' |
sed -E 's/(<_n|n_>)//g' |
sed -e 's|<_b|\'$'\n|g' |
sed -E 's|<_t|<|g' |
sed -E 's|t_>|>|g' |
sed -E 's|<_c|[|g' |
sed -E 's|c_>|]|g' |
# Replace special chars
sed -E 's|MXS_SLASH|/|g' |
sed -E 's|MXS_PLUS|+|g' |
sed -E 's|MXS_DASH|-|g' |
sed -E 's|MXS_SPACE| |g' |
# Other replacements
sed -E 's|((<[^>]*> +)*)(<_s([^>]*)s_>)|\3 \1|g' |
sed -E 's#( |^)[^ ]+ +((NE/[^ ]* +)*)<_s([^>]*)s_>#\1\4 \2#g' |
sed -E "s| ' |' |g" |
# Finalize
grep -v '^$' |
sed -E 's/^ +//g' |
sed -E 's/  +/ /g'


