
all: ../../../files/texts/input.text


../../../files/texts/input.text:
	python XMLparser.py

../../../files:
	mkdir -p ../../../files

../../../files/raw: ../../../files
	mkdir -p $@
	#curl http://www.ibiblio.org/xml/examples/shakespeare/ | perl -ne 'if (m/href="(.+.xml)"/) {print "http://www.ibiblio.org/xml/examples/shakespeare/$1\n"}' | xargs wget
	mv *.xml ../../../files/raw

clean:
	rm ../../../files/texts/input.txt
	rm ../../../files/metadata/jsoncatalog.txt
