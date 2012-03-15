setwd("/presidio/Rscripts")
source("Rbindings.R")
wordgrid <- function (
  wordlist = list("democracy")
  ,
  comparelist=list()
  ,
  WordsOverride = NULL
  ,
  excludeStopwords = T
  ,
  excludeList = c()
  ,
  fitAgainst='raw'
  ,
  collation = 'Case_Insensitive'
  ,
  wordfield = 'stem'
  ,
  yearlim=c(1821,2000)
  ,
  n=50
  ,
  freqClasses = 3
  ,
  language = list("eng")
  ,
  trendClasses = 3
  ,
  mydb=con
  ,
  returnData=F
  ,
  field = "word2",
  totalProxy="the"
  ) {
  if (field=="word1") {
    otherfield="word2"
  } else {otherfield = "word1"}
  query = dbGetQuery(mydb,"USE ngrams")

  if (is.null(WordsOverride)){
    samplingSpan=13
    wheres = list(year = seq(yearlim[1],yearlim[2],by=samplingSpan),word2=unlist(wordlist))
    names(wheres)[2] = field
    data = dbGetQuery(
      mydb,
      paste(
        "
        SELECT w1.",wordfield,"
        as word1,w2.",wordfield,"
        as word2,sum(words) as words,year FROM 2grams 
        JOIN presidio.wordsheap as w1 
        ON  w1.casesens = 2grams.word1
        JOIN presidio.wordsheap as w2 ON w2.casesens = 2grams.word2
        WHERE ",
        whereterm(wheres),
      " GROUP BY word1,word2,year",sep=""))
    data = data[!is.na(data$word1) & !is.na(data$word2),]
    data$fixfield = get(otherfield,data)
    totals = dbGetQuery(
      mydb,
      paste(
        "SELECT words,year FROM presidio.1grams WHERE ",
        whereterm(list(year = seq(yearlim[1],yearlim[2],by=samplingSpan),word1=totalProxy))))
    ratios = xtabs(words ~ year + fixfield,data)
    total = totals$words[match(rownames(ratios),totals$year)]
    ratios = ratios/total
    ratios = ratios[,order(-colSums(ratios))]
    dunwords = colnames(ratios)[1:(n+400)]
  }
  
  if (length(WordsOverride)>0) {
    dunwords = WordsOverride
  }
  
  dunwords = dunwords[grep("^[A-Za-z]+$",dunwords,perl=T)]
  
  if (excludeStopwords) {
    stopwords = dbGetQuery(mydb,"SELECT word FROM presidio.words WHERE stopword = 1; ")[,1]
    excludeList = c(excludeList,stopwords)
  }
  dunwords = dunwords[!dunwords %in% excludeList]

  if (length(WordsOverride)>0) {dunwords = WordsOverride}
  
  dunwords = dunwords[1:min(n,length(dunwords))]
  cat("wordlist chosen... Selecting results for those words\n")
    if (field=="word2") { 
      wherewords = list(dunwords,unlist(wordlist)) 
      } else {
      wherewords = list(unlist(wordlist),dunwords) 
    }
    
    names(wherewords) = paste(c('w1.','w2.'),wordfield,sep="")
   data = dbGetQuery(
      mydb,
      paste(
        "
        SELECT w1.",wordfield,"
        as word1,w2.",wordfield,"
        as word2,sum(words) as words,year FROM 2grams 
        JOIN presidio.wordsheap as w1 
        ON  w1.casesens = 2grams.word1 
        JOIN presidio.wordsheap as w2 ON w2.casesens = 2grams.word2
        WHERE ",
        whereterm(wherewords),
      " GROUP BY word1,word2,year",sep=""))
    totals = dbGetQuery(
      mydb,
      paste(
        "SELECT words,year FROM presidio.1grams WHERE ",
        whereterm(list(word1=totalProxy))))
    data = data[data$year > yearlim[1] & 
    data$year < yearlim[2],]
    data$fixfield = get(otherfield,data)    
    ratios = xtabs(words ~ year + fixfield,data)
    ratios = ratios[,order(-colSums(ratios))]
    total = totals$words[match(rownames(ratios),totals$year)]
    ratios = ratios/total
    matrified = 100*ratios/rowSums(ratios)
    matrified[is.na(matrified)] = 0
  #ratio = apply(matrified,2,function(col) {col/sum(col)})
  #fitting = matrified
  #if (fitAgainst == 'smoothed') {
  #  fitting  = apply(matrified,2,function(col) {
  #    lo.model = loess(col~as.numeric(rownames(matrified)))
  #    predict(lo.model,as.numeric(rownames(matrified)))
  #    })
  #}
  #p = kmeans(cor(fitting),clusters)
  #rm(fitting)                   
  melted = melt(matrified)
    
  #Create some factors to divide up the plot by; left to right ascending to declining,
    #top to bottom frequent to infrequent
  freqs = colSums(matrified)
  trends = apply(matrified,2,function(z) {
    lm(z~as.numeric(rownames(matrified)))$coefficients[2]
  })
  names(freqs) = names(trends) = colnames(matrified)
  

#freqClasses =3;trendClasses=2
   z = kmeans(
    data.frame(trends = rank(trends),
               freqs = rank(freqs)),
    freqClasses*trendClasses,
    nstart=7,
    iter.max=40)
  frame = as.data.frame(z$centers)
  
  frame$r.freq = rank(frame$freqs,ties.method='random')
  frame$r.trend = rank(frame$trends,ties.method='random')
  frame$name = rownames(frame)
  frame$cut.freq = floor((rank(frame$r.freq,ties.method='random')-1)/(trendClasses))
  frame = frame[order(-frame$cut.freq,-frame$trends),]
  clusternames = frame$name
                        
  plot(rank(trends),rank(freqs),type='p',col=z$cluster,pch=16)
  text(z$centers[as.numeric(clusternames),],as.character(1:nrow(z$centers)))

  melted$cluster = z$cluster[match(melted$fixfield,names(z$cluster))]
  melted$trend = trends[match(melted$fixfield,names(trends))]
  melted$commonness = freqs[match(melted$fixfield,names(freqs))]     
  names(melted)[1] = "year"
  charts = lapply(clusternames,function(num) {
    my_data = melted[num==melted$cluster,]
    my_data$word = factor(my_data$fixfield)
    require(zoo)
    #my_data$smoothed = rollapply(my_data$value,11,median,fill=NA)
    #my_data$smoothed = rollapply(my_data$smoothed,11,median,fill=NA)
    ggplot(
      my_data,
      aes(x=year,y=value,color=word)) +  
        geom_line(size=.1) +
        geom_smooth(span=.4,size = 1,se=F,fullrange=T) +
        #geom_line(aes(y=smoothed),size=1) +
        ylab("") + xlab("")
        })
    require(gridExtra)
    mytitle = "preceding"; if (field=="word1") {mytitle = "following"}
    args.list <- c(
      charts,
      freqClasses,
      trendClasses,
      paste("Relative share of most frequent words",
            mytitle,paste(wordlist,collapse="/")),
      "Percentage of all displayed words",
      "Year")
    names(args.list) <- c(clusternames, "nrow","ncol","main","left","sub")
  plot = do.call(grid.arrange,args.list)
  if (returnData) {plot = list(plot,matrified)}  
  plot
}
if (FALSE) {
  rm(list=ls())
  mylist = wordgrid(list("capitalism","Capitalism"),
    returnData=F,
    wordfield='casesens',
    field='word2',n=45,
    yearlim=c(1900,2000)
  )
  mylist
  source("Word Spread.R")
  genreplot(
    word = list('democratic idea'),
    years = c(1830,1922),
    grouping = 'lc0',
    counttype = 'Occurrences_per_Million_Words',
    groupings_to_use=15,ordering=NULL,smoothing=15,
    comparison_words=list(),
    words_collation = "Case_Sensitive",
   country = list()) 

}