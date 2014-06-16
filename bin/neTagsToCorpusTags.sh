#!/bin/bash

sed -E 's#<(/?)([^>]*)># <\1NE-\2> #g' |
sed -E 's/  +/ /g'

