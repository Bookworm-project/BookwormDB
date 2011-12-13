#!/usr/bin/R
rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")
wordlist = list("evolution")
search_terms = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list('catalog.bookid as id, catalog.nwords as words','year'),      
    words_collation = 'Case_Insensitive',
    search_limits = 
      list(
       list(
        'word' = wordlist,
        'alanguage' = list('eng')
        )
       )
    )
  query = APIcall(search_terms)
  mainwords = dbGetQuery(con,query)
  mainwords$ratio = mainwords$count/mainwords$words * 1000000
plottable =    mainwords[sample(1:nrow(mainwords),1000),]
plottable =    mainwords[mainwords$year>1800 & mainwords$year < 2000,]
ggplot(plottable,
    aes(factor(year),ratio)) +
      geom_boxplot()  + scale_y_log10() 
ylim(0,2000)

      geom_jitter(color='red',alpha=.09) + 
      geom_smooth(span=.4,size = 1,se=F,fullrange=T) +
      xlim(1800,2000) + 
      ylim(0,2000)
      
