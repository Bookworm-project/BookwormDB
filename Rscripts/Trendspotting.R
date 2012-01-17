#!/usr/bin/R
melville = dbConnect(MySQL())
changefrom = function(n,basemat) {
  compare_span = abs(n)
  comparison = matrix(NA,nrow = nrow(basemat),ncol = ncol(basemat),dimnames = dimnames(basemat))
  if (n<0) {
    comparison[-c(1:compare_span),] = basemat[1:(nrow(basemat)-compare_span),]
  }
  if (n>=0) {
    comparison[1:(nrow(basemat)-compare_span),] = basemat[-c(1:compare_span),]
  }
  basemat/comparison
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
  
  if (grams==2) {
    #silent = dbGetQuery(melville,"UPDATE ngrams.2gramcommon SET wflag=0")
    #silent = dbGetQuery(melville,"UPDATE presidio.wordsheap JOIN presidio.words USING(wordid) SET wflag=1 WHERE stopword=1;")
    #silent = dbGetQuery(melville,"
    #                    UPDATE ngrams.2gramcommon as g1 JOIN presidio.wordsheap as w1 ON w1.casesens = g1.word1 
    #                    JOIN presidio.wordsheap AS w2 ON w2.casesens = g1.word2
    #                    SET g1.wflag = 1 WHERE w1.wflag != 1 AND w2.wflag != 1")
    #silent = dbGetQuery(melville,"UPDATE ngrams.2gramcommon SET wflag=0 WHERE wflag=1 AND words < 182516;")
    z = dbGetQuery(melville,"
                        SELECT n1.word1,n1.word2,year,n1.words FROM ngrams.2grams as n1 
                        JOIN ngrams.2gramcommon as n2 ON n1.word1=n2.word1 AND n1.word2=n2.word2
                        WHERE n2.wflag=1")
    z$word1 = paste(z$word1,z$word2)
  }       
            
  totals = dbGetQuery(
    melville,
    "SELECT year,words from presidio.1grams WHERE word1='the'"
    )  
  
            
  z$word1 = factor(z$word1)
  counts = table(z$word1)           
  z = z[z$word1 %in% names(counts)[counts>50],]
  z$word1 = factor(z$word1)
  z$words = as.numeric(z$words)
  cat("Tabulating results")
  tabbed = xtabs(words~year+word1,z)
  
  tabbed = tabbed/totals$words[match(rownames(tabbed),totals$year)]*12*1000000
  tabbed
}
          