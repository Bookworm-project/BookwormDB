#Oceans2
rm(list=ls())
require(ggplot2)
require(plyr)

#Preprocessing is done by downloading the files, and then some perl-ing around
data = read.delim(
  "/media/mardi/ICOADS/maury.txt",sep="\t",fill=T,header=F,
  col.names =  c("ID",      "Year",   "Month",  "Day",    "Hour",   "lat",    "long",   "country","ShipType","what",   "captain","origin","destination"),
  colClasses = c("factor",  "integer","integer","numeric","numeric","numeric","numeric","factor", "factor",  "factor", "factor", "factor", "factor"),
                  comment.char="",quote="",flush=T)

data$bin = factor(round(data$lat/14)*14000+round(data$long/14)*14)
data$date = as.Date(paste(data$Year,data$Month,data$Day,sep="-"))
data$yearday = as.integer(format(data$date,"%j"))
?as.Date
data = data[!is.na(data$date),]

levels(data$origin) = gsub("^ +","",levels(data$origin))
levels(data$origin) = gsub(" +$","",levels(data$origin))
levels(data$destination) = gsub("^ +","",levels(data$destination))
levels(data$destination) = gsub(" +$","",levels(data$destination))

#Set an integer, continuous time variable
data$time = as.numeric(data$date-as.Date("0000-01-01"))
#Sort in a way that groups a single ship's voyages
data = data[order(data$ID,data$time,data$Hour),]
points = cbind(data[-1,c("long","lat")],data[-nrow(data),c("long","lat")])
require(sp)
#This is really computationally intensive, but keeps distances appropriately closer at the poles and doesn't split voyages going from -179 to 179 longitude
dist = apply(points,1,function(pointset) {
  spDistsN1(matrix(pointset[1:2],ncol=2),pointset[3:4],longlat=T)
})
#The first distance is defined
dist = c(0,dist)    
timeoff=c(0,
          data[-1,c("time")]-
          data[-nrow(data),c("time")]
)
newship=c(0,data[-1,c("ID")]!=data[-nrow(data),c("ID")])
#qplot(dist[!newship & timeoff < 60]) + scale_x_log10()

#At every point, see if : it's been resting 60 days; it's moved 600km; it has a different identifying tag
breaks = timeoff > 60  | newship | dist > 1000
sum(as.numeric(breaks),na.rm=T)
#Keep a ticker that bumps up for every break.
data$voyageid = factor(cumsum(breaks)+1)
length(levels(data$voyageid))

#rm(list=c("newship","timeoff","dist","breaks","points"))
#Drop voyages with only a single point
data = data[data$voyageid %in% names(table(data$voyageid))[table(data$voyageid)>1],]
nrow(data)
data$voyageid = factor(data$voyageid)
#Back to my stuff. Rename to get it to plot easier.




#This is neat--only start or end points of voyages
#home = ddply(data,.(ID),function(ship){
#  data.frame(port=as.character(unlist(ship[!duplicated(ship$voyageid),c("destination","origin")])))
#})
#sort(table(home$port))
#values = data.frame(sort(table(home$port)))

#data$cities = NA
#cities = c("NEW ORLEANS","SAN FRANCISCO","CHARLESTON","NORFOLK",
#           "MOBILE","RICHMOND","SAVANNAH","BOSTON","NEW YORK",
#           "HAMPTON ROADS","SALEM","BALTIMORE","PORTLAND",
#           "NEW LONDON","PHILADELPHIA","NEW BEDFORD",
#           "SAG HARBOR","SALEM")
#for (city in cities) {
#  data$cities[grepl(city,data$origin) | grepl(city,data$destination)]=city
#}
#data$cities = factor(data$cities)
#home = ddply(data,.(ID),function(ship){
#  ship$home=names(sort(-table(ship$cities)))[1]
#  ship
#})
#data$home = home$home[match(data$ID,home$ID)]
#head(home)
#table(data$home)

data$color=as.character("#A65628")

colors = data.frame(
  city = c(  "Boston",    "New York", "Baltimore", "New Bedford", "Sag Harbor", "Nantucket","Salem",  "Philadelphia", "Other"),
  color  = c("#E41A1C",   "#377EB8", "#FF7F00",    "#4DAF4A",   "#4DAF4A",   "#4DAF4A",     "#984EA3", "#F781BF",   "#A65628"))
