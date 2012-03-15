#!/usr/bin/R
rm(list=ls())
setwd('/presidio/Rscripts')
source("Rbindings.R")
source('Word Spread.R')
genres =genreplot(list("Pittsburgh"),
          grouping='country',
          groupings_to_use = 2,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1822,1922),
          smoothing=3,
          comparison_words = list("Pittsburg"),
          words_collation='Case_Sensitive')


USA = genres$data[genres$data$groupingVariable=='USA',]
events = data.frame(x = c(1891,1911),y=c(1/5,5),label=c("Government\nmandates\n'Pittsburg'","Government\nmandates\n'Pittsburgh'"))
ggplot(USA,aes(x=year,y=ratio)) + 
  opts(title="Ratio of books using 'Pittsburgh' to books using 'Pittsburg'") + 
  geom_point(aes(fill=ratio),shape=21,color='grey') + geom_smooth(se=F,span=.2,lty=3) + 
  scale_y_log10(
    breaks = c(1/3,1/2,2/3,4/5,1,5/4,3/2,2,3),
    labels = c('1/3','1/2','2/3','4/5','1','1.2',1.5,2,3),limits = c(1/4,4)) + 
  scale_fill_gradient2(low=muted("blue"),high=muted("red"),trans='log') +
  geom_hline(aes(yintercept=1),col='grey',lty=3,size=4) + 
  geom_vline(aes(xintercept=c(1891,1911)),
             lty=2,colour=c(muted('red'))) +  ylab('   More use of "Pittsburg"       <-------->      More use of "Pittsburgh"   ') +
  annotate("text",x = c(1911),y=c(2),label=c("Government\nmandates\n'Pittsburgh'"),size=3,col=muted('red')) +
  annotate("text",x = c(1891),y=c(1/3),label=c("Government\nmandates\n'Pittsburg'"),size=3,col=muted('red'))

genres =genreplot(list("Pittsburgh"),
          grouping='author_age',
          groupings_to_use = 55,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1822,1922),
          smoothing=5,
          comparison_words = list("Pittsburg"),
          words_collation='Case_Sensitive',country=list("USA"))
genres +   annotate("text",x = c(1911),y=c(80),label=c("Government\nmandates\n'Pittsburgh'"),size=3,col=muted('red')) +
  annotate("text",x = c(1891),y=c(60),label=c("Government\nmandates\n'Pittsburg'"),size=3,col=muted('red')) + 
  geom_vline(aes(xintercept=c(1891,1911)),
             lty=2,colour=c(muted('red'))) 

genres =genreplot(list("Pittsburgh"),
          grouping='country',
          groupings_to_use = 3,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1860,1922),
          smoothing=5,
          comparison_words = list("Pittsburg"),
          words_collation='Case_Sensitive')
genres +   annotate("text",x = c(1911),y=4,label=c("Government\nmandates\n'Pittsburgh'"),size=3,col=muted('red')) +
  annotate("text",x = c(1891),y=3,label=c("Government\nmandates\n'Pittsburg'"),size=3,col=muted('red')) + 
  geom_vline(aes(xintercept=c(1891,1911)),
             lty=2,colour=c(muted('red'))) 

genres +   annotate("text",x = c(1911),y=3,label=c("Government\nmandates\n'Pittsburgh'"),size=3,col=muted('red')) +
  annotate("text",x = c(1891),y=3,label=c("Government\nmandates\n'Pittsburg'"),size=3,col=muted('red')) + 
  geom_vline(aes(xintercept=c(1891,1911)),
             lty=2,colour=c(muted('red')))

genres =genreplot(list("Pittsburgh"),
          grouping='state',
          groupings_to_use = 15,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1860,1922),
          smoothing=6,
          comparison_words = list("Pittsburg"),
          words_collation='Case_Sensitive')
