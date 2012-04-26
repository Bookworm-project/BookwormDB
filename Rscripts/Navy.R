#Oceans2
require(ggplot2)
rm(list=ls())
dir = "/media/mardi/ICOADS"
Name = "Germany"
Deck = c(155,156)
years = c("18*","19[012345]")
#Preprocessing is done by downloading the files, and then some perl-ing around
try(system(paste("rm ", dir, "/",Deck,".txt",sep="")))
clauses = sapply(Deck,function(deck) paste("$11==",deck,sep=""))

awkjoin = function(listed) {
  #awk seems to like nested parenthesis on this, so a recursive function does the trick.
  if (length(listed)==2) {
    return (paste("(",listed[1]," || ",listed[2],")",sep=""))
  } else {
    return (paste("(",listed[1]," || ",awkjoin(listed[2:length(listed)]),")",sep=""))
  }
}
sapply(years,function(yearspan) {
  system(paste(
    "awk '{if ",
    awkjoin(clauses)," print}' ",
    dir,"/rewritten/", yearspan, "*.txt >> ",dir,"/",Name,".txt",sep=""))
})
data = read.delim(
  file=paste(dir,"/",Name,".txt",sep=""),sep="\t",fill=T,header=F,
  col.names =  c("ID",      "Year",   "Month",  "Day",    "Hour",   "lat",    "long",   "country","c2", "ShipType","Deck",   "Source",  "SC",    "SS"),
  colClasses = c("factor",  "integer","integer","numeric","numeric","numeric","numeric","factor", "factor","factor",  "factor", "factor", "factor", "factor"),
                  comment.char="",quote="",flush=T)


data$long[data$long>180] = data$long[data$long>180] -360
data$date = as.Date(paste(data$Year,data$Month,data$Day,sep="-"))
data = data[!is.na(data$date),]
nrow(data)
#Set an integer, continuous time variable
data$time = as.numeric(data$date-as.Date("0000-01-01"))
#Sort in a way that groups a single ship's voyages
data = data[order(data$Deck,data$ID,data$time,data$Hour),]
points = cbind(data[-1,c("long","lat")],data[-nrow(data),c("long","lat")])
require(sp)
#This is really computationally intensive
dist = apply(points,1,function(pointset) {
  spDistsN1(matrix(pointset[1:2],ncol=2),pointset[3:4],longlat=T)
})
dist = c(0,dist)    
timeoff=c(0,
          data[-1,c("time")]-
          data[-nrow(data),c("time")]
)
newship=c(0,data[-1,c("ID")]!=data[-nrow(data),c("ID")])
qplot(dist[newship & timeoff < 60]) + scale_x_log10()

#At every point, see if : it's been resting 60 days; it's moved 600km; it has a different identifying tag
breaks = timeoff > 60  | newship | dist > 5000
sum(as.numeric(breaks),na.rm=T)/length(breaks)
#Keep a ticker that bumps up for every break.
data$voyageid = factor(cumsum(breaks)+1)
length(levels(data$voyageid))
#rm(list=c("newship","timeoff","dist","breaks","points"))
#Drop voyages with only a single point
data = data[data$voyageid %in% names(table(data$voyageid))[table(data$voyageid)>1],]
nrow(data)
#Back to my stuff. Rename to get it to plot easier.
#plotData[plotData$ID=="15278    ",]
data$color="steelblue"
data$color[data$Deck==118] = "red"
data$color = factor(data$color)

offset = 220
source("/presidio/Rscripts/Map Functions.R")
plotWorld = Recenter(world,offset,idfield='group')
plotData = Recenter(data,offset,shapeType="segment",idfield="voyageid")

#ggplot(plotData[1:1000000,],aes(x=long,y=lat,color=color,group=group))+geom_path(alpha=.1)
day = median(plotData$time)
length(levels(plotData$voyageid))
day = day+300
mapPlot(
  plotData,
  mytime=day,
  timevar="time",
  timelag=15,
  polygons=plotWorld,
  orientation=c(90,offset,0),
  ylim=c(-75,75),
  proj='mercator')+opts(
    title=paste(plotData[plotData$time==day,2:4][1,],collapse="-")) + theme_nothing()

