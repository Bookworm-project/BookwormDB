#!/usr/bin/R
#melville = dbConnect(MySQL())
melville=con
changefrom = function(n,basemat) {
  comparison = lag(n,basemat)
  basemat/comparison
}

lag = function(n,basemat) {
  compare_span = abs(n)
  comparison = matrix(NA,nrow = nrow(basemat),ncol = ncol(basemat),dimnames = dimnames(basemat))
  if (n<0) {
    comparison[-c(1:compare_span),] = basemat[1:(nrow(basemat)-compare_span),]
  }
  if (n>=0) {
    comparison[1:(nrow(basemat)-compare_span),] = basemat[-c(1:compare_span),]
  }
  comparison
}


return_matrix = function(
  sampling=100
  ,
  offset=95
  ,
  max=1000000
  ,
  min = 1
  ,
  grams=1
  ,
  wordInput=NULL,
  yearlim = c(1789,2008)
  ) {
  cat("Getting Counts from Database\n")
  if (grams == 1) {
    z = dbGetQuery(
      melville,
      paste("
      SELECT word1,year,words from presidio.1grams JOIN presidio.wordsheap ON 1grams.word1 = wordsheap.casesens 
      WHERE year >= 1780 AND year <= 2008 and (wordid -", offset,")/",
               sampling," = ROUND((wordid -", offset,")/",sampling,") and wordid < ",max,
               " AND wordid >= ",min,sep=""
      ))
  }
  
  if (grams==2 & is.null(wordInput)) {
        dbGetQuery(melville,"
               CREATE TABLE ngrams.tmplookup (word1  VARCHAR(33),word2 VARCHAR(33), 
               INDEX(word2,word1)) ENGINE=MEMORY")
        
      #Currently I've just coded one particular set of 2-grams in: should be generalized to allow better queries; but things like stopword exclusion is tricky.
    silent = dbGetQuery(melville,"UPDATE ngrams.2gramcounts SET wflag=0 WHERE wflag !=0")
    silent = dbGetQuery(melville,"UPDATE presidio.wordsheap JOIN presidio.words USING(wordid) SET wflag=1 WHERE stopword=1;")
    silent = dbGetQuery(melville,"
                        UPDATE ngrams.2gramcounts as g1 JOIN presidio.wordsheap as w1 ON w1.casesens = g1.word1 
                        JOIN presidio.wordsheap AS w2 ON w2.casesens = g1.word2
                        SET g1.wflag = 1 WHERE w1.wflag != 1 AND w2.wflag != 1")
    silent = dbGetQuery(melville,"UPDATE ngrams.2gramcounts SET wflag=0 WHERE wflag=1 AND words < 182516;")
  }
  
  if (grams==2 & !is.null(wordInput)) {
    #silent = dbGetQuery(melville,"UPDATE ngrams.2gramcounts SET wflag=0 WHERE wflag !=0")
    #The new strategy is to create a temporary table that can be joined in lieu of a real search.
    dbGetQuery(melville,"DROP TABLE IF EXISTS ngrams.tmplookup")
    dbGetQuery(melville,"
               CREATE TABLE ngrams.tmplookup (word1  VARCHAR(33),word2 VARCHAR(33), 
               INDEX(word2,word1)) ENGINE=MEMORY")
    dbGetQuery(melville,paste("INSERT INTO ngrams.tmplookup (word1,word2) VALUES ",
                              paste("(",apply(wordInput,1,function(row) {paste('"',row[1],'","',row[2],'"',sep="")})
                                    ,")",collapse=","),
                              ""))
    #phrases = paste("(",apply(wordInput,1,function(row) {whereterm(list(word1=row[1],word2=row[2]))}),")",collapse=" OR ")
    #silent = dbGetQuery(melville, paste("UPDATE ngrams.2gramcounts SET wflag=1 WHERE ",phrases))
  }
  
  if (grams==2) {
    z = dbGetQuery(melville,"
                        SELECT CONCAT(n1.word1,' ',n1.word2) as word1,year,n1.words FROM ngrams.2grams as n1 
                        JOIN ngrams.tmplookup as n2 ON n1.word1=n2.word1 AND n1.word2=n2.word2")
    z$word1 = factor(z$word1)
    z$words = as.numeric(z$words)          
    dbGetQuery(melville,"DROP TABLE ngrams.tmplookup")
  }                   
  totals = dbGetQuery(
    melville,
    "SELECT year,words from presidio.1grams WHERE word1='the'"
    )  
  
  #z$word1 = factor(z$word1)
  yearAppearances = table(z$word1)
  #Set some floors; it has to appear in 10 distinct years
  z = z[z$word1 %in% names(yearAppearances)[yearAppearances>10],]
  totcounts = xtabs(as.numeric(words) ~ word1,z)
  #And at least 500 times overall.
  z = z[z$word1 %in% names(totcounts)[totcounts>500],] 
  #xtabs takes up a _lot_ of memory, so I set a floor here: should probably become a variable somewhere. The rule is:
  #if a word doesn't appear in 50 years, it's probably not common enough that we're interested in it
  cat("Tabulating results")
  z = z[z$year >= yearlim[1],]
  z = z[z$year <= yearlim[2],]
  tabbed = xtabs(words~year+word1,z)
  
  tabbed = tabbed/totals$words[match(rownames(tabbed),totals$year)]*12*1000000
  tabbed
}

if (FALSE) { #Failed TF-IDF experiment
  words = dbGetQuery(con,"
  SELECT data.words,data.books,data.words/tot.words*LOG(tot.books/data.books) AS TFIDF,
                     CONCAT_WS(' ',2g.word1,2g.word2) as word,data.year
    FROM ngrams.2gramcounts as 2g JOIN
                     ngrams.2grams as data 
    JOIN (SELECT sum(words) as words,sum(books) as books,year
          FROM presidio.1grams WHERE word1='the' GROUP BY year) as tot
    ON tot.year=data.year AND data.word1 = 2g.word1 AND data.word2=2g.word2
    WHERE 2g.wflag=1 AND data.year > 1789")
    dat = xtabs(TFIDF ~ year+word,words)
   dim(dat)
    plot(rownames(dat),rowSums(dat))
    dim(words)
  rm(words)
  }

          