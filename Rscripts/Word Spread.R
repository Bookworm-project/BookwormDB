#rm(list=ls())
#setwd("/presidio/Rscripts")
#source("Rbindings.R")
  

genreplot = function(word = list('call attention')
                     ,
                     years = c(1830:1922)
                     ,
                     grouping = 'author_age'
                     ,
                     counttype = 'Occurrences_per_Million_Words'
                     ,
                     groupings_to_use=65
                     ,
                     ordering=NULL
                     ,
                     smoothing=1
                     ,
                     comparison_words=list()
                     ,
                     words_collation = "Case_Sensitive"
                     ,
                     chunkSmoothing=1
                     ,
                     x.value = 'year'
                     ,
                     conn=con
                     ,
                     database="presidio"
                     ,
                     ...
                     #ChunkOffset can be false, in which the smoothed data is presented as is;
                     #or it can be numeric, in which case if span is 15, for example, only years with 
                     #15 %/% chunkOffset==15/chunkOffset will be included
                     ) {  
  #If smoothing is less than 1, it's a loess span; if greater, it's a moving average;
  #If exactly 1, no smoothing
  #Moving average not currently implemented for double-numeric plots
  dbGetQuery(conn,paste("USE",database))
  catalog = dbGetQuery(conn,"EXPLAIN catalog")
  numeric.y=FALSE
  #Find out if the grouping is numeric; this affects smoothing and some other things.
  if (length(catalog$Field[catalog$Field==grouping])>0) {
    numeric.y = as.logical(!length(grep('char',catalog$Type[catalog$Field==grouping])))
  }
  cat("numeric.y is ",as.character(numeric.y))
  
  groupeds = list(paste(grouping,'as groupingVariable'),
                  paste('ROUND(',x.value,'/',chunkSmoothing,')*',chunkSmoothing,' as timeVariable',sep=""))
  
  if(numeric.y) {
    groupeds[[1]] = paste('ROUND(',grouping,'/',chunkSmoothing,')*',chunkSmoothing,' as groupingVariable',sep="")

  }
  
  core_search = list(
      method = 'counts_query',
      counttype = counttype,
      words_collation=words_collation,
      groups=groupeds,
      database=database,
      search_limits = 
        list(
            'word' = word
        )
  )
  core_search[['search_limits']][[x.value]] = as.list(years)
  for (element in names(list(...))) {
    cat(element,"\n")
    core_search[['search_limits']][[element]] = list(...)[[element]]
  }
  #return(APIcall(core_search))

  mainquery =    try(dbGetQuery(conn,APIcall(core_search)))
  
  if(class(mainquery) == "try-error") {
    source("Rbindings.R")
    mainquery =    try(dbGetQuery(conn,APIcall(core_search)))
  } 

  #Get the totals by deleting the words terms from the search
  new = core_search
  new[['search_limits']][['word']] = comparison_words
  allwords = dbGetQuery(conn,APIcall(new))
  names(allwords)[ncol(allwords)] = 'nwords'
  #merge them together
  mylist = merge(mainquery,allwords,by=gsub(".* as ","",groupeds),all=T)
  
  mylist$count[is.na(mylist$count)]=0
  mylist$ratio = mylist$count/mylist$nwords

  #Limit the number of columns by frequency (could also be by something else, or passed in to start with,
  #but nothing else is implemented here.)
  totalcounts = xtabs(mylist$nwords ~ mylist$groupingVariable)
  
  if (!numeric.y | chunkSmoothing != 1) {
    mylist = mylist[mylist$groupingVariable %in% names(totalcounts)[order(totalcounts,decreasing=T)][1:groupings_to_use],]
  }
  if (numeric.y & chunkSmoothing==1) {
    numbers_to_use = sort(as.numeric(names(totalcounts)[order(totalcounts,decreasing=T)][1:groupings_to_use]))  
    numbers_to_use = 
      (numbers_to_use[floor(length(numbers_to_use)/2)]-floor(length(numbers_to_use)/2)):
      (numbers_to_use[floor(length(numbers_to_use)/2)]+floor(length(numbers_to_use)/2))
    mylist = mylist[mylist$groupingVariable %in% numbers_to_use,] 
  }
  mylist$count[is.na(mylist$count)] = 0
  mylist$nwords[is.na(mylist$nwords)] = 0
  genretabs = xtabs(count~timeVariable+groupingVariable,mylist)/xtabs(nwords~timeVariable+groupingVariable,mylist)
  genretabs[genretabs==Inf] = max(genretabs)
  if (smoothing > 1) {
    totalwords = xtabs(nwords~timeVariable+groupingVariable,mylist) + xtabs(count~timeVariable+groupingVariable,mylist)
    smoothname = paste("\nMoving average with span",smoothing)
    if (!numeric.y) {
      smoothed = sapply(
        1:nrow(genretabs),function(row) {
          rows = (row-floor(smoothing/2)):(row+floor(smoothing/2))
          rows = rows[rows>0]
          rows = rows[rows<=nrow(genretabs)]
          sapply(1:ncol(genretabs),function(col) {
            columns = col
            columns = columns[columns>0]
            columns = columns[columns<=ncol(genretabs)]
            weighted.mean(
              x=genretabs[rows,columns],
              w=totalwords[rows,columns],
              na.rm=T)
        })
      })
      smoothed = t(smoothed)
      rownames(smoothed)=rownames(genretabs)
      colnames(smoothed) = colnames(genretabs)
    }
    if (numeric.y) {
      smoothed = sapply(1:nrow(genretabs),function(row) {
          rows = (row-floor(smoothing/2)):(row+floor(smoothing/2))
          rows = rows[rows>0]
          rows = rows[rows<=nrow(genretabs)]
        sapply(1:ncol(genretabs),function(col) {
          columns = (col-floor(smoothing/2)):(col+floor(smoothing/2))
          columns = columns[columns>0]
          columns = columns[columns<=ncol(genretabs)]
            weighted.mean(x=genretabs[rows,columns],
                          w=totalwords[rows,columns],
                          na.rm=T)
        })
      })
      smoothed = t(smoothed)
      rownames(smoothed)=rownames(genretabs)
      colnames(smoothed) = colnames(genretabs)
    }
    if (FALSE) { #chunkOffset=="This isn't needed no more") {
        range = floor(smoothing/2)*2 + 1
        effectiveYear = as.numeric(rownames(smoothed)) + chunkOffset
        smoothed = smoothed[effectiveYear %/% range  == effectiveYear / range,]
        if (numeric.y) {
          effectiveY = as.numeric(colnames(smoothed)) + chunkOffset
          smoothed = smoothed[,effectiveY %/% range  == effectiveY / range]
        }
    }
    total = melt(as.matrix(smoothed))

  }
  if(smoothing < 1) {
    smoothname = paste("\nLoess smoothing with span=",smoothing)
    if (!numeric.y) {
      smoothed = apply(genretabs,2,function(col) {
        model = loess(col ~ as.numeric(rownames(genretabs)),span=smoothing)
        predict(model,newdata = as.numeric(rownames(genretabs)))
      })
      rownames(smoothed)=rownames(genretabs)
      total = melt(as.matrix(smoothed))
    }
    if (numeric.y) {
      model = loess(ratio ~ timeVariable+groupingVariable,mylist,weights = nwords,span=smoothing)
      groupingVariable = seq(from=min(mylist$groupingVariable),to = max(mylist$groupingVariable),length.out=length(unique(mylist$groupingVariable)))
      year = seq(from=years[1],to=years[length(years)],length.out=length(years[1]:years[length(years)]))
      predictions = merge(year,groupingVariable,all=T)
      names(predictions) = c("timeVariable","groupingVariable")      
      predictions$ratio = predict(model,newdata = predictions)
      predictions$ratio[predictions$ratio<0] = 0
      total=predictions
    }
  }
  
  if (smoothing==1) {
    smoothname = ''
    total = melt(genretabs)
  }
  
  comparegroup = "Per Million Words"
  if (length(comparison_words) > 0) {
    comparegroup = paste(
      "Per Usage of '",
      paste(
        comparison_words,
        collapse="' or '"),
      "'",sep="")
  }
  title = paste(
    "Frequency of '",
    paste(word,collapse="' or '"),
    "' \n ",comparegroup,smoothname,sep="")
  colnames(total) = c("timeVariable","groupingVariable","value")
  #XXXNot sure whether I still need this line.
  total = total[total$timeVariable >= years[1],]
  
  #Some weird behavior to get the levels to display nicely.
  total$groupingVariable = factor(total$groupingVariable)
  total$groupingVariable = factor(total$groupingVariable,levels = rev(levels(total$groupingVariable)))
  if (length(ordering>0)) {
    if (ordering=="frequency") {
      total$groupingVariable = factor(total$groupingVariable,levels=names(sort(apply(genretabs,2,mean,na.rm=T))))
    }
  }
  total =   total[!is.na(total$groupingVariable),]
  total$timeVariable = as.numeric(total$timeVariable)
  total = merge(total,mylist,by=c('groupingVariable','timeVariable'))
  if (numeric.y) {
    total$groupingVariable=as.numeric(as.character(total$groupingVariable))
  }
  mytrans='log10'
  color_scale = scale_fill_gradient2(paste(gsub("_","\n",counttype)),trans = 'log')
  
  if (length(comparison_words)==0) {
    if (counttype == 'Occurrences_per_Million_Words') {
      total$value = total$value *1000000
    }
    if (counttype == 'Percentage_of_Books') {
      total$value = total$value *100
    }
    color_scale = scale_fill_gradientn(paste(gsub("_","\n",counttype)),
      colours = c('white','steelblue','red'))
  }
  yscale = scale_y_discrete(expand=c(0,0))
  if (numeric.y){
    yscale = scale_y_continuous(expand=c(0,0))
      #geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'grey',lty=3)
  }
  #total$value[total$value>max(total$value)/5] = max(total$value)/5
  genres <- ggplot(total, aes(y=groupingVariable,x=timeVariable,fill=value)) + 
    scale_x_continuous(expand=c(0,0)) +
    yscale  +    
    geom_tile() + 
    opts(title = title,
         panel.background = theme_rect(fill="grey"),
         panel.grid.major = theme_blank(),
         panel.grid.major = theme_blank()) + 
    labs(fill="score",x="",y="") + 
    color_scale
  genres$data$year = genres$data$timeVariable
  genres
  }
