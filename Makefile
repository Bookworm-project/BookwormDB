#invoke with any of these variables, but particularly by specifying bookwormName: eg, `make bookwormName=OL`

bookwormName="OL"
webDirectory="/var/www/"



#The data format may vary depending on how the raw files are stored. The easiest way is to simply pipe out the contents from input.txt: but any other method that produces the same format (a python script that unzips from a directory with an arcane structure, say) is just as good.
#The important thing, I think, is that it not insert EOF markers into the middle of your stream.
textStream=scripts/justPrintInputTxt.sh
webSite = $(addsuffix bookwormName,webDirectory)

all: bookworm.cnf files/targets files/targets/database

bookworm.cnf:
	python makeConfiguration.py

#These are all directories that need to be in place for the other scripts to work properly
files/targets: files/texts
	mkdir -p files/texts/encoded
	mkdir -p files/texts/encoded/unigrams
	mkdir -p files/texts/encoded/bigrams
	mkdir -p files/texts/encoded/trigrams
	mkdir -p files/texts/encoded/completed
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
	rm -rf files/targets
	rm -rf files/texts/wordlist
	rm -f files/metadata/jsoncatalog_derived.txt
	rm -f files/metadata/field_descriptions_derived.json

# The wordlist is an encoding scheme for words: it tokenizes in parallel, and should
# intelligently update an exist vocabulary where necessary.

files/texts/wordlist/wordlist.txt:
	$(textStream) | parallel --pipe python bookworm/printTokenStream.py | python bookworm/wordcounter.py

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

# The tokenization script dispatches a bunch of parallel processes to bookworm/tokenizer.py,
# each of which saves a binary file. The cat stage at the beginning here could be modified to 
# check against some list that tracks which texts we have already encoded to allow additions to existing 
# bookworms to not require a complete rebuild.

files/targets/encoded: files/texts/wordlist/wordlist.txt files/metadata/jsoncatalog_derived.txt
	#builds up the encoded lists that don't exist yet.
	$(textStream) | parallel --block 100M --pipe python bookworm/tokenizer.py
	touch files/targets/encoded

# The database is the last piece to be built: this invocation of OneClick.py
# uses the encoded files already written to disk, and loads them into a database.
# It also throws out a few other useful files at the end into files/

files/targets/database: files/targets/database_wordcounts files/targets/database_metadata 
	touch $@

files/targets/database_metadata: files/targets/encoded files/texts/wordlist/wordlist.txt files/targets/database_wordcounts
	python OneClick.py $(bookwormName) database_metadata
	touch $@

files/targets/database_wordcounts: files/targets/encoded files/texts/wordlist/wordlist.txt
	python OneClick.py $(bookwormName) database_wordcounts
	touch $@

# the bookworm json is created as a sideeffect of the database creation: this just makes that explicit for the webdirectory target.
# I haven't yet gotten Make to properly just handle the shuffling around: maybe a python script inside "etc" would do better.

files/$(bookwormNames).json: files/targets/database	

$(webDirectory)/$(bookwormName): files/$(bookwormName).json
	git clone https://github.com/econpy/BookwormGUI $@
	cp files/*.json $@/static/options.json



