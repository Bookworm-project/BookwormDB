setwd('/presidio/Rscripts')
rm(list=ls())
source("Rbindings.R")
source('Word Spread.R')
source("Trendspotting.R")
require(zoo)

#First I get some words from elsewhere


melville = dbConnect(MySQL())
dbGetQuery(melville,"USE ngrams")
date()
     
window = 3
window = (floor(window/2)*2 + 1)
tabbed = return_matrix(sampling=1,offset=0,max=10000,min=1,grams=1)

smoothed = apply(tabbed,2,rollmedian,k=window,na.pad=T)
          rownames(smoothed) = as.numeric(rownames(tabbed)[1:nrow(smoothed)])
rownames(smoothed) = as.numeric(rownames(tabbed)[1:nrow(smoothed)])

yearlim = c(1850,1921)
cors = apply(
  smoothed[which(rownames(smoothed)==yearlim[1]):which(rownames(smoothed)==yearlim[2]),],2,
  cor,method='pearson',y=yearlim[1]:yearlim[2])

change  = changefrom(yearlim[1]-yearlim[2],smoothed)[rownames(tabbed) == yearlim[2],]
increasing = cors> .75 & change > 2

words = names(which(increasing))
#rm(tabbed)
#rm(smoothed)

words = words[grep("[^\\d\\w]",words,perl=T,invert=T)]

