setwd("/presidio/Rscripts")
source("Rbindings.R")

wordgrid <- function (
  wordlist = list("library")
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
  plotData=T
  ,
  
  field = "w2.casesens"
  ,
  totalProxy="the"
  ,
  samplingSpan=13

  )
  {
  if (grepl("w1",field)) {
    otherfield="w2.casesens"
    otherfieldname = "word2"
  } else {
    otherfield = "w1.casesens";     otherfieldname="word1"
  }
  wordcollation = sub(".*\\.","",field)
  query = dbGetQuery(mydb,"USE ngrams")

  if (is.null(WordsOverride)){
    wheres = list(year = seq(yearlim[1],yearlim[2],by=samplingSpan),w2.casesens=unlist(wordlist))
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
    data$fixfield = get(otherfieldname,data)

    totals = dbGetQuery(
      mydb,
      paste(
        "
        SELECT words,year FROM 
        presidio.1grams JOIN presidio.wordsheap as w1 
        ON w1.casesens=1grams.word1 WHERE ",
        whereterm(list(year = seq(yearlim[1],yearlim[2],by=samplingSpan),w1.casesens=totalProxy))))
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
  if (grepl("2",field)) { 
    wherewords = list(dunwords,unlist(wordlist))
    names(wherewords) = paste(c('w1.','w2.'),c(wordfield,wordcollation),sep="")

    } else {
    wherewords = list(unlist(wordlist),dunwords) 
    names(wherewords) = paste(c('w1.','w2.'),c(wordcollation,wordfield),sep="")

  }

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
    data$fixfield = get(otherfieldname,data)    
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
            mytitle,paste(wordlist,collapse="/")," (", yearlim[1],"-",yearlim[2],")"),
      "Percentage of all displayed words",
      "Year")
    names(args.list) <- c(clusternames, "nrow","ncol","main","left","sub")
  cat("preparing plot\n")
  if (plotData) {plot = do.call(grid.arrange,args.list)
                 return(plot)}
  if (returnData) {return(matrified)}  
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

ngramsGridMovie = function(word = "attention",
                           field = 'w2.casesens',range = 20) { 
  source("Rbindings.R")
  dbGetQuery(con,"Use ngrams")
  source("ngrams wordgrid.R")
  mylist = wordgrid(list(word),
        wordfield='stem',
        field=field,
        freqClasses=4,
        n=450,
        excludeStopwords = F,
        yearlim=c(1825,2008),
        mydb=con,
        samplingSpan=4,
        returnData=T,
        plotData=F
      )

  loessSmooth = function(col) {
    vals = 1:length(col)
    y = log(col)
    model = loess(y~vals,span=.3)
    vals = exp(predict(model))
  }
  unzeroed = mylist
  unzeroed[unzeroed<=0] = min(unzeroed[unzeroed>0])
  smoothed = apply(unzeroed,2,loessSmooth)
  head(smoothed)
  rownames(smoothed) = rownames(mylist)
  nearterm = smoothed[-1,]/smoothed[-nrow(smoothed),]
  nearterm = apply(nearterm,2,loessSmooth)
  rownames(nearterm) = rownames(mylist)[-1]  
  longterm = smoothed[-c(1:range),]/smoothed[-c((nrow(smoothed)-range+1):nrow(smoothed)),]
  longterm = apply(longterm,2,loessSmooth)
  rownames(longterm) = rownames(mylist)[-c(1:range)] 
  merged = merge(melt(nearterm),melt(longterm),by=c("Var.1","fixfield"))
  merged = merge(merged,melt(smoothed),by=c("Var.1","fixfield"))
  names(merged) = c("year","word","nearterm","longterm","freq")
  
  try(system(paste("mkdir ~/movies/",word,sep="")))
  for (year in min(merged$year):max(merged$year)) {
    cat("writing ",year,"\n")
  png(
    paste("~/movies/",word,"/output",year,'.png',sep=''),
    width=1920,height=1080)
  myplot = ggplot(merged[merged$year==year,]) + 
    geom_text(aes(x=freq,y=longterm,label=word,size=freq)) + 
    scale_y_continuous(trans='log10',
                       limits = c(1/10,range(merged$longterm)[2])) + 
    scale_x_continuous(trans='log',
                       limits = c(range(merged$freq))) + 
    scale_size_continuous(trans='log') + opts(legend.position = 'none',title=paste(year-range,year))
  print (myplot)
  graphics.off()  
  }
  system(paste("cd ~/movies; ~/movies/moviemake.sh",word,sep=" "))
  system(command=paste("cp ~/movies/",word,".mp4 /var/www/",word,".mp4",sep=""))
} 

