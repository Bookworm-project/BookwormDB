#!/bin/sh

#test for input.txt; if it doesn't exist, check if there's one the level just above: finally, use every file in /files/texts/raw as an input per the old input format.

if [ -f files/texts/input.txt ]; then
    echo "Using stored input.txt file" 1>&2
    cat files/texts/input.txt

else

    if [ -f ../input.txt ]; then
	echo "Reading input.txt from single file at the directory above this" 1>&2
	cat ../input.txt
    else
	echo "Reading in a file at a time from files/texts/raw: note that this method may be slow on more than a few hundred thousand texts" 1>&2
        find -L files/texts/raw -name "*.txt" | perl -pe 's/.*files\/texts\/raw\/(.*).txt/$1/g' | xargs -I filename bash scripts/singleFileFromDirectories.sh filename
    fi
fi
