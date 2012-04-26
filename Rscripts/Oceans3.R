#Oceans2

#Preprocessing is done by downloading the files, and then this:
#
if (FALSE) {
rm all.txt
awk '
BEGIN{
  ORS="\n";
  OFS="\t";
  OS = "\t"}
{if ($9 != -999999999) print $1,$2,$3,$5,$6,$7,$8,$9,$10,$13}' batch/ICOADS*_1 >> all.txt 
}
require(ggplot2)
data = read.delim(
  "~/ICOADS/all.txt",sep="\t",fill=T,header=F,
  col.names =  c("Year",   "Month",  "Day",    "lat",    "long",   "NID",    "II",    "ID",    "country","ShipType"),
  colClasses = c("integer","integer","integer","numeric","numeric","integer","factor","factor","factor", "factor"),
                  comment.char="",quote="",flush=T)
dim(data)
data$long[data$long>180] = data$long[data$long>180] -360
data$time = data$Year*373+(data$Month-1)*31+data$Day


data$voyageid = factor(paste(data$ID,data$II))
data = data[order(data$voyageid,data$time),]
dist=c(0,
              sqrt(rowSums((
                data[-1,c("long","lat")]-
                data[-nrow(data),c("long","lat")]
              )^2)))
timeoff=c(0,
                 data[-1,c("time")]-
                 data[-nrow(data),c("time")]
                )
sort(table(data$country[!duplicated(data$voyageid)]))

newship=c(0,data[-1,c("voyageid")]!=data[-nrow(data),c("voyageid")])
#At every point, see if : it's been resting 60 days; it's moved 25 lat-long points; it has a different identifying tag
breaks = timeoff > 60 | dist > 15 | newship
#Keep a ticker that bumps up for every break.
data$voyageid = factor(cumsum(breaks)+1)
rm(list=c("newship","timeoff","dist","breaks"))

require("rgdal") # requires sp, will use proj.4 if installed
require("maptools")
require("ggplot2")
require("plyr")

gpclibPermit() # required for fortify method

world = readOGR(dsn="/home/bschmidt/shipping", layer="110m_land")
world@data$id = rownames(world@data)
world.points = fortify(world, region="id")
world.df = join(world.points, world@data, by="id")
world = world.df

#Back to my stuff. Rename to get it to plot easier.
world$id=world$group

mapPlot(tmp)
theme_nothing <- function (base_size = 12){
  structure(list(
    axis.line = theme_blank(), 
    axis.text.x = theme_blank(), axis.text.y = theme_blank(),
    axis.ticks = theme_blank(), 
    axis.title.x = theme_blank(), axis.title.y = theme_blank(), 
    axis.ticks.length = unit(0, "lines"), axis.ticks.margin = unit(0, "lines"), 
    legend.position = "none", 
    panel.background = theme_rect(fill='#E0FFFF', colour='#E0FFFF'), panel.border = theme_blank(), 
    panel.grid.major = theme_blank(), panel.grid.minor = theme_blank(), 
    panel.margin = unit(0, "lines"), 
    #plot.background = theme_blank(), 
    #plot.title = theme_text(size = base_size * 1.2), 
    plot.margin = unit(c(0,0,0,0), "lines")
  ), class = "options")
}
myframe = data[data$Year==1820,]
#This can be used for either type of plot--it's agnostic about the time variable going, and the lag can be set.
mapPlot = function(myframe=useful,mytime=654100,timelag=34,timevar="time",...) {
  #I define half the plot here, and half later. No real reason. This is why I don't usually share that much code.
  myframe$timevar=get(timevar,myframe)
  myframe=myframe[myframe$timevar >= (mytime-timelag) & myframe$timevar <= mytime,]
  if (timevar=="time") {myframe$grouping = factor(myframe$voyageid)}
  if (timevar=="yearday") {myframe$grouping = paste(myframe$voyageid,myframe$Year)}
  ggplot(myframe,
         aes(y=lat,x=long))+
    geom_polygon(data=world,aes(x=long,y=lat,group=id),drop=T)+
    geom_path(data=myframe,size=.5,
              aes(group=grouping,
                  #This alpha here decaying by time is what makes the trails slowly erase.
                  alpha=(timevar-mytime)/timelag
                  #,color=color
                  ))+ 
                  #  scale_color_identity() +
    geom_point(data=myframe[myframe$timevar==mytime,],size=.75,
               aes(group=voyageid,alpha=(timevar-mytime)/timelag,
                #  color=color
                   )) + 
    ylab("")+xlab("")  +
    opts(legend.position = "none",axis.text.x=theme_blank(),
        axis.text.y=theme_blank(),axis.ticks=theme_blank()) + 
    coord_map(...)
}
max(data$Year)

