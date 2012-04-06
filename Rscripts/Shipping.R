#Ocean routes

#All this code was posted by Erian on http://spatialanalysis.co.uk/2012/03/mapped-british-shipping-1750-1800/

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
ggplot(tmp,aes(Lon3,Lat3))+
geom_point(alpha=0.01,size=1) +
coord_map() +
ylim(-90,90)

#Here's my stuff
names(dat$CLIWOC15)
head(dat$CLIWOC15[,1:15])
useful=dat$CLIWOC15[,c("Lon3","Lat3","Year",
              "Month","Day","PartDay",
                       "Nationality",
                       "LogbookIdent",
                       "ShipName")]
useful$voyage = factor(
  as.numeric(
    factor(
      paste(
        useful$ShipName,
        useful$LogbookIdent))))
#And here's a value to fill in more later
#Here's a hack to make sure they're sequential even letting months be 31 days
useful$time = useful$Year*373+(useful$Month-1)*31+useful$Day
useful = useful[,! (colnames(useful) %in% c("LogbookIdent","ShipName"))]
useful$Nationality = factor(useful$Nationality)
useful = useful[!is.na(useful$Lon3) & !is.na(useful$Lat3),]
useful = useful[order(useful$voyage,useful$time),]

useful$dist=c(0,sqrt(rowSums((useful[-1,c("Lon3","Lat3")]-route[-nrow(useful),c("Lon3","Lat3")])^2)))
useful$timeoff=c(0,useful[-1,c("time")]-useful[-nrow(useful),c("time")])
useful$newship=c(0,useful[-1,c("voyage")]!=useful[-nrow(useful),c("voyage")])
breaks = useful$timeoff > 60 | useful$dist > 20 | useful$newship
useful$voyageID = factor(paste(useful$id,"-",cumsum(breaks)+1))
  

library(maps)
reg <- as.data.frame(map("world", plot = FALSE)[c("x", "y")]) 
qplot(x, y, data = reg, geom = "path") 

timelag = 180
mytime = 656995
summary(useful$time)
i=0
plots = lapply(c(seq(674200,674500,by=1),seq(658000,665000,by=1)),function(mytime) {
  if (mytime %in% useful$time) {
    i <<- i+1
    savable = 
          ggsave(filename=paste("~/shipping/",mytime,".jpg",sep=""),plot=savable,width=5.5,height=3.5,quality=100)
    }
})
mapPlot = function(myframe=useful,mytime=654200,timelag=180) {
  ggplot(myframe[myframe$time>(mytime-timelag) & myframe$time<mytime,])+
    geom_path(size=1,
              aes(group=voyageID,alpha=(time-mytime)/timelag,
                  x=Lon3,y=Lat3,color=Nationality)) +
    scale_x_continuous(expand=c(0,0)) +  scale_y_continuous(expand=c(0,0)) + 
    geom_point(data=myframe[myframe$time==mytime,],aes(group=voyageID,alpha=(time-mytime)/timelag,
                  x=Lon3,y=Lat3,color=Nationality)) + 
    geom_path(data=reg,aes(x=x,y=y),color='grey') + ylab("")+xlab("") + 
    opts(legend.position = "none",axis.text.x=theme_blank(),
        axis.text.y=theme_blank(),axis.ticks=theme_blank()) + 
    coord_map(projection='mollweide',
              xlim = c(-79, 25),
              ylim = c(-49, 69),
              orientation=c(100,0,-30)) + 
    opts(title = paste(myframe[myframe$time==mytime,c("Year","Month","Day")][1,],collapse="-"))
}
mapPlot()



table(useful$Nationality[!duplicated(useful$voyageID)])
myplot = plots[[10]]

lapply(plots)