
#!/usr/bin/sh

#just clone the whole guy in there--probably a better way to do this.
#The dot keeps it from copying into itself.

curl -o HistoryDiss.tar.gz chaucer.fas.harvard.edu/HistoryDiss.tar.gz
tar -zxf HistoryDiss.tar.gz
rm HistoryDiss.tar.gz

mkdir files
mv files oldfiles
mv .presidio HistoryDiss/presidio

cd HistoryDiss/presidio

#This will drop any databases called "historyDissTest"
echo "DROP DATABASE IF EXISTS HistoryDissTest;" | mysql mysql
python OneClick.py HistoryDissTest test password > results.txt

echo "Delete the files (you should only keep to check for errors)"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) rm -r files; mv oldfiles files; break;;
        No ) exit;;
    esac
done
