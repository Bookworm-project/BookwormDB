Some questions that may come up outside the purview of the tutorial?

How much RAM does Bookworm need?
-----------------------

4GB, let's say? There may be problems with lots of processors and low RAM; in these cases, the line in the Makefile setting the parallel chunk size.

A running installations also stores a number of files in memory.

How much disk space does Bookworm need?
------------------------------

Bookworm is quite disk-space intensive, to get the fastest possible lookups on the user end. I'll give an absolute worse-case scenario to test the limits here. If you're doing texts that are larger than these (here, the average text length is 43 words), the bloat will not be so bad. (Because the number of **distinct** words in the text increases as log(n), where n is the number of words in the text).

**As an upper limit,** take one very metadata-heavy corpus: each text is under a paragraph long with about 14 million texts. This means that the Bookworm file stroage will be at its worse; the tokenized wordcounts will usually be longer than the original documents, which is very rarely the case. 

## For a build.

The pure text files are 3 gigabytes: the intermediary files take up 56GB altogether. THe largest are the metadata (which in this case includes a couple different copies of each individual text); next are the binaries and the encoded load files, at about 5x the original files.

2.8G input.txt
14G	 files/texts/encoded
16G	 files/texts/binaries
23G	 files/metadata
229M	 files/texts/textids
114M	 files/texts/wordlist
118M	 files/texts/binaries/completed
33G	 files/texts
56G	 files


## Plus the database.

The database itself, if on the same machine, is another 42GB; and because MySQL needs scratch spaces for indexes, this particular example would need another 15GB available as scratch.

## For final storage

The final database takes up 42 GB. The largest files are the unigram **indexes**, which are 3x the size of the unigram **words**.

-rw-rw---- 1 mysql mysql  13G Apr 16 17:42 master_bookcounts.MYI
-rw-rw---- 1 mysql mysql 9.3G Apr 16 17:54 master_bigrams.MYI
-rw-rw---- 1 mysql mysql 6.5G Apr 16 17:45 master_bigrams.MYD
-rw-rw---- 1 mysql mysql 4.9G Apr 16 21:30 catalog.MYD
-rw-rw---- 1 mysql mysql 4.1G Apr 16 17:33 master_bookcounts.MYD
-rw-rw---- 1 mysql mysql 4.0G Apr 18 13:26 catalog.MYI
-rw-rw---- 1 mysql mysql 115M Apr 18 13:26 nwords.MYI
-rw-rw---- 1 mysql mysql  99M Apr 16 18:07 nwords.MYD
-rw-rw---- 1 mysql mysql  43M Apr 16 17:31 words.MYD


## Is this too much?

The structuring principle here has been that hard drive space is cheap, and user speed matters. There are a lot of optimizations possible that may slightly increase build time, but require susbstantially less space in the build. For the final storage, the ratio is different.