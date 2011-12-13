midwords = dbGetQuery(con,APIcall(
  list(
    method = 'allwords_query',
    words_collation="Case_Insensitive",
    search_limits = list(
      list('lc1'=list("BF"),'alanguage'=list('eng'),'wflag' = list(1))
     )
    )
))
words = dbGetQuery("SELECT word,count FROM words WHERE wordid <= 200000")

p = dun.with.merge(words,midwords)
distinguishingwords = sort(p)[1:1000]
flagWordids(names(distinguishingwords))

midwords = dbGetQuery(con,APIcall(
  list(
    method = 'allwords_query',
    words_collation="Case_Insensitive",
    groupings = "bookid",
    search_limits = list(
      list('lc1'=list("BF"),'alanguage'=list('eng'),'wflag' = list(1))
     )
    )
))
names(midwords) = c("word","bookid","count")
require(ca)
crosstabs = table(count)
tmp = midwords[1:20,]
tmp$word = factor(tmp$word)
tmp$bookid = factor(tmp$bookid)
xtabs(count ~ bookid+word,tmp)