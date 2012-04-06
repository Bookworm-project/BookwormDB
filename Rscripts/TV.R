setwd("/presidio/Rscripts")
source("Rbindings.R")
source("Dating tools.R")
source("Trendspotting.R")
getwd()

scriptize = function(show) {
  #Go through the folder hierarchy and read in the srt files for each show.
  setwd(paste("~/tv/",show,sep=""))
  #list.files using recursive so we get even the subfolders
  files = list.files(recursive=T)
  files = files[grep("srt$",files)]
  raweps = lapply(files,scan,what='raw',sep="\n")
  cleaned = lapply(raweps, function (text) {
    text[grep("[A-Za-z]",text,perl=T,invert=T)]=" ";
    text = paste(text,collapse=" ")
    text = gsub(" +"," ",text)
    text = gsub("([\\.\\?!]+)","\\1\n",text)
    text = strsplit(text,"\n")[[1]]
  })
  names(cleaned) = files
  names(cleaned)
  setwd("/presidio/Rscripts")
  #rather than just a list of scripts, I split the scripts into multiple lists based on the first letter of filename
  #In most cases, this is the season folders.
  results = split(cleaned,factor(substr(names(cleaned),1,1)))
}

bigramize = function(cleaned) {
  bigrams = lapply(cleaned,function(text) {
    MakeNgramCounts(tokenize(text))
    })
  names(bigrams) = 1:length(bigrams)
  bigrams
}

shows = list.files("~/tv")
shows = shows[shows!="Downton Abbey"]
scripts = lapply(shows,scriptize)
names(scripts) = shows

example=function(search,shownames = names(scripts),n=5) {
  #This is a great example of a time that vectorizing code in R 
  #produces uglier, more difficult to read, and slower results than
  #just using a for-loop.
  silent=lapply(shownames,function(showname) {
    scriptz = scripts[[showname]]
    for (season in 1:length(scriptz)) {
      for (ep in 1:length(scriptz[[season]])) {
        matches = grep(search,scriptz[[season]][[ep]])
        if (length(matches)>=1) {
          sapply(matches,function(match){
            try(cat(toupper(x=paste(showname,season,ep)),scriptz[[season]][[ep]][(match-n):(match+n)],sep="\n"))
          })
        }       
      }
    }
  }
  )
}

totalframe = ldply(shows,function(show) {
  cat(show,"\n")
  showframe = ldply(1:length(scripts[[show]]),function(seasonnum) {
      framelist = bigramize(scripts[[show]][[seasonnum]])
      framelist = lapply(1:length(framelist),function(epnum) {
        myframe = framelist[[epnum]]
        myframe$ep = epnum
        myframe
      })
      returnable = do.call(rbind,framelist)
      returnable$season = seasonnum
      returnable
  })
  showframe$show = show
  showframe
})
totalframe=totalframe[grepl("Kennedy",totalframe$show) | grepl("Johnson",totalframe$show) | (totalframe$show=="Mad Men" & totalframe$season==5),]
unique(totalframe$show)

names(totalframe)[1:2] = c("w1","w2")
totalframe$word1 = paste(totalframe$w1,totalframe$w2)

length(unique(totalframe$word1))
totalframe$show = factor(totalframe$show)
totalframe$ep = factor(totalframe$ep)
totalframe$season = factor(totalframe$season)
#rm(con)
#source("Rbindings.R")
fullcounts = function(allbigrams,...) {
  #This returns a data.frame with year,word,count information for every bigram in a list of bigrams,
  #so we don't have to keep pulling the same words from the database.
  allbigrams = allbigrams[!duplicated(paste(allbigrams[,1],allbigrams[,2])),]
  #additional arguments are passed to smoothedCounts
  smoothed = smoothedCounts(allbigrams[,1:2],...)
  smoothed[!is.na(smoothed$word1) & !is.na(smoothed$value),]
}
words = fullcounts(totalframe,yearlim=c(1935,2008))
melville=con

totalframe$y1 = words$value[words$year==1964][match(totalframe$word1,words$word1[words$year==1964])]
totalframe$y2 = words$value[words$year==1995][match(totalframe$word1,words$word1[words$year==1995])]
locframe = totalframe[!is.na(totalframe$y1*totalframe$y2),]
locframe = locframe[,3:ncol(locframe)]
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

#Set a variable to track if they're any good:
locframe$real=F
locframe$real[locframe$show %in% c("Lilies of the Field", 
                                   "The Apartment", "Twilight Zone",
                                   "Lover Come Back",
                                   "The Hustler",
                                   "Dr Strangelove","Johnson Tapes","Kennedy Tapes")] = T

