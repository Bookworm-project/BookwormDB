#Dating tools

parseScriptline = function(html) {
  script = html[grep('entry-content',html)]
  script = gsub("<[^>]+>","\n",script,perl=T)
  script = gsub("\\[.*\\]"," ",script,perl=T)
  #script = gsub("\\n[A-Z ,]+\\n"," ",script,perl=T)
}

weeklyscriptParse = function(myurl,...) {
  DuckSoup = scan(url(myurl),what="raw",sep="\n")
  lengths = sapply(DuckSoup,function(line) {try(nchar(line))})
  DuckSoup = DuckSoup[!is.na(as.numeric(lengths))]
  Marx = paste(as.character(DuckSoup),collapse = " ")
  f = as.character(DuckSoup)
  DuckSoup = gsub("  +"," ",DuckSoup)
  lapply(list(tokenize(Marx)),fullGrid,...)
  lapply(lapply(list(Marx),tokenize),fullGrid,...)
}

subtitlrScore = function(episode,...) {
  men = scan(url(episode),what='raw',sep="\n")
  men = men[grep('<div class="transcript">',men)[1]:length(men)]
  men = men[1:grep('</div>',men)[1]]
  men = men[!grepl('>',men)] 
  p = fullGrid(MakeNgramCounts(tokenize(men)),...)
 }


tokenize = function(script,grams=2) {
  script = gsub("\n"," ",script)
  script = gsub("([\\.,!\\?\\[\\]])"," \\1",script)
  splitted = strsplit(script," ")
  splitted = unlist(splitted)
  splitted = splitted[grep("^$",splitted,invert=T)]
  words = cbind(splitted[-length(splitted)],splitted[-1])
  words = words[grepl("^[A-Za-z]+$",words[,1]) & grepl("^[A-Za-z]+$",words[,2]),]
  words
}

MakeNgramCounts = function(dcounts) {
  #This is separate so we can paste together some serialized works.
  counts = table(paste(dcounts[,1],dcounts[,2]))
  words = as.data.frame(do.call(rbind,strsplit(names(counts)," ")))
  words$count = counts
  words = words[!grepl("[B-HJ-Z]",apply(words,1,paste,collapse=" ")),]
}

modernityCheck = function(row,
                          compareYear=1921,baseyear=2000,
                          yearlim=c(1789,2008),returnAll = F,k=15,weighted = F) {
  cat(row,"\n")
  word1 = row[1]
  word2 = row[2]
  local = dbGetQuery(con,paste(
    "SELECT words,year FROM ngrams.2grams WHERE word1='",word1,"' AND word2='",word2,"'",sep=""
                       ))
    if(dim(local)[1]) {
      merged = merge(total,local,by='year',all.x=T)
      merged = merged[merged$year >= yearlim[1] & merged$year <= yearlim[2],]
      merged$words.y[is.na(merged$words.y)]=0
      merged$ratio = merged$words.y/merged$words.x
      require(zoo)
      k = k%/%2*2+1
      if (weighted) {
        merged$smoothed = rollapply(merged$ratio,width=k,FUN=weighted.mean,w = sqrt(c(1:(k%/%2),k%/%2+1,(k%/%2):1)),fill=NA)
      } else {
         merged$smoothed = rollapply(merged$ratio,15,mean,fill=NA)       
      }
      if(returnAll) {merged$smoothed} else {
      c(
        merged$smoothed[merged$year==compareYear],
        merged$smoothed[merged$year==baseyear])
      }
    } 
  else {
    if (returnAll) {
      rep(NA,length(yearlim[1]:yearlim[2]))
      } else {c(NA,NA)}}
}

