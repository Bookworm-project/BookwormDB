#invoke with any of these variables, but particularly by specifying bookwormName: eg, `make bookwormName=OL`
threads = 4
bookwormName = "OL"
filesPerProcess = 100

files/texts/unigrams: files/texts/raw
	mkdir -p files/texts/unigrams
	mkdir -p files/texts/bigrams
	mkdir -p files/texts/encoded
	mkdir -p files/texts/encoded/unigrams
	mkdir -p files/texts/encoded/bigrams
	sh scripts/copyDirectoryStructures.sh


testSettings:
	echo $(bookwormName)

encoded: files/texts/raw
	#Create metadata files.
	python OneClick.py $(bookwormName) metadata
	#Rather than call the one click method, these three lines in shell allow us much more parallelism than would be easily possible in python.
	#The next three lines could be replaced by `python OneClick.py $(bookwormName) 
	find -L files/texts/raw/ -type f | sed 's/.*raw\///;s/.txt$$//' | xargs -P $(threads) -n $(filesPerProcess) perl scripts/makeUnigramsandBigrams.pl
	#Count the words--this takes a while, and could probably be optimized.
	python bookworm/WordsTableCreate.py
	#Here it actually encodes unigrams and bigrams.
	find -L files/texts/raw/ -type f | sed 's/.*raw\///;s/.txt$$//' | xargs -P $(threads) -n $(filesPerProcess) perl scripts/encodeAllTypes.pl
	#Create database files.
	python OneClick.py $(bookwormName) database

