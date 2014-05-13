#!/bin/bash

# General configuration
. $MXS_PATH/bin/conf_generic.sh

# Processing parameters
export SMINER_SEGMENTAL='1'
export DICO_USE='1'
#export UNCAPITALIZE='1'
export SENTENCEPOS_USE='1'
export LEARN_TOOLKIT='SciKitBin' # SciKit, SciKitBin, MaxEnt, MaxEntBin, Wapiti
. $MXS_BIN/conf_preprocess_TreeTagger.sh

# Corpus data configuration
export CORPUS_PATH=$MXS_PATH/data/DatasetExample
export CORPUS_TMP=$CORPUS_PATH/tmp
export CORPUS_MODEL=$CORPUS_PATH/model
#export ANNOTATION_FORMAT='DatasetExample'
export HYP_DIR=corpus_test
export SMINER_CORPUS_FILENAME_PREFIX=corpus_Train
export LEARN_CORPUS_FILENAME_PREFIX=$SMINER_CORPUS_FILENAME_PREFIX
#export HELD_CORPUS_FILENAME_PREFIX=corpus_Held
export HYP_IN_EXT=txt
export HYP_OUT_EXT=ne
export CORPUS_DATA_SCRIPT=$MXS_BIN/corpusToNe.sh
export DATA_CORPUS_SCRIPT=$MXS_BIN/neToCorpus.sh
#export SELECT_SCRIPT=$MXS_BIN/selectOuter.sh
