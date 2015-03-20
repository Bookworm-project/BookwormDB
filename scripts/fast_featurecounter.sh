#!/usr/bin/env bash
# Usage:
#    htrc_wordcounter.sh [infile] [tmpdir] [blocksize]

# Important: Need to set locale in order to sort properly
export LC_ALL=C
infile=$1
# Explicitly set tmp directory to better manage disk needs
tmpdir=$2
blocksize=$3
outfile=$4
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

mkdir -p $tmpdir
cat $infile |\
parallel --block $blocksize -j95% --pipe --files --tempdir $tmpdir \
	awk '{print\ \$2\,\ \$3}' "|" sort "|" awk -f $DIR/mergecounted.awk >tmp1files.txt

# We've processed the files in a big batch, but in all likelihood, there's still too many
# of them to glob all together and sort. So, let's merge in batches of 30 and dedupe again
cat tmp1files.txt | parallel --files --tempdir $tmpdir -Xn30 -j95% \
	sort -m {} "|" awk -f scripts/mergecounted.awk ";" rm {} |\
	parallel -Xj1 sort -m {} "|" awk -f $DIR/mergecounted.awk ";" rm {} |\
	sort -n -r -k2 | awk 'BEGIN {i=0}{i+=1;print i "	" $1 "	" $2}' >$outfile # Format for bw

rm tmp1files.txt
