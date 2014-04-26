#!/bin/sh

#test for input.txt; if it doesn't exist, use every file in /files/texts/raw as an input per the old input format.

if [ -f files/texts/input.txt ]; then
   cat files/texts/input.txt
else
    find -L files/texts/raw -name "*.txt" | perl -pe 's/.*files\/texts\/raw\/(.*).txt/$1/g' | xargs -I filename bash scripts/singleFileFromDirectories.sh filename
fi
