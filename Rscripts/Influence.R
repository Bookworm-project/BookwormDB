#Influence

setwd("/presidio/Rscripts")
source("Rbindings.R")
source("Dating tools.R")
source("Trendspotting.R")

values = APIcall(constraints=list(
  method="counts_query",
  groups=list('words1.word as w1','words2.word as w2'),
  search_limits=list("bflag"=1)))

bigrams = dbGetQuery(con,values)
smoothed = smoothedCounts(bigrams[,1:2],yearlim=c(1830,1980))
smoothed = smoothed[!is.na(smoothed$value),]
words = smoothed
totalframe=data.frame(word1=unique(smoothed$word1),show=factor("MD"))
totalframe$y1 = words$value[words$year==1848][match(totalframe$word1,words$word1[words$year==1963])]
totalframe$y2 = words$value[words$year==1975][match(totalframe$word1,words$word1[words$year==1975])]
head(totalframe)
locframe = totalframe[!is.na(totalframe$y1*totalframe$y2),]
#A whole bunch of spellings are obviously not dialogue changes, but rather spelling of common words: so are swears
locframe = locframe[grep("gonna",locframe$word1,invert=T),]
locframe = locframe[grep("gotta",locframe$word1,invert=T),]
locframe = locframe[grep("outta",locframe$word1,invert=T),]
locframe = locframe[grep("wanna",locframe$word1,invert=T),]
locframe = locframe[grep("anybody",locframe$word1,invert=T),]
locframe = locframe[grep("anyone",locframe$word1,invert=T),]
locframe = locframe[grep("someone",locframe$word1,invert=T),]
locframe = locframe[grep("everyone",locframe$word1,invert=T),]
locframe = locframe[grep("cannot",locframe$word1,invert=T),]
locframe = locframe[grep("shit",locframe$word1,invert=T),]
locframe = locframe[grep("fuck",locframe$word1,invert=T),]
locframe = locframe[grep("piss",locframe$word1,invert=T),]
#Some scripts don't capitalize well:
locframe = locframe[grep("^i ",locframe$word1,invert=T),]
locframe = locframe[grep(" i$",locframe$word1,invert=T),]
locframe$word1=gsub("^i ","I ",locframe$word1)
locframe$word1=gsub(" i$"," I",locframe$word1)

textcloud = function(plottable) {
  #Just a quick thing to convert ratios to numbers
  labelz = c("1000:1","300:1","100:1","30:1","10:1","3:1","1:1","1:3","1:10","1:30")
  numberplot = function(string) {rel=as.numeric(strsplit(string,":")[[1]]);rel[1]/rel[2]}
  ggplot(plottable,aes(x=(y2+y1)/2,y=y2/y1,label=word1)) + 
  scale_y_continuous(
    "Ratio of modern use to period use",
    labels=labelz,
    breaks = sapply(labelz,numberplot),
    trans='log10') + 
  scale_x_continuous("Overall Frequency",labels = c("1 in 10M","1 in 1K","1 in 100K","1 in 1B"),
                     breaks = c(1/100000,1/10,1/1000,1/10000000),
                     trans='log10')+
        geom_text(data=subset(plottable[plottable$y1*plottable$y2!=0,]), 
                  size=2.5) + 
        geom_text(data=subset(plottable[plottable$y1==0 & plottable$y2 != 0,]),
                  size=2.5,color='red',aes(y=500),position=position_jitter(width=0)) + 
        geom_hline(yint=1,color='black',alpha=.7,lwd=3,lty=2)
}
textcloud(locframe[locframe$word1!='him bolt',])

head(locframe)