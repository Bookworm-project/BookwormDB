melville = dbConnect(MySQL(),
                host="melville.seas.harvard.edu",
                password="oldPassword",
                user="oldUser",
                db="presidio")

dbGetQuery(melville,"UPDATE wordsheap SET wflag=0")

dbGetQuery(melville,"UPDATE wordsheap JOIN words USING (wordid) SET wordsheap.wflag=1 
           WHERE wordsheap.casesens REGEXP '^[A-Za-z][a-z]*$' AND words.stopword=0")

date()
z = dbGetQuery(
  melville,
  "SELECT word1,year,books from 1grams JOIN wordsheap ON 1grams.word1 = wordsheap.casesens 
  WHERE year >= 1800 AND year <= 2005 and wflag=1 and wordid < 200000"
  )
totals = dbGetQuery(melville,"SELECT year,max(books) as books FROM 1grams WHERE word1='the' or word1 = '.' or word1 = 'a' GROUP BY year")

date()
summary(z)
z$books = as.numeric(z$books)
z$word1 = factor(z$word1)


as.numeric(z[1:5,]$word1)
           
subset = z[1:10000000,]
subset$word1 = factor(subset$word1)           
tabbed = xtabs(books~year+word1,subset,sparse=T)
           
dim(tabbed)
tabbed = tabbed[,1:(ncol(tabbed)-1)]


commonish = tabbed
commonish = commonish/totals$books[match(rownames(commonish),as.character(totals$year))]
           
ave_times_from = function(loctabbed,start = 1800, span=15) {
  start = which(rownames(loctabbed)==start)
  colSums(loctabbed[(start):(start+span-1),])/span
}
ave_times_at_end = ave_times_from(commonish,max(as.numeric(rownames(commonish)))-14)
ave_times_at_beginning = ave_times_from(commonish,min(as.numeric(rownames(commonish))))
ave_times_at_f_transition = ave_times_from(commonish,1816)
interesting = (
           ave_times_at_end/ave_times_at_f_transition > .8 & 
           ave_times_at_beginning/ave_times_at_f_transition < 2)  
           
commonish = commonish[,interesting]
dim(commonish)

#Set a smoothing window
window = 4
           
smoothed = apply(commonish,2,rollmedian,k=window*2+1,na.pad=T)
rownames(smoothed) = as.numeric(rownames(tabbed)[1:nrow(smoothed)])
  

changefrom = function(n,basemat) {
  compare_span = abs(n)
  comparison = matrix(NA,nrow = nrow(basemat),ncol = ncol(basemat),dimnames = dimnames(basemat))
  if (n<0) {
    comparison[-c(1:compare_span),] = basemat[1:(nrow(basemat)-compare_span),]
  }
  if (n>=0) {
    comparison[1:(nrow(basemat)-compare_span),] = basemat[-c(1:compare_span),]
  }
  basemat/comparison
}
compare_span=10           

change_from_before = changefrom(-compare_span,smoothed)
change_from_after  = changefrom(compare_span,smoothed)
#longafter = changefrom(25,smoothed)  
bigones = which(change_from_before > 3 & change_from_after < 2 & smoothed > .001 ,arr.ind=T)

big_change = change_from_before > 3 & change_from_after < 2 & smoothed > .001

which(big_change,arr.ind=T)
changes = data.frame(year = dimnames(smoothed)[[1]][bigones[,1]],
                     word = dimnames(smoothed)[[2]][bigones[,2]])

demo = 1859
changes = changes[order(changes$year),]
           changes[changes$word=='Texas',]
changes[!duplicated(changes$word),]
           
plot(rownames(change_from_before),
  change_from_before[,colnames(change_from_before)==
           "concept"],log='y',
  type='l')