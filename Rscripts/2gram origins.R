setwd('/Presidio/Rscripts')
rm(list=ls())
source("Rbindings.R")
source('Word Spread.R')
source("Trendspotting.R")
require(zoo)

#Window must be odd

tabbed = return_matrix(sampling=2,offset=0,max=200000,min=1,grams=1)
window = 15
window = (floor(window/2)*2 + 1)
yearlim = c(1780,2005)
smoothed = tabbed[rownames(tabbed) %in% yearlim[1]:yearlim[2],]
dim(smoothed)
smoothed = apply(smoothed,2,rollmedian,k=window,na.pad=T)
rownames(smoothed) = as.character(yearlim[1]:yearlim[2])
#smoothed = oldsmoothed
#Require words with 'fs' or esses to behave well.
words = colnames(smoothed)



goodword =
    #If it has an 'F', it can't be 4x as common in 1805 as 1835; vice versa if it has an 's'
  (!grepl('f',words) |
   smoothed[rownames(smoothed)=='1805',]/smoothed[rownames(smoothed)=='1835',] < 4  ) & 
  ((!grepl('s',words)) ||
   (smoothed[rownames(smoothed)=='1805',]/smoothed[rownames(smoothed)=='1835',] > .25)) &
  #And it can't be very frequent before we start
  smoothed[rownames(smoothed)=='1820',] > .1
summary(goodword)
#Here we set some criteria for 'entering the language,'
oldsmoothed=smoothed
smoothed=smoothed[rownames(smoothed) %in% as.character(1822:1922),goodword]
dim(smoothed)
good = 
  changefrom(10,smoothed) < 1 &
  changefrom(-1,smoothed) > 1 &
  lag(-1,smoothed) ==0



bigchanges = which(good,arr.ind=T)[,2]

newwords = data.frame(
  year = as.numeric(names(bigchanges)),
  word = colnames(smoothed)[bigchanges])
newwords = newwords[!duplicated(newwords$word),]
entrance = newwords[order(newwords$year),]
entrance$year = as.numeric(as.character(entrance$year))

dim(entrance)
entrance[sample(nrow(entrance),15),]


smoothed[,colnames(smoothed)=="profefs"]
findorigin = function(year=row[,1],word=row[,2]) {
  row = data.frame(year=year,word=word)
  f = genreplot(list(as.character(row$word)),grouping="lc0",groupings_to_use=15,smoothing=10,
                years = c(row$year -10 ,row$year +10 ))
  loc = f$data[f$data$year==row$year,]
  solution = loc[which(loc$value == max(loc$value)),]$groupingVariable
  as.character(solution)
}
  
row= entrance[sample(nrow(entrance),1),]
row
findorigin()->z
entrance$genre = apply(entrance,1,function(row){
  cat(row,"\n")
  try(findorigin(as.numeric(row[1]),row[2]))})
entrance[1:25,]  
entrance$genre[sapply(entrance$genre,length)>1] = NA
entrance$field = factor(unlist(entrance$genre))

entrance$domain = NA
entrance$domain[entrance$field %in% c("Q","R","S","T")] = "Science and Technology"
entrance$domain[entrance$field %in% c("J","K")] = "Law and Politics"
entrance$domain[entrance$field %in% c("B")] = "Philosophy, Psychology and Religion"
entrance$domain[entrance$field %in% c("H")] = "Philosophy and Religion"
entrance$domain[entrance$field %in% c("C","D")] = "World History"
entrance$domain[entrance$field %in% c("E","F")] = "American History"
entrance$domain[entrance$field %in% c("P")] = "Literature"
entrance$domain[entrance$field %in% c("L")] = "Education"

  plotting = entrance
plotting = entrance[!is.na(entrance$field) & entrance$year > 1842 & !(entrance$field %in% c('N',"Error in fix.by(by.x, x) : 'by' must specify valid column(s)\n")),]
#plotting = plotting[sample(nrow(plotting),100),]
  plotting[plotting$word=="Sherlock Holmes",]
  ggplot(plotting,
       aes(y=year,x=0)) +
         scale_x_continuous(breaks = NA) +
         geom_point(
           color="white",
           position=position_jitter(height = 0.5,width=16)) +
         scale_y_continuous(trans='reverse',breaks = seq(1840,1920,by=5)) +
         facet_grid(.~domain) + 
         geom_text(
           aes(label=word),
           size=2.5,
           position=position_jitter(height = 0.5,width=7)
           ) +
          xlab("") +
         theme_bw()

  
