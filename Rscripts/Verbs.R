rm(list=ls())
require(RCurl)
setwd("/presidio/Rscripts")
source("Rbindings.R")
myCsv <- getURL("https://docs.google.com/spreadsheet/pub?hl=en_US&hl=en_US&key=0AjMccO2n_mi6dDlPVm16U2tBM2kydFlQQ2JyemkwOVE&single=true&gid=0&output=csv")
verbs = read.csv(textConnection(myCsv))
verbs = verbs
verbs = verbs[verbs$Include,]
summary(verbs)

a = dbGetQuery(con,"SELECT author_age,year,count(*) as books FROM catalog WHERE aLanguage='eng' AND year > 1800 AND year < 1922 AND author_age > 0 AND author_age < 100 GROUP BY author_age,year")
ggplot(a,aes(x=year,y=author_age,fill=books)) + 
  geom_tile() + 
  scale_fill_gradientn(colours=c('white','red'),trans='sqrt') + 
  opts(title="Books published, by year and author age, in Open Library dataset")

verblist = apply(verbs,1,function(row) {
  irregular = as.list(unique(unlist(strsplit(
    gsub(" ","",c(
      tolower(as.character(row[names(verbs)=='IrrPreterit'])),
      tolower(as.character(row[names(verbs)=='IrrPart']))
      )),","))))
  regular = as.list(unique(unlist(strsplit(
    gsub(" ","",c(
      tolower(as.character(row[names(verbs)=='RegPreterit']))
      )),","))))
  list(irregular,regular)
})
  
#Build up a search

  core_search = list(
      method = 'ratio_query',
      counttype = "Occurrences_per_Million_Words",
      words_collation="Case_Insensitive",
      groups=list('year'),      
      search_limits = 
        list(
          list(
            'word' = list(),
            'year' = as.list(1830:1922),
            'alanguage' = list('eng')
            )
    )
  )  


countVerbs = function(verblist) {
  IrregOverReg = lapply(verblist, function(verb){
    
    core_search[['search_limits']][[1]][['word']] = verb[[1]]
    irreg = dbGetQuery(con,APIcall(core_search))
    core_search[['search_limits']][[1]][['word']] = verb[[2]]
    reg = dbGetQuery(con,APIcall(core_search))
    sum(irreg[,2])/sum(reg[,2])
  })
}

IrregOverReg = countVerbs(verblist)

names(IrregOverReg) = verbs$Verb

vectored = unlist(IrregOverReg)

good = vectored < 4 & vectored > 1/4

changers = verblist[good]
source('Word Spread.R')

unsmoothed = lapply(1:length(changers),function(n) {
word = changers[[n]]
  genres =genreplot(word[[2]],
            grouping=list('author_age'),
            groupings_to_use = 63,
            counttype = 'Occurrences_per_Million_Words',
            ordering=NULL,
            years=c(1830,1922),
            smoothing=1,
            comparison_words = word[[1]],
            words_collation='Case_Insensitive')
  genres})

smoothed = lapply(1:length(changers),function(n) {
  word = changers[[n]]
  genres =genreplot(word[[2]],
            grouping=list('author_age'),
            groupings_to_use = 63,
            counttype = 'Percentage_of_Books',
            ordering=NULL,
            years=c(1830,1922),
            smoothing=8,
            comparison_words = word[[1]],
            words_collation='Case_Insensitive')
  genres  + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub)
})

source('Word Spread.R')
countries = lapply(1:length(changers),function(n) {
  word = changers[[n]]
  results = lapply(c("UK","USA"),function(mycountry) {
    genres =genreplot(word[[2]],
            grouping=list('author_age'),
            groupings_to_use = 63,
            counttype = 'Percentage_of_Books',
            ordering=NULL,
            years=c(1830,1922),
            smoothing=8,
            comparison_words = word[[1]],
            words_collation='Case_Insensitive',
                    country=list(mycountry)
                      )
  genres$options$title = paste(word[[2]],mycountry,sep=" ")
  p[[1]]$options$labels$x = ""
  genres  + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub)
  })
  names(results) = c("UK","USA")
  results
  })


p = unlist(countries,recursive=F)
p[['ncol']] = 2
do.call(grid.arrange,p)
?grid.arrange

do.call(grid.arrange,args = list(countries[[4]],ncol=2))
?grid.arrange
?do.call

Though that
gsave(smoothed,paste(names(IrregOverReg[good]),"smoothed.png"))
?ggsave
?geom_abline
source('Word Spread.R')

  genres =genreplot(list('awesome'),
            grouping=list('author_age'),
            groupings_to_use = 63,
            counttype = 'Percentage_of_Books',
            ordering=NULL,
            years=c(1830,1922),
            smoothing=7,
            words_collation='All_Words_with_Same_Stem')
genres + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub)

require(gridExtra)
grid.arrange(unsmoothed[[1]],smoothed[[1]])
