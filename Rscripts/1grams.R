con2 = dbConnect(
  MySQL(),db="presidio",host='chaucer.fas.harvard.edu',password='newton')

totals = dbGetQuery(con2,"SELECT year,max(books) as books FROM 1grams 
  WHERE word='of' OR word='the' OR word='and' 
  GROUP BY year")
  
  
n = 5000  

get_counts <- function (n1,n2) {
  words = dbGetQuery(
    con2,"UPDATE wordsheap SET wflag=0")
  words = dbGetQuery(
    con2,
    paste("UPDATE wordsheap SET wflag=1 
  WHERE wordid >= ",
  n1,
  " AND wordid <= ",n2))
  wordz=  dbGetQuery(
    con2,
    paste(
    "SELECT 1grams.word as wordname,books as count,year
    FROM 1grams 
    JOIN (SELECT word FROM wordsheap WHERE wflag=1) as words 
    ON (words.word=1grams.word) WHERE year >= 1800 AND year <= 2000 GROUP BY year,wordname;",
    sep=""))
}

    wordz =   get_counts(50000, 55000)
tabulated = xtabs(count~year+wordname,wordz)
tabulated = tabulated[,colSums(tabulated)>20]

percentages = tabulated/totals$books[match(rownames(tabulated),totals$year)]
    
cors = apply(tabulated,2,cor,as.numeric(rownames(tabulated)))
years = apply(percentages,2,function(col) {
    min(as.numeric(rownames(percentages)[cumsum(col)>sum(col)/5]))
    })
hist(years)
sort(years[years>=1900]   ) 
years[names(years)=='Gorbachev']

    relative = t(t(tabulated)/colSums(tabulated))
    
    

n = nrow(tabulated); z = apply(tabulated,2,function(col) {col[1:(n-20)]/col[21:n]})