qplot(
  as.numeric(rownames(change)),
  rowSums(change>13 & smoothed > 1),geom='line')+
    scale_x_continuous(breaks=seq(1800,2000,by=10))+
    geom_smooth(span=.1)

good = good & grepl("^[a-z ]+$",colnames(smoothed),perl=T)
good[is.na(good)] = FALSE
plotword = function(good) {
word = names(sample(good[good],1))
f = data.frame(year=as.numeric(rownames(smoothed)),
               permillion = smoothed[,colnames(smoothed)==word])
#f$permillion[f$permillion==0] = min(f$permillion[f$permillion>0])/5

ggplot(f,aes(x=year,y=permillion)) + geom_line() + 
  scale_y_continuous(trans='log10') +
  opts(title=word,legend=FALSE) +scale_x_continuous(breaks=seq(1800,2000,by=10))
}
plotword(good)
  
  sum(good)

genreplot(list(word),smoothing=5),grouping="country",groupings_to_use=15,counttype='Percentage_of_Books')


cors = apply(
  smoothed[which(rownames(smoothed)==yearlim[1]):which(rownames(smoothed)==yearlim[2]),],2,
  cor,method='pearson',y=yearlim[1]:yearlim[2])

change  = changefrom(yearlim[1]-yearlim[2],smoothed)[rownames(tabbed) == yearlim[2],]
increasing = cors> .75 & change > 2

colSums(tabbed[,increasing])
splitted = do.call(rbind,strsplit(names(change)," "))
increasing = cors> .75 & change > 2 & !(duplicated(splitted[,1]) & duplicated(splitted[,2]))

words = names(which(increasing))
rm(smoothed)
rm(tabbed)

#First I flag some interesting words from the other computer.
#words has already been filled from 'Identify new words'
agedata = function(word) {
  cat(word,"\n")
  f = genreplot(list(word),
            grouping='author_age',
            groupings_to_use = 63,
            counttype = 'Occurrences_per_Million_Words',
            ordering=NULL,
            years=c(1850,1922),
            smoothing=7,
            comparison_words = list(),
            words_collation='Case_Sensitive') + opts(title=word)
  f$data$birth = f$data$year-f$data$groupingVariable
  model = lm(ratio ~ year + birth,f$data,weights=nwords)
  list(plot=f,scores=summary(model)$coefficients[2:3,3])
}
            
mywords = words
models = lapply(words,agedata)
names(models) = mywords
scores = as.data.frame(t(sapply(models,'[[',2)))
plots = lapply(models,'[[',1)
names(plots)
scores$word = mywords
scores
scores$uppercase = grepl("[A-Z]",scores$word,perl=T)
models[['Total number']][[1]]
  
scores$uppercase = factor(grepl("[A-Z]",scores$word,perl=T))
levels(scores$uppercase) = c("No uppercase letters","Has an uppercase letter")
scores$word[order(scores$year-scores$birth)][1:10]
models[['hand corner']]
plobject = scores

plobject$length = cut(
  nchar(plobject$word),
  quantile(nchar(plobject$word), probs = seq(0, 1, 1/4)),include.lowest=T)
levels(plobject$length) = paste("character length in",levels(plobject$length))
ratio <- ddply(plobject, .(uppercase,length), 
     function(x) c(score=
       paste(
         as.character(round(sum(x$year<x$birth)*100/sum(x$year > -100),1)),
         "%\nn=",
         sum(x$year > -100),sep=""
         ) ))
ratio$score

  
ggplot(plobject,aes(x=year,y=birth,label=word)) + 
  #geom_point(alpha=.1,color=muted('red')) +
  geom_hex() +
  geom_text(
    size=10,alpha=.5,
    aes(x=25,y=-5,label=score),
    data=ratio) + 
  geom_segment(aes(x=0,y=0,xend=max(c(year,birth)),yend=max(c(year,birth))),lty=2) + ylab("Strength of birth effect (t-value)") + 
  xlab("Strength of publication year effect (t-value)") + 
  facet_grid(length~uppercase)+
  opts(title=paste(
    "Selection of the top 10,000 non stopword-including two-grams with\nR > .75 and increase > 2x 1850-1922:\n",
    round(sum(plobject$year<plobject$birth)/nrow(plobject)*100,1),
                   "% of grams show greater effect\nfor author birth year than for publication year"))

  
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
  facet_grid(IDFquantile~ncharquantile,labeller=c(1:16)) + 
  opts(title=paste(sum(plotta$birth>plotta$year)/nrow(plotta), "% of words show greater effect\nfor author birth year than for publication year"))

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