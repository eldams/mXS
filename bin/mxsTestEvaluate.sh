#!/bin/sh

[[ "$#" == 2 && -d $MXS_PATH/data/$1 && -d ~/Projets/$1 ]] || { echo "Usage mxsTestEvaluate.sh Dataset SandBoxName" >&2; exit 0; }

echo "Sandboxing binaries and resources in $MXS_PATH.$1-$2"
MXS_PATH_MAIN=$MXS_PATH
export MXS_PATH=$MXS_PATH.$1-$2
rm -rf $MXS_PATH
mkdir $MXS_PATH $MXS_PATH/data
cp -r $MXS_PATH_MAIN/bin $MXS_PATH/bin
cp -r $MXS_PATH_MAIN/dicos $MXS_PATH/dicos
cp -r $MXS_PATH_MAIN/data/$1 $MXS_PATH/data/$1

echo "Annotate"
. $MXS_PATH/bin/conf_$1.sh
$MXS_PATH/bin/testCorpus.sh > $MXS_PATH_MAIN/logs/$1-$2 2>&1

echo "Evaluate"
~/Projets/$1/scripts/evaluation/evaluate_support-confidence.sh >> $MXS_PATH_MAIN/logs/$1-$2 2>&1

