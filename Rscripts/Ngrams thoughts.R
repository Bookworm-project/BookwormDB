#Thinking about ngrams
setwd("/presidio/Rscripts")
source("Rbindings.R")

wheres = list(word1=c("automobile"))

capitalism = dbGetQuery(
  con,
  paste("SELECT year,words FROM presidio.1grams WHERE ",
        whereterm(wheres)," GROUP BY year"))
the = dbGetQuery(
  con,
  paste("SELECT year,words FROM presidio.1grams WHERE ",
        whereterm(list(word1="the"))))
joint = merge(capitalism,the,by='year')
joint$ratio = joint$words.x/joint$words.y*12/100
require(zoo)
k = 15
joint$rollmedian = rollapply(joint$ratio,k,median,fill=NA)
joint$rollmean = rollapply(joint$ratio,k,mean,fill=NA)
joint$rollmedian2 = rollapply(joint$ratio,k/2,median,fill=NA,na.rm=T)
joint$rollmedian2 = rollapply(joint$rollmedian2,k/2,median,fill=NA,na.rm=T)

joint = joint[joint$year > 1800,]
ggplot(
  joint,aes(x=year,y=ratio))+
    geom_smooth(span=.15,se=F,size=2,color=muted("red"))+
    geom_line(size=.5,color="grey")+
    #geom_line(size=.5,color="blue",aes(y=rollmedian2))+
        #geom_line(size=.5,color="red",aes(y=rollmedian))+
        geom_line(size=.5,color="purple",aes(y=rollmean))+
     #scale_y_log10() + 
    opts(title=paste(
      "Ngrams frequency of ",
      paste(wheres[['word1']]),
      collapse="/"))

con=dbConnect(MySQL())
dbGetQuery(con,"Use ngrams")
source("ngrams wordgrid.R")
  
  mylist = wordgrid(list("advertising"),
      returnData=F,
      wordfield='stem',
      field='w1.casesens',
      freqClasses=4,n=50,
      yearlim=c(1960,2008),
      mydb=con,
      excludeList=c("man","men"),
      samplingSpan=4
    )
  mylist

dbGetQuery(con,"Use presidio")
genreplot(list("democratic principles"),grouping="lc0",groupings_to_use = 15,chunkSmoothing=5)