#Ocean routes

#All this code was posted by Eiran on http://spatialanalysis.co.uk/2012/03/mapped-british-shipping-1750-1800/
setwd("~/shipping")
require(Hmisc) # need also mdbtools installed
path <- "~/shipping"
URL <- "http://www.knmi.nl/";
PATH <- "cliwoc/download/"
FILE <- "CLIWOC15_2000.zip"
download.file(paste(URL,PATH,FILE,sep=""),
paste(path,"CLIWOC15_2000.zip",sep=""))
dir <- unzip(paste(path,"CLIWOC15_2000.zip",sep=""))
file <- substr(dir,3,nchar(dir))
dat <- mdb.get(file)
tmp <- dat$CLIWOC15[,c("Lon3","Lat3")]

#Here's my stuff

useful=dat$CLIWOC15[,c("Lon3","Lat3","Year",
                       "Month","Day","PartDay",
                       "Nationality",
                       "LogbookIdent",
                       "ShipName","VoyageTo","VoyageFrom")]
names(dat$CLIWOC15)
#For ease of calling:
useful$Lat=useful$Lat3
useful$Long=useful$Lon3

#At a first approximation, voyages are a combination of the shipname and the logbook.
useful$voyage = factor(
  as.numeric(
    factor(
      paste(
        useful$ShipName,
        useful$LogbookIdent))))

names = ddply(useful,.(ShipName,Nationality,Year,VoyageTo,VoyageFrom),function(frame) {data.frame(nrow(frame))})
names[order(-names[,6]),][1:100,]
counts = ddply(names,.(Nationality),function(frame){
  place = c(as.character(frame$VoyageFrom),as.character(frame$VoyageTo));
  x = table(place);
  data.frame(x)}
      )
f = head(counts[order(-counts$Freq),],20)
rownames(f)=1:20
f

#Add a looping value to give the position in the year (which is 370-odd days, since each month of 31 days)
useful$yearday = as.numeric(factor((useful$Month-1)*31+useful$Day))
#God knows what this does. Removes things like March 31 and December 32 from the list, I think.
#doesn't remove February 29th, though:
useful$yearday[  useful$yearday %in%     names(table(useful$yearday))[table(useful$yearday)<=20]]=useful$yearday[
  useful$yearday %in% 
    names(table(useful$yearday))[table(useful$yearday)<=20]
]+1
useful$yearday = as.numeric(factor(useful$yearday))

#373 days per year keeps there from issues where November 1st might come before Oct 31st.
useful$time = useful$Year*373+(useful$Month-1)*31+useful$Day
#Drop some columns we no longer need
useful = useful[,! (colnames(useful) %in% c("LogbookIdent","ShipName"))]
useful$Nationality = factor(useful$Nationality)
useful = useful[!is.na(useful$Lon3) & !is.na(useful$Lat3),]
useful = useful[order(useful$voyage,useful$time),]

#Capture the distance between two adjacent lat/long points. (I use the same distances in degrees, inappropriately, at the poles in equator.)
useful$dist=c(0,
              sqrt(rowSums((
                useful[-1,c("Lon3","Lat3")]-
                useful[-nrow(useful),c("Lon3","Lat3")]
              )^2)))
useful$timeoff=c(0,
                 useful[-1,c("time")]-
                 useful[-nrow(useful),c("time")]
                )
useful$newship=c(0,useful[-1,c("voyage")]!=useful[-nrow(useful),c("voyage")])
breaks = useful$timeoff > 60 | useful$dist > 20 | useful$newship
#Sequentially order each ship voyage in the database by incrementing a factor every spot where there's a break
useful$voyageID = factor(paste(useful$id,"-",cumsum(breaks)+1))
  
#Here's some code from the ggplot2 github page. Written by Hadley himself, I think.
#It reads in a shape file that, unlike the "Maps" package, doesn't have country borders
require("rgdal") # requires sp, will use proj.4 if installed
require("maptools")
require("ggplot2")
gpclibPermit() # required for fortify method
world = readOGR(dsn=".", layer="110m_land")
world@data$id = rownames(world@data)
world.points = fortify(world, region="id")
#world<- fortify(readShapePoly("110m_ocean.shp"))
world.df = join(world.points, world@data, by="id")
world = world.df

#Back to my stuff. Rename to get it to plot easier.
world$Lat = world$lat
world$Long = world$long
head(world)
world$y=world$Lat
world$x=world$Long
world$id=world$group

#Code from http://groups.google.com/group/ggplot2/msg/f1c381055c29b358; changed to a blue background.
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

