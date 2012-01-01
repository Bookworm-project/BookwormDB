melville = dbConnect(MySQL(),
                host="melville.seas.harvard.edu",
                password="oldPassword",
                user="oldUser",
                db="presidio")

dbGetQuery(melville,"CREATE TABLE 2grams (
           word1 VARBINARY(255), INDEX (word1(15),word2(15),year,words),
           word2 VARBINARY(255), INDEX (word2(15),word1(15)),
           year MEDIUMINT, INDEX(year,words,word1(15),word2(15)),
           words INT,
           pages INT,
           books INT) DATA DIRECTORY = '/media/omoo/mysql'
           INDEX DIRECTORY = '/media/omoo/mysql' 
           ENGINE = MyISAM"); dbGetQuery(melville,"ALTER TABLE 2grams DISABLE KEYS")

           
dbGetQuery(melville,"CREATE TABLE 1grams (
           word1 VARBINARY(255), INDEX (word1,year,words),
           year MEDIUMINT, INDEX (year,words,word1),
           words INT,
           pages INT,
           books INT) DATA DIRECTORY = '/media/omoo/mysql'
           INDEX DIRECTORY = '/media/omoo/mysql' 
           ENGINE = MyISAM");dbGetQuery(melville,"ALTER TABLE 1grams DISABLE KEYS")

           
#dbGetQuery(melville,"DROP TABLE 1grams")
#dbGetQuery(melville,"DROP TABLE 2grams")
#perl -pi -e 's/ /\t/gi' /media/mardi/ngrams/googlebooks-eng-all-2gram*.csv 

#Load in each of the 1grams files.
for (i in 0:9) {
  dbGetQuery(melville,paste("LOAD DATA INFILE '/media/omoo/ngrams/googlebooks-eng-all-1gram-20090715-",i,".csv' 
           INTO TABLE 1grams FIELDS ESCAPED BY ''",sep="")    )     
  cat("now working on ",i)
           }
dbGetQuery(melville,"SELECT * FROM 1grams LIMIT 1;")
dbGetQuery(melville,"ALTER TABLE 1grams ENABLE KEYS")
dbGetQuery(melville,"CREATE TABLE 2grams (
           word1 VARBINARY(255), INDEX (word1(15),word2(10),year,words),
           word2 VARBINARY(255), INDEX (word2(15),word1(10),year,words),
           year MEDIUMINT, INDEX(year,words,word1(15),word2(10)),
           words INT,
           pages INT,
           books INT) DATA DIRECTORY = '/media/omoo/mysql'
           INDEX DIRECTORY = '/media/omoo/mysql' 
           ENGINE = MyISAM"); dbGetQuery(melville,"ALTER TABLE 2grams DISABLE KEYS")

           
for (i in 0:99) {
  dbGetQuery(melville,paste("LOAD DATA INFILE '/media/omoo/ngrams/googlebooks-eng-all-2gram-20090715-",i,".csv' 
           INTO TABLE 2grams FIELDS ESCAPED BY ''",sep="")    )     
  cat("now working on\n",i)
           } 
dbGetQuery(melville,"ALTER TABLE 2grams ENABLE KEYS")


dbGetQuery(melville,"CREATE TABLE 2gramcounts (
           word1 VARBINARY(255), INDEX (word1(15),word2(10),year,words),
           word2 VARBINARY(255), INDEX (word2(15),word1(10),year,words),
           year MEDIUMINT, INDEX(year,words,word1(15),word2(10)),
           words INT,
           pages INT,
           books INT) DATA DIRECTORY = '/media/omoo/mysql'
           INDEX DIRECTORY = '/media/omoo/mysql' 
           ENGINE = MyISAM"); dbGetQuery(melville,"ALTER TABLE 2grams DISABLE KEYS")



#dbGetQuery(melville,"DROP TABLE 2grams")