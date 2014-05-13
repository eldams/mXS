#!/bin/bash

# Reformat ne tags
sed -r 's#<(/?)NEm-([^>]*)>#<\1\2>#g'

