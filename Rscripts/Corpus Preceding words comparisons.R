rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")

wordlist=list("attention")

search_terms = list(
  method = 'counts_query',
  smoothingType="None",      
  groupings='words1.word',      
  words_collation = 'Case_Sensitive',
  search_limits = 
    list(
     list(
      'word2' = wordlist,
      'alanguage' = list('eng'),
      'country' = list("USA"),
      'year' = as.list(1820:1835)
      ),
      list(
      'word2' = wordlist,
      'alanguage' = list('eng'),
      'country' = list("USA"),
      'year'    = as.list(1915:1922)
      )
     )
  )

values = lapply(APIcall(search_terms),dbGetQuery,conn=con)
merged = merge(values[[1]],values[[2]],by='word',all=T)
merged$diff = merged$count.x/merged$count.y
comparison = compare_groups(search_terms)
comparison[[1]][1:25]