example("ways to")
levels(locframe$ep)
extra = data.frame(word1="off the\nphone with",y1=.00000017,y2=.00000325)
locframe = locframe[locframe$y2>0 & locframe$y1 > 0,]
source("Dating tools.R")
textcloud(locframe[locframe$y2/locframe$y1 <= 50 & !duplicated(paste(locframe$word1,locframe$show)),]) + facet_wrap(~show) + geom_smooth()

cloud(locframe[locframe$y2/locframe$y1 <= 50 & !duplicated(paste(locframe$word1,locframe$show)),]) + geom_hex()+ 
  facet_wrap(~show,ncol=1)

locframe$freqgroup = cut((locframe$y2+locframe$y1)/2,quantile((locframe$y2+locframe$y1)/2,probs = seq(0, 1, 1/3)),include.lowest=T)
#Just a quick thing to convert ratios to numbers
labelz = c("1000:1","300:1","100:1","30:1","10:1","3:1","2:1","1.5:1","1.2:1","1:1","1:2.1","1:1.5","1:2","1:3","1:10","1:30")
numberplot = function(string) {rel=as.numeric(strsplit(string,":")[[1]]);rel[1]/rel[2]}
 
levels(locframe$show)[levels(locframe$show)=="The Kennedys"]="Kennedys miniseries"
levels(locframe$show)=levels(locframe$show)=="The Kennedys"]=
locframe$show = factor(locframe$show)
ggplot(locframe[locframe$y2/locframe$y1 <= 50 & !duplicated(paste(locframe$word1,locframe$show)),]) +
  geom_density(aes(x=y2/y1,fill=show,color=show),alpha=.2,adjust=1) + 
  scale_x_continuous("ratio of modern to period use",trans='log10',limits=c(1/5,5),labels=labelz,
    breaks = sapply(labelz,numberplot)) + 
  opts(title="And Mad Men is worst of all") 


locframe[sample(nrow(locframe),100),]
example("on the phone with",n=0)
summary(locframe$ep)
?facet_wrap
attach(locframe)
locframe[locframe$show=='Playboy Club' & ( (y2/y1 > 30 & mean(y1+y2)>1e-06 & y1 > 0) | (y1==0 & y2> 1e-07) ),]
detach(locframe)
textcloud(locframe[!(grepl('just',locframe$word1) | grepl('need',locframe$word1)),]) + 
  opts(title="Mad Men Season 5 premiere, two word phrases") + 
  geom_text(data=locframe[grepl('just',locframe$word1) | grepl('need',locframe$word1),],
            size=4,color=muted('red'))

textcloud(locframe[locframe$y2/locframe$y1>20 & locframe$y1!=0 & locframe$season==1,]) + aes(color=show)
example("romantic dinner")
plottable = totalframe[totalframe$show=="Mad Men",]

labelz = c("300:1","100:1","30:1","10:1","3:1","1:1","1:3","1:10","1:30")
  numberplot = function(string) {rel=as.numeric(strsplit(string,":")[[1]]);rel[1]/rel[2]}

ggplot(locframe,aes(x=(y2+y1)/2,y=y2/y1,label=word1,color=show)) + 
  geom_density2d(alpha=.2)+ 
  scale_y_continuous("Ratio of modern use to period use",
            breaks=sapply(labelz,numberplot),labels = labelz,
            trans='log10') + 
              scale_x_continuous(trans='log10') + 
              facet_wrap(~show)
head(locframe)
locframe$freq = locframe$y2<10e-5
ggplot(locframe[locframe$y1>0 & locframe$freq,],aes(x=y2/y1,color=real,group=c(show,ep))) + 
  geom_density() + scale_y_sqrt() + 
  scale_x_continuous(trans='log10')
 
textcloud(locframe[locframe$show=='Mad Men' & locframe$season==4 & locframe$ep %/%2==2,])
example("need to") #2-13
locframe[locframe$word1=='need to',]
#Unheard of 
example("safety protocol") #2-13
#Extremely rare
example("signing bonus")
example("no big deal")
example("ploy to")
example("reinvent the")
example("fantasize about") #2-4 and 2-8
example("translate to") #2-6
example("host you") #"hosted" as a verb

#rare
example("to resize the","Mad Men")
example("eye contact","Mad Men")
example("basically sa","Mad Men",10) #in 1-9, 1-10, AND 3-12
example("lips sink ships")
example("reinvent the wheel")
example("sign off on")
example("fantasize about") #2-4 and 2-8
example("feel good about","Mad Men",15)
example("playing field")
example("focus") #lot's of times.


example("can access")


wordpers = 
  ddply(locframe,.(word1),function(wordframe) {
      if(nrow(wordframe)>5) {
        data.frame(real=sum(wordframe$count[wordframe$real])/sum(wordframe$count),
                  count=sum(wordframe$count))}
})

