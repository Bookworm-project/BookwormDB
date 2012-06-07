
setwd("/presidio/Rscripts")
rm(con)
source("Rbindings.R")
table = dbGetQuery(con,"
                   SELECT authorid,author,gender,lc0,lc1,year,authorbirth,country,state,publishers 
                   FROM gender JOIN open_editions
                   USING (bookid)")
head(table)           
table$lc0 = factor(table$lc0)
table$lc1 = factor(table$lc1)
table$country = factor(table$country)
table$state = factor(table$state)
table$gender = factor(table$gender,levels = c(1,2))
table$publishers = toupper(as.character(table$publishers))
table$publishers = factor(table$publishers)
table$publisher = iconv(table$publishers,from="UTF-8",to="ASCII")
table$publisher = tolower(table$publisher)
sort(-table(table$publisher))[1:10]
table$publisher = gsub(" ?(and|&) ? [cC]o.*","",table$publisher)
table$publisher = gsub(",","",table$publisher)
table$publisher = gsub(" ?company","",table$publisher)
table$publisher = gsub("and","",table$publisher)
table$publisher = gsub("&","",table$publisher)
table$publisher = gsub("the ","",table$publisher)
table$publisher = gsub(" $","",table$publisher)
table$publisher = gsub("  +"," ",table$publisher)
write.table(table,file="/var/www/genderdata.txt")
sort(-table(table$publisher))[1:25]

goodlcs = names(table(table$lc1))[table(table$lc1)>500]
goodpubs = names(table(table$publisher[table$year < 1922]))[table(table$publisher[table$year < 1922])>500]

fpertime = ddply(table[table$lc1 %in% goodlcs,],.(lc1,year),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[1])
})

fper = ddply(table[table$lc1 %in% goodlcs & table$year < 1922 & table$year > 1800,],.(lc1),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[!is.na(loc$lc0)][1])
})


ggplot(fper) + geom_bar(aes(x=lc1,y=FemalePercent*100,alpha=totalBooks),fill="red") + 
  facet_wrap(~lc0,scale="free_x",ncol=3) + 
  scale_alpha_continuous("Number of books",trans="log10",breaks=c(1,500,1000,2000,5000,10000,15000,25000))+
  scale_y_continuous("Percentage of books by women") +
  opts(title="Female Percentage of Authors, by LC class")

table$state=toupper(table$state)
fper = ddply(table[table$lc1 %in% goodlcs & table$year < 1922 & table$year > 1800,],
             .(state),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[!is.na(loc$lc0)][1])
})
fper$state[fper$state=="NB"] = "NE"
library(ggplot2)
library(maps)
d1 <- map_data("state")
table(fper$state)
states = read.csv(file=url("http://www.fonz.net/blog/wp-content/uploads/2008/04/states.csv"))
states$State=tolower(as.character(states$State))
d1$state = states$Abbreviation[match(d1$region,states$State)]
head(d1)
head(fper)
fper = merge(fper,d1,by="state")
head(d1)

ggplot(fper,aes(map_id=region)) + 
  geom_map(map=d1,aes(fill=FemalePercent)) +   
  expand_limits(x = d1$long, y = d1$lat) +opts(panel.background=theme_blank()) + xlab("") + ylab("") + opts(title = "Percentage of Female authors, by state")

ggplot(fper,aes(x=state,y=FemalePercent*100)) + geom_bar(aes(alpha=totalBooks),fill='red') + coord_flip() +   scale_alpha_continuous("Number of books",trans="log10",breaks=c(1,500,1000,2000,5000,10000,15000,50000)) + scale_y_continuous("Percentage of Books by Women") + xlab("") + opts(title="Percentage of books by women, 1800-1922, by state")

fper = ddply(table[table$year < 1922 & table$year > 1800,],
             .(country),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1,na.rm=T)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[!is.na(loc$lc0)][1])
})
ggplot(fper,aes(x=country,y=FemalePercent*100)) + geom_bar(aes(alpha=totalBooks),fill='red') + coord_flip() +   scale_alpha_continuous("Number of books",trans="log10",breaks=c(1,500,1000,2000,5000,10000,15000,50000)) + scale_y_continuous("Percentage of Books by Women") + xlab("") + opts(title="Percentage of books by women, 1800-1922, by country")

fper = ddply(table[table$year < 1922 & table$year > 1800 & table$publisher %in% goodpubs,],
             .(publisher),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1,na.rm=T)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[!is.na(loc$lc0)][1])
})
ggplot(fper,aes(x=publisher,y=FemalePercent*100)) + geom_bar(aes(alpha=totalBooks),fill='red') + coord_flip() +   scale_alpha_continuous("Number of books",trans="log10",breaks=c(1,500,1000,2000,5000,10000,15000,50000)) + scale_y_continuous("Percentage of Books by Women") + xlab("") + opts(title="Percentage of books by women, 1800-1922\namong publishers with > 400 books")


fper = ddply(table[table$year < 2005 & table$year > 1800,],
             .(year),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1,na.rm=T)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[!is.na(loc$lc0)][1])
})
             
ggplot(fper,aes(x=year,y=FemalePercent*100)) + geom_line(color='red')+
  scale_y_continuous("Percentage of Books by Women") + 
  xlab("") + 
  opts(title="Percentage of books by women in the Open Library/Internet Archive",limits = c(0,50)) +
  geom_vline(x=1922,lty=2,lwd=4,alpha=.5) +annotate("text",x=1924,y=35,label="Results\nafter\n1922\nare\nless\nmeaningful",hjust=0)
             
nbooks = ddply(table[table$year < 1922 & table$year > 1800,],
             .(authorid),function(loc){
  data.frame(authorbooks = nrow(loc))
})

table = merge(nbooks,table,by="authorid")
fper = ddply(table[table$year < 1922 & table$year > 1800,],
             .(nbooks),function(loc){
  data.frame(FemalePercent = sum(loc$gender==1)/nrow(loc),
             totalBooks = nrow(loc),
             lc0 = loc$lc0[!is.na(loc$lc0)][1])
})


