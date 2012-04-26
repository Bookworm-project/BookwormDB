#!LDA
rm(con)
setwd("/presidio/Rscripts")
source("Rbindings.R")
dbGetQuery(con,'UPDATE fastcat JOIN open_editions USING (bookid) SET fastcat.bflag=0')
dbGetQuery(con,'
           UPDATE fastcat JOIN open_editions USING (bookid) SET fastcat.bflag=1 WHERE (fastcat.aLanguage="eng" OR 
           fastcat.aLanguage="Lat" OR fastcat.aLanguage="Fre") AND author="Cicero"')

dbGetQuery(con,"UPDATE fastcat SET bflag=2 WHERE aLanguage = 'Fre' AND bflag=1 ORDER BY RAND() LIMIT 10")
dbGetQuery(con,"UPDATE fastcat SET bflag=2 WHERE aLanguage = 'Eng' AND bflag=1 ORDER BY RAND() LIMIT 10")
dbGetQuery(con,"UPDATE fastcat SET bflag=2 WHERE aLanguage = 'Lat' AND bflag=1 ORDER BY RAND() LIMIT 10")

f = APIcall(list(method='counts_query',groups=list('word','fastcat.bookid as bid'),search_limits=list(bflag=list(2))))
counts = dbGetQuery(con,f)

head(counts)
words = xtabs(count~word,counts)
words = words[nchar(names(words))>1]

V=15
counts = counts[counts$word %in% names(sort(-words))[1:V],]
tokens = dlply(counts,.(bid),function(frame) {sample(rep(frame$word,frame$count),100)})

length(tokens[[15]])
M = length(books)
K = 3

alpha = 50/K
beta = 1/V
theta = matrix(.33,nrow=K,ncol=V)
phi = matrix(1/K,nrow=M,ncol=K)
phi %*% theta