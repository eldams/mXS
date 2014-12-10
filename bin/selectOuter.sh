#!/bin/bash

lev=0
sed 's/$/__NEWLINE__/g' |
sed -E 's/<(_[^>]*)>/__TB__\1__TE__/g' |
sed -E 's#<(/?NEc[^>]*)>#__TB__\1__TE__#g' |
sed -e 's/(<[^>]*>)/\'$'\n\1\'$'\n/g' |
while read wrd; do
	if [[ ${wrd:0:2} == '</' ]]; then
		lev=`expr $lev - 1`
		if [[ $lev -eq 0 ]]; then
			echo $wrd
		fi
	else
		if [[ ${wrd:0:1} == '<' ]]; then
			if [[ ${wrd:0:2} == '<_' ]]; then
				echo $wrd
			else
				if [[ $lev -eq 0 ]]; then
					echo $wrd
				fi
				lev=`expr $lev + 1`
			fi
		else
			echo $wrd
		fi
	fi
done |
tr '\n' ' ' |
sed 's/__TB__/</g' |
sed 's/__TE__/>/g' |
sed -e 's/__NEWLINE__/\'$'\n/g' |
sed -E 's/ +/ /g'
