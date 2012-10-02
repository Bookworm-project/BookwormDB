cd ../../../texts/raw/

for i in {0..9}; do 
[ -f googlebooks-eng-all-1gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-all-1gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..99}; do 
[ -f googlebooks-eng-all-2gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-all-2gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..199}; do 
[ -f googlebooks-eng-all-3gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-all-3gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..9}; do 
[ -f googlebooks-eng--us-all-1gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-us-all-1gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..99}; do 
[ -f googlebooks-eng--us-all-2gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-us-all-2gram-20090715-$i.csv.zip || echo "" &
done;

for i in {0..9}; do 
[ -f googlebooks-eng-1M-all-1gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-1M-all-1gram-20090715-$i.csv.zip || echo "" & 
done;

for i in {0..99}; do
[ -f googlebooks-eng-1M-all-2gram-20090715-$i.csv ] || wget http://commondatastorage.googleapis.com/books/ngrams/books/googlebooks-eng-1M-all-2gram-20090715-$i.csv.zip || echo "" & 
done;




unzip '*.zip'
