setwd('/presidio/Rscripts')
rm(list=ls())
source("Rbindings.R")
source('Word Spread.R')

#First I flag some interesting words from the other computer.
<<<<<<< HEAD

words = dbGetQuery(con,"SELECT word,IDF FROM wordsheap WHERE wflag=1 and stem IS NOT NULL")
morewords = dbGetQuery(con,"SELECT words.word,count,books FROM words JOIN wordsheap USING (wordid) WHERE wflag=1 and words.stem IS NOT NULL")
=======
words = 
#words = dbGetQuery(con,"SELECT word,IDF FROM wordsheap WHERE wflag=1 and stem IS NOT NULL")
>>>>>>> 6765f7d4542112c6021db593b89a31617ab43fb4
words = words[grep("\\d",words$word,perl=T,invert=T),]
words[rev(order(words$IDF)),]
dim(words)
agedata = function(word,counttype = 'Percentage_of_Books') {
  f = genreplot(list(word),
            grouping='author_age',
            groupings_to_use = 63,
            counttype = counttype,
            #counttype = 'Occurrences_per_Million_Words',
            ordering=NULL,
            years=c(1850,1922),
            smoothing=7,
            comparison_words = list(),
            words_collation='Case_Insensitive') + opts(title=word)
  f$data$birth = f$data$year-f$data$groupingVariable
  #f$data$groupingVariable = as.numeric(f$data$groupingVariable)
  model = lm(ratio ~ year + birth,f$data,weights=nwords)
  scorez=summary(model)$coefficients[2:3,3]
  list(plot=f,scores=scorez)
}
word = "potassium";agedata(word)[[1]];agedata(word)[[2]]


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
mywords = words$word
models = lapply(words$word,agedata)
names(models) = mywords
scores = as.data.frame(t(sapply(models,'[[',2)))
plots = lapply(models,'[[',1)
names(plots)
scores$word = mywords
scores

ggplot(scores,aes(x=year,y=birth,label=word)) + 
  #geom_point(alpha=.2) +
  geom_text(size=2,alpha=.5) + 
  #geom_hex() + 
  geom_segment(aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  xlab("Strength of publication year effect (t-value)") + 
  opts(title=paste(
    sum(scores$year<scores$birth)/nrow(scores)*100,
    "% of words show greater effect\nfor author birth year than for publication year"))
word = "potassium";agedata(word)[[1]];agedata(word)[[2]]

scores$pos='unknown'
scores$pos[grep('tions?$',scores$word,perl=T)] = 'noun'
scores$pos[grep('ment?$',scores$word,perl=T)] = 'noun'
scores$pos[grep('ist$',scores$word,perl=T)] = 'adverb'
scores$pos[grep('ity$',scores$word,perl=T)] = 'noun'
scores$pos[grep('ed$',scores$word,perl=T)] = 'verb'
scores$pos[grep('ly$',scores$word,perl=T)] = 'adverb'
scores$pos[grep('al$',scores$word,perl=T)] = 'adjective'
scores$pos[scores$word %in% c("coal","metal")] = 'noun'
scores$pos=factor(scores$pos)
scores$nchar = factor(nchar(scores$word))
scores$IDF = words$IDF
scores$word[scores$pos=='unknown']
scores[c('word','pos')]
strReverse <- function(x) sapply(lapply(strsplit(x, NULL), rev), paste,
collapse="")
scores$word[order(strReverse(scores$word))]
strong = scores[scores$year > 10 | scores$birth > 10,]
scores$IDFquantile = cut(scores$IDF,quantile(scores$IDF),include.lowest=T)
scores$ncharquantile = cut(nchar(scores$word),quantile(nchar(scores$word)),include.lowest=T)
scores$commonness = cut(morewords$count,quantile(morewords$count),include.lowest=T)
summary(scores$IDFquantile)
scores[is.na(scores$IDFquantile),]
?cut

?split

ggplot(scores) + geom_histogram(aes(x=IDF))

plotta = scores
ggplot(plotta,aes(x=year,y=birth,label=word)) + 
  #geom_point(alpha=.2) +
  geom_hex() + geom_rug(col=rgb(.5,0,0,alpha=.2)) + 
  #geom_text(size=3,alpha=.5) + 
  geom_segment(aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  xlab("Strength of publication year effect (t-value)") + 
<<<<<<< HEAD
  facet_grid(IDFquantile~commonness) + 
=======
  facet_grid(IDFquantile~ncharquantile,labeller=c(1:16)) + 
>>>>>>> 6765f7d4542112c6021db593b89a31617ab43fb4
  opts(title=paste(sum(plotta$birth>plotta$year)/nrow(plotta), "% of words show greater effect\nfor author birth year than for publication year"))
summary(scores)

t
models[['helpful']][[1]]

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
abstractArt = v[['using']] + geom_contour(aes(z=ratio)) + ylab("") + xlab("") + opts(title="",legend.position = "none", axis.ticks = theme_blank(), axis.text.x = theme_blank(),axis.text.y = theme_blank())

lapply(verblist, function(words))

f = verblist[[1]]
f
#ageplot("nationwide")