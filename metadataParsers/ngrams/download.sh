cd ../../../texts/raw/

for i in {0..9}; do 
test -e googlebooks-eng-all-1gram-20090715-$i.csv.zip  && wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-all-1gram-20090715-$i.csv.zip || echo "" &

done;

for i in {0..99}; do 
test -e googlebooks-eng-all-2gram-20090715-$i.csv.zip  && wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-all-2gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..9}; do 
test -e googlebooks-eng--us-all-1gram-20090715-$i.csv.zip  && wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-us-all-1gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..99}; do 
test -e googlebooks-eng--us-all-2gram-20090715-$i.csv.zip  && wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-us-all-2gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..9}; do 
test -e googlebooks-eng-1M-all-1gram-20090715-$i.csv.zip  && wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-1M-all-1gram-20090715-$i.csv.zip || echo "" & 
done;

for i in {0..99}; do
test -e googlebooks-eng-1M-all-2gram-20090715-$i.csv.zip  && wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-1M-all-2gram-20090715-$i.csv.zip || echo "" & 
done;




unzip '*.zip'
