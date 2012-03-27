v = dbConnect(MySQL(),host='chaucer.fas.harvard.edu',password='fake')
dbGetQuery(v,"USE arxiv")

times = dbGetQuery(v,'
                   SELECT date_format(date, "%w") AS day,
                   date_format(date, "%Y") AS year,
                   date_format(date, "%H") AS hour FROM catalog GROUP BY day,hour,year')
head(times)
times$yearcut = factor(times$year>2000)

ggplot(times) + geom_histogram(aes(x=as.numeric(hour),fill=day),binwidth=1,position='dodge') + facet_grid(yearcut~day)
source("Trendspotting.R")

a= APIcall(
  list("method"="ratio_query",
       "groups"=list("month"),
        "counttype"="Number_of_Books",
           "words_collation"="Case_Sensitive",
           "smoothingSpan"="0",
       "database"="arxiv",
      "search_limits"=list(
             "word"=list("$grep"=list("1780")),

             "archive"=list("Physics")
)
  ))
dbGetQuery(v,a)
authors = dbGetQuery(v,"SELECT author FROM catalog")[,1]
head(authors)
auth1=gsub("\\([^\\)]*\\)",'',authors)
head(auth1)
auth1 = strsplit(auth1,' and ')
auth1 = lapply(auth1,function(loc) unlist(lapply(loc,strsplit,',')))
head(auth1)
auth2 = lapply(auth1,function(names) gsub("^ *([A-Za-z-]+)[\\. ].*","\\1",unlist(names)))
auth2[1:250]
-sort(-table(unlist(auth2)))[1:250]

lists = lapply(1880:2010,function(year) {
  })
names(lists)
SSdat = ldply(1880:2010,function(year){
  tab = read.table(paste("/data/SSA/yob",year,".txt",sep=''),sep=',')
  tab$year=year
  tab
})
names(SSdat)=c("name","gender","count","year")
SSdat$count=as.numeric(SSdat$count)
SSdat$name=factor(SSdat$name)
namesCount = xtabs(count~name,SSdat)
goodNames = names(namesCount[namesCount>400])

tabbed = xtabs(count~name+gender,SSdat[SSdat$year>1930 & SSdat$year<1995 & SSdat$name %in% goodNames,])
tabbed = tabbed[rowSums(tabbed)>0,]
ratios = apply(tabbed,1,function(row) {row[1]/(row[1]+row[2]) } ) 
namedat = data.frame(name=rownames(tabbed),
           ratios = apply(tabbed,1,function(row) {row[1]/(row[1]+row[2]) } ),
           counts = apply(tabbed,1,function(row) {(row[1]+row[2]) }))
namedat$gender[namedat$ratios>.97]="F"
namedat$gender[namedat$ratios<.03]="M"

head(namedat,50)

auth2[1:5]
papergenders = sapply(auth2[sample(1:length(auth2),25000)],function(namelist){
  genders = sapply(namelist,function(name) {namedat$gender[match(name,namedat$name)]})
  c("Female" = sum(genders=="F",na.rm=T),"Male" = sum(genders=="M",na.rm=T))
})

genders = as.data.frame(t(papergenders))
genderats = sapply(1:13,function(n){
sum(genders$Female[rowSums(genders)>=n])/sum(rowSums(genders[rowSums(genders)>=n,c(1:2)]))
})
genderats