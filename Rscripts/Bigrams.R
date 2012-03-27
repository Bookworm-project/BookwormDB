rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")

wordlist = list('competition')
comparelist = list('carriage','language','advantage','passage')
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
      'country' = list("USA")
      )
     )
  )
query = APIcall(search_terms)
mainwords = dbGetQuery(con,query)

compare_terms = search_terms
compare_terms[['search_limits']][[1]][['word2']] = comparelist
query = APIcall(compare_terms)
comparison = dbGetQuery(con,query)

dunning.comparison = dun.with.merge(mainwords,comparison)

sort(-dunning.comparison)[1:25]
dunwords = names(sort(-dunning.comparison))[1:150]
dunwords.competition = c("free","keen","unfair","fair","active","foreign","fierce","successful",
             "sharp","direct","increased","ruinous","water","industrial",
             "international","intense","open","effective","domestic","destructive",
             "excessive","increasing","potential","severe","healthy",
             "commercial","market","railroad","unlimited","cutthroat",
             "business","American","perfect","friendly","serious","global",
             "unrestrained","restricting","growing","unregulated","economic",
             "local","athletic","honorable","legitimate","wasteful","keener",
             "lively","close","strenuous","unequal","individual")
flagWordids(dunwords,field="casesens")

year_search = list(
  method = 'counts_query',
  smoothingType="None",      
  groupings='words1.word,year',      
  words_collation = 'Case_Sensitive',
  search_limits = 
    list(
     list(
      'words1.wflag' = list(1),
      'word2' = wordlist,
      'alanguage' = list('eng'),
      'country' = list("USA")
      )
     )
  )
yearly.frame = dbGetQuery(con,APIcall(year_search))
yearly.frame = yearly.frame[
  yearly.frame$year > 1821 & 
  yearly.frame$year < 1923,]
melted = melt(yearly.frame[1:25,],c('word','year'),'count')
casted = cast(melted,year+word~variable)
matrified = xtabs(count ~ year+word,yearly.frame)
matrified = matrified[,colSums(matrified)>=100]

matrified = 100*matrified/rowSums(matrified)
#ratio = apply(matrified,2,function(col) {col/sum(col)})
p = kmeans(cor(matrified),12)

melted = melt(matrified)
melted$cluster = p$cluster[match(melted$word,names(p$cluster))]
names(melted)[1] = "year"

a = lapply(1:12,function(num) {
my_data = melted[num==melted$cluster,]
my_data$word = factor(my_data$word)
ggplot(
  my_data,
  aes(x=year,y=value,color=word)) +  
    geom_line(size=.1) +
    geom_smooth(span=.4,size = 1,se=F,fullrange=T) 
    })

require(gridExtra)
do.call(grid.arrange,a)

query = APIcall(search_terms)
fullcounts = dbGetQuery(con,query)
topwords = list[order(-list[,2]),1][1:100]

names(fullcounts)[1] = 'word'
fullcounts = fullcounts[fullcounts$word %in% topwords,]
fullcounts$word = factor(fullcounts$word)
fullcounts$bookid = factor(fullcounts[,2])
unsparse = xtabs(count ~ bookid+word,fullcounts)
#rm(fullcounts)
unsparse = unsparse/rowSums(unsparse)
#percentages = t(t(unsparse)/colSums(unsparse))
#rm(unsparse)

covarians = cov(unsparse)

gplot(covarians,
      label=rownames(covarians),
      mode='kamadakawai',
      edge.col=rgb(.7,.7,.7,0),
      label.pos=5,
      label.col=rgb(0,0,0,.5),
      displayisolates=F,
      boxed.labels=F,
      vertex.cex=0,vertex.col='white'
      )



dunning.comparison = dun.with.merge(theory,fact)
benlog = function(scores) {
  scores[scores==0] = min(abs(scores[scores!=0]))
  convert = log(abs(scores))
  
}


data.frame(Theory = names(sort(dunning.comparison)[1:50]),theory = names(rev(sort(dunning.comparison))[1:50]))
