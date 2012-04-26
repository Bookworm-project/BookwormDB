setwd("/presidio/Rscripts")
source("Rbindings.R")
source("Word Spread.R")
require(reshape)
require(ggplot2)
genres =genreplot(
      word = list("concentrate attention"),
      grouping='lc1',
      groupings_to_use = 35,
      counttype = 'Occurrences_per_Million_Words',
      ordering=NULL,
      years=c(1840:1922),
      smoothing=10,
      comparison_words = list(),
      words_collation='Case_Insensitive',
      chunkSmoothing=1,
      country=list(),
      aLanguage=list('eng'))

genres

source("ngrams wordgrid.R")
  
  mylist = wordgrid(list("research"),
      returnData=F,
      wordfield='stem',
      field='w1.casesens',
      freqClasses=4,n=50,
      yearlim=c(1880,2008),
      mydb=con,
      excludeList=c("man","men"),
      samplingSpan=4
    )
  mylist
