rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")
source("Trendspotting.R")
require(zoo)

melville = dbConnect(MySQL())
dbGetQuery(melville,"USE ngrams")
#dbGetQuery(melville,"UPDATE wordsheap SET wflag=0")

#dbGetQuery(melville,"UPDATE wordsheap JOIN words SET wordsheap.wflag=1 
#           WHERE wordsheap.casesens REGEXP '^[A-Za-z][a-z]*$' AND words.stopword=0")
date()
     
window = 3
#Window must be odd
window = (floor(window/2)*2 + 1)
tabbed = return_matrix(sampling=1,offset=0,max=10000,min=1,grams=1)
#backup = tabbed
#tabbed = return_matrix(sampling=1,offset=0,max=10000,min=1,grams=2)

smoothed = apply(tabbed,2,rollmedian,k=window,na.pad=T)
          rownames(smoothed) = as.numeric(rownames(tabbed)[1:nrow(smoothed)])
rownames(smoothed) = as.numeric(rownames(tabbed)[1:nrow(smoothed)])

yearlim = c(1850,1921)
cors = apply(
  smoothed[which(rownames(smoothed)==yearlim[1]):which(rownames(smoothed)==yearlim[2]),],2,
  cor,method='pearson',y=yearlim[1]:yearlim[2])

change  = changefrom(yearlim[1]-yearlim[2],smoothed)[rownames(tabbed) == yearlim[2],]
increasing = cors> .75 & change > 2

colSums(tabbed[,increasing])
splitted = do.call(rbind,strsplit(names(change)," "))
increasing = cors> .75 & change > 2 & !(duplicated(splitted[,1]) & duplicated(splitted[,2]))

words = names(which(increasing))



length(words)
words = words[grep("^[a-z]+$",words,perl=T,invert=F)]

flagWordids(words)
decliners = lapply(colnames(smoothed)[disappearing],function(word) {
 paste("<a href=http://books.google.com/ngrams/graph?content=",word,"&year_start=1900&year_end=2000&corpus=0&smoothing=3)>",word,"</a><br>",sep="")
})


disappearing = 
          changefrom(-50,smoothed)[rownames(tabbed) == '1990',] < .75 & 
          changefrom(-50,smoothed)[rownames(tabbed) == '2000',] < .75 &
          changefrom(-50,smoothed)[rownames(tabbed) == '1860',] > .33 &
          changefrom(-50,smoothed)[rownames(tabbed) == '1965',] < 3   &          
          changefrom(-50,smoothed)[rownames(tabbed) == '1980',] < .75 &
          changefrom(-100,smoothed)[rownames(tabbed) == '1980',] < .75
disappearing = which(disappearing)          
num = sample(disappearing,1)
plot(rownames(smoothed),smoothed[,sample(disappearing,1)],type='l',main=colnames(smoothed)[num],xlim=c(1950,2000))
word = colnames(smoothed)[num]
  



  
             
#smoothed = smoothed[,smoothed[rownames(tabbed) == '1921',] >= 1]
#smoothed = smoothed[,smoothed[rownames(tabbed) == '1826',] <= .1]

compare_span=10
          
good = changefrom(-95,smoothed)[rownames(tabbed) == '1925',] > 5
good = good & changefrom(-105,smoothed)[rownames(tabbed) == '1925',] > 5
good = good & changefrom(-110,smoothed)[rownames(tabbed) == '1940',] > 5
good = good & colSums(smoothed[1:15,],na.rm=T)<=.1 
good = good & !is.na(colnames(smoothed))
good = good & colSums(tabbed[as.numeric(as.character(rownames(tabbed)))>=1950,]) >= 500
good = good & !is.na(good)
hist(colSums(tabbed[as.numeric(as.character(rownames(tabbed)))>=1950,]))
          changers = smoothed[,good] 
  col = sample(1:ncol(changers),1)
            #example = 'footwear','nuggets'
  plot(rownames(smoothed),
            .1+changers[,col],
            log='',main=colnames(changers)[col],
            type='l',
            ylim=c(0.1,1000))
abline(v=1922,lty=2)
colnames(changers)          
change_from_before = changefrom(-10,smoothed)
change_from_after  = changefrom(10,smoothed)
longafter = changefrom(25,smoothed)  
bigones = which(change_from_before>5 & change_from_after < 2 & smoothed*1000000 > .1,arr.ind=T)

changes = data.frame(year = dimnames(change)[[1]][bigones[,1]],
                     word = dimnames(change)[[2]][bigones[,2]])

demo = 1859
changes = changes[order(changes$year),]
changes[!duplicated(changes$word),]
  