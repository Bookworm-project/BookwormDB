rm(list=ls())
require(RCurl)
setwd("/presidio/Rscripts")
source("Rbindings.R")
myCsv <- getURL("https://docs.google.com/spreadsheet/pub?hl=en_US&hl=en_US&key=0AjMccO2n_mi6dDlPVm16U2tBM2kydFlQQ2JyemkwOVE&single=true&gid=0&output=csv")
verbs = read.csv(textConnection(myCsv))
verbs = verbs
verbs = verbs[verbs$Include,]
summary(verbs)

if (FALSE) {
  #Here's some background info on where the author data comes from
  a = dbGetQuery(con,"SELECT author_age,year,count(*) as books FROM catalog WHERE aLanguage='eng' AND year > 1800 AND year < 1922 AND author_age > 0 AND author_age < 100 GROUP BY author_age,year")
  ggplot(a,aes(x=year,y=author_age,fill=books)) + 
    geom_tile() + 
    scale_fill_gradientn(colours=c('white','red'),trans='sqrt') + 
    opts(title="Books published, by year and author age, in Open Library dataset")
  }

#Just some parsing of the list of verbs
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
  
#Build up a search to use with the Bookworm API:
  core_search = list(
      method = 'ratio_query',
      counttype = "Occurrences_per_Million_Words",
      words_collation="Case_Sensitive",
      groups=list('year','words1.lowercase as verb','country'),      
      search_limits = 
          list(
            'word' = list('placeholder'),
            'year' = as.list(1830:1922),
            'alanguage' = list('eng'),
            'country' = list('USA','UK')
            )
  )  

  verbz = as.list(as.vector(unlist(verblist)))
  groups = split(verbz,nchar(verbz))
  tmp = lapply(groups, function(group) {
    core_search[['search_limits']][['word']] = as.list(unlist(group))
      verbs = dbGetQuery(con,APIcall(core_search))
  })

verbarray = do.call(rbind,tmp)

countVerbs = function(verblist) {
  IrregOverReg = lapply(verblist, function(verb){
    sapply(c("USA","UK"), function(country) {
      reg = verbarray$value[verbarray$country==country & verbarray$verb %in% tolower(unlist(verb[[1]]))]
      irreg = verbarray$value[verbarray$country==country & verbarray$verb %in% tolower(unlist(verb[[2]]))]
      sum(irreg)/sum(reg)
    })
  })
}
IrregOverReg = countVerbs(verblist)
names(IrregOverReg) = verbs$Verb

vectored = do.call(rbind,IrregOverReg)
vectored = as.data.frame(vectored)
smallest_proportion = apply(vectored,1,function(pair) {
  min(abs(log10(pair)))
})
sort(smallest_proportion)
qplot(smallest_proportion)
good = smallest_proportion < 1.5

changers = verblist[good]
names(changers) = verbs$Verb[good]
#Put one pair in that _doesn't_ have an age effect.
changers[['Pittsburgh']] = list(list("Pittsburgh"),list("Pittsburg"))
source("Word Spread.R")

chunk(changers[[6]])



modelStrength = function(genres) {
  test = genres$data
  test$birth = test$timeVariable-test$groupingVariable
  #f$data$groupingVariable = as.numeric(f$data$groupingVariable)
  test$ratio[test$ratio==0] = min(test$ratio[test$ratio!=0])
  size = xtabs(nwords ~ groupingVariable+timeVariable,test)
  ratio = xtabs(ratio ~ groupingVariable+timeVariable,test)
  #what's the square difference 
  strength = mean((ratio[-1,]-ratio[-(nrow(ratio)),])^2)/
    mean((ratio[-(nrow(ratio)),-(ncol(ratio))]-ratio[-1,-1])^2)  
  model = lm(log(ratio) ~ timeVariable + birth,test,weights=nwords)
  scorez=summary(model)$coefficients[2:3,3]
  returnt = c(scorez,strength)
  names(returnt)[3] = "relativeBirth"
  returnt
}

smoothed = lapply(changers,function(wordz) {
  genres =try(genreplot(
    word = wordz[[2]],
    grouping=list('author_age'),
    groupings_to_use = 63,
    counttype = 'Percentage_of_Books',
    ordering=NULL,
    years=c(1830,1922),
    smoothing=8,
    comparison_words = wordz[[1]],
    words_collation='Case_Insensitive',
    chunkSmoothing=1,
    country=list('USA')))
    try(genres  + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub))
})

chunk = function(wordz) {
    genres =genreplot(
    word = wordz[[2]],
    grouping=list('author_age'),
    groupings_to_use = 7,
    counttype = 'Percentage_of_Books',
    ordering=NULL,
    years=c(1830,1922),
    smoothing=1,
    comparison_words = wordz[[1]],
    words_collation='Case_Insensitive',
    chunkSmoothing=10,
    country=list('USA'),
    lc0=list("D","E","F")
    )
    genres  + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub)
}
chunked = lapply(changers,chunk)

compareplot("burned","burnt")+scale_y_log10()
names(chunked)
scores = t(sapply(chunked[sapply(chunked,length) > 1],modelStrength))
strengthScores = as.data.frame(scores)
strengthScores$word = rownames(strengthScores)
strengthScores$relative = abs(strengthScores$birth) - abs(strengthScores$timeVariable)
smoothed[['Pittsburgh']]
ggplot(strengthScores,aes(x=abs(timeVariable),y=abs(birth),label=word)) + 
  geom_text() + geom_abline() + ylim(0,10) + xlim(0,10)
chunked[['Burn']]

chunked[['Spell']]
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
  genres$options$labels$x = ""
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

  genres =genreplot(list('Christ'),
            grouping=list('author_age'),
            groupings_to_use = 63,
            counttype = 'Percentage_of_Books',
            ordering=NULL,
            years=c(1830,1922),
            smoothing=7,
            words_collation='All_Words_with_Same_Stem',
                    comparison_words = list("Jesus"))
genres + geom_abline(data = data.frame(ints = seq(-1700,-2000,by=-10),slp=rep(1,31)),aes(intercept=ints,slope=slp),color = 'black',lty=3) + opts(sub) + geom_contour(aes(z=value))
genres$data$birth = genres$data$year-genres$data$groupingVariable
summary(lm(ratio ~ year + birth,genres$data,weights=nwords))

require(gridExtra)
grid.arrange(unsmoothed[[1]],smoothed[[1]])


