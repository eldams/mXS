#!/bin/bash

# Import specific corpus configuration
if [[ -z $MXS_BIN ]]; then
	export MXS_BIN=$MXS_PATH/bin
	#. $MXS_PATH/bin/conf_Ester2.sh
	. $MXS_PATH/bin/conf_Etape.sh
	#. $MXS_PATH/bin/conf_FrenchTreebank.sh
fi
[[ -x $SELECT_SCRIPT ]] || { SELECT_SCRIPT=cat; }

function mine {
	echo '-------------------------'
	echo 'Mining extraction corpus:'
	echo '-------------------------'
	support_minimum=0
	confidence_minimum=0
	for supportconfidencedir in $CORPUS_PATH/hyp_support-confidence/* ; do
		support=`basename $supportconfidencedir | cut -d '-' -f 1`
		confidence=`basename $supportconfidencedir | cut -d '-' -f 2`
		[[ "$support" != 'inf' && (( $support_minimum == 0 || $support -lt $support_minimum )) ]] && support_minimum=$support
		[[ "$confidence" != 'inf' && (( $confidence_minimum == 0 || $confidence -lt $confidence_minimum )) ]] && confidence_minimum=$confidence
	done
	cat $CORPUS_PATH/$SMINER_CORPUS_FILENAME_PREFIX$PREPROCESS_SUFFIX.txt | $SELECT_SCRIPT > $CORPUS_TMP/mine.txt
	$MXS_BIN/mineCorpus.sh $support_minimum $confidence_minimum $CORPUS_TMP/mine.txt > $CORPUS_MODEL/patterns.txt
}

function prepare {
	echo '-----------------'
	echo 'Preparing corpus:'
	echo '-----------------'
	/bin/rm -f $CORPUS_TMP/held_tagged.txt $CORPUS_TMP/mine_tagged.txt $CORPUS_TMP/train_tagged.txt
	echo 'Preprocessing train corpus'
	cat $CORPUS_PATH/$LEARN_CORPUS_FILENAME_PREFIX$PREPROCESS_SUFFIX.txt | $SELECT_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT > $CORPUS_TMP/train_tagged.txt
	if [[ -f $CORPUS_PATH/$HELD_CORPUS_FILENAME_PREFIX$PREPROCESS_SUFFIX.txt && "$LEARN_TOOLKIT" != 'Wapiti' ]]; then
		echo 'Preprocessing held corpus'
		/bin/rm -f $CORPUS_TMP/held.txt $CORPUS_TMP/held_tagged.txt
		cat $CORPUS_PATH/$HELD_CORPUS_FILENAME_PREFIX$PREPROCESS_SUFFIX.txt | $SELECT_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT > $CORPUS_TMP/held_tagged.txt
	fi
}

function tag {
	echo '---------------------'
	echo 'Training and tagging:'
	echo '---------------------'
	/bin/rm -f $CORPUS_TMP/train.log
	for supportconfidencedir in $CORPUS_PATH/hyp_support-confidence/* ; do
		/bin/rm -f $supportconfidencedir/*
		support=`basename $supportconfidencedir | cut -d '-' -f 1`
		confidence=`basename $supportconfidencedir | cut -d '-' -f 2`
		echo "Training using patterns with support $support/100000 and confidence $confidence/100"
		export SMINER_MINIMUM_SUPPORT=$support
		export SMINER_MINIMUM_CONFIDENCE=$confidence
		echo 'Tagging with patterns and learning train corpus'
		learn
		if [[ -f $CORPUS_TMP/held_tagged.txt ]]; then
			echo 'Testing accuracy on held corpus'
			held
		fi
		echo 'Tagging test files'
		for infile in $CORPUS_PATH/$HYP_DIR$PREPROCESS_SUFFIX/* ; do
			echo " file $infile"
			outfilebasename=`basename $infile .$HYP_IN_EXT`
			echo ' > preparing test file'
			cat $infile | $DATA_CORPUS_SCRIPT | $PREPROCESS_SCRIPT | $SEQUENCE_SCRIPT > $CORPUS_TMP/text_tagged.txt
			echo ' > labelling test file'
			label
			cat $CORPUS_TMP/text_ne.txt | $CORPUS_DATA_SCRIPT > $CORPUS_PATH/hyp/$outfilebasename.$HYP_OUT_EXT
		done
		/bin/cp -f $CORPUS_PATH/hyp/*.$HYP_OUT_EXT $supportconfidencedir/
	done
}

function learn {
	learn$LEARN_TOOLKIT
}

function held {
	held$LEARN_TOOLKIT
}

function label {
	label$LEARN_TOOLKIT
}

function learnWapiti {
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/getLexicalFeatures.py > $CORPUS_TMP/train_lex.txt
	/bin/cp -f $CORPUS_PATH/wapiti_patterns_base.txt $CORPUS_TMP/train_wapiti.txt
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/applyRules.py -ct $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/train.tsv 2>> $CORPUS_TMP/train_wapiti.txt
	wapiti train -t 4 --stopwin 30 -p $CORPUS_TMP/train_wapiti.txt $CORPUS_TMP/train.tsv $CORPUS_MODEL/model_markers.txt >> $CORPUS_TMP/train.log 2>&1
}

function heldWapiti {
	echo 'No held for Wapiti'
}

function labelWapiti {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -cl $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged.tsv 2> $CORPUS_TMP/text_standoffs.txt
	wapiti label -m $CORPUS_MODEL/model_markers.txt $CORPUS_TMP/text_tagged.tsv > $CORPUS_TMP/text_tagged_ne.txt 2> /dev/null
	cat $CORPUS_TMP/text_tagged_ne.txt | $MXS_BIN/labelsToNeTags.py $CORPUS_TMP/text_standoffs.txt | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

function learnMaxEnt {
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/applyRules.py -mt $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/train.tsv
	cat $CORPUS_TMP/train.tsv | $MXS_BIN/expandTrain.py > $CORPUS_TMP/train_mc.tsv
	cat $CORPUS_TMP/train_mc.tsv | grep -E '^\+' > $CORPUS_TMP/train_mc-b.tsv
	cat $CORPUS_TMP/train_mc.tsv | grep -E '^-' > $CORPUS_TMP/train_mc-e.tsv
	MAXENT_HELD_B=''
	MAXENT_HELD_E=''
	if [[ -f $CORPUS_TMP/held_tagged.txt ]]; then
		cat $CORPUS_TMP/held_tagged.txt | $MXS_BIN/applyRules.py -mt $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/held.tsv
		cat $CORPUS_TMP/held.tsv | $MXS_BIN/expandTrain.py > $CORPUS_TMP/held_mc.tsv
		cat $CORPUS_TMP/held_mc.tsv | grep -E '^\+' > $CORPUS_TMP/held_mc-b.tsv
		cat $CORPUS_TMP/held_mc.tsv | grep -E '^-' > $CORPUS_TMP/held_mc-e.tsv
		MAXENT_HELD_B="--heldout=$CORPUS_TMP/held_mc-b.tsv"
		MAXENT_HELD_E="--heldout=$CORPUS_TMP/held_mc-e.tsv"
	fi
	maxent -v -i 300 -g 1 -m $CORPUS_MODEL/model_markers-b.txt $MAXENT_HELD_B $CORPUS_TMP/train_mc-b.tsv >> $CORPUS_TMP/train.log 2>&1
	maxent -v -i 300 -g 1 -m $CORPUS_MODEL/model_markers-e.txt $MAXENT_HELD_E $CORPUS_TMP/train_mc-e.tsv >> $CORPUS_TMP/train.log 2>&1
}

function heldMaxEnt {
	echo 'Held retrieved from train.log files:'
	cat $CORPUS_TMP/train.log
}

function labelMaxEnt {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -ml $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged_ne.txt
	cat $CORPUS_TMP/text_tagged_ne.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

function learnMaxEntBin {
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/applyRules.py -mt $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/train.tsv
	if [[ -f $CORPUS_TMP/held_tagged.txt ]]; then
		cat $CORPUS_TMP/held_tagged.txt | $MXS_BIN/applyRules.py -mt $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/held.tsv
	fi
	cat $CORPUS_TMP/train.tsv | cut -f 1 | tr ',' '\n' | sort | uniq | grep -v '^=$' > $CORPUS_MODEL/markers.lst
	cat $CORPUS_MODEL/markers.lst | while read marker; do
		if [[ -f $CORPUS_TMP/held_tagged.txt ]]; then
			cat $CORPUS_TMP/held.tsv | sed "s/^[^\t]*$marker[^\t]*/1/g" | sed 's/^[^1=\t]*\t/=\t/' > $CORPUS_TMP/held_$marker.tsv
			MAXENT_HELD="--heldout=$CORPUS_TMP/held_$marker.tsv"
		fi
		cat $CORPUS_TMP/train.tsv | sed "s/^[^\t]*$marker[^\t]*/1/g" | sed 's/^[^1=\t]*\t/=\t/' > $CORPUS_TMP/train_$marker.tsv
		maxent -v -i 30 -g 1 -m $CORPUS_MODEL/model_$marker.txt $MAXENT_HELD $CORPUS_TMP/train_$marker.tsv >> $CORPUS_TMP/train.log 2>&1
	done
}

