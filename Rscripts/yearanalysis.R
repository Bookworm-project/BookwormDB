setwd("/presidio")
source("Rbindings.R")

p =APIcall(list(method="ratio_query",smoothingType="None",groupings="year,bookid",search_limits = list(list('word'=list('1860')))))

values = lapply(1848:1922,function(num) {
p = paste("SELECT word,bookid,sum(count) FROM beta_bookcounts JOIN catalog USING (bookid) JOIN wordsheap
USING (wordid)
WHERE year > 1848 and year < 1922 and word='",num,"' GROUP BY word,bookid",sep="")
dbGetQuery(con,p)
})

a = do.call(rbind,values)
a$word = as.numeric(a$word)
colnames(a)[3] = "count"

          
z = xtabs(count ~ bookid+word,a)
bookids = dbGetQuery(con,"SELECT bookid,catalog.year,ocaid,editionid FROM catalog LEFT JOIN open_editions USING(bookid)")
years = bookids$year[match(rownames(z),bookids$bookid)]
plot(years,apply(z,1,mean))
          
          
          
words = as.numeric(colnames(z))
averageyear = apply(z,1,function(row) {sum(row*words)/sum(row)})
maxyear  = apply(z,1,function(row) {max(as.numeric(words[row >0])})
modeyear = apply(z,1,function(row) {
   as.numeric(max(names(row[which(row==max(row))]) ))
})
90peryear = apply()

modelframe = data.frame(years,averageyear,maxyear,modeyear)
modelframe = modelframe[!is.na(modelframe$years),]
plot(modelframe$year+sample(-1000:1000,nrow(modelframe),replace=T)/500,
          modelframe$max+sample(-1000:1000,nrow(modelframe),replace=T)/500,
          pch=16,col=rgb(.5,0,0,.01))
sample = modelframes[ample(1:nrow(modelframe),5000),]
model = lm(years ~ maxyear+modeyear+averageyear,sample)
          
for (editionid in 
          bookids$editionid[match(names(rev(sort(abs(model$residuals)))[1:20]),
           bookids$bookid)]) {
   cat(paste("http://openlibrary.org/books/",editionid,"\n",sep=""))
}

          
          plot(model)
  
        years[1:5]; maxyear[1:5]
cat("http://www.archive.org")