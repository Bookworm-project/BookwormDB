#rm(list=ls())
#setwd("/presidio/Rscripts")
#source("Rbindings.R")


ageplot = function(
  word
  ,
  permitted_values= list("author_age" = 25:80,"year" = 1830:1922)
  ,
  loess.span=.05
  ,
  words_collation = "Case_Sensitive"
  ,  
  loess=T)
{
  groupeds = list('author_age','year') #,'catalog.bookid as id')
#      counttype="Percentage_of_Books",
  core_search = list(
      method = 'counts_query',
      words_collation = words_collation,
      groups=groupeds,      
      search_limits = 
        list(
          list(
            'word' = word,
            'year' = as.list(permitted_values[['year']][1]:max(permitted_values[['year']])),
            'alanguage' = list('eng'),
            'country'  = list("USA")
            )
    )
  )  
   
  new = core_search
  new[['search_limits']][[1]][['word']] = list()
  allwords = dbGetQuery(con,APIcall(new))
  names(allwords)[ncol(allwords)] = 'nwords'
  mainquery =  dbGetQuery(con,APIcall(core_search))
  
  mylist = merge(mainquery,allwords,by=gsub(".* as ","",groupeds),all.y=T)
  mylist[is.na(mylist)] = 0
  mylist$ratio = 1000000*mylist$count/mylist$nwords


  model = loess(ratio ~ author_age+year,mylist,weights = nwords,span=loess.span)
  linear = lm(ratio ~ author_age+year,mylist,weights = nwords)

  mylist = mylist[mylist$author_age %in% permitted_values[['author_age']],]
  mylist = mylist[mylist$year %in% permitted_values[['year']],]
  size = c(200,200)
  
  author_age = seq(from=min(permitted_values[['author_age']]),to=max(permitted_values[['author_age']]),length.out=size[1])
  year = seq(from=min(permitted_values[['year']]),to=max(permitted_values[['year']]),length.out=size[2])
  predictions = merge(author_age,year,all=T)
  names(predictions) = c("author_age","year")
  predictions$ratio = predict(model,newdata = predictions)
  predictions$ratio[predictions$ratio<0] = 0
  summary(predictions)

if (loess) {
plotting = predictions
}
if (!loess) {
plotting = mylist
}
  
ggplot(plotting, aes(x=year,y=author_age,fill=ratio)) + 
  scale_x_continuous(expand=c(0,0)) +
  scale_y_continuous(expand=c(0,0))  +    
  geom_tile(linetype=3) + 
  opts(title = paste(
    "Frequency of '",
    unlist(word),
    "' by age of author",sep=""),
       panel.background = theme_blank(),
       panel.grid.major = theme_blank(),
       panel.grid.minor = theme_blank()) + 
           labs(fill="score",x="",y="") +
           scale_fill_gradientn("Occurrences\nper Million",min=0,limits = c(0,max(plotting$ratio)),
                                #trans='sqrt',
             colour = c("black","darkblue", "blue", "lightblue", "lightgreen","green", "yellow", "orange", "darkorange", "red","pink")) +
      geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'grey',lty=3)

  }
               #c('light blue','light green','purple','yellow','red','black','white')) 