function heldMaxEntBin {
	echo 'Held retrieved from train.log files:'
	cat $CORPUS_TMP/train.log
}

function labelMaxEntBin {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -mbl $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged_ne.txt
	cat $CORPUS_TMP/text_tagged_ne.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

function learnSciKit {
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/applyRules.py -st $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/train.tsv 2>$CORPUS_MODEL/model_infos.tsv
	cat $CORPUS_TMP/train.tsv | $MXS_BIN/learnSciKit.py $CORPUS_MODEL/model_infos.tsv
}

function heldSciKit {
	echo '... testing on train corpus for comparison purposes'
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/applyRules.py -sh $CORPUS_MODEL/patterns.txt
	echo '... testing on held corpus'
	cat $CORPUS_TMP/held_tagged.txt | $MXS_BIN/applyRules.py -sh $CORPUS_MODEL/patterns.txt
}

function labelSciKit {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -sl $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged_ne.txt
	cat $CORPUS_TMP/text_tagged_ne.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

function learnSciKitBin {
	cat $CORPUS_TMP/train_tagged.txt | $MXS_BIN/applyRules.py -st $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/train.tsv 2>$CORPUS_MODEL/model_infos.tsv
	cat $CORPUS_TMP/train.tsv | $MXS_BIN/learnSciKitBin.py $CORPUS_MODEL/model_infos.tsv
}

function heldSciKitBin {
	echo '... not implemented yet!'
}

function labelSciKitBin {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -slb $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged_ne.txt
	cat $CORPUS_TMP/text_tagged_ne.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

function learnRules {
	echo 'No learn for Rules'
}

function heldRules {
	echo 'No held for Rules'
}

function labelRules {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -rl $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged_ne.txt
	cat $CORPUS_TMP/text_tagged_ne.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

function learnBayes {
	echo 'No learn for Bayes'
}

function heldBayes {
	echo 'No held for Bayes'
}

function labelBayes {
	cat $CORPUS_TMP/text_tagged.txt | $MXS_BIN/applyRules.py -bl $CORPUS_MODEL/patterns.txt > $CORPUS_TMP/text_tagged_ne.txt
	cat $CORPUS_TMP/text_tagged_ne.txt | $CORPUS_MERGE_SCRIPT | $CORPUS_OUTPUT_SCRIPT > $CORPUS_TMP/text_ne.txt
}

mine
prepare
tag

echo 'Done !'

echo 'Cleaning'
#/bin/rm -f $CORPUS_TMP/*
