#!/usr/bin/R
rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")
dbGetQuery(con,"UPDATE catalog SET bflag=0")
for (year in 1775:2000) {
    flagRandomBooks(200,1,
    whereclause = paste(
      " aLanguage='eng' AND country='USA'",
      "AND year =",year),preclear=F)
} 
search_terms = list(
  method = 'ratio_query',
  smoothingType="None",      
  groups=list('year','catalog.bookid as id'),      
  words_collation = 'Case_Insensitive',
  search_limits = 
    list(
     list(
      'word' = list("evolution"),
      'alanguage' = list('eng'),
      'country' = list("USA"),
      'bflag' = list(1)
      )
     )
  )

vals = dbGetQuery(con,APIcall(search_terms))
years=unique(vals$year)
splitted = lapply(years,function(year) {vals[vals$year==year,]})
names(splitted) = years
splitted = splitted[sapply(splitted,nrow)>25]

vals = sapply(1:length(splitted),function(n) 
  {quantile(splitted[[n]]$value,.9)})
plot(names(splitted),vals,type='l',ylim = c(0,250))
framed = data.frame(year = names(splitted),quantile=vals)
search_terms = list(
  method = 'ratio_query',
  smoothingType="None",      
  groups=list('year'),      
  words_collation = 'Case_Insensitive',
  search_limits = 
    list(
     list(
      'word' = list("evolution"),
      'alanguage' = list('eng'),
      'country' = list("USA"),
      'bflag' = list(1)
      )
     )
  )

oldstyle = dbGetQuery(con,APIcall(search_terms))
framed$year = as.numeric(framed$year)
plot(framed)