#rm(list=ls())
#setwd("/presidio/Rscripts")
#source("Rbindings.R")
  

genreplot = function(word = list('attention')
                     ,
                     years = c(1830,1922)
                     ,
                     grouping = 'lc1'
                     ,
                     counttype = 'Occurrences_per_Million_Words'
                     ,
                     groupings_to_use=15
                     ,
                     ordering=NULL
                     ,
                     smoothing=1
                     ,
                     comparison_words=list()
                     ,
                     words_collation = "Case_Sensitive"
                     ) {  
  #If smoothing is less than 1, it's a loess span; if greater, it's a moving average;
  #If exactly 1, no smoothing
  groupeds = list(paste(grouping,'as groupingVariable'),'year') #,'catalog.bookid as id')
  
  core_search = list(
      method = 'counts_query',
      counttype = counttype,
      words_collation=words_collation,
      groups=groupeds,      
      search_limits = 
        list(
          list(
            'word' = word,
            'year' = as.list(years[1]:years[2]),
            'alanguage' = list('eng'),
            'country' = list('usa')
            )
    )
  )  
  
  new = core_search
  new[['search_limits']][[1]][['word']] = comparison_words
  #Get the totals by deleting the words terms from the search
  allwords = dbGetQuery(con,APIcall(new))
  
  names(allwords)[ncol(allwords)] = 'nwords'
  mainquery =  dbGetQuery(con,APIcall(core_search)) 
  mylist = merge(mainquery,allwords,by=gsub(".* as ","",groupeds),all.y=T)
  
  mylist$count[is.na(mylist$count)]=0
  mylist$ratio = mylist$count/mylist$nwords
  
  totalcounts = xtabs(mylist$nwords ~ mylist$groupingVariable)
  mylist = mylist[mylist$groupingVariable %in% names(totalcounts)[order(totalcounts,decreasing=T)][1:groupings_to_use],]
  
  genretabs = xtabs(count~year+groupingVariable,mylist)/xtabs(nwords~year+groupingVariable,mylist)
  genretabs[genretabs==Inf] = NA
  if (smoothing > 1) {
  require(zoo)
  smoothed = rollapply(genretabs,round(smoothing),mean,fill=NA)
  rownames(smoothed)=rownames(genretabs)
  total = melt(as.matrix(smoothed))
}
if(smoothing < 1) {
  smoothed = apply(genretabs,2,function(col) {
    model = loess(col ~ as.numeric(rownames(genretabs)),span=smoothing)
    predict(model,newdata = as.numeric(rownames(genretabs)))
  })
  rownames(smoothed)=rownames(genretabs)
  total = melt(as.matrix(smoothed))
}
if (smoothing==1) {
  total = melt(genretabs)
  }
  colnames(total) = c("year","groupingVariable","value")
  total = total[total$year >= years[1],]
  
#This sorted variable comes from "pca on one vocab.R"
#  total$groupingVariable = factor(total$groupingVariable, levels=sorted_levels)
  total$groupingVariable = factor(total$groupingVariable)
  total$groupingVariable = factor(total$groupingVariable,levels = rev(levels(total$groupingVariable)))
  if (length(ordering>0)) {
    if (ordering=="frequency") {
      total$groupingVariable = factor(total$groupingVariable,levels=names(sort(apply(genretabs,2,mean,na.rm=T))))
    }
  }
  total =   total[!is.na(total$groupingVariable),]
  total$year = as.numeric(total$year)
  total = merge(total,mylist,by=c('groupingVariable','year'))
  
  ggplot(total, aes(y=groupingVariable,x=year,fill=value*1000000)) + 
  scale_x_continuous(expand=c(0,0)) +
  scale_y_discrete(expand=c(0,0))  +    
    geom_tile() + 
  opts(title = paste(
    "Frequency of '",
    unlist(word),
    "'' across genres\nordered by descending usage\n7-year smoothing window",sep=""),
       panel.background = theme_rect(fill="white"),
       panel.grid.major = theme_blank(),
       panel.grid.major = theme_blank()) + 
           labs(fill="score",x="",y="") +
           scale_fill_gradientn(
             colours = c('ghost white','steelblue',('red'))) #,
             #trans='sqrt',limits = c(0,max(total$value*1000000)))
}