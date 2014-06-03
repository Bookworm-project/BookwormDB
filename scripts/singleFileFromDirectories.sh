#!/bin/bash

#This is super-simple; it just takes a filename and converts it into the format that the line-style slurper likes.

filename=$1
echo "$filename	$(cat files/texts/raw/$filename.txt | perl -pe 's/[\n\r]/ /g')"