mydat=genres$data
mydat = mydat[mydat$year >= 1910 & !is.na(mydat$value),]
statecounts = xtabs(nwords~groupingVariable,mydat)
mydat = mydat[mydat$groupingVariable %in% names(statecounts)[statecounts>10],]
mydat$state = factor(mydat$groupingVariable,
                     levels= unique(
                       as.character(mydat$groupingVariable)))
scores = sapply(
  levels(mydat$state),function(state) {
    year = 1923
    year = min(mydat$year[mydat$value >= 1 & mydat$state==state])
    year[year==Inf] = 1923
    year
    })
statedata = data.frame(
  state = paste('US',toupper(names(scores)),sep='-'),
  TransitionYear = scores)
require(googleVis)
plot(gvisGeoChart(
  data = statedata,'state','TransitionYear',
  options=list(region="US", displayMode="regions", resolution="provinces",
  width=650, height=420,colorAxis = "{colors:['DE2D26','FEE0D2']}")))

#That method doesn't work so well for the earlier years.
maxyear = 1900
genres =genreplot(list("Pittsburgh"),
          grouping='state',
          groupings_to_use = 50,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1891,1900),
          smoothing=6,
          comparison_words = list("Pittsburg"),
          words_collation='Case_Sensitive')
mydat=genres$data
mydat = mydat[!is.na(mydat$ratio),]
statecounts = xtabs(nwords~groupingVariable,mydat)
mydat = mydat[mydat$groupingVariable %in% names(statecounts)[statecounts>10],]
mydat$state = factor(mydat$groupingVariable,
                     levels= unique(
                       as.character(mydat$groupingVariable)))
scores = sapply(
  levels(mydat$state),function(state) {
    year = 1900
    year = min(mydat$year[mydat$value <= .5 & mydat$state==state])
    year[year==Inf] = 1900
    year
    })
statedata = data.frame(state = paste('US',toupper(names(scores)),sep='-'),TransitionYear = scores)
plot(gvisGeoChart(
  data = statedata,'state','TransitionYear',
  options=list(region="US", displayMode="regions", resolution="provinces",
  width=650, height=420,colorAxis = "{colors:['DE2D26','FEE0D2']}")))


maxyear = 1900
genres =genreplot(list("Pittsburgh"),
          grouping='state',
          groupings_to_use = 50,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1850,1922),
          smoothing=6,
          comparison_words = list("Pittsburg"),
          words_collation='Case_Sensitive')
mydat=genres$data
mydat = mydat[!is.na(mydat$value),]
levels(mydat$state)[levels(mydat$state)=='nb'] = 'ne'
statecounts = xtabs(nwords~groupingVariable,mydat)
mydat = mydat[mydat$groupingVariable %in% names(statecounts)[statecounts>20],]
mydat$state = factor(mydat$groupingVariable,
                     levels= unique(
                       as.character(mydat$groupingVariable)))
scores = sapply(
  levels(mydat$state),function(state) {
      change = NA
      diff = mydat$value[mydat$state==state & mydat$year==1917]/mydat$value[mydat$state==state & mydat$year==1904]
      if (length(diff) > 0) {change = diff}
      change
      })
scores = scores[!is.na(scores)]
realscores = scores
scores = log(scores)
realscores = realscores[!is.infinite(abs(scores))]
scores = scores[!is.infinite(abs(scores))]
statecounts = xtabs(nwords ~ state, mydat[mydat$year > 1896,])
statedata = data.frame(
  state = paste('US',toupper(names(scores)),sep='-'),
  LogofChange04to17 = scores,realscores = realscores,
  nwords = statecounts[match(names(scores),names(statecounts))])
statedata
plot(gvisGeoChart(
  data = statedata,'state','LogofChange04to17',
  options=list(region="US", displayMode="regions", resolution="provinces",
  width=650, height=420,colorAxis = "{colors:['red','white','blue']}")))

#Here's some code from stack overflow'
library(RCurl)
library(RJSONIO)

construct.geocode.url <- function(address, return.call = "json", sensor = "false") {
  root <- "http://maps.google.com/maps/api/geocode/"
  u <- paste(root, return.call, "?address=", address, "&sensor=", sensor, sep = "")
  return(URLencode(u))
}

