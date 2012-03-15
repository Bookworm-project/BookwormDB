#Time

flagWordids(as.character(1700:1922))
genreplot()

core_query = list(
      method = 'counts_query',
      groups=list('year','words1.lowercase as textyear'),      
      search_limits = 
        list(
            'word' = as.list(as.character(1700:1922)),
            'year' = as.list(1850:1922),
            'alanguage' = list('eng')
    ))

years = dbGetQuery(con,APIcall(core_query))
head(years)
ggplot(years,aes(x=year,y=as.numeric(textyear),color=count,size=sqrt(count))) + geom_point(position='jitter',alpha=.3)

ddply(years,.(year),function(frame) {
  
})
?quantile

core_query[['search_limits']][['word']] = list()
core_query[['groups']] = list('year')
totals = dbGetQuery(con,APIcall(core_query))
years = merge(years,totals,by='year')
head(years)
years$ratio = years$count.x/years$count.y

ggplot(years[years$year==1866,],
       aes(x=year,fill=as.numeric(textyear))) + 
         geom_bar()



core_query = list(
      method = 'ratio_query',
      groups=list('country','words1.lowercase as w1','words2.lowercase as w2'),      
      search_limits = 
        list(
            'word' = list ("just might","might just"),
            'year' = as.list(1915:1922),
            'alanguage' = list('eng'),
            'country' = list("UK","USA")
    ))
dat = dbGetQuery(con,APIcall(core_query))
dat = dat[dat$word1!=dat$word2,]
core_query = list(
      method = 'ratio_query',
      groups=list('country'),      
      search_limits = 
        list(
            'word' = list ("just might","might just"),
            'year' = as.list(1915:1922),
            'alanguage' = list('eng'),
            'country' = list("UK","USA")
    ))
genreplot(list("woke"),grouping='lc0',groupings_to_use=40)')