build_model = function() {
  bigmat = xtabs(count~show+word1,locframe)
  bigmat = bigmat/rowSums(bigmat)
  bigmat = data.frame(unclass(bigmat)) 
  bigmat = bigmat[,order(-colSums(bigmat))]
  bigmat = bigmat[,apply(bigmat,2,mean)>10e-07]
  bigmat[,1:5]
  bigmat$real = locframe$real[match(rownames(bigmat),locframe$show)]
  diffs = apply(
    bigmat[,1:1000],2,
    function(col){
      c(
        mean(col[bigmat$real]),
        mean(col[!bigmat$real]),
        wilcox.test(col[bigmat$real],col[!bigmat$real])[[3]]
      )})
  bigmat = b
  words = names(sort(-abs(log(diffs[3,])))[1:100])
  trainmat=bigmat[,colnames(bigmat) %in% words]
  hugemat = xtabs(count~paste(show,season,ep)+word1,locframe[locframe$word1 %in% gsub("\\."," ",words),])
  hugemat = hugemat/rowSums(hugemat)
  hugemat = data.frame(unclass(hugemat))
  predictor = bigmat[,match(colnames(hugemat),colnames(bigmat))]
  real = locframe$real[match(rownames(bigmat),paste(locframe$show,locframe$season,locframe$ep))]
  require(class)
  predictions = knn(
    trainmat,
    hugemat,
    cl=bigmat$real,
    k=3,prob=T)
  actual = real
  data.frame(predictions,actual)
}

howlers = ddply(locframe,.(show),function(frame){
  data.frame(ratio = sum(frame$count[frame$y>log(50)],na.rm=T)/nrow(frame),
             real=frame$real[1])
})

head(locframe)
textcloud(locframe[locframe$show%in%c('Mad Men'),]) + facet_wrap(~show+season) + 
  opts(title="All the two-word phrases in Mad Men, by overall frequency\nand over-representation in modern books")
example("focu.+ on")
ggplot(howlers,aes(x=show,y=ratio,fill=real))+geom_bar() + coord_flip()
NeedTo = ddply(locframe,.(show,season),function(frame){
  data.frame(ratio = 1000*sum(frame$count[frame$word1 %in% c("need to","needed to","needs to","needing to")])/sum(frame$count),
             count = sum(frame$count[frame$word1 %in% c("need to","needed to","needs to","needing to")]),
             ought = 1000*sum(frame$count[frame$word1 %in% c("ought to")])/sum(frame$count),
             totalWords=sum(frame$count),
             real=frame$real[1])
})

NeedTo = NeedTo[order(NeedTo$season)]
show = "Twilight Zone"
fixup = function(show) {
NeedTo$season[NeedTo$show==show] + year-1
}
years = list()
years[["Twilight Zone"]] = 1961
years[["X-Men First Class"]] = 2011
years[["Mad Men"]] = 2007
years[["The Apartment"]] = 1960
years[["Pan Am"]] = 2011
years[["Lilies of the Field"]] = 1963
years[["Lover Come Back"]] = 1961
years[["Playboy Club"]] = 2011
years[["The Hustler"]] = 1961
years[["The Kennedys"]] = 2011
years[["Dr Strangelove"]] = 1964

NeedTo$year = unlist(sapply(as.character(unique(NeedTo$show)),function(show) {
  fixup(show=show,year=years[[show]])}))


NeedTo$displayname = factor(
  paste(NeedTo$show," (",NeedTo$year,")",sep=""),
  levels = paste(NeedTo$show," (",NeedTo$year,")",sep="")[order(-NeedTo$year)],
  ordered=T)

labelz = c("1:100","1:50","1:30","1:10","1:5","1:3","1:2","1:1","2:1","3:1","5:1","10:1","20:1","50:1","100:1")
numberplot = function(string) {rel=as.numeric(strsplit(string,":")[[1]]);rel[1]/rel[2]}

plot2 = ggplot(NeedTo[NeedTo$ratio > 0 | NeedTo$ought > 0,],aes(
  y=(ratio/ought),fill=real,color=real,x=displayname))  + 
  geom_bar(position='') + coord_flip() + 
  scale_y_continuous(breaks=sapply(labelz,numberplot),labels=labelz,trans='log')+ 
  opts(legend.position="none",
       title="60s movies use 'ought to' more:\nmodern ones set then use 'need to'") + 
  xlab("")+ylab("Usage of 'need to' per usage of 'ought to'")
names(plot2$scales)
plot2
plot2$data

shows
example('fe[^ ]* good about')
example('single malt',"Pan Am")
example('be kidding',"Pan Am")
example('bathroom break',"Pan Am")
example('wimp out',"Pan Am")
example('a klutz',"Pan Am")
example('accident waiting to happen',"Pan Am")
example('photo shoot',"Pan Am")
example('ice princess',"Pan Am")

