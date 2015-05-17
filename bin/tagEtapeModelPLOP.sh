#!/bin/bash

[[ -d $MXS_PATH ]] || export MXS_PATH=`pwd`
[[ -d $TREETAGGER_PATH ]] || source $MXS_PATH/bin/conf_machineExample.sh
source $MXS_PATH/bin/conf_EtapeModelPLOP.sh
$MXS_PATH/bin/tagSciKit.sh
