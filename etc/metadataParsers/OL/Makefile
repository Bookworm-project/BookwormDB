
root = ../../..
files = $(root)/files
catinfo = $(files)/catinfo



downloads: $(root)/files/metadata/jsoncatalog.txt
	mkdir -p $(root)/files/downloads
	python OL_download.py

catinfo:
	mkdir -p $(files)
	mkdir -p $(catinfo)

$(catinfo)/: catinfo
	curl http://openlibrary.org/data/ol_dump_editions_latest.txt.gz

$(files)/metadata/field_descriptions.json:
	mv field_descriptions.json $(files)/metadata/field_descriptions.json

$(root)/metadata/catalog.json: $(catinfo)/ol_dump_editions_latest.txt
	mkdir -p $(root)/files/metadata
	python OLparser.py


$(catinfo)/ol_dump_editions_latest.txt: $(catinfo)
	#grep ocaid to keep it smaller and more relevant
	curl -L http://openlibrary.org/data/ol_dump_editions_latest.txt.gz | gunzip -c | grep ocaid > $(catinfo)/ol_dump_editions_latest.txt

$(catinfo)/ol_dump_authors_latest.txt: $(catinfo)
	curl -L http://openlibrary.org/data/ol_dump_authors_latest.txt.gz | gunzip -c > $(catinfo)/ol_dump_editions_latest.txt

$(catinfo)/ol_dump_editions_latest.txt: $(catinfo)
	curl -L http://openlibrary.org/data/ol_dump_editions_latest.txt.gz | gunzip -c > $(catinfo)/ol_dump_editions_latest.txt




#Phony targets for testing.

metadata: $(catinfo)/ol_dump_editions_latest.txt 
catalog: $(root)/metadata/catalog.json
authors: $(catinfo)/ol_dump_authors_latest.txt
