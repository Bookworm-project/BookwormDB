rsync -a --include '*/' --exclude '*' ../texts/raw/ ../texts/cleaned;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/unigrams;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/bigrams;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/encoded/unigrams;
rsync -a --include '*/' --exclude '*' ../texts/cleaned/ ../texts/encoded/bigrams;