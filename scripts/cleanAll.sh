cat files/texts/textids/* | awk '{print $2}' | xargs -n 1000 -P 8 perl scripts/bulkCleanText.pl > output.log
