#!/bin/bash

# Remove new lines
sed 's/$/__NEWLINE__/' |
tr '\n' ' ' |
# Keep only inner, CasEN and comments tags
sed -r 's/<(_[^>]*)>/__TB__\1__TE__/g' |
sed -r 's#<(/?NEc[^>]*)>#__TB__\1__TE__#g' |
sed -r 's#<([^>]*)>([^<]*)</\1>#__TB__\1__TE__\2__TB__/\1__TE__#g' |
sed -r 's/<[^>]*>//g' |
sed 's/__TB__/</g' |
sed 's/__TE__/>/g' |
sed 's/__NEWLINE__/\n/g' |
# Finalize
sed -r 's/  +/ /g'