plots = llply(sort(unique(plotData$time))[61:length(unique(plotData$time))],function(day) {
  myplot = 
      mapPlot(
  plotData,
  mytime=day,
  timevar="time",
  timelag=5,
  polygons=plotWorld,
  orientation=c(90,offset,0),
  ylim=c(-60,70),xlim=c(90,360),
  proj='mollweide')+opts(
    title=paste(plotData[plotData$time==day,2:4][1,],collapse="-"))+ theme_nothing()
  #And then save it to a file.
  ggsave(filename=paste("/media/mardi/ICOADS/images/WWII/",
                        formatC(day,digits=4,format='d',flag='0')
,".png",sep=""), plot=myplot,width=6,height=4)
})
?llply

      #+ geom_text(aes(label=ID),size=2,alpha=.5)
day=day+50
max(data$Year)

ggplot(data[data$destination %in% names(sort(-table(data$destination)))[1:10],],aes(x=destination))+geom_bar()

tmp=data[data$voyageid %in% 
  unique(data$voyageid[
    data$lat > -10 & data$lat < 0 & data$long >85 & data$lat < 95]),]
ggplot(data,aes(x=long,y=lat)) + geom_hex(bins=133)+ 
  theme_nothing() + 
  opts(title="Density of log readings in the Maury collection",  legend.position="right",
       panel.background = theme_rect(fill='grey', colour='grey'),
       panel.border = theme_blank())  +
         scale_fill_gradient("number of observations",trans='log',low="white",high="steelblue") 
data$yeargrp = factor(floor(data$Year/10)*10)
data$yeargrp[as.numeric(as.character(data$yeargrp))<1820] = "1820" 
data$yeargrp[as.numeric(as.character(data$yeargrp))>1850] = "1850" 

data$yeargrp = factor(data$yeargrp)

data$cities = NA
cities = c("NEW ORLEANS")
for (city in cities) {
  data$cities[grepl(city,data$origin) | grepl(city,data$destination)]=city
}
sort(table(data$destination))
data$cities = factor(data$cities)
ggplot(coordShift(data[!is.na(data$cities),],0),
       aes(x=long,y=lat,group=voyageid)) + 
  geom_path(alpha=.1) + theme_nothing() + 
  opts(title="Ship paths from Maury's collection (ICOANS data)",  
       panel.background = theme_rect(fill='white', colour='white'), 
       panel.border = theme_blank())   +  
         geom_polygon(data=world,aes(x=long,y=lat,group=id),drop=T,fill='lightgreen') + 
         coord_map(proj='mercator',orientation=c(90,0,0)) + facet_grid(yeargrp~cities)

max(world$long)
coordShift =function(myframe,meridian) {
  myframe$long[myframe$long>meridian+180] = myframe$long[myframe$long>meridian+180]-360
  myframe$long[myframe$long<=meridian-180] = myframe$long[myframe$long<=meridian-180]+360
  myframe
}
qplot(coordShift(world,180)$long)

melville = data[grepl("ACUSHNET",data$ID) & data$Year>=1841 & data$time < 687270,c(1:8,14)]
ggplot(data,aes(x=long,y=lat)) + geom_hex(bins=133)+ 
  theme_nothing() + 
  opts(title="Density of log readings in the Maury collection",  legend.position="right",
       panel.background = theme_rect(fill='grey', colour='grey'),
       panel.border = theme_blank())  +
         scale_fill_gradient("number of observations",trans='sqrt',low="white",high="steelblue") + 
         #geom_path(data=melville,color='red')+
         facet_wrap(~yeargrp)


melville

+ geom_text(
          data=yearday[yearday$yearday==timevars$yearday,],
          aes(label=Month,y=loc),
          x=25,color="yellow",size=4) + theme_nothing() +
    geom_text(data=a,aes(label=Nationality,color=color),size=3.3)

