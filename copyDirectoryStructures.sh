#This copies the directory structure of the 'raw' folder to all later folders.
#The directories are assumed to exist by the later scripts, although the files can be created.
#Can take a while with sufficiently complicated folder structures: currently only
#can be disabled by commenting relevant lines out.
rsync -a --include '*/' --exclude '*' ../texts/raw/ ../texts/cleaned;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/unigrams;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/bigrams;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/encoded/unigrams;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/encoded/bigrams;