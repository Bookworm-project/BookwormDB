all: ~/Presidio/files/metadata/jsoncatalog.txt ~/Presidio/files/texts/input.txt
clean:
	rm ~/Presidio/files/metadata/jsoncatalog.txt ~/Presidio/files/texts/input.txt

~/Presidio/files/metadata/jsoncatalog.txt:
	mysql -B rateMyProfessors -e "SELECT * FROM RATINGS JOIN TEACHERS USING(ID)" | python RMP.py > $@

~/Presidio/files/texts/input.txt:
	mysql -B rateMyProfessors -e "SELECT ratingName,comment FROM RATINGS" > $@
