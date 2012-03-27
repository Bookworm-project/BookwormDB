#! /usr/bin/R

#This takes two API lists specifying words preceding a given word. 
setwd("/presidio/Rscripts")
source("Rbindings.R")
core_search = list(
  method = 'counts_query',
  smoothingType="None",      
  groupings='words1.stem',      
  words_collation = 'Case_Insensitive',
  tablename='master_bigrams',
  search_limits = 
    list(
      list(
        'alanguage'=list('eng'),
        'word2' = list('attention'),
        'word1' = list('')
        'country' = list("USA"),
        'year'    = as.list(1820:1840)
        )
  )
)


core_search = list(
  method = 'ratio_query',
  smoothingType="None",      
  groups=list('year','lc0'),      
  words_collation = 'Case_Insensitive',
  search_limits = 
    list(
      list(
        'word'=list('ice cream'),
        'lc0' = list('H','Q','P')
        )
  )
)
results = dbGetQuery(con,APIcall(core_search))
results = results[results$year<1922 & results$year > 1800,]
ggplot(results,aes(x=year,y=value,color=lc0)) + geom_line()

values = lapply( seq(1820,1920,by=10) , function(i) {
  core_search[['search_limits']][[1]][['year']] = as.list(i:(i+9))
  dbGetQuery(con,APIcall(core_search))
  })


allwords = dbGetQuery(con,"SELECT stem as word,sum(normcount) as count FROM words ORDER BY count DESC LIMIT 200000")

yearvalues = lapply(values,function(frame) {
  dunning = dun.with.merge(frame,allwords)
  words = names(dunning[dunning>20])
  })


lists = lapply(APIcall(core_search), function(query){dbGetQuery(con,query)})

allwords = dbGetQuery(con,"SELECT stem as word,sum(normcount) as count FROM words ORDER BY count DESC LIMIT 200000")
compared = dun.with.merge(dbGetQuery(con,APIcall(core_search)[[1]]),allwords)
compared = compare_groups(core_search,returnFrame=25)
compared


attention = dbGetQuery(con,APIcall(core_search)[[2]])


wordlist1 = search_terms
wordgrid("God")