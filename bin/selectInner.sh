#!/bin/bash

# Remove new lines
sed 's/$/__NEWLINE__/' |
tr '\n' ' ' |
# Keep only inner, CasEN and comments tags
sed -E 's/<(_[^>]*)>/__TB__\1__TE__/g' |
sed -E 's#<(/?NEc[^>]*)>#__TB__\1__TE__#g' |
sed -E 's#<([^>]*)>([^<]*)</\1>#__TB__\1__TE__\2__TB__/\1__TE__#g' |
sed -E 's/<[^>]*>//g' |
sed 's/__TB__/</g' |
sed 's/__TE__/>/g' |
sed -e 's/__NEWLINE__/\'$'\n/g' |
# Finalize
sed -E 's/  +/ /g'

