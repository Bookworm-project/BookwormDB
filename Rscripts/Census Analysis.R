setwd("~/Census")
#This is an IPUMS dump.
data = read.csv("census.csv")
descriptions = scan("usa_00005.sas",what="raw",sep="\n")
descriptions = paste(descriptions,collapse="\n")
#working with SAS load files is a real pain.

require(plyr)
#Clean stuff up a bit.
data$SEX = factor(data$SEX)
data$NAMEFRST = factor(data$NAMEFRST)
#Sometimes the first name has a space in it. That might be "Billie Jean", but a lot of 
#of the time (the vast majority) it's "Harry S" or "Franklin Delano" (ie.,
#a middle initial or middle name). So 
#I define the first name as before the space.
data$REALFRST = gsub(" .*","",data$NAMEFRST)
data$REALFRST = factor(data$REALFRST)

counts = table(data$REALFRST)
goodnames = names(sort(-counts)[1:10000])
#create a list of the top 10,000 names in the sample.
#I'm creating the using ddply, because I'm obsessed with ddply right now.
genderbreakdown = ddply(data[data$REALFRST %in% goodnames,],.(REALFRST),
  function(frame) {
  #using sum() across true/false clauses is generally the easiest way to do a COUNTIF function, I find, since
  #TRUE returns 1 and FALSE returns 0
  data.frame(male = sum(frame$SEX==1),female=sum(frame$SEX==2))
})
head(genderbreakdown)

#Here's a hack:any term that doesn't appear at all for the opposite gender, we say
#actually appears 1/10 of a time. This allows ratios to make sense even w/ zeroes.
genderbreakdown$male[genderbreakdown$male==0] = .1
genderbreakdown$female[genderbreakdown$female==0] = .1
#Add dummy variable for color, because: why not?
genderbreakdown$color = factor(sample(1:12,nrow(genderbreakdown),replace=T))
#Here's where I'm putting axis labels:
breaks = c(1/10000,1/1000,1/100,1/30,1/10,1/3,1,3,10,30,100,1000,10000)
#It's easier to think of percentages than logs; this does that, since a 1/1000 ratio mean
labels=100*round(breaks/(breaks+1),2)

#Here's a function I just pulled out of a help page in R to lowercase the names but keep the first letter upper:
capwords <- function(s, strict = T) {
    cap <- function(s) paste(toupper(substring(s,1,1)),
                  {s <- substring(s,2); if(strict) tolower(s) else s},
                             sep = "", collapse = " " )
    sapply(strsplit(s, split = " "), cap, USE.NAMES = !is.null(names(s)))
}


ggplot(genderbreakdown,
       aes(label=capwords(as.character(REALFRST)),size=sqrt((male+female)),
                           x=male/female,color=color,alpha=.1,
                           y=male+female)) +
                             geom_vline(xint=c(1),lty=2,color='grey',alpha=.4,size=2.5) +
       geom_text() +  
         opts(title="Top 10,000 names in the 1910-1920 censuses",
    panel.grid.major = theme_blank(),
    panel.grid.minor = theme_blank(),
    panel.background = theme_blank(),
    text.size=4,
    axis.ticks = theme_blank(),legend.position = "none") +
  scale_y_continuous("Frequency",trans='log10') + 
    scale_x_continuous("Percentage Male",breaks=breaks,
                       labels = labels,trans='log10',limits = c(1/2000,2000)) +
    geom_vline(xint=c(1/100,100))  + scale_size(to=c(3,12)) 


#And then write the table over.
con=dbConnect(MySQL())
f=data.frame(name=capwords(as.character(genderbreakdown$REALFRST)),frequency=genderbreakdown$male+genderbreakdown$female,gender=NA)
f$gender[genderbreakdown$male/genderbreakdown$female<=1/50]=1
f$gender[genderbreakdown$male/genderbreakdown$female>=50]=2
f=f[!is.na(f$gender) & f$frequency>50,]
head(f)
write.table(f,file="/tmp/genders",sep="\t",row.names=F,quote=F)

