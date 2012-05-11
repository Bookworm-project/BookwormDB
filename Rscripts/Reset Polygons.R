
### Recenter ####

require("rgdal") # requires sp, will use proj.4 if installed
require("maptools")
require("ggplot2")
require("plyr")
if(!exists("world")) {
gpclibPermit() # required for fortify method
world = readOGR(dsn="/home/bschmidt/shipping", layer="110m_land")
world@data$id = rownames(world@data)
world.points = fortify(world, region="id")
world.df = join(world.points, world@data, by="id")
world = world.df
}
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
  myframe=myframe[myframe$timevar >= (mytime-timelag) & myframe$timevar <= mytime,]
  if (timevar=="time") {myframe$grouping = factor(myframe$voyageid)}
  if (timevar=="yearday") {myframe$grouping = paste(myframe$voyageid,myframe$Year)}
  if (timevar=="Year") {myframe$grouping = myframe$voyageid}
  myframe$alpha = (myframe$timevar-mytime)/timelag
  
  pointdata = myframe[myframe$timevar==mytime,]
  pointdata = myframe[!duplicated(myframe$timevar,fromLast=T),]
  ggplot(myframe,
         aes(y=lat,x=long))+
    geom_polygon(data=world,aes(x=long,y=lat,group=id),drop=T)+
    geom_path(data=myframe,size=.5,
              aes(group=grouping,
                  #This alpha here decaying by time is what makes the trails slowly erase.
                  alpha= alpha
                  ,color=color
                  ))+ 
                  #  scale_color_identity() +
    geom_point(data=pointdata,size=.75,
               aes(group=voyageid,
                 color=color
                   )) + 
    ylab("")+xlab("")  +
    opts(legend.position = "none",axis.text.x=theme_blank(),
        axis.text.y=theme_blank(),axis.ticks=theme_blank()) + 
    coord_map(...)
}

Recenter = function(
  data=world,
  center=260,
  # positive values only - US centered view is 260
  shapeType=c("polygon","segment"),
  idfield=NULL
  # shift coordinates to recenter great circles
  ) {
  
  #use inherited id column, or create a new one from breaks in the data
  if(is.null(idfield)) {
    data$id=factor(cumsum(is.na(data$long)))
    }else{
    data$id = get(idfield,pos=data)
    }
    
  # shift coordinates to recenter worldmap
  data$long <- ifelse(data$long < center - 180 , data$long + 360, data$long)
  
  ### Function to regroup split lines and polygons
  # takes dataframe, column with long and unique group variable, 
  #returns df with added column named group.regroup
  RegroupElements <- function(df, longcol, idcol){
    g <- rep(1, length(df[,longcol]))
    if (diff(range(df[,longcol])) > 300) { 
      # check if longitude within group differs more than 300 deg, ie if element was split
      d <- df[,longcol] > mean(range(df[,longcol])) 
      # we use the mean to help us separate the extreme values
      g[!d] <- 1 
      # some marker for parts that stay in place (we cheat here a little, as we do not take into account concave polygons)
      g[d] <- 2 
      # parts that are moved
    }
    g <- paste(df[, idcol], g, sep=".") # attach to id to create unique group variable for the dataset
    df$group.regroup <- g
    df
  }
  
  ### Function to close regrouped polygons
  # takes dataframe, checks if 1st and last longitude value are the same, if not, inserts first as last and reassigns order variable
  ClosePolygons <- function(df, longcol, ordercol){
    if (df[1,longcol] != df[nrow(df),longcol]) {
      tmp <- df[1,]
      df <- rbind(df,tmp)
    }
    df
  }
  
  # now regroup
  
  returnframe <- ddply(data, .(id), RegroupElements, "long", "id")
  
  # close polys
  if(shapeType[1]=="polygon") {
    returnframe <- ddply(returnframe, .(group.regroup), ClosePolygons, "long", "order") # use the new grouping var
  }
  ggplot(returnframe,aes(x=long,y=lat))+geom_polygon(aes(group=group.regroup))
  returnframe
}
l = Recenter(world,215,idfield="id");ggplot(l,aes(x=long,y=lat))+geom_polygon(aes(group=group.regroup))+coord_map()
# plot