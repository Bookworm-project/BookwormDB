setwd("/presidio/Rscripts")
source("Rbindings.R")


results = lapply(c(1825,1835),function(year) {
  lapply(c("USA","UK"),function(country) {
  search_terms = list(
    method = 'counts_query',
    groups=list('year'),      
    words_collation = 'Case_Sensitive',
    search_limits =
       list(
        'country' = list(country),
        'year' = list(year),
        'word' = list("Washington")
        #,'hasword' = list("butter")
        )
       )
  dbGetQuery(con,APIcall(search_terms))
}
         )})


merged = merge(results[[1]][[1]],results[[1]][[2]],by='word',all=T)
names(merged) = c("word","a1","a2")
merged = merge(merged,results[[2]][[1]],by='word',all=T)
names(merged) = c("word","a1","a2","a3")
merged = merge(merged,results[[2]][[2]],by='word',all=T)
names(merged) = c("word","a1","a2","b1","b2")

attach(merged)
merged$USchange = b1/a1
merged$UKchange = b2/a2
detach(merged)
attach(merged)
merged$diff = USchange/UKchange
merged$diff[is.na(merged$diff)] = 1
merged$word[merged$diff >= 20 & merged$a1 > 100][1:10]
merged[merged$word=='color',]