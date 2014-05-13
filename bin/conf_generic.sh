#!/bin/bash

# General configuration
export MXS_BIN=$MXS_PATH/bin
export DICOS_PATH=$MXS_PATH/dicos
export CORPUS_UNTAG_SCRIPT=$MXS_BIN/untagCorpus.sh
export CORPUS_OUTPUT_SCRIPT=$MXS_BIN/neTagsToCorpus.sh
export CORPUS_MERGE_SCRIPT=$MXS_BIN/mergeCasENSminer.py

# Clean environment variables
unset SMINER_SEGMENTAL PREPROCESS_SUFFIX LEARN_TOOLKIT LEARN_SEQ_STEPS DICO_USE SENTENCEPOS_USE UNCAPITALIZE

