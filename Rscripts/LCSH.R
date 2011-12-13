rm(list=ls())
setwd("/presidio")
source("Rbindings.R")

#First, get all the books--then take a sample of 500 from each of the major languages.
books = dbGetQuery(con,"SELECT bookid,language,aLanguage FROM catalog")
languages = names(table(books$language))[table(books$language)>400]
languages = languages[!languages %in% c("grc","","ukr","dan","ota")]

dbGetQuery(con,"UPDATE catalog SET bflag=0")
sample = lapply(languages,function(language) {
  loc = books[books$language==language,]
  loc[sample(1:nrow(loc),min(1000,nrow(loc))),]})
silent =lapply(sample, function(loc) {
  apply(loc,1,function(row){
    dbGetQuery(con,paste("UPDATE catalog SET bflag=1 WHERE bookid =",row[1],sep=""))
  })
})

topwords = lapply(languages,function(language) {
  frame = dbGetQuery(con,paste("
                   SELECT word,sum(count) as count
                   FROM master_bookcounts
                   JOIN catalog USING (bookid) 
                   JOIN wordsheap USING (wordid) 
                   WHERE language = '", language , "' 
                   AND CHAR_LENGTH(word)>=3 AND bflag=1 group by wordid 
                    ORDER BY count DESC LIMIT 1000",sep=""))
  frame = frame[nchar(frame$word) >= 3,]
  }
)
backup = topwords
topwords = lapply(topwords,function(frame) {frame[1:250,]})
words = do.call(rbind,topwords)$word
duplicated = unique(words[duplicated(words)])
uniquewords = lapply(topwords,function(frame) {
  frame$word[!frame$word %in% duplicated][1:30]
})
names(uniquewords) = languages
words = unlist(uniquewords)
#Set those particular words as the the ones to use.
dbGetQuery(con,"UPDATE wordsheap SET wflag=0")
silent = lapply(words,function(word) {
  z = dbGetQuery(con,paste("UPDATE wordsheap SET wflag=1 WHERE casesens = '",word,"'",sep=""))
})                      
                               
training = dbGetQuery(con,"
                      SELECT language,
                        wh.word,
                        cat.bookid,
                        IFNULL(1000000*count/nwords,0) as ratio 
                      FROM
                      wordsheap as wh JOIN catalog as cat 
                       ON (wflag = 1 and bflag=1)
                       LEFT JOIN master_bookcounts as mb ON 
                        (wh.wordid = mb.wordid AND cat.bookid = mb.bookid)
                      ")                            
reparse = function(set) {
  parseable = xtabs(set$ratio ~ set$bookid + set$word)
  parseable = as.data.frame(unclass(parseable))                              
  mlanguage = as.factor(set$language[match(rownames(parseable),set$bookid)])
  parseable = cbind(mlanguage,parseable)
}

training = reparse(training)

  
#build a linear model

#build a cluster model
km = kmeans(training[,-1],50,iter.max = 30,nstart=3)
tabs = table(km$cluster,training$mlanguage)
clusternames = apply(tabs,1,function(row) {colnames(tabs)[which(row==max(row)[1])]})
clusternames[apply(tabs,1,max)/rowSums(tabs)<=.5] = "Unknown"

#train an lda model on the cluster model
require(MASS); modeltype = svm
training$mlanguage = clusternames[km$cluster]
model = modeltype(mlanguage ~ .,training); predicted = predict(model,training[,-1])
table(predicted$class,training$mlang)
  newmodel = modeltype(mlanguage ~ .,usable); predicted = predict(newmodel,usable[,-1])
sample()
  diag())/colSums(table(predicted$class,usable$mlang))

#Here's some code I used to see what sort of text was in the clusters:
lapply(sample(rownames(training)[predicted$class=="eng" & training$mlang=="Unknown"],3),example)

for (i in seq(0,1500000,by=4000)) {
  testing = dbGetQuery(con,paste("
              SELECT language,wh.word,cat.bookid,IFNULL(1000000*count/nwords,0) as ratio 
              FROM
              wordsheap as wh JOIN catalog as cat 
                  ON (wflag= 1 AND aLanguage=""
                  AND cat.bookid < ", i + 4000 ," AND cat.bookid >= ", i , ")
                      LEFT JOIN master_bookcounts as mb ON 
                    (wh.wordid = mb.wordid AND cat.bookid = mb.bookid)
                        ",sep=""))
  if (nrow(testing) > 0) {
   testing = reparse(testing)
   redone = predict(model,newdata = testing[,-1])
    updates = data.frame(orig = as.character(testing$mlanguage),learned = as.character(redone[1]$class),bookid = rownames(testing))
    apply(updates,1,function(row) {
      if (as.character(row[1]) != as.character(row[2])) {
        query = paste("UPDATE catalog SET aLanguage ='",row[2],"' WHERE bookid = ",row[3],sep="")
        dbGetQuery(con,query)
      }
    })
  }
  cat("completed " , i,"\n")
}              
#After this, all the blanks need to be updated en masse to equal the default settings.
                         
  catpred = apply(predicted,1,function(row) {names(row)[which(row==max(row))]})
apply(predicted,1,max)==1
table(catpred[apply(predicted,1,max)>=.9],parseable$mlanguage[apply(predicted,1,max)>=.9])

predicted       
                                 
link = function(bookid,connn=con)  {
  id = dbGetQuery(connn,paste("SELECT ocaid FROM open_editions WHERE bookid = ",bookid,";",sep="")  )[1,1]
  cat("http://www.archive.org/stream/",id,"\n",sep="")
}

example = function(bookid,connn=con,lines = 10) {
  id = dbGetQuery(connn,paste("SELECT ocaid FROM open_editions WHERE bookid = ",bookid,";",sep="")  )[1,1]
  p = scan(
    url(
      paste(
        "http://www.archive.org/download/",id,"/",id,"_djvu.txt",sep=""
        )),what='raw',sep="\n")
  start = sample(length(p)-lines,1)
  p[start:(start+lines)]
} 
                                 