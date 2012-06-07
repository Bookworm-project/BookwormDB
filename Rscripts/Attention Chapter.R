#Attention Chapter
rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")
source("NewerAPI.R")
source("ngrams wordgrid.R")
wordlist = list('attention')

preceders = APIcall(list(
         "method"="counts_query",
         "collation"="Case_Sensitive",
         "search_limits"=list(
            "word2"=list("attention"),
            "alanguage"=list("eng")),
         "groups"=list("words1.lowercase as w1","catalog.bookid as bid"),
         "database"="presidio"))
catalog = dbGetQuery(con,"SELECT * FROM catalog")

values = dbGetQuery(con,preceders)
values = values[!grepl("[^A-Za-z]",values$w1),]
values$w1 = factor(values$w1)
words = xtabs(count~w1,values)
goodwords = names(words[words>500])
length(goodwords)
using = values[values$w1 %in% goodwords,]

#using = using[using$year>1750,]
#using = using[using$year<2005,]

#using$year = factor(using$year)
#using$lc1 = factor(using$lc1)
#using$lc0 = factor(using$lc0)

require(reshape2)
head(using)
melted = melt(using,id.var=c("bid","w1"))
m = acast(melted,formula=bid~w1,.fun.aggregate="sum")
head(melted)
m = dcast(melted,formula=year+lc0+lc1~w1,fun.aggregate=sum)
m[,-c(1,2,3)] = m[,-c(1,2,3)]/rowSums(m[,-c(1,2,3)] )
lm(year~a+able+about+absolute+absorb+absorbed)

?formula
m = m[,-1]
m = m/rowSums(m)
rowSums(m)

years = as.numeric(gsub("y","",colnames(m)))

range = 10

y1 = 1830
y2 = 1860
y1 = y1+1
y2 = y2+1
scores = rowSums(m[,years %in% (y2-range):(y2+range)])/rowSums(m[,years %in% (y1-range):(y1+range)])
max(scores)
vals = data.frame(
  word = m$w1,
  ratio = scores,
  commonness = (rowSums(m[,years %in% (y2-range):(y2+range)])+rowSums(m[,years %in% (y1-range):(y1+range)]))/2/(range*2+1))
vals = vals[!is.na(vals$ratio),]
vals$ratio[is.infinite(vals$ratio)] = 2.7*max(vals$ratio[!is.infinite(vals$ratio)])
vals$ratio[vals$ratio==0] = (1/2.7)*min(vals$ratio[!vals$ratio==0])
word
ggplot(vals[!is.na(vals$ratio),]) + 
  geom_text(aes(label=word,y=ratio,x=100*commonness),size=3) + 
  scale_y_continuous(trans='log10',limits = c(1/10,1000)) + 
  scale_x_continuous("Percentage",trans='log10',limits = c(1/1000,20)) + opts(
    title=paste("change between",paste(y1,y2,sep=" and " )))

mylist = wordgrid(
        list("attention"),
        wordfield='stem',
        field='w2.word',
        freqClasses=4,
        n=200,
        yearlim=c(1825,2008),
        mydb=con,
        samplingSpan=4,
        returnData=F,
        plotData=T,
        WordsOverride=adunwords
      )

  if (FALSE) {
  ngramsGridMovie("Attention",field='w1.word')
  ngramsGridMovie("attention",field='w2.casesens')
  ngramsGridMovie("slave",field='w1.casesens')
  ngramsGridMovie("slavery",field='w2.casesens')
  ngramsGridMovie("academic",field='w1.casesens')
  ngramsGridMovie("guilt",field='w2.casesens')
  ngramsGridMovie("capitalist",field='w1.casesens')
  ngramsGridMovie("free",field='w1.casesens')
  ngramsGridMovie("attentive",field='w1.casesens')
  ngramsGridMovie("conscious",field='w1.casesens')
  ngramsGridMovie("democratic",field='w1.casesens')
  ngramsGridMovie("Freedom",field='w1.word')
  ngramsGridMovie("freedom",field='w2.casesens')
}

year = year+1
ggplot(merged[merged$year==year,]) + 
  geom_text(aes(x=nearterm,y=longterm,label=word,size=freq)) + 
  scale_y_continuous(trans='log10') + scale_x_continuous(trans='log') + 
  scale_size_continuous(trans='log') + opts(title=year)

  m$y1[is.na(m$y1)] = 0
m$y2[is.na(m$y2)] = 0
names(m)
m$y1 = m$y1/sum(m$y1)
m$y2 = m$y2/sum(m$y2)
m$change = m$y2/m$y1
m$total = m$y1+m$y2
head(m)
qplot(log(m$change[m$total>.01]),binwidth=.1)
ggplot(m[m$total>.00001,],aes(x=total,y=change,label=w1,group=1)) + scale_y_continuous(trans='log') +scale_x_continuous(trans='log')+ geom_text(size=4)



m[m$w1=="His",]

pairs = list(
    c("called","call"),
    c("excited","excite"),
    c("fixed","fix"),
    c("engaged","engage"),
    c("drawn","draw"),
    c("drew","draw"),
    c("arrested","arrest"),
    c("especially","especial"),
    c("direction","direct"),
    c("awakened","awake"),
    c("concentration","concentrate"),
    c("aroused","arouse"),
    c("amusement","amuse"),
    c("compelled","compel"),
    c("care","careful"),
    c("confined","confine"))
silent =   lapply(pairs,function(pair) {
    dbGetQuery(con,paste("UPDATE presidio.wordsheap SET stem='",pair[2], "' WHERE stem='",pair[1],"'",sep=""))
  })

source("Rbindings.R")
source("ngrams wordgrid.R")
words = wordgrid(list("attention"),freqClasses=4,
    returnData=F,
    wordfield='casesens',
    field='word1',n=45, 
    yearlim=c(1800,2000)
  )