dbGetQuery(con,"DROP TABLE IF EXISTS genders")
dbGetQuery(con,"
CREATE TABLE genders (name VARCHAR(255), INDEX (name),frequency MEDIUMINT,gender TINYINT, INDEX (gender));")
dbGetQuery(con,"LOAD DATA LOCAL INFILE '/tmp/genders' INTO TABLE genders")
dbGetQuery(con,"DROP TABLE IF EXISTS gender")
dbGetQuery(con,"
           CREATE TABLE gender (bookid MEDIUMINT, PRIMARY KEY (bookid),
           gender TINYINT, INDEX(gender)) ENGINE = MEMORY")
dbGetQuery(con," 
           INSERT INTO gender
           SELECT bookid,gender FROM open_editions 
           JOIN genders ON (substring(author,1,instr(author,' ')-1)=name)
           ;")
dbGetQuery(con," 
           UPDATE gender JOIN open_editions USING(bookid)
           SET gender=1 WHERE author='George Eliot'
           ;")


authors = dbGetQuery(con,"SELECT author FROM open_editions WHERE year > 1905 AND year < 1922 AND country='USA' AND lc1='PZ'")
authors = authors[,1]
authors = gsub(" .*","",authors)
authors = table(authors)
authframe = data.frame(authors)
#"invalid multibyte strings lead me to a try wrapper
authframe$name = gsub("[^A-Za-z]","",authframe$authors)
authframe$name = capwords(authframe$name)
authmerge = ddply(authframe,.(name),function(frame) {
  data.frame(count = sum(frame$Freq))})

mergeable = genderbreakdown
mergeable$name = capwords(gsub("[^A-Za-z]","",mergeable$REALFRST))
mergeable = mergeable[mergeable$name != "",]
mergeable$name = factor(mergeable$name)
mergeable = ddply(mergeable,.(name),function(frame) {
  data.frame(men = sum(frame$male),
             women = sum(frame$female),
             total = sum(frame$female)+sum(frame$male),
             female = sum(frame$female)>=sum(frame$male)
             )
})
head(mergeable)
merged=merge(authmerge,mergeable,by='name')
merged$gender = factor(merged$female,labels=c("male","female"))
ggplot(merged,
       aes(label=name,
           x=((men+women)/sum(men+women))/(count/sum(count)),fill=gender,color=gender))+ 
             geom_density(position='dodge',alpha=.5,adjust=1.2) + 
             scale_x_continuous("times in census per times in library",trans='log10') + 
             opts(title="Women's names (blue) are under-represented on average") + coord_flip() + geom_vline(xint=1,color='red',size=2)

ggplot(merged,
       aes(label=name,
           x=(men+women)/sum(men+women),
           y= ((men+women)/sum(men+women))/(count/sum(count)),color=gender)) + geom_hline(yint=1,color='red',size=2)+
             geom_point() + scale_x_continuous("Overall Frequency in population",trans='log10',lim = c(1/8000,1/20))+ 
             scale_y_continuous("times in census per times in library",trans='log10') + opts(title="And that pattern is independent of frequency...")

ggplot(merged,
       aes(label=name,
           x=(men+women)/sum(men+women),
           y= ((men+women)/sum(men+women))/(count/sum(count)),
           color=gender)) + geom_hline(yint=1,color='red',size=2)+
             geom_text(alpha=.8) + scale_x_continuous("overall frequency in census",trans='log10',lim = c(1/2000,1/20))+ 
             scale_y_continuous("times in census per times in library",trans='log10',lim=c(1/10,100)) +
             facet_wrap(~gender,ncol=1) + 
             opts(title="But some male names are under-represented\nand some female names over-represented")



head(merged)
merged$FirstLetter = factor(substr(merged$name,1,1))
merged$totalPop = merged$women+merged$men
letters = levels(merged$FirstLetter)
letters = letters[letters!="X" & letters !="Z"& letters !="O"]
letterdata = ldply(letters,function(letter) {
  myframe = merged[merged$FirstLetter==letter,]
  data.frame(totalPop = sum(myframe$totalPop),
             PercentFemaleInPopulation = 100*sum(myframe$women)/sum(myframe$totalPop),
             PercentLetterInPopulation = 100*sum(myframe$count)/sum(merged$count),
             PercentJustLetterInBookAuthors = 100*sum(myframe$count[myframe$name==letter])/sum(myframe$count),
             letter = letter,
             totalAuths = sum(myframe$count))
})

ggplot(letterdata,
       aes(x=PercentFemaleInPopulation,y=PercentJustLetterInBookAuthors,
           size = sqrt(totalPop),label=letter))+geom_text() + 
             geom_smooth(method='lm') + 
             opts(legend.position="none",title="Restricting to Fiction, the pattern is less strong") + ylab("% of author names using just the first inital") +
              xlab("women, as % of people with that first initial in the census")
?lm

cor(letterdata$PercentFemaleInPopulation,letterdata$PercentJustLetterInBooks)
vals = dbGetQuery(con,
           APIcall(
             list(method = 'ratio_query',
      smoothingType="None",      
      groups = list("year",'gender','words1.word as word','lc1'),                           
      search_limits = 
        list(
         list(
          'word'=list('she','he')
     )))
             ))
vals = vals[vals$gender %in% c(1,2),]
vals$gender = factor(vals$gender)
vals$year = as.numeric(vals$year)
vals$word = factor(tolower(vals$word))
vals = vals[vals$year>1822 & vals$year < 1922,]
ggplot(vals[vals$lc1 %in% names(rev(sort(table(vals$lc1))))[1:17],],
       aes(x=factor(1),fill=word)) + 
  geom_bar(width=1,height=1) +
  facet_wrap(~lc1+gender)
?geom_bar
warnings()
?facet_wrap
warnings()
head(vals)
vals
f = NA
f[f>.95] = 2
f[f<.95]
head(f)
genderbreakdown$graphPos = log(.5)
  
  
good = names(sort(-table(data$NAMELAST))[1:10000])
names(data)
#countrynames = read.table(stdin()) #This works great just cut and pasting.

geobreakdown = ddply(
  data[data$NAMELAST %in% good,],.(NAMELAST),function(frame) {
    countries = sort(table(frame$FBPL))
    returnval = data.frame(
      code = names(countries),
      count = countries,
      rank = rank(-countries),
      foreign = as.numeric(names(countries)) > 100,
      percent = countries/sum(countries),
      fpercent = countries/sum(countries[as.numeric(names(countries)) > 100])
      )
    returnval$wrank = NA
    returnval$wrank[returnval$foreign] = rank(-returnval$percent[returnval$foreign])
    returnval$wrank[!returnval$foreign] = rank(-returnval$percent[!returnval$foreign])
    returnval
})
geobreakdown$country = factor(geobreakdown$code,levels = countrynames[,1],labels=countrynames[,3])
geobreakdown = geobreakdown[order(geobreakdown$wrank),]
tops = geobreakdown[geobreakdown$foreign & geobreakdown$wrank==1,]
tops[order(-tops$fpercent),][1:2500,]
tops[round(tops$fpercent,2)==.97,]
ggplot(data[tops$country %in% names(sort(-table(tops$country))[1:10]),]) + geom_bar(aes(x=factor(country)))
geobreakdown[1:35,]
countrynames = sort(-table()

geobreakdown$F1 = factor(geobreakdown$F1,levels = names[,1],labels=names[,3])
#data[data$NAMELAST %in% good,][1:5,]
geobreakdown[geobreakdown$F1=="Scotland",]


genderbreakdown[genderbreakdown$genderFreq<.9 & genderbreakdown$genderFreq>.1, ]