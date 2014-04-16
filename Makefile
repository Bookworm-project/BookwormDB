#invoke with any of these variables, but particularly by specifying bookwormName: eg, `make bookwormName=OL`

bookwormName="OL"
webDirectory="/var/www/"

#The data format may vary depending on how the raw files are stored. The easiest way is to simply pipe out the contents from input.txt: but any other method that produces the same format (a python script that unzips from a directory with an arcane structure, say) is just as good.
#The important thing, I think, is that it not insert EOF markers into the middle of your stream.
textStream=scripts/justPrintInputTxt.sh


webSite = $(addsuffix bookwormName,webDirectory)

oldFormat: files/texts/input.txt files/targets/database
all: files/targets files/targets/database

#These are all directories that need to be in place for the other scripts to work properly
files/targets: files/texts
	mkdir -p files/texts/binaries
	mkdir -p files/texts/binaries/completed
	mkdir -p files/texts/encoded
	mkdir -p files/texts/encoded/unigrams
	mkdir -p files/texts/encoded/bigrams
	mkdir -p files/texts/encoded/trigrams
	mkdir -p files/targets
	mkdir -p files/texts/wordlist

#A "make clean" removes everything created by the bookworm.
#This can be dangerous
#It doesn't do a drop database, though, because that could be even more dangerous.
#But this won't ensure consistency with earlier versions.

clean:
	#Remove inputs.txt if it's a pipe.
	find files/texts -maxdepth 1 -type p -delete
	rm -rf files/texts/encoded/*
	rm -rf files/targets/*
	rm -rf files/texts/binaries/*
	mkdir -p files/texts/binaries/completed
	rm -rf files/texts/wordlist/*
	rm -f files/metadata/jsoncatalog_derived.txt
	rm -f files/metadata/field_descriptions_derived.json


# The tokenization script dispatches a bunch of parallel processes to bookworm/tokenizer.py,
# each of which saves a binary file. The cat stage at the beginning here could be modified to 
# check against some list that tracks which texts we have already encoded to allow additions to existing 
# bookworms to not require a complete rebuild.

files/targets/tokenization: files/metadata/jsoncatalog_derived.txt
	$(textStream) | parallel --block 30M --pipe python bookworm/tokenizer.py
	touch files/targets/tokenization

# The wordlist is an encoding scheme for words: it uses the tokenizations, and should
# intelligently update an exist vocabulary where necessary.

files/texts/wordlist/wordlist.txt: files/targets/tokenization
	python bookworm/WordsTableCreate.py

# This invokes OneClick on the metadata file to create a more useful internal version
# (with parsed dates) and to create a lookup file for textids in files/texts/textids

files/metadata/jsoncatalog_derived.txt:
	#Create metadata files.
	python OneClick.py $(bookwormName) metadata

# This is the penultimate step: creating a bunch of tsv files 
# (one for each binary blob) with 3-byte integers for the text
# and word IDs that MySQL can slurp right up.

# This could be modified to take less space/be faster by using named pipes instead
# of pre-built files inside the files/targets/encoded files: it might require having
# hundreds of blocked processes simultaneously, though, so I'm putting that off for now.

files/targets/encoded:  files/targets/tokenization files/texts/wordlist/wordlist.txt
	#builds up the encoded lists that don't exist yet.
	find files/texts/binaries -type f -maxdepth 1 | parallel -m python bookworm/encoder.py {} 
	touch files/targets/encoded

# The database is the last piece to be built: this invocation of OneClick.py
# uses the encoded files already written to disk, and loads them into a database.
# It also throws out a few other useful files at the end into files/

files/targets/database: files/targets/encoded files/texts/wordlist/wordlist.txt
	python OneClick.py $(bookwormName) database
	touch files/targets/database

# input.txt is standard format for bringing in data. The old standard was a bunch of individual files in folders:
# this creates a named pipe that will transparently convert an old-format bookworm into a new one.
# There is not yet, but should be, a method to do the same for a zipped archive. (and/or a .tar.gz archive).

#files/texts/input.txt: files/metadata/jsoncatalog_derived.txt
	#This will build it from the normal layout.
	#dynamically. Possibly slower, though.
#	mkfifo files/texts/input.txt
#	cat files/texts/textids/* | perl -ne "print unless m/[']/g" | awk '{print $$2}' | xargs -n 1 bash scripts/singleFileFromDirectories.sh > $@ &


# the bookworm json is created as a sideeffect of the database creation: this just makes that explicit for the webdirectory target.
# I haven't yet gotten Make to properly just handle the shuffling around: maybe a python script inside "etc" would do better.

files/$(bookwormNames).json: files/targets/database	

$(webDirectory)/$(bookwormName): files/$(bookwormName).json
	git clone https://github.com/econpy/BookwormGUI $@
	cp files/*.json $@/static/options.json



