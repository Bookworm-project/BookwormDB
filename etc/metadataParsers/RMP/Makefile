all: ../../../files/metadata/jsoncatalog.txt ../../../files/texts/input.txt
clean:
	rm ../../../files/metadata/jsoncatalog.txt ../../../files/texts/input.txt

../../../files/metadata/jsoncatalog.txt:
	mysql -B rateMyProfessors -e "SELECT * FROM RATINGS JOIN TEACHERS USING(ID)" | python RMP.py > $@

../../../files/texts/input.txt:
	mysql -B rateMyProfessors -e "SELECT ratingName,comment FROM RATINGS" > $@
