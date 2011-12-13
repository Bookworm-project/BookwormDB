#!/usr/bin/R
rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")
#Testing for fictiveness.

n=5

  flagRandomBooks(n,1,whereclause = " aLanguage='eng'")
  flagRandomBooks(n,2,whereclause = " aLanguage='eng'",preclear=F)
  

lapply(1000:1025,function(n) {
  p = list(
      method = 'counts_query',
      smoothingType="None",
      groupings="stem,main.bookid,nwords,bflag",
      search_limits = list(
        list(
          'bflag' = list(1,2),
          'main.wordid' = list(n)
          )
       )
      )
        
frame = dbGetQuery(con,APIcall(p))
frame
})






Random_Dunning <- function (n) {
  flagRandomBooks(n,1,whereclause = " aLanguage='eng'")
  flagRandomBooks(n,2,whereclause = " aLanguage='eng'",preclear=F)
  
  p = list(
      method = 'counts_query',
      smoothingType="None",
      groupings="stem",
      search_limits = list(
        list(
          'bflag' = list(1)
          ),
        list(
          'bflag' = list(2)
          )
       ))
        
  queries=compare_groups(p)
  queries
  }
lapply(Random_Dunning(10),length)

system.time(Random_Dunning(500))

samples = lapply(
  c(seq(1,10,by=1),
    seq(10,100,by=10),
    seq(100,1000,by=100),
    seq(1000,10000,by=1000)),
  Random_Dunning)
backup = samples
names(samples) = c(seq(1,10,by=1),
    seq(10,100,by=10),
    seq(100,1000,by=100),
    seq(1000,10000,by=1000))
results = lapply(queries,function(query) {dbGetQuery(con,query)})
names = table(unlist(lapply(samples,function(sample) 
{lapply(sample,names)})))

framed = data.frame(names)
names(framed)[1]="stem"
differences = lapply(samples,function(result) {length(unlist(result))})
wordlist = dbGetQuery(con,"SELECT stem, sum(count) as count,min(IDF) as IDF FROM words WHERE wordid < 1000000 GROUP BY stem")

merged = merge(wordlist,framed,by='stem',all=T)

summary(merged)
merged$framed
plot(merged$count*merged$IDF,merged$Freq,log='xy',pch=16,col=rgb(.7,0,0,.02))
the = results
p[['search_limits']][[1]][['word']] = list('evolution')
queries=APIcall(p)
results = lapply(queries,function(query) {dbGetQuery(con,query)})[[1]]

merged = merge(the,results,by='bookid',all=T)
merged$count.y[is.na(merged$count.y)] = 1

ggplot(merged,
  aes(x=count.y/nwords.x,y=bookid
      )
  ) + 
    geom_point() 

results$stem = factor(results$stem)
stems = dbGetQuery(con,"SELECT stem FROM wordsheap  GROUP BY stem ORDER BY wordid LIMIT 100000")
results = results[results$stem %in% stems[,1],]

scores= corpus.mann.whitney(results)

hist(scores)
sort(scores)[1:25]
sort(-scores)[1:25]

corpus.mann.whitney <- function (z) {
  #This requires a data frame with entries for ''
  z$score = z$count/z$nwords
  z$bflag = factor(z$bflag)
  z$stem = factor(z$stem)
  z$bookid = factor(z$bookid)
  tab = table(z$stem)
  stems = names(tab)[tab>=length(levels(z$bookid))/100]
  z = z[z$stem %in% stems,]
  z$stem = factor(z$stem)
  cat("splitting frame...\n")
  framelist = split(z[,c('score','bflag')],z$stem,drop=T)
  lengtha=length(unique(z$bookid[z$bflag==1]))
  lengthb=length(unique(z$bookid[z$bflag==2]))
  mylengths = c(lengtha,lengthb) 
  totScores = (lengtha+lengthb)*(lengtha+lengthb+1)/2 
  cat("calculating scores...\n")
  scores = vapply(framelist,mann.whitney,.5)
}

mann.whitney <- function(seta,lengths=mylengths,TotalScoreSum=totScores) {
  loclengths = as.vector(table(seta$bflag))
  locScoreSum=nrow(seta)*(nrow(seta)+1)/2
  missingScores = TotalScoreSum-locScoreSum
  if(missingScores > 0) {
    missingScores = missingScores*(lengths- loclengths)[1]/sum(lengths-loclengths)
  }
  seta$rank = rank(seta$score)
  score = sum(seta$rank[seta$bflag==1]) + missingScores
  U = score - (lengths[1])*(lengths[1]+1)/2
  U/(lengths[1]*lengths[2])
}
