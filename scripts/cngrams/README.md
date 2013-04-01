# About #
The C++ package in this folder is my derivative work of this package: https://code.google.com/p/ngrams/

# Changes #
The changes I made to the package to make it play nice with Presidio are the following:

* Removed for loop to prevent it from calculating all ngrams from 1 to N by default. It now calculates only the ngrams for the value of N that is passed as an argument.
* Modified output structure to fit how the txt files holding ngrams in Presidio (i.e. files that get created in texts/unigrams/, /texts/bigrams/) are intended to be structured.
* For input text that contains numbers, rather than returning \<NUMBER\> for all number characters, the actual number is written as a string.
