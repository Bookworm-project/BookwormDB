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
      paste("SELECT word1,year,words from presidio.1grams JOIN presidio.wordsheap ON 1grams.word1 = wordsheap.casesens 
      WHERE year >= 1780 AND year <= 2008 and (wordid -", offset,")/",
               sampling," = ROUND((wordid -", offset,")/",sampling,") and wordid < ",max,
               " AND wordid >= ",min,sep=""
      ))
  }
  
  if (grams==2) {
    dbGetQuery()
    z = dbGetQuery(
               melville,
      paste("SELECT word1,word2,year,words from ngrams.2grams as 2g JOIN presidio.wordsheap as w1 ON 2g.word1 = w1.casesens JOIN presidio.wordsheap as w2 ON 2g.word2=w1.casesens WHERE w1.wflag=1 AND w2.wflag=1"
      ))
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
          