gGeoCode <- function(address) {
  u <- construct.geocode.url(address)
  doc <- getURL(u)
  x <- fromJSON(doc,simplify = FALSE)
  lat <- x$results[[1]]$geometry$location$lat
  lng <- x$results[[1]]$geometry$location$lng
  return(c(lat, lng))
}

statedata = statedata[rownames(statedata) != 'xx',]



backup = statedata
statedata = statedata[rownames(statedata)!='dc',]
locations = as.list(rep(NA,nrow(statedata)))

lengths = lapply(locations,length)
while (min(unlist(lengths)) == 1) {
  try(function () {
  lengths = lapply(locations,length)
  for (i in which(lengths==1)) {
    locations[[i]] = gGeoCode(toupper(rownames(statedata)[i]))
  }})
}

locations = do.call(rbind,locations)
PAloc = gGeoCode("Washington, DC")

statedata$PittDist = apply(locations,1,function(row) {
    sqrt((row[1] - PAloc[1])^2 + (row[2] - PAloc[2])^2)
    })
ggplot(statedata,aes(y=realscores,x=PittDist)) + 
  geom_point() + 
  ylab("Degree of Spelling Change") + 
  xlab("Distance from Washington") + stat_smooth(method='lm')


summary(lm(realscores ~ PittDist,statedata))
ggplot(statedata,aes(x=realscores,y=PittDist)) + 
  geom_point(aes(size=(nwords))) + 
  ylab("Distance from Washington") + 
  xlab("Degree of Spelling Change") + scale_x_log10()



summary(lm(realscores ~ PittDist,statedata))

ggplot(statedata,aes(x=log(realscores),y=log(PittDist))) + 
  geom_point(aes(size=nwords)) + 
  ylab("Distance from Washington") + 
  xlab("Degree of Spelling Change") + stat_smooth(method='lm')

summary(lm(log(realscores) ~ log(PittDist),statedata,weight=nwords))

testsize = 10000
testlocs = cbind(sample(2600:4900,testsize,replace=T)/100,sample(-6600:-12800,testsize,replace=T)/100)
scores = apply(testlocs,1,function(PAloc) {
  statedata$PittDist = apply(locations,1,function(row) {
    (row[1] - PAloc[1])^2 + (row[2] - PAloc[2])^2
    })
  #summary(lm(log(realscores) ~ log(PittDist),statedata))
  summary(lm(log(realscores) ~ log(PittDist),statedata,weights = nwords))$coefficients[2,3]
})


hist(scores)
myframe = data.frame(scores=scores,lat=testlocs[,1],long=testlocs[,2])
library(maps)
reg <- as.data.frame(map("state", plot = FALSE)[c("x", "y")])
states <- data.frame(map("state", plot=FALSE)[c("x","y")])
model = loess(scores ~ lat+long,myframe,span=.02)
size = .33
f = merge(seq(26,49,by=size),seq(-66,-128,by=-size))
names(f) = c("lat","long")
f$scores = predict(model,newdata = f)

ggplot(myframe) + geom_point(aes(x=long,y=lat,colour=scores),size=4,pch=15) + 
  scale_color_gradient2()  +
  geom_path(data=states,aes(x=x,y=y)) + 
  coord_map(project="bonne", lat0 = 50) + 
  opts (title = 'Strength of model predicting change in Pittsburgh spelling,\n in non-Washington-DC states, 1890s to 1900s, from that point')

??inside

ggplot(statedata,aes(x=log(realscores),y=log(PittDist))) + geom_point() + opts(title = "Log of distance from ")

f = dbGetQuery(con,"
               SELECT publish_places,COUNT(*) as count 
               FROM open_editions GROUP BY publish_places ORDER BY count DESC LIMIT 25")
lapply(f$publish_places[2:25],gGeoCode)
plot()
    statedata$state