for (city in colors$city[colors$city!="Other"]) {
  cat(city,"\n")
  data$color[grep(city,data$origin,ignore.case=T)]=as.character(colors$color[colors$city==city])
  data$color[grep(city,data$destination,ignore.case=T)]=as.character(colors$color[colors$city==city])
}
colors = colors[order(nchar(as.character(colors$city))),]
colors$lat = seq(62,35,length.out=nrow(colors))
colors$long = 80


#ports = ddply(data[data$color=="#A65628",],.(voyageid),function(frame) {
#  names(sort(-table(c(as.character(frame$origin),as.character(frame$destination)))))[1]
#})
#sort(table(ports$V1))
#data$color = factor(data$color)


source("/presidio/Rscripts/Map Functions.R")
require(plyr)
offset = 200
data$whaling=NA
data$whaling[grepl("SAG HARBOR",data$origin) | grepl("NEW BEDFORD",data$origin) | grepl("NANTUCKET",data$origin) | grepl("WHALING",data$origin) |grepl("WHALING",data$destination)]=T

data$whaling[grepl("NEW YORK",data$origin) | 
  grepl("BOSTON",data$origin) | 
  grepl("CANTON",data$destination) | 
  grepl("CALCUTTA",data$origin) | 
  grepl("HAMPTON ROADS",data$destination) | 
  grepl("BATAVIA",data$destination) | 
  grepl("HONG KONG",data$destination) |
  grepl("SHANGHAI",data$destination) |
  grepl("LIVERPOOL",data$destination) |
  grepl("BALTIMORE",data$destination) |
  grepl("LIVERPOOL",data$origin)] = F

require(plyr)
plotWorld = Recenter(world,offset,idfield='group')
plotData = Recenter(data,offset,shapeType="segment",idfield="voyageid")
control = plotData[!is.na(plotData$whaling),]
control$voyageid=factor(control$voyageid)
ddply(control,.(whaling),function(frame) {length(unique(frame$voyageid))})
keep = sample(unique(control$voyageid[!control$whaling]),length(unique(control$voyageid[control$whaling])))

control = control[control$whaling | control$voyageid %in% keep,]
control$voyageid=factor(control$voyageid)
ddply(control,.(whaling),function(frame) {length(unique(frame$voyageid))})

#Visual inspections confirms this works reasonably for whaling/nonwhaling:
ggplot(control,aes(x=long,y=lat,color=whaling,group=group))+
  geom_path(alpha=.1)+geom_polygon(data=plotWorld,aes(group=group),color='black')


require(class)
if (!exists("segs")) {
  segs = ddply(control,.(voyageid),function(locframe){
    segments = ddply(locframe,.(group,Year,Month),function(segment) {
      if(nrow(segment)>15) {
        diffs = diff(as.matrix(segment[,c("long","lat")]))
        directions = atan2(diffs[,1],diffs[,2])
        bendiness=mean(abs(diff(directions)))
        days=nrow(segment)
        distrat = sqrt(sum(diff(as.matrix(segment[c(1,nrow(segment)),c("long","lat")]))^2))/sum(sqrt(rowSums(diffs^2)))
        data.frame(bendiness,days,distrat)
      }
    })
    returnt = data.frame(locframe$voyageid[1],
               locframe$origin[1],
               locframe$destination[1],
                distrat = min(c(1,segments$distrat,na.rm=T)),
               distratmean = mean(segments$distrat,na.rm=T),
    bendinessmax = max(segments$bendiness,na.rm=T),
    bendinessmean = mean(segments$bendiness,na.rm=T),
               months = nrow(segments),
    whaling = locframe$whaling[1])
    returnt
  })
}

crosscut = table(plotData$voyageid,plotData$bin)
#Not sure if normalizing or allowing whaling voyages to be naturally longer is better. Classifier accuracy is about the same.
crosscut = (crosscut/rowSums(crosscut))
dim(crosscut)

training = crosscut[rownames(crosscut) %in% control$voyageid,]
applygroup = crosscut[!rownames(crosscut) %in% control$voyageid,]
applygroup = crosscut
dim(training)
dim(testgroup)

classes = knn(training,applygroup,
           cl=
             control$whaling[
               match(rownames(training),control$voyageid)
               ],
           k=3)