fullGrid = function(cnts,yearlim=c(1789,2008),sampling = nrow(cnts),comps=c(1921,2000),
                    smoothing = 9,weighted=F,compareword = 'you') {
  tmp = return_matrix(grams=2,wordInput=cnts[sample(1:nrow(cnts),sampling),])
  tmp = tmp/1000000
  the = dbGetQuery(con,"SELECT words,year FROM presidio.1grams WHERE word1='the'")
  you = dbGetQuery(con,paste("SELECT words,year FROM presidio.1grams WHERE word1='",compareword,"'",sep=""))
  totals = merge(the,you,by='year')
  attach(totals)
  totals$ratio = (words.x/(words.y))
  totals$ratio = totals$ratio/median(totals$ratio)
  detach(totals)
  #Using "you" as a proxy for the total words of dialogue--slightly tricky, but workable?
  tmp = tmp*totals$ratio[match(rownames(tmp),totals$year)]
  #qplot(as.numeric(rownames(tmp)),tmp[,colnames(tmp)=="of the"],xlim=c(1800,2000),geom='line',ylim=c(0,5))
  
  factor = totals$ratio               
  k = smoothing%/%2*2+1
  cat("\nSmoothing matrix\n")
  require(zoo)
  smoothed = apply(tmp,2,function(col) {
      if (weighted) {
        col = rollapply(col,width=k,FUN=weighted.mean,w = sqrt(c(1:(k%/%2),k%/%2+1,(k%/%2):1)),fill=NA)
      } else {
         col = rollapply(col,k,mean,fill=NA)       
      }
      col
  })
  dim(smoothed)
  dim(tmp)  
  dimnames(smoothed) = dimnames(tmp)
  smoothed = smoothed[rownames(smoothed) %in% yearlim[1]:yearlim[2],]
  
  dataf = melt(smoothed)
  cat("Getting word summaries\n")
  word_data = ddply(dataf,.(word1),function(dat) {
    data.frame(
      peak_year = dat$year[which(dat$value==max(dat$value,na.rm=T))],
      y1 = dat$value[dat$year==comps[1]],
      y2 = dat$value[dat$year==comps[2]]
     )
  })
  hist(log10(word_data$y2))
  word_data$y1[word_data$y1<=1e-9] = 1e-9
  word_data$y2[word_data$y2<=1e-9] = 1e-9

  change_from_2001 = ddply(dataf,.(year),function(dat) {
      data.frame(
        percentage_new = sum(dat$value>dataf$value[dataf$year==comps[[2]]])/sum(!is.na(dat$value))
        )})

  mylist = list(year_guesses = ggplot(dataf,aes(x=year))+
    geom_line(data=change_from_2001,aes(y=percentage_new)) + 
    geom_smooth(data=change_from_2001,aes(y=percentage_new)),
  
    wordplot = ggplot(word_data,aes(y=log10(y2)-log10(y1),x=(y1+y2)/2
          )) + 
        geom_text(aes(label=word1),size=3,alpha=.6) + 
        scale_y_continuous("over-representation",trans='') + 
        scale_x_continuous("Overall Frequency",trans='log10'))
}

smoothedCounts = 
  function(cnts,smoothing = 9,weighted=F,compareword = 'the',sampling=nrow(cnts),yearlim = c(1900,2010)
           ) {
  tmp = return_matrix(grams=2,wordInput=cnts[sample(1:nrow(cnts),sampling),],yearlim=yearlim)
  tmp = tmp/1000000
  the = dbGetQuery(con,"SELECT words,year FROM presidio.1grams WHERE word1='the'")
  you = dbGetQuery(con,paste("SELECT words,year FROM presidio.1grams WHERE word1='",compareword,"'",sep=""))
  totals = merge(the,you,by='year')
  attach(totals)
  totals$ratio = (words.x/(words.y))
  totals$ratio = totals$ratio/median(totals$ratio)
  detach(totals)
  #Using "you" as a proxy for the total words of dialogue--slightly tricky, but workable?
  tmp = tmp*totals$ratio[match(rownames(tmp),totals$year)]

  factor = totals$ratio               
  k = smoothing%/%2*2+1
  cat("\nSmoothing matrix\n")
  require(zoo)
  
  tmp = tmp[rownames(tmp) %in% (yearlim[1]-k):(yearlim[2]+k),]
  smoothed = apply(tmp,2,function(col) {
      if (weighted) {
        col = rollapply(col,width=k,FUN=weighted.mean,w = sqrt(c(1:(k%/%2),k%/%2+1,(k%/%2):1)),fill=NA)
      } else {
         col = rollapply(col,k,mean,fill=NA)       
      }
      col
  })
  dimnames(smoothed) = dimnames(tmp)
  smoothed = smoothed[rownames(smoothed) %in% yearlim[1]:yearlim[2],]
  dataf = melt(smoothed)
  dataf
}

example = function(downtons,word,k=3) {
  readable = unlist(lapply(downtons,strsplit,"\n"))
  readable = readable[readable!=""]
  lapply(grep(word,readable),function(n) {
    readable[(n-k):(n+k)]})
}


#Scriptline files have their own parsing rule.s
downtons = c("http://scriptline.livejournal.com/41950.html",
             "http://scriptline.livejournal.com/42491.html",
             "http://scriptline.livejournal.com/42876.html",
             "http://scriptline.livejournal.com/43317.html",
             "http://scriptline.livejournal.com/43860.html",
             "http://scriptline.livejournal.com/45325.html",
             "http://scriptline.livejournal.com/45845.html",
             "http://scriptline.livejournal.com/46091.html"
             )

pandp = c("http://scriptline.livejournal.com/449.html",
          "http://scriptline.livejournal.com/1095.html",
          "http://scriptline.livejournal.com/1349.html",
          "http://scriptline.livejournal.com/1691.html",
          "http://scriptline.livejournal.com/1962.html",
          "http://scriptline.livejournal.com/2181.html")