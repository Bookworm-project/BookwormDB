#invoke with any of these variables, but particularly by specifying bookwormName: eg, `make bookwormName=OL`
threads = 4
bookwormName = "OL"
filesPerProcess = 100

all: files/targets/database

files/texts/unigrams: files/texts/raw
	mkdir -p files/texts/unigrams
	mkdir -p files/texts/bigrams
	mkdir -p files/texts/trigrams
	mkdir -p files/texts/encoded
	mkdir -p files/texts/encoded/unigrams
	mkdir -p files/texts/encoded/bigrams
	mkdir -p files/texts/encoded/trigrams
	mkdir -p files/targets
	#sh scripts/copyDirectoryStructures.sh

files/targets/tokenization: files/texts/input.txt
	mkdir -p files/texts/wordcounts
	cat files/texts/input.txt | parallel --block 10M --pipe python bookworm/tokenizer.py
	touch files/targets/tokenization

files/texts/wordlist/wordlist.txt:
	python bookworm/WordsTableCreate.py

files/metadata/jsoncatalog_derived.txt:
	#Create metadata files.
	python OneClick.py $(bookwormName) metadata

files/unigrams:
	find -L files/texts/raw/ -type f | sed 's/.*raw\///;s/.txt$$//' | xargs -P $(threads) -n $(filesPerProcess) perl scripts/makeUnigramsandBigrams.pl
	#Count the words--this takes a while, and could probably be optimized.
	#Here it actually encodes unigrams and bigrams.
	find -L files/texts/raw/ -type f | sed 's/.*raw\///;s/.txt$$//' | xargs -P $(threads) -n $(filesPerProcess) perl scripts/encodeAllTypes.pl
	#Create database files.


files/targets/database: files/targets/encoded files/texts/wordlist/wordlist.txt files/metadata/jsonatalog_derived.txt
	python OneClick.py $(bookwormName) database
	touch files/targets/database

files/targets/encoded: files/targets/tokenization
	#builds up the encoded lists.
	find files/texts/wordcounts -type f | parallel python bookworm/encoder.py {} 
	touch files/targets/encoded

all: files/targets/database

files/texts/input.txt:
	#This will build it from the normal layout.
	mkfifo files/texts/input.txt
	cat files/texts/textids/* | awk '{print $2}' | xargs -n 1 bash scripts/singleFileFromDirectories.sh > $@ &
	#mysql -B rateMyProfessors -e "SELECT ratingName,comment FROM RATINGS" > $@

#Specific junk to pull out.

files/metadata/jsoncatalog.txt:
	mysql -B rateMyProfessors -e "SELECT * FROM RATINGS JOIN TEACHERS USING(ID)" | python etc/metadataParsers/RMP.py > $@