#sum(test==control$whaling[match(rownames(testgroup),control$voyageid)],na.rm=T)/length(test)*100
results = control[control$voyageid %in% rownames(testgroup),]
results$derived = test[match(results$voyageid,rownames(testgroup))]
require(ggplot2)
ggplot(results,aes(x=long,y=lat,color=derived,group=group))+
  geom_path(alpha=.31)+geom_polygon(data=plotWorld,aes(group=group),
                                   color='black')

plotData$derived = classes[match(plotData$voyageid,rownames(applygroup))]
summary(plotData$derived)
ggplot(plotData[plotData$Year==1849,],aes(x=long,y=lat,color=derived,group=group))+
  geom_path(alpha=.31)+geom_polygon(data=plotWorld,aes(group=group),
                                   color='black')
plotData$color[plotData$derived==TRUE]="red"
plotData$color[plotData$derived==FALSE]="grey"

ggplot(plotData,aes(x=long,y=lat,color=color,group=group))+
  geom_path(alpha=.41)


require(reshape2)

day = median(plotData$time)
length(levels(plotData$voyageid))
day = day+1
day = median(plotData$time)
day = day-1000
day = 1

SeasonalityPlots = llply(as.vector(1:365),function(day) {
  if (!file.exists(paste("/media/mardi/ICOADS/images/Mauryear/",
                        formatC(day,digits=7,format='d',flag='0')
,".png",sep=""))) {
    altered = plotData
    if( day<6 )
      {
      altered$Year[altered$yearday > 355 & altered$yearday != 366] = altered$Year[altered$yearday > 355 & altered$yearday != 366] + 1
      altered$yearday[altered$yearday > 355 & altered$yearday != 366] = altered$yearday[altered$yearday > 355 & altered$yearday != 366] -365
      }
  myplot = mapPlot(
    altered,
    mytime=day,
    timevar="yearday",
    timelag=5,
    polygons=plotWorld,
    orientation=c(90,offset,0),
    ylim=c(-70,75),
    proj='gall',lat0=10) + 
        theme_nothing() + geom_text(data=colors,aes(label=city,color=color),size=3.5) +
    annotate("text",x=260,y=40,size=3,
             label=paste(altered[altered$year==day,c(3,4)][1,],collapse="-"),
             color='yellow',align=1) + opts(plot.margin = unit(rep(0, 4), "lines"))
    #And then save it to a file.
    ggsave(filename=paste("/media/mardi/ICOADS/images/Mauryear/",
                          formatC(day,digits=7,format='d',flag='0')
  ,".png",sep=""), plot=myplot,width=6,height=4)
  }
},.progress="text")


#Fill in from the middle to make prettier charts I can check on in progress:
days = sort(unique(plotData$time[plotData$Year>=1825 & plotData$Year<1855]))
days = days[days/2==days%/%2]
rounds = floor(log(length(days),2))+1

ordered = unlist(sapply(1:rounds,function(round) {
  quantile(1:length(days),probs=seq(0,1,1/(2^round)),type=1)
}))
ordered = ordered[!duplicated(ordered)]
length(ordered)/365
day = days[ordered][5]

#length(sort(unique(plotData$time)))/2/3/13
source("/presidio/Rscripts/Dating tools.R")
plots = llply(as.vector(days[ordered]),function(day) {
  if (!file.exists(paste("/media/mardi/ICOADS/images/whaling/",
                        formatC(day,digits=7,format='d',flag='0')
,".png",sep=""))) {
    require(grid)
  myplot = mapPlot(
    plotData[plotData$derived==TRUE,],
    mytime=day,myalpha=.5,
    timevar="time",
    timelag=30,
    polygons=plotWorld,
    orientation=c(90,offset,0),
    ylim=c(-70,70),
    proj='gall',lat0=10) + 
        theme_nothing() +# geom_text(data=colors,aes(label=city,color=color),size=3.5) +
    annotate("text",x=260,y=40,size=4,
             label=paste(plotData[plotData$time==day,c(3,2)][1,],collapse="-"),
             color='yellow',align=1) + opts(plot.margin = unit(rep(0, 4), "lines")) 
    #And then save it to a file.
    ggsave(filename=paste("/media/mardi/ICOADS/images/whaling/",
                          formatC(day,digits=7,format='d',flag='0')
  ,".png",sep=""), plot=myplot,width=6,height=4)
  }
},.progress="text")






























myframe=data

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

