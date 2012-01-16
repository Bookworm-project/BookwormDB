#Attention Chapter
rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")

wordlist = list('attention')
comparelist = list('carriage','language','advantage','passage')


  pairs = list(
    c("called","call"),
    c("excited","excite"),
    c("fixed","fix"),
    c("engaged","engage"),
    c("arrested","arrest"),
    c("awakened","awake"),
    c("concentration","concentrate"),
    c("aroused","arouse"),
    c("amusement","amuse"),
    c("compelled","compel"),
    c("confined","confine"))
  lapply(pairs,function(pair) {
    dbGetQuery(con,
               paste(
                 "UPDATE wordsheap SET stem='",
                 pair[2],
                 "' WHERE stem='",
                 pair[1],
                 "'",
                 sep=""))
  })

source("Rbindings.R")
words = wordgrid(wordlist=list("attention")
         ,
         collation='Case_Insensitive'
         ,
         flagfield='word'
         ,
         n=80,
         yearlim=c(1850,1922)
         ,
         freqClasses = 4
         ,
         trendClasses=3
         )

adunwords = c("absorbed", "amused", "aroused", "arrest", "arrests", "attract", 
"attracted", "attracting", "attracts", "attracts", "awaken","awake","awakened","call", "called", 
"calling", "calls", "challenge", "claimed", "command", "commanded", 
"commands", "compelled", "compelling", "compels", "concentrate", 
"concentrate", "concentrated", "confine","demand", "demanded", "demanding", "demands",
"devoted", "directed", "directing", "distract", "distracted", 
"diverted", "diverting", "divided", "draw", "drawing", "drawn", 
"draws", "drew", "enforce","engage","engaged", "escape","escaped","excited", "excite", "fix","focus", "gave", 
"giving", "increased", "increase","invite","merit", "need", "needed", "needing", 
"needs", "paid", "pay", "paying", "pays", "received", "receiving", 
"required", "riveted", "startled", "strained", "turn", 
"turn", "turned","wander", "wandering","withdraw")

adjectives = c("active", "anxious", "assiduous", "breathless", "careful", 
"child's", "close", "closer", "closest", "conscious", "considerable", 
"constant", "continuous", "critical", "deep", "deepest", "devout", 
"diligent", "direct", "divided", "divided", "due", "eager", "earnest", 
"enough", "entire", "especial", "exclusive", "expectant", "faithful", 
"favorable", "first", "fixed", "great", "his", "immediate", "increased", 
"increasing", "insufficient", "intelligent", "keen", "kind", 
"least", "less", "marked", "medical", "minute", "most", "much", "national", 
"ordinary", "our", "particular", "patient", 
"peculiar", "persevering", "personal", "polite", "principal", 
"profound", "prompt", "proper", "rapt", "renewed", "respectful", 
"rigid", "scant", "scrupulous", "sedulous", "serious", "slightest", 
"special", "special", "steady", "strained", "strict", "strictest", 
"sufficient", "sustained", "thoughtful", "undivided", "undue", 
"unremitted", "unremitting", "unwearied", "utmost", "vigilant", 
"voluntary", "watchful", "whole", "wide", "widespread")



adjectives = wordgrid(
  wordlist=list("attention")
         ,
         comparelist = list('Freiheit','Wahrheit','Einheit'),
         WordsOverride = adjectives
         ,
         collation='Case_Insensitive'
         ,
         flagfield='casesens'
         ,
         n=80
         ,
         language = list('eng')
         ,
         yearlim=c(1823,1922)
         ,
         freqClasses = 4
         ,
         trendClasses=3
         ) 
wordgrid(list("God"),yearlim=c(1750,1922),freqClasses=4,trendClasses=3)


find_distinguishing_words <- function (
  word1,
  word2 = list('attention'),
  years = as.list(1820:1840),
  country = list("USA")
  ) {
  core_search = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list('lc1','catalog.bookid as id','catalog.nwords as length'),      
    words_collation = 'All_Words_with_Same_Stem',
    tablename='master_bigrams',
    search_limits = 
      list(
        list(
          'alanguage'=list('eng'),
          'word2' = word2,
          'word1' = word1,
          'country' = list("USA"),
          'year'    = years
          )
    )
  )
  #Now we flag the books that have the phrase 'call attention' before 1840,
  #and a baseline comparison of 1000 books.
  
  v = dbGetQuery(con,APIcall(core_search))
  flagBookids(v$id,1)
  flagRandomBooks(
    1000,
    2,
    paste(
      'year >= ',
      years[1],
      ' AND year <= ',
      rev(years)[1],
      " AND alanguage = 'eng' ",
      " AND (",
      paste("country='",country,"'",sep="",collapse = " OR "),
      ")"),
    preclear=F
    )
  v[order(v[,4]),]
  
  
  core_search = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list('words1.word as word'),      
    words_collation = 'All_Words_with_Same_Stem',
    tablename='master_bigrams',
    search_limits = 
      list(
        list(
          'bflag' = list(1)
          ),
        list(
          'bflag'  = list(2))
    )
  )
  z = compare_groups(core_search)
}

words = find_distinguishing_words(
  word1 = list('focus'),
  word2 = list('attention'),
  years = as.list(1915:1920),
  country = list("USA")
  )
  
words[[1]][1:25]

find_distinguishing_words()

#What are the age patterns for 'pay attention' more frequently used 

limits = list("word1"=list("of"),"word2" = list("the"))
p = median_ages(limits)
z = median_ages(list("word"=list("smile")));z + geom_smooth(se=F,lwd=2,span=.3)

plot(z[,1],z[,2]-p[,2],type='l')
source('Word Spread.R')
  genres =genreplot(list('Focus attention'),
            grouping=list('lc1'),
            groupings_to_use = 30,
            counttype = 'Occurrences_per_Million_Words',
            ordering=NULL,
            years=c(1870,1922),
            smoothing=6,
            comparison_words = list(),
            words_collation='All_Words_with_Same_Stem')
  genres  

ggplot(melt(volcano)) + geom_tile()
