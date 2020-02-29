#!/bin/bash

# Mining configuration
SMINER_MINIMUM_SUPPORT=$1
SMINER_MINIMUM_CONFIDENCE=$2
CORPUS_FILE_PATH=$3
SMINER_SMOOTHING=0
SMINER_TARGET_STR='NE'

[[ "$#" == 3 && -f $CORPUS_FILE_PATH ]] || { echo "Usage mineCorpus.sh frequency confidence corpusfile" >&2; exit 0; }
export CORPUS_TMP=$CORPUS_PATH/tmp

echo 'Preprocessing and encoding corpus with translations and hierarchies' >&2
cat $CORPUS_FILE_PATH | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT $CORPUS_TMP/corpus_mine.translation $CORPUS_TMP/corpus_mine.hierarchy > $CORPUS_TMP/corpus_mine.bin

echo "Looking for patterns (support:$SMINER_MINIMUM_SUPPORT, confidence:$SMINER_MINIMUM_CONFIDENCE)" >&2
SMINER_TARGET_ID=$(grep " $SMINER_TARGET_STR\$" $CORPUS_TMP/corpus_mine.translation | sed 's/ .*//')
SMINER_PARAMS="-mf $SMINER_MINIMUM_SUPPORT -omc $SMINER_TARGET_ID $SMINER_MINIMUM_CONFIDENCE -smooth $SMINER_SMOOTHING"
SMINER_PARAMS=$SMINER_PARAMS" -hierarchy $CORPUS_TMP/corpus_mine.hierarchy -translation $CORPUS_TMP/corpus_mine.translation"
#SMINER_PARAMS=$SMINER_PARAMS" -st"
SMINER_PARAMS=$SMINER_PARAMS" -lt"
#SMINER_PARAMS=$SMINER_PARAMS" -ot"
#SMINER_PARAMS=$SMINER_PARAMS" -red 50"
#SMINER_PARAMS=$SMINER_PARAMS" -omi 50"
#SMINER_PARAMS=$SMINER_PARAMS" -ml 7"
#SMINER_PARAMS=$SMINER_PARAMS" -min"
#SMINER_PARAMS=$SMINER_PARAMS" -stats"
[[ $SMINER_SEGMENTAL ]] && SMINER_PARAMS=$SMINER_PARAMS" -segs"
$MXS_BIN/sminer $SMINER_PARAMS $CORPUS_TMP/corpus_mine.bin

echo 'Cleaning' >&2
#/bin/rm -f $CORPUS_TMP/*
