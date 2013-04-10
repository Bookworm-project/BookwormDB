#This copies the directory structure of the 'raw' folder to all later folders.
#The directories are assumed to exist by the later scripts, although the files can be created.
#Can take a while with sufficiently complicated folder structures: currently only
#can be disabled by commenting relevant lines out.
rsync -a --include '*/' --exclude '*' files/texts/raw/ files/texts/cleaned;
rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/unigrams;
rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/bigrams;
rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/encoded/unigrams;
rsync -a --include '*/' --exclude '*' files/texts/cleaned/ files/texts/encoded/bigrams;