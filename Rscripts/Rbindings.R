#/usr/bin/R
require(RJSONIO)
require(RMySQL)
require(ggplot2)
con = dbConnect(MySQL(),db="presidio")

dbDisconnect(con)
#install.packages("RMySQL")

APIcall = function(constraints = 
     list(method = 'ratio_query',
      smoothingType="None",      
      groups = list("year"),                           
      search_limits = 
        list(
         list(
          'word'=list('polka','dot'),
          'lc1'=list("BF"),
          'state'=list('NY'))
     )),internal=T) {
  constraints = toJSON(constraints)
  value = system(paste(
    "python /usr/lib/cgi-bin/APIimplementation.py ","'",
    constraints,
    "'",
    sep=""),
    intern=T)
  #We leave the actual result in the last spot
  value = fromJSON(value[[length(value)]])
  value
}

wordgrid <- function (
  wordlist
  ,
  comparelist=list('carriage','language','advantage','passage')
  ,
  WordsOverride = NULL
  ,
  excludeStopwords = T
  ,
  fitAgainst='raw'
  ,
  collation = 'Case_Insensitive'
  ,
  flagfield = 'lowercase'
  ,
  yearlim=c(1821,1922)
  ,
  n=96
  ,
  freqClasses = 3
  ,
  language = list("eng")
  ,
  trendClasses = 2
  ) {
  cat("building initial wordlist...\n")
  search_terms = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list(paste('words1.',flagfield,' as w1',sep='')),      
    words_collation = collation,
    search_limits = 
      list(
       list(
        'word2' = wordlist,
        'alanguage' = language
        )
       )
    )
  year_counts_terms = search_terms
  year_counts_terms[['groups']]=list('year')
  #Getting Year Counts
  year_counts = dbGetQuery(con,APIcall(year_counts_terms))
  
  if (is.null(WordsOverride)){
   query = APIcall(search_terms)
    mainwords = dbGetQuery(con,query)
    compare_terms = search_terms
    compare_terms[['search_limits']][[1]][['word2']] = comparelist
    query = APIcall(compare_terms)
    comparison = dbGetQuery(con,query)
    dunning.comparison = dun.with.merge(mainwords,comparison)
    dunwords = names(sort(-dunning.comparison))[1:(n*3)]
  }
  
  if (length(WordsOverride)>0) {
    dunwords = WordsOverride
  }
  
  if (excludeStopwords) {
    stopwords = dbGetQuery(con,"SELECT word FROM words WHERE stopword = 1; ")[,1]
    dunwords = dunwords[!dunwords %in% stopwords]
  }
  cat("wordlist chosen... Selecting results for those words\n")
  
  flagWordids(dunwords,field='word')
  fielded = dbGetQuery(con,paste("SELECT ",flagfield," FROM wordsheap where wflag=1"))
  flagWordids(fielded[,1],field=flagfield)
  year_search = list(
    method = 'counts_query',
    smoothingType="None",      
    groups=list(
      paste('words1.',flagfield,' as w1',sep=''),
      'year'),      
    words_collation = collation,
    search_limits = 
      list(
       list(
        'words1.wflag' = list(1),
        'word2' = wordlist,
        'alanguage' = language
        )
       )
    )
    
  yearly.frame = dbGetQuery(con,APIcall(year_search))
  yearly.frame = yearly.frame[
    yearly.frame$year > yearlim[1] & 
    yearly.frame$year < yearlim[2],]
  matrified = xtabs(count ~ year+w1,yearly.frame)
  matrified = matrified[,order(-colSums(matrified))[1:(min(n,ncol(matrified)))]]
  matrified = 100*matrified/rowSums(matrified)
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

  melted$cluster = z$cluster[match(melted$w1,names(z$cluster))]
  melted$trend = trends[match(melted$w1,names(trends))]
  melted$commonness = freqs[match(melted$w1,names(freqs))]     
  names(melted)[1] = "year"
  charts = lapply(clusternames,function(num) {
    my_data = melted[num==melted$cluster,]
    my_data$w1 = factor(my_data$w1)
    ggplot(
      my_data,
      aes(x=year,y=value,color=w1)) +  
        geom_line(size=.1) +
        geom_smooth(span=.4,size = 1,se=F,fullrange=T) +
        ylab("% of all displayed words")
        })
    require(gridExtra)
    args.list <- c(charts,freqClasses,trendClasses)
    names(args.list) <- c(clusternames, "nrow","ncol")
    do.call(grid.arrange,args.list)
  
    return(sort(-dunning.comparison))
}


