#!/bin/bash

sed -r 's#<(/?)([^>]*)># <\1NE-\2> #g' |
sed -r 's/  +/ /g'

