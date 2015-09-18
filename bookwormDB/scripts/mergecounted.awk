#/usr/bin/awk -f
# Awk script to merge sorted "word\tcount" files.
# Speed is the reason necessitating awk.
BEGIN {start = 1;} { word = $1; 
if (last == word) { sum += $2; } 
else { 
	if (!start) print last " " sum
	else start = 0; last=word; sum = $2;
     }
} END { print last " " sum } 
