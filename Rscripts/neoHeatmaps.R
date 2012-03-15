rm(list=ls())
setwd("/presidio")
source("Rbindings.R")

words = list("bank","banks")
search_terms = list(method = 'ratio_query',
      smoothingType="None",      
      groupings='author_age,year',      
      words_collation = 'Case_Insensitive',
      search_limits = 
        list(
         list(
          'word'=words,
          'alanguage'=list('eng'))
     ))

agemat = dbGetQuery(con,APIcall(search_terms))