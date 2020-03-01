#!/bin/bash

# Treetagger options: OPTIONS="-token -lemma -sgml -no-unknown -eos-tag <sent/>"
sed -E 's/([0-9]+)\.( |$)/\1 .\2/g' |
$MXS_BIN/treetagger-sminer 2>/dev/null |
#$MXS_BIN/treetagger-chunker-sminer 2>/dev/null |
$MXS_BIN/treetaggerPostProcess.py