adunwords = c("absorbed", "amused", "aroused", "arrest", "arrests", "attract", 
"attracted", "attracting", "attracts", "attracts", "awaken","awake","awakened","call", "called", 
"calling", "calls", "challenge", "claimed", "command", "commanded", 
"commands", "compelled", "compelling", "compels", "concentrate", 
"concentrate", "concentrated", "confine","demand", "demanded", "demanding", "demands",
"devoted", "directed", "directing", "distract", "distracted", 
"diverted", "diverting", "divided", "draw", "drawing", "drawn", 
"draws", "drew", "enforce","engage","engaged", "escape","escaped",
"excited", "excite", "fix","focus", "gave", 
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


#What are the age patterns for 'pay attention' more frequently used 

limits = list("word1"=list("of"),"word2" = list("the"))
p = median_ages(limits)
z = median_ages(list("word"=list("smile")));z + geom_smooth(se=F,lwd=2,span=.3)

plot(z[,1],z[,2]-p[,2],type='l')
rm(con)
source('Rbindings.R')
source('Word Spread.R')

genreplot(
    word = list('concentrate attention'),
    years = c(1880:1922),
    grouping = 'lc1',
    counttype = 'Occurrences_per_Million_Words',
    groupings_to_use=40,
    ordering=NULL,
    smoothing=5,
    chunkSmoothing=1,
    comparison_words=list(),
    words_collation = "All_Words_with_Same_Stem",
    alanguage=list("eng"),
    country = list(),
    authgender=list(),
    lc0=list()) + 
    scale_fill_gradientn("Occurrences\nper\nmillion\nwords",colours=c("white","steelblue","red")) + 
    opts(title="Usage of 'concentrate attention' by Library of Congress Classification")

source("ngrams wordgrid.R")


mylist = wordgrid(list("attention"),
        wordfield='stem',
        field='w2.word',
        freqClasses=4,
                  WordsOverride=adunwords,
        n=400,
        yearlim=c(1825,2008),
        mydb=con,
        samplingSpan=4,
        returnData=F,
        plotData=T,
          wordgrid         
      ) + options(title="Relative shares of verbs preceding 'attention' (1825-2008)")


counts = dbGetQuery(con,"SELECT word1,word2,year,words FROM ngrams.2grams WHERE word2='attention'")
counts$w1 = paste(counts$word1,counts$word2)
counts = counts[,c("w1","year","words")]
counts = counts[!grepl("[^A-Za-z ]",counts$w1,perl=T),]
counts$w1 = factor(counts$w1)
tdm = xtabs(words~w1+year,counts[counts$year>1820,])
tdm = apply(tdm,2,function(col){
  col/sum(col)
  })
dim(tdm)
tdm = tdm[rowSums(tdm)>1/200,]
tdm = as.matrix(tdm)
predicted = apply(tdm,1,function(row){
  model = loess(row~as.numeric(colnames(tdm)),span=56)
  model$fitted
})
predicted[predicted<=0] = min(predicted[predicted>0])/4
rownames(predicted) = colnames(tdm)
colnames(predicted) = rownames(tdm)

head(predicted)
change = (predicted[-1,]-predicted[-nrow(predicted),])
change2 = (predicted[-1,]/predicted[-nrow(predicted),])
colnames(change2) = rownames(tdm)

qplot(as.numeric(rownames(change)),rowSums(abs(change)))
names(sort(change2[rownames(change2)==1900,])[1:15])
risers = names(sort(-change2[rownames(change2)==1900,])[1:50])
fallers = names(sort(change2[rownames(change2)==1900,])[1:50])
as.list(words)
source("Word Spread.R")
rm(con)
source("Rbindings.R")
genreplot(
    word = list("concentrate attention","focus attention"),
    years = c(1870:1922),
    grouping = 'authgender',
    counttype = 'Occurrences_per_Million_Words',
    groupings_to_use=2,
    ordering=NULL,
    smoothing=7,
    chunkSmoothing=1,
    comparison_words=list("attention"),
    words_collation = "All_Words_with_Same_Stem",
    alanguage=list("eng"),
    country = list(),
    authgender=list("Female","Male")) + 
    scale_fill_gradientn("Occurrences\nper\nmillion\nwords",colours=c("white","steelblue","red")) + 
    opts(title="Usage of 'concentrate attention' or 'focus attention'\nby probable author gender",base_size=7)

ggsave(plot,file="~/dropbox/concentrateLC.png",width=8,height=6)
?ggsave
genres =genreplot(list("waked"),
          grouping='author_age',
          groupings_to_use = 63,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1822,1922),
          smoothing=8,
          comparison_words = list("woke"),
          words_collation='Case_Sensitive',country=list("USA"))

core_query = 
  list(method = 'counts_query',
      smoothingType="None",      
      groups = list(
        "words1.word as w1","words1.stem as stem1",
        "year","lc1","lc0","state","country","aLanguage","nwords"),                           
      search_limits = 
         list(
          'word2'=list('attention')
     ))

vals = dbGetQuery(con,APIcall(core_query))

words = vals[!is.na(vals$stem1),]

normstemscore = ddply(words,.(stem1),function(frame) {
  data.frame(
    average = mean(xtabs(frame$count~frame$year)/xtabs(frame$nwords~frame$year)))*nrow(frame)
})
qplot(normstemscore$average) + scale_x_log10()
normstemscore$stem1[order(-normstemscore$average)][1:500]

top = words[words$stem1 %in% normstemscore$stem1[order(-normstemscore$average)][1:1000]
,]

dim(top)
head(top)

ggplot(top,aes(x=year,y=count/nwords)) + geom_smooth()
