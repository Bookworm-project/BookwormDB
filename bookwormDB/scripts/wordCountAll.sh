#!/usr/bin/sh

#cat files/texts/textids/* | awk '{print $2}' | xargs -n 1000 -P 8 perl scripts/makeUnigramsandBigrams.pl > output.log
#This is going to be faster than anything we write in python, and take up about a tenth as much code. 
#And yet we'll probably end up having to write it in python just to keep the damned thing scripted. So sad.

find -L files/texts/raw/ -type f | sed "s/.txt//gi" | sed "s/.*raw\///gi" | xargs -n 2000 -P 8 perl scripts/makeUnigramsandBigrams.pl > output.log
