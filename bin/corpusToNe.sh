#!/bin/bash

# Reformat ne tags
sed -E 's#<(/?)NEm-([^>]*)>#<\1\2>#g'

