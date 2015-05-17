#!/bin/bash

applyoption="-slb"
[[ $LEARN_TOOLKIT == 'SciKit' ]] && applyoption="-sl"

$DATA_CORPUS_SCRIPT |
$PREPROCESS_SCRIPT |
$SEQUENCE_SCRIPT |
$MXS_BIN/applyRules.py $applyoption $CORPUS_MODEL/patterns.txt |
$CORPUS_MERGE_SCRIPT |
$CORPUS_OUTPUT_SCRIPT |
$CORPUS_DATA_SCRIPT
