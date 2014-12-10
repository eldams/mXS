#!/bin/bash

# Recover new items
sed -E 's|NEW/(NE/</?NE)|\1m|g' |
# Remove tags from items
sed -E 's#( |^)[^ ]*[^<]/([^/ ]*)#\1\2#g' |
# Finalize
sed -E 's| +| |g'

