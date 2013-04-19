#This copies the directory structure of the 'raw' folder to all later folders.
#The directories are assumed to exist by the later scripts, although the files can be created.
#Can take a while with sufficiently complicated folder structures: currently only
#can be disabled by commenting relevant lines out.

#I have also just switched it from using 'rsync' to using 'find,' which should reduced the
#dependencies needed.

#rsync -a --include '*/' --exclude '*' files/texts/raw/ files/texts/cleaned;

echo "copying main directory (this will take the longest)"
cd files/texts/raw

find -L . -type d | xargs -I path mkdir -p ../cleaned/path

echo "making unigrams and bigrams"
cd ../cleaned
find -L . -type d | xargs -I path mkdir -p ../unigrams/path
find -L . -type d | xargs -I path mkdir -p ../bigrams/path

echo "making encoded directories"
find -L . -type d | xargs -I path mkdir -p ../encoded/unigrams/path
find -L . -type d | xargs -I path mkdir -p ../encoded/bigrams/path



cd ../../..

#find should be faster than rsync
#rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/unigrams;
#rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/bigrams;
#rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/encoded/unigrams;
#rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/encoded/bigrams;