yp = .1
year = 1810
tmp = data[round(data$Year*yp)/yp==round(year*yp)/yp,]
tmp = data
tmp$yr = round(tmp$Year*yp)/yp
precision = .5
goal = c(49.5,-4.5)
goal = round(goal*precision)/precision
tmp$lat = round(tmp$lat*precision)/precision
tmp$long = round(tmp$long*precision)/precision
tmp = tmp[tmp$voyageid %in% unique(tmp$voyageid[tmp$lat == goal[1] & tmp$long==goal[2]]),]

f = tmp[1:100,]
distanceframe = ddply(tmp,.(voyageid),function(f) {
  roots = f$time[f$lat==goal[1] & f$long==goal[2]]
  #This assumes transitivity, which is incorrect
  distance = NA
  if(length(roots)==1){
    distance = abs(f$time-roots)
    }
  if (length(roots)>1) {
    distance = apply(sapply(roots,function(root) abs(f$time-root)),1,min)
    }
  data.frame(lat=f$lat,long=f$long,distance=distance,Year = f$Year)
})
yp = .05
distanceframe$yr = factor(round(distanceframe$Year*yp)/yp)
ggplot(distanceframe,aes(x=long,y=lat)) + 
  stat_summary_hex(aes(z=distance),fun="median",bins=15)+
  geom_polygon(data=world,aes(group=id),drop=T) + 
  scale_fill_gradient("hi",trans='log',low='white',high='red') +
    #ylim(0,60) + xlim(-100,15) + 
  facet_wrap(~yr)
?stat_summary_hex

f=data[data$Year==1883,]
f = data[sample(nrow(f),nrow(f)/10),c("time","lat","long","voyageid")]
f$lat = round(f$lat*precision)/precision
f$long = round(f$long*precision)/precision
f$loc = factor(paste(f$long,f$lat,sep="="))

f = f[f$voyageid %in% names(table(f$voyageid)[table(f$voyageid)>1]),]
ggplot(f,aes(y=lat,x=long))+geom_point()

precision = 1/4

levels(f$loc)

#Compare within a voyage
s = merge(f,f,by='voyageid')
s$distance = abs(s$time.x-s$time.y)
qplot(s$distance)

?daply
install.packages("foreach")
require(foreach)
dist = daply(s,.(loc.x,loc.y),function(frame) {
  median(frame$distance)
},.progress="text")

dist[is.na(dist)]=0
require(igraph)
sort(rownames(dist))
adj = graph.adjacency(dist,weighted=T)
paths = shortest.paths(adj,algorithm="dijkstra")

paths[rownames(dist)=="-8=40",]
PlaceTimes = data.frame(distance = paths[rownames(dist)=="-8=40",])
PlaceTimes = cbind(PlaceTimes,do.call(rbind,strsplit(rownames(dist),"=")))
names(PlaceTimes) = c("distance","long","lat")
PlaceTimes$lat = as.numeric(as.character(PlaceTimes$lat))
PlaceTimes$long = as.numeric(as.character(PlaceTimes$long))
ggplot(PlaceTimes,aes(y=lat,x=long,fill=distance))+geom_raster()
#qplot(PlaceTimes$long)

length(unique(tmp$voyageid))
tmp=data[data$voyageid %in% 
  unique(data$voyageid[
    data$lat > -10 & data$lat < 0 & data$long >85 & data$lat < 95]),]
mapPlot(tmp,mytime=max(tmp$time),timevar="time",timelag=180,
        orientation=c(90,0,0),
        ylim=c(-75,75),
        proj='harrison'
        ,'lat0'=-35,'lat1'=35)
ddply(tmp,.(voyageid),function(voyage) {
  length(unique((tmp$lat-round(tmp$lat))))
})

        
) + 
    geom_text(
          data=yearday[yearday$yearday==timevars$yearday,],
          aes(label=Month,y=loc),
          x=25,color="yellow",size=4) + theme_nothing() +
    geom_text(data=a,aes(label=Nationality,color=color),size=3.3)

