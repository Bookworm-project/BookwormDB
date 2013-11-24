files/texts/unigrams: files/texts/raw
	mkdir -p files/texts/unigrams
	mkdir -p files/texts/bigrams
	mkdir -p files/texts/encoded
	mkdir -p files/texts/encoded/unigrams
	mkdir -p files/texts/encoded/bigrams
	sh scripts/copyDirectoryStructures.sh


encoded: files/texts/raw
	find files/texts/raw/ -type f | sed 's/files\/texts\/raw\///;s/.txt$$//' | xargs -P 4 -n 100 perl scripts/makeUnigramsandBigrams.pl