#examples of much more common words
example('opting to',"Pan Am")
example('the expertise of',"Pan Am")
example('to debrief',"Pan Am")
example('your current',"Pan Am")
example('strict guidelines',"Pan Am")
example('big deal',"Pan Am")
example('no big deal',"Pan Am")
example('translates to',"Pan Am")
example('having sex',"Pan Am")

?density

ggplot(locframe[locframe$y1>0,]) + 
  #geom_point(aes(x=(y2+y1)/2,y=y2/y1,color=show)) +
  geom_point(aes(x=(y2+y1)/2,y=y2/y1,color=show))+
  scale_y_continuous("Ratio of modern use to period use",
            breaks=sapply(labelz,numberplot),labels = labelz,
            trans='log10') + 
  scale_x_continuous(trans='log10') +
  facet_wrap(~show) + 
  geom_smooth() 
dim(locframe)
plot(density()
Show = locframe[locframe$show=="Playboy Club",]
textcloud(Show)
rm(summaryStats)
summaryStats = ddply(locframe,.(show,season,ep),function(Show,midCutoff=0.7){
  adjust=4
  OK=Show[Show$y1>=0 & Show$y2>=0,]
  Uncommon = OK[(OK$y2+OK$y1)/2 < 1e-03,]
  dens = density(log(Uncommon$y2/Uncommon$y1),na.rm=T,adjust=adjust)
  dens2 = density(log(OK$y2/OK$y1),na.rm=T,adjust=adjust)
  returnt = data.frame(
    peakDensity=dens$x[which(dens$y==max(dens$y))],
    highDensity=sum(dens2$y[dens2$x>=(midCutoff)]*(dens2$x[dens2$x>midCutoff])),
    goodDensity=sum(dens2$y[dens2$x<=(-1*midCutoff)]*(dens2$x[dens2$x<=(-1*midCutoff)])),
    howlers=sum((Show$y2/Show$y1)>100,na.rm=T)/nrow(Show),
    wcount = nrow(Show),
    real=Show$real[1])
})
     
locframe$x = log((locframe$y1+locframe$y2)/2)
locframe$y = log(locframe$y2/locframe$y1)
locframe$useful = locframe$y1 != 0 & locframe$y2 != 0

realframe = locframe[locframe$useful & locframe$real,]     

?kde2d
twoDensity = kde2d(x=realframe$x,y=realframe$y,n=100,
                   h=c(bandwidth.nrd(realframe$x)*3,bandwidth.nrd(realframe$y)*3),
                   lims = 1.2*c(range(realframe$x),range(realframe$y)))
image(twoDensity)

likelihoods = ddply(locframe[locframe$useful & !is.na(locframe$y),],.(word1),function(f) {
  data.frame(likelihood = twoDensity$z[
    which(abs(f$x[1]-twoDensity$x)==min(abs(f$x[1]-twoDensity$x))),
    which(abs(f$y[1]-twoDensity$y)==min(abs(f$y[1]-twoDensity$y)))],
    x=f$x[1],
    y=f$y[1])
})
locframe[order(locframe$likelihood),][1:100,1:5]

locframe$likelihood = likelihoods$likelihood[match(locframe$word1,likelihoods$word1)]
locframe$likeranks = rank(-locframe$likelihood)
likelidiff = ddply(locframe[!is.na(locframe$likeranks),],.(show,season,ep),
                   function(myframe) {
  data.frame(ave_rank = sum(log(1/myframe$likelihood[myframe$y > 0]),na.rm=T),
             variance = sum(
               myframe$likeranks[myframe$y > 0]>(.9*max(locframe$likeranks)),na.rm=T)/
                 nrow(myframe),
             real = myframe$real[1])
})
ggplot(likelidiff,aes(x=ave_rank,color=real,y=variance,label=show))+
  geom_point(position='jitter') +
  coord_flip()+geom_text()
ggplot(locframe,aes(x=likelihood,fill=real))+geom_density(alpha=.5)
     
rank(locframe$likelihood)

     ggplot(summaryStats,aes(x=highDensity/goodDensity,y=howlers,
                        color=real,pch=real,color=ep,label=show)) + geom_text()
?svm   
summary(summaryStats)     
     textcloud(locframe[locframe$show=="The Apartment",])
training = rep(FALSE,nrow(summaryStats))
training[sample(1:nrow(summaryStats),nrow(summaryStats)%/%2)] = TRUE
svmodel = svm(factor(real)~peakDensity+highDensity+howlers+highDensity/goodDensity+goodDensity,data=summaryStats[training,])
data.frame(summaryStats$real[!training],
           predict(svmodel,summaryStats[!training,]))
plot(predict(svmodel,summaryStats[!training,]))
     print(svmodel)     