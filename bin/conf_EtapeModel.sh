#!/bin/bash

# General configuration
. $MXS_PATH/bin/conf_generic.sh

# Processing parameters
export SMINER_SEGMENTAL='1'
export DICO_USE='1'
#export UNCAPITALIZE='1'
export SENTENCEPOS_USE='1'
export LEARN_TOOLKIT='SciKitBin' # SciKit, SciKitBin, MaxEnt, MaxEntBin, Wapiti
#export LEARN_SEQ_STEPS='20' # Post processing after scikit to learn markers > markers sequences
. $MXS_BIN/conf_preprocess_TreeTagger.sh
#export PREPROCESS_SUFFIX='.CasEN' # .CasEN, .Frmg

# Corpus data configuration
export CORPUS_PATH=$MXS_PATH/data/EtapeModel
export CORPUS_TMP=$CORPUS_PATH/tmp
export CORPUS_MODEL=$CORPUS_PATH/model
export ANNOTATION_FORMAT='Etape'
#export HYP_DIR=ne_Etape_Test
#export SMINER_CORPUS_FILENAME_PREFIX=corpus_Etape_DevTrain
#export LEARN_CORPUS_FILENAME_PREFIX=$SMINER_CORPUS_FILENAME_PREFIX
#export HELD_CORPUS_FILENAME_PREFIX=corpus_Etape_Test
export HYP_IN_EXT=ne
export HYP_OUT_EXT=ne
export CORPUS_DATA_SCRIPT=$MXS_BIN/corpusToNe.sh
export DATA_CORPUS_SCRIPT=$MXS_BIN/neToCorpus.sh
#export SELECT_SCRIPT=$MXS_BIN/selectOuter.sh
