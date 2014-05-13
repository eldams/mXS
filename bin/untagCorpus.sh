#!/bin/bash

# Recover new items
sed -r 's|NEW/(NE/</?NE)|\1m|g' |
# Remove tags from items
sed -r 's#( |^)[^ \n]*[^<]/([^/ \n]*)#\1\2#g' |
# Finalize
sed -r 's| +| |g'