flagBookids = function(bookids,flag=1,preclear=T) {
 con <- dbConnect(MySQL())

 if (preclear) {
  dbGetQuery(con,"UPDATE catalog SET bflag=0")
 }
 dbGetQuery(con,
            paste("UPDATE catalog SET bflag = ",flag," WHERE ",
                      paste("bookid=",bookids,collapse = " OR ")))
 dbDisconnect(con)
}

flagWordids = function(words,field='casesens',n=1,preclear=T) {
 if (preclear) {
   dbGetQuery(con,"UPDATE wordsheap SET wflag=0")
 }
 wordfield = paste(field,'=')
 if (length(grep("'",words)) > 0) {
   cat ("removing words because of quotations")
   words = words[grep("'",words,invert=T)]
 }
 dbGetQuery(con,paste("UPDATE wordsheap SET wflag = ", n, " WHERE ",
                      paste(wordfield,"'",words,"'",sep="",collapse = " OR ")))
}

flagRandomBooks = function(n,flag_number=1,whereclause = "TRUE",preclear=T) {
  if (preclear) {
    dbGetQuery(con,"UPDATE catalog SET bflag=0")
  }
  dbGetQuery(con,paste(
    "UPDATE catalog set bflag=",
    flag_number,
    " WHERE bflag=0 AND ",
    whereclause, 
    " ORDER BY RAND() LIMIT ",
    n,
    ";",sep=""))
}

compare_groups <- function (
  core_search,
  returnFrame = F,
  conn=con) {
  #This is a function that takes an API list to get 
  #qeuries out of it, and then compares the results returning a list w/ two elements.
  #If returnFrame is a number, it gives a data frame of the top n
  #words in each Frame.
  queries = APIcall(core_search)
  frames = lapply(queries,function(query) {dbGetQuery(conn,query)})
  compared = dun.with.merge(frames[[1]],frames[[2]])
  returnable = list(sort(-compared[compared>=20]),sort(compared[compared<=-20]))
  if (returnFrame) {
    returnable = data.frame(
      group1 = names(returnable[[1]])[1:returnFrame],
      group2 = names(returnable[[2]])[1:returnFrame])
  }
  returnable
  }

dun.with.merge = function(wordsa,wordsb) {
  names(wordsa) = names(wordsb) = c("word","count")
  merged = merge(wordsa,wordsb,all=T,by=c("word"))
  names(merged)[1] = "word"
  merged$word = iconv(merged$word)
  merged = merged[!is.na(merged$word),]
  #merged = merged[merged$word==tolower(merged$word),]
  merged = merged[nchar(merged$word)>1,]
  merged[is.na(merged[,2]),2] = 0.5
  merged[is.na(merged[,3]),3] = 0.5
  p = dunning.log(merged)
}

dunning.log = function(wordlist) {
  #takes a data frame with columns "word," "count.x" and "count.y"
  #Formula (whence variable names) taken from http://wordhoard.northwestern.edu/userman/analysis-comparewords.html
  attach(wordlist)
  wordlist[wordlist==0] = .1
  c = sum(count.x); d = sum(count.y); totalWords = c+d
  wordlist$count.total = count.x+count.y
  wordlist$exp.x = c*(wordlist$count.total)/(totalWords)
  wordlist$exp.y = d*(wordlist$count.total)/(totalWords)
  wordlist$over.x = wordlist$count.x - wordlist$exp.x
  wordlist$over.y = wordlist$count.y - wordlist$exp.y

  wordlist$score = 2*(
    (wordlist$count.x*log(
      wordlist$count.x/wordlist$exp.x)) + 
        wordlist$count.y*log(wordlist$count.y/wordlist$exp.y))
  #This makes it negative if the second score is higher
  wordlist$score = wordlist$score * ((wordlist$over.x > 0)*2-1)
  detach(wordlist)
  dunning = wordlist$score
	names(dunning) = wordlist[,1]
	dunning
}


