#Dunning bigrams
setwd("/presidio/Rscripts")
source("Rbindings.R")



compare_group_bigrams = function(limitsa,limitsb) {
  dbGetQuery(con,"UPDATE wordsheap SET wflag=0")
  dbGetQuery(con,"UPDATE wordsheap,words SET wflag=1 WHERE stopword=1 and wordsheap.wordid=words.wordid")
  dbGetQuery(con,"UPDATE wordsheap SET wflag=1 WHERE stem is null")


  base_query = list(
  method = 'counts_query',
  smoothingType="None",      
  groups=list('words1.word as w1','words2.word as w2'),      
  words_collation = 'Flagged',
  search_limits = 
    list(

  )
  )

  results = lapply(list(limitsa,limitsb), function(limits) {
    mesearch=base_query
    mesearch[['search_limits']][[1]] = limits
    mesearch[['search_limits']][[1]][['word1']] = list('uncommon')
    mesearch[['search_limits']][[1]][['word2']] = list('vocabulary')
    query = dbGetQuery(con,APIcall(mesearch))
    query$phrase = paste(query$w1,query$w2)
    frame = data.frame(phrase = query$phrase,count = query$count)
    frame[frame$count>1,]
  })
  comped = dun.with.merge(results[[1]],results[[2]])
}
  
                   
comped = compare_group_bigrams(limitsa =       list(
        'alanguage'=list('eng'),
        'country' = list("USA"),
        'year'    = as.list(1990)
        ),
limitsb = list(
        'alanguage'=list('eng'),
        'country' = list("USA"),
        'year'    = as.list(2000)
        ))