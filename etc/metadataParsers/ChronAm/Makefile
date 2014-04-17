targets=$(addprefix downloads/,$(shell curl http://chroniclingamerica.loc.gov/ocr.json | perl -ne 'if (m/"name": ?"(.*)"/) {print "$$1\n"}'))

all: $(targets)

downloads/%.tar.bz2:
	curl -o $@ $(subst downloads/,http://chroniclingamerica.loc.gov/data/ocr/,$@)

../../../input.txt:
	mkfifo ../../../input.txt
	python parseBZ2.py


metadata:
	curl -o newspapers.rdf http://chroniclingamerica.loc.gov/newspapers.rdf