median_ages <- function (limits) {
  core_search = list(
      method = 'counts_query', 
      counttype = 'Number_of_Books',
      groups=list('author_age','year'),      
      words_collation = 'All_Words_with_Same_Stem',
      tablename='master_bigrams',
      search_limits = 
        list(
          list(
            'alanguage'=list('eng')
            )
      )
    )
  for (limit in names(limits)) {
    core_search[['search_limits']][[1]][[limit]] = limits[[limit]]
  }
  
  local = dbGetQuery(con,APIcall(core_search))
  
  
  local = local[!is.na(local$author_age),]
  good = local[local$year > 1823 & local$year <= 1922,]
  
  years = sort(unique(good$year))
  medians = sapply(years,function(year) {
    myframe = good[good$year==year,]
    median(rep(myframe$author_age,myframe$count))
  })
  broad_search= core_search
  broad_search[['search_limits']][[1]] = core_search[['search_limits']][[1]][grep('word',names(core_search[['search_limits']][[1]]),invert=T)]
  totals = dbGetQuery(con,APIcall(broad_search))
  totals = totals[!is.na(totals$author_age),]
  medianz = sapply(years,function(year) {
    myframe = totals[totals$year==year,]
    median(rep(myframe$author_age,myframe$count))
  })
  diff = medians-medianz
  if (FALSE) {
    levels = 4
    offset = matrix(NA,nrow=nrow(as.matrix(medians)),ncol=ncol(as.matrix(medians)))
    for (n in 1:levels) {
    offset = offset + 
      rbind(rep(NA,nrow(medians)),medians[,1:(ncol(medians)-n)]) + 
      rbind(rep(NA,nrow(medians)),medians[,n:(ncol(medians))])
    }
    medians = medians + offset
  }
  mydata = data.frame(
    year = as.numeric(years),difference_from_median=diff)
  
  if (TRUE) { #Whether to plot or not
  ggplot(mydata,aes(x=year,y=difference_from_median)
         ) + 
           geom_line(color='grey',lwd=.5) + ylab("Deviation from overall median age") + xlab("Publication year")  + opts(title=
           paste(
             "Median age of authors using the phrase '",
                 paste(core_search[['search_limits']][[1]][['word']],collapse = "/"),

                 paste(core_search[['search_limits']][[1]][['word1']],collapse = "/"),
             " ",
                paste(core_search[['search_limits']][[1]][['word2']],collapse="/"),
             "'\ncompared to all authors in that year",sep=""))
  }
}

whereterm = function(terms=list(year = c(1876,1896),word1 = c("home","away"))) {
    paste(
      "(",
      lapply(
        names(terms),
        function(term) {
          seper = ""
          if (is.character(terms[[term]][1])) {seper="'"}
          paste(
            term,
            "=",seper,
            terms[[term]],
            seper,
            collapse = " OR ",
            sep="")
          }
        ),
      collapse = " AND ",")",
      sep="")
  }


compareplot = function(word1,word2,country="USA") {
  genres =genreplot(as.list(word1),
          grouping='country',
          groupings_to_use = 2,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1822,1922),
          smoothing=1,
          comparison_words = as.list(word2),
          words_collation='Case_Sensitive')
  USA = genres$data[genres$data$groupingVariable=='USA',]
  USA$ratio[USA$ratio==0] = min(USA$ratio[USA$ratio!=0)]
  ggplot(USA,aes(x=year,y=ratio)) + 
    opts(
      title=paste(
        "Ratio of books using ",
        paste(word1,collapse="/"),
        " to those using ",
        paste(word2,collapse="/"),
        sep="",collapse="")) + 
    geom_point(aes(fill=ratio),shape=21,color='grey') + 
    geom_smooth(se=F,span=.2,lty=2,size=2) + 
    scale_y_log10() + 
    scale_fill_gradient2(low=muted("blue"),high=muted("red"),trans='log') 
}