#This can be used for either type of plot--it's agnostic about the time variable going, and the lag can be set.
mapPlot = function(myframe=useful,mytime=654100,timelag=34,timevar="time",...) {
  #I define half the plot here, and half later. No real reason. This is why I don't usually share that much code.
  myframe$timevar=get(timevar,myframe)
  myframe=myframe[myframe$timevar>=(mytime-timelag) & myframe$timevar<=mytime,]
  if (timevar=="time") {myframe$group = myframe$voyageID}
  if (timevar=="yearday") {myframe$group = paste(myframe$voyageID,myframe$Year)}
  ggplot(myframe,
         aes(y=Lat,x=Long))+
    geom_polygon(data=world,aes(x=x,y=y,group=id),drop=T)+
    geom_path(size=.5,
              aes(group=group,
                  #This alpha here decaying by time is what makes the trails slowly erase.
                  alpha=(timevar-mytime)/timelag,color=color))+ 
                    scale_color_identity() +
    geom_point(data=myframe[myframe$timevar==mytime,],size=.75,
               aes(group=voyageID,alpha=(timevar-mytime)/timelag,
                  color=color)) + 
    ylab("")+xlab("")  +
    opts(legend.position = "none",axis.text.x=theme_blank(),
        axis.text.y=theme_blank(),axis.ticks=theme_blank()) + 
    coord_map(...)
}

#Use the classic colors.
useful$color = "#8DA0CB"
useful$color[useful$Nationality=="British"] = "#E7298A"
useful$color[useful$Nationality=="British "] = "#E7298A"
useful$color[useful$Nationality=="Dutch"] = "#D95F02"
useful$color[useful$Nationality=="Spanish"] = "#66A61E"


yearday = data.frame(yearday=sort(unique(useful$yearday)))
yearday$loc = c(sin((yearday$yearday-100)/(369/pi/2))*23.5)
#This will occasionally be off by a day or two.
yearday$Month = c("Jan","Feb","Mar","Apr","May","Jun","Jul",
                  "Aug","Sep","Oct","Nov","Dec")[(yearday$yearday+30)%/%31]

#Position a legend on the screen:
a = data.frame(Nationality = useful$Nationality,color = useful$color)
a = a[!duplicated(a) & a$Nationality %in% c("Dutch","Spanish","British","French"),]
levels(a$Nationality)[levels(a$Nationality)=="French"] = "Other"
    a$Lat = seq(0,-15,length.out=4)
    a$Long = -60
day=1

special = useful
#Make the yearday plot. I just rewrote this bit here to add days 0,-1,-2 for the first days later, so 
#the year doesn't start with points. but the lapply should run usually w/ the 'useful' frame.
special$Year[special$yearday>363] = special$Year[special$yearday>363] + 1
special$yearday[special$yearday>363] = special$yearday[special$yearday>363]-366
plots = lapply(1:6,function(day) {
  timevars = list(yearday=useful$yearday[useful$yearday==day][1],year=useful$Year[useful$yearday==day][1])
  myplot = 
      mapPlot(special,mytime=day,timevar="yearday",timelag=5,
        orientation=c(90,0,0),
        ylim=c(-70,70),
        proj='gilbert') + 
    geom_text(
          data=yearday[yearday$yearday==timevars$yearday,],
          aes(label=Month,y=loc),
          x=25,color="yellow",size=4) + theme_nothing() +
    geom_text(data=a,aes(label=Nationality,color=color),size=3.3)
  #And then save it to a file.
  ggsave(filename=paste("~/shipping/images/",formatC(day,digits=4,format='d',flag='0')
,".png",sep=""), plot=myplot,width=6,height=4)
})
system("./moviemake.sh")

#For the main chart, skip every other day and don't include any February 29ths, September 31sts, and so on.
plotting2 = sort(unique(useful$time[useful$yearday%/%2!=useful$yearday/2 & !is.na(useful$yearday)&useful$Year>=1750]))

plots = lapply(plotting2,function(day) {
  timevars = list(yearday=useful$yearday[useful$time==day][1],year=useful$Year[useful$time==day][1])
  myplot = 
    mapPlot(useful,mytime=day,timevar="time",timelag=180,
        orientation=c(90,0,0),
        ylim=c(-70,70),
        proj='gilbert') + 
    geom_text(
          data=yearday[yearday$yearday==timevars$yearday,],
          aes(label=Month,y=loc),
          x=25,color="yellow",size=4) + 
  #could have just used annotate geom for this, too. Oh well.
  geom_text(
          data=data.frame(year=timevars$year),aes(label=year),
            x=5,y=18,color="yellow",size=4) + theme_nothing()+
    geom_text(data=a,aes(label=Nationality,color=color),size=3.3)
  #And then save it to a file.
  ggsave(filename=paste("~/shipping/alltime/",formatC(day,digits=4,format='d',flag='0')
,".png",sep=""), plot=myplot,width=6,height=4)
})
system("./moviemake.sh")

mapPlot(useful,mytime=668000,timevar="time",timelag=100,
        ylim=c(-65,80),xlim=c(-180,180),
        proj='gilbert')
        
projection="tetra")
?coord_map
