#!/bin/sh

#test for input.txt; if it doesn't exist, use every file in /files/texts/raw as an input per the old input format.

[ -f files/texts/input.txt ] && 
   cat files/texts/input.txt || 
   find files/texts/raw/ | perl -pe 's/files\/texts\/raw\/(.*).txt/$$1/g' | xargs bash scripts/singleFileFromDirectories.sh {}