dim(words)
agedata = function(word,counttype = 'Occurrences_per_Million_Words',comparison_words=list()) {
  cat(word,"\n")
  f = genreplot(list(word),
            grouping='author_age',
            groupings_to_use = 63,
            counttype = counttype,
            #counttype = 'Occurrences_per_Million_Words',
            ordering=NULL,
            years=c(1850,1922),
            smoothing=7,
            comparison_words = comparison_words,
            words_collation='Case_Sensitive') + opts(title=word)
  f$data$birth = f$data$year-f$data$groupingVariable
  #f$data$groupingVariable = as.numeric(f$data$groupingVariable)
  model = lm(ratio ~ year + birth,f$data,weights=nwords)
  scorez=summary(model)$coefficients[2:3,3]
  list(plot=f,scores=scorez)
}
genreplot(list('hi'))
if (FALSE) {
  #There are very weird effects of using percentage of books as a measure: that's because length is a function of author age.
  word = sample(names(models),1)
  f = agedata(word,counttype='Occurrences_per_Million_Words')
  g = agedata(word,counttype='Percentage_of_Books')
  grid.arrange(f[[1]] + 
    opts(title = paste(word,paste(round(f[[2]]),collapse=" "))),
               g[[1]]+ 
    opts(title = paste(word,paste(round(g[[2]]),collapse=" "))))
  a = dbGetQuery(con,"
                 SELECT author_age,year,sum(nwords)/count(*) as length FROM catalog WHERE aLanguage='eng' 
                 AND year > 1850 AND year < 1922 AND author_age > 25 
                 AND author_age < 85 GROUP BY author_age,year")
  b = dbGetQuery(con,"
                 SELECT author_age,year,nwords as length FROM catalog WHERE aLanguage='eng' 
                 AND year > 1850 AND year < 1922 AND author_age > 25 
                 AND author_age < 85")
  dim(b)
  ggplot(a,aes(x=year,y=author_age,fill=log10(length))) + 
    geom_tile() + 
    scale_fill_gradientn(colours=c('white','yellow','orange','red'),
                         trans='') + 
    opts(title="Books published, by year and author age, in Open Library dataset")
  
  ggplot(b,aes(x=year,y=author_age)) + 
    geom_tile() + 
    opts(title="Books published, by year and author age, in Open Library dataset")
  dbGetQuery(con,"
           SELECT author,title,catalog.nwords FROM catalog JOIN open_editions USING (bookid)
           WHERE catalog.author_age=88 AND catalog.year = 1914 ORDER BY RAND() LIMIT 1")
  }

models = lapply(words,agedata)
names(models) = words
scores = as.data.frame(t(sapply(models,'[[',2)))
plots = lapply(models,'[[',1)
names(plots)
scores$word = words
plots[sample(length(plots),1)]
agedata('')
#Add a variable to group by length
scores$length = cut(
  nchar(scores$word),
  quantile(nchar(scores$word), probs = seq(0, 1, 1/4)),include.lowest=T)
levels(scores$length) = paste("character length in",levels(scores$length))

#Add a variable to group by character type.
scores$funnychars = "Only lower case"
scores$funnychars[grep("[A-Z]",scores$word,perl=T)] = "Has uppercase letter"
scores$funnychars[grep("[1-9]",scores$word,perl=T)] = "Has number"
scores$funnychars = factor(scores$funnychars)

scores$cor = cors[match(scores$word,names(cors))]
scores$cor = cut(
  scores$cor,
  quantile(scores$cor, probs = seq(0, 1, 1/4)),include.lowest=T)
levels(scores$cor) = paste("correlation in range",levels(scores$cor))

counts = sort(colSums(tabbed))
scores$counts = counts[match(scores$word,names(counts))]
scores$counts = cut(
  scores$counts,
  quantile(scores$counts, probs = seq(0, 1, 1/4)),include.lowest=T)
levels(scores$counts) = paste("correlation in range",levels(scores$counts))



ratio <- ddply(scores, .(funnychars,length), 
     function(x) c(score=
       paste(
         as.character(round(sum(x$year<x$birth)*100/sum(x$year > -100),1)),
         "%\nn=",
         sum(x$year > -100),sep=""
         ) ))
ggplot(scores,aes(x=year,y=birth,label=word)) + 
  geom_point(alpha=.2,col=muted('red')) +
  #geom_text(size=2,alpha=.5) + 
  #geom_hex() + 
  geom_text(
    size=10,alpha=.5,
    aes(x=25,y=10,label=score),
    data=ratio)+
  geom_segment(
    aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  facet_grid(length~funnychars) +
  xlab("Strength of publication year effect (t-value)") + 
  opts(title=paste(
    sum(scores$year<scores$birth)/nrow(scores)*100,
    "% of words show greater effect\nfor author birth year than for publication year"))

ggplot(scores[scores$funnychars=="Has number",],aes(x=year,y=birth,label=word)) + 
  #geom_point(alpha=.2,col=muted('red')) +
  geom_text(size=2.5,alpha=.5,aes(color=log(as.numeric(word)))) + 
  #geom_hex() + 
  #geom_text(
   # size=10,alpha=.5,
    #aes(x=25,y=10,label=score),
    #data=ratio)+
  geom_segment(
    aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  #facet_grid(length~funnychars) +
  xlab("Strength of publication year effect (t-value)") + 
  opts(title=paste(
    sum(scores$year<scores$birth)/nrow(scores)*100,
    "% of words show greater effect\nfor author birth year than for publication year"))
f = models[['49']]$plot
yearSampling=7; shift = 3 #Shift is so I can check what it looks like for different windows
f=agedata('Grover Cleveland')[[1]]
#f$data = f$data[(f$data$year-shift) %/% yearSampling == (f$data$year-shift)/yearSampling & (f$data$groupingVariable-shift) %/% yearSampling == (f$data$groupingVariable-shift)/yearSampling,]
f
word = "potassium";agedata(word)[[1]];agedata(word)[[2]]


#Can we get some part of speech help?
if (FALSE) {
  #It turns out: no.
  findPOS <- function(word,all=F) {
    #This checks the local wordNet installation to find out what parts of speech a word can be
    require(wordnet)
    initDict()
    partsofSpeech = c("ADJECTIVE", "ADVERB", "NOUN", "VERB")
    exists = lapply(partsofSpeech, function(POS) {
      length(getIndexTerms(POS, 1, getTermFilter("ExactMatchFilter", word, TRUE)))
    })
    value = partsofSpeech[as.logical(unlist(exists))]
  }
  getSynonyms(getIndexTerms("ADJECTIVE",7,getTermFilter("ExactMatchFilter","healthy",T)))
  test = sample(parts,1)
  if ("ADJECTIVE" %in% test) {
    word = names(test)
    adjective = test[1]
    syns = getSynonyms(getIndexTerms(test[1],7,
                                     getTermFilter("ExactMatchFilter",names(test),T))[[1]])
   syns  
  }
  agedata("syns",comparison_words=list("locomotive"))->f
  f[[1]] + geom_contour(z=value)
  comparison_words=list()
  ?getSynonyms
  scores$pos=NA
  
  
  parts = lapply(scores$word[grep("\\d",scores$word,invert=T)],findPOS)
  names(parts) = scores$word[grep("\\d",scores$word,invert=T)]
  newparts = sapply(parts, function(part) {
    returnval=NA; if (length(part)==1) {returnval = part}
    returnval
  })
  
  scores$pos[grep("\\d",scores$word,invert=T)] = newparts
  scores$pos = factor(scores$pos)
  require(ggplot2)
  ratio <- ddply(scores[scores$funnychars=="Only lower case",], .(pos,length), 
       function(x) c(score=
         paste(
           as.character(round(sum(x$year<x$birth)*100/sum(x$year > -100),1)),
           "%\nn=",
           sum(x$year > -100),sep=""
           ) ))
  
  levels(scores$funnychars)
  ggplot(scores[scores$funnychars=="Only lower case",],aes(x=year,y=birth,label=word)) + 
    geom_point(alpha=.2,col=muted('red')) +
    #geom_text(size=2.5,alpha=.5) + 
    #geom_hex() + 
    geom_text(
      size=10,alpha=.5,
      aes(x=25,y=10,label=score),
      data=ratio)+
    geom_segment(
      aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
    facet_grid(length~pos) +
    xlab("Strength of publication year effect (t-value)") + 
    opts(title=paste(
      sum(scores$year<scores$birth)/nrow(scores)*100,
      "% of words show greater effect\nfor author birth year than for publication year"))

}

f = models[sample(length(models),1)]

values  = xtabs(ratio ~ year+birth,f[[1]]$plot$data)
weights = xtabs(nwords ~ year+birth,f[[1]]$plot$data)
cov.wt(values,rowSums(weights))

weights[1:5,1:5]
models[['helpful']][[1]]
?sd
names(v) = mywords
v[[i]] + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub)

scores = sapply(v,function(item) {
  loc = summary(lm(ratio ~ year+groupingVariable,item$data,weights=nwords))$coefficients  
  c(loc[3,3],loc[2,3],loc[3,3]/loc[2,3])
})
as.data.frame(t(scores)) -> scores
rownames(scores) = mywords
names(scores) = c('age','year','slope')
ggplot(scores,aes(x=age,y=year,size=log(abs(slope)))) + geom_point()
v[['Then']]
abstractArt = agedata('using')[[1]] + geom_contour(aes(z=ratio)) + ylab("") + xlab("") + opts(title="",legend.position = "none", axis.ticks = theme_blank(), axis.text.x = theme_blank(),axis.text.y = theme_blank())

lapply(verblist, function(words))

f = verblist[[1]]
f
#ageplot("nationwide")