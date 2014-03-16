#!/bin/bash

#This is super-simple; it just takes a filename and converts it into the format that the line-style slurper likes.

filename=$1
filetext=$(cat files/texts/raw/$filename.txt | sed 's/[\n\r]//g')
echo "$filename	$filetext" 
