USE LOC;

CREATE TABLE IF NOT exists words (wordid INT AUTO_INCREMENT PRIMARY KEY,word VARCHAR(64),count BIGINT,casesens VARBINARY(64), INDEX (casesens));

CREATE TABLE rawWords (word VARCHAR(64),count INT);

LOAD DATA LOCAL INFILE '../texts/wordlist/raw.txt' INTO TABLE rawwords;

SELECT word,sum(count) as count FROM words GROUP BY word ORDER BY count DESC LIMIT 2000000 INTO outfile '/tmp/wordlist.txt';


