#!/usr/bin/R

setwd("/presidio/Rscripts")
rm(list=ls())
source("Rbindings.R")
#install.packages('gdata')
require(gdata)

panel = read.csv("/home/bschmidt/Downloads/AHD08_numeric_edited_for_occupation.csv",as.is=T)
websurvey = read.csv("/home/bschmidt/Downloads/GSAS_091111.csv",as.is=T)
survey = websurvey
extractVerbData = function(survey=survey,dataStartPoint=25,age = rep(NA,nrow(survey))) {
  survey = survey[,survey[1,] != "Open-Ended Response"]
  verb = as.vector(survey[1,dataStartPoint:ncol(survey)])
  verb = gsub(".*<b>","",verb)
  verb = gsub("</b>.*","",verb)
  verb = gsub(" .*","",verb)
  verb[duplicated(verb)] = paste(verb[duplicated(verb)],'-',sep='')
  
  answers = survey[2:nrow(survey),dataStartPoint:ncol(survey)]
  answers = apply(answers,2,as.numeric)
  colnames(answers) = verb
  
  newpair = grepl("Please.rate",colnames(survey))[dataStartPoint:ncol(survey)]
  #Create categories for each of the different groups
  wordcat = as.factor(sapply(1:length(newpair), function(i) {
    sum(as.numeric(newpair[1:i]))
  }))
  groups=split(verb,wordcat)
  names(groups) = lapply(groups,function(group) {group[length(group)]})
  wordcat
  subsets = lapply(levels(wordcat),function(grouping){
    answers[,which(wordcat==grouping),drop=F]
  })
  names(subsets) = names(groups)
  f = lapply(subsets,function(subseta) {
    group1 = subseta[,1:min(c(ncol(subseta)-1,1)),drop=F]
    group2 = subseta[,ncol(subseta)]
    results = apply(group1,1,max,na.rm=T)-
      group2
    results[abs(results) > 100] = NA
    results
  })
  names(f) = names(groups)
  preference = do.call(cbind,f)
  preference = data.frame(preference)
  preference$age = age
  melted = melt(preference,'age')
  names(melted) = c('age','regform','preference')
  summary(melted)
  melted = melted[!is.na(melted$preference),]
  melted = melted[!is.na(melted$age),]
  list(melted=melted,groups = groups,subsets=subsets)
}

#PANEL RESULTS
results = extractVerbData(survey=panel,dataStartPoint=107,age = 2009- as.numeric(panel$Year.of.Birth[2:nrow(panel)]))
results$groups
#WEBSURVEY RESULTS
age = websurvey$Please.enter.your.year.of.birth..required..[2:nrow(websurvey)]
age = as.numeric(gsub(".*[/ ]","",age))
age[age < 1900] = NA
age[age > 2010] = NA
age = 2010-age
results = extractVerbData(survey=websurvey,dataStartPoint=25,age=age)



plot = ggplot(rbind(results$melted),aes(x=age,y=preference,color=muted('blue'))) + 
  geom_point(alpha=.15,aes(color=muted("red"))) +
  facet_wrap(~regform,ncol=10) +
  geom_smooth(method='lm') + 
  opts(legend.position = "none",title=
  "Strength of preference of internet panel for the listed form\nacross verbs in site, and trend by age") 
plot
groups = results$groups
ngramsusage = sapply(groups,function(verbs) {
  verbs = gsub('-','',verbs)
  irreg = paste(paste('word1="',verbs[1:(length(verbs)-1)],'"',sep=""),collapse = " OR ")
  irreg = dbGetQuery(con,paste(
      "SELECT year,max(books) as irreg FROM 1grams WHERE year < 2008 and ",irreg," GROUP BY year",sep="") )
  
  reg = dbGetQuery(con,paste(
      "SELECT year,books as reg FROM 1grams WHERE year < 2008 and word1='",verbs[length(verbs)],"'",sep="") )
  merged = merge(irreg,reg,by='year',all=T)
  
  merged = merged[merged$year >= 1980,]
  merged = merged[merged$year <= 2005,]
  merged[is.na(merged)] = 0
  start = mean(head(merged[,2],10)/head(merged[,3],10),na.rm=T)
  end = mean(tail(merged[,2],10)/tail(merged[,3],10),na.rm=T)
  end/start
})

ngramsslope= sapply(groups,function(verbs) {
  cat(verbs,"\n")
  verbs = gsub('-','',verbs)
  irreg = paste(paste('word1="',verbs[1:(min(c(length(verbs)-1),1))],'"',sep=""),collapse = " OR ")
  irreg = dbGetQuery(con,paste(
      "SELECT year,max(books) as irreg FROM 1grams WHERE year < 2008 and ",irreg," GROUP BY year",sep="") )
  
  reg = dbGetQuery(con,paste(
      "SELECT year,books as reg FROM 1grams WHERE year < 2008 and word1='",verbs[length(verbs)],"'",sep="") )
  
  merged = merge(irreg,reg,by='year',all=T)
  merged = merged[merged$year >= 1980,]
  merged = merged[merged$year <= 2005,]
  merged[is.na(merged)] = NA
  lm(log(irreg/reg) ~ year,merged)$coefficients[2]
})
verbs = groups[[10]]
verbs
names(ngramsusage) = lapply(groups,function(group) {group[length(group)]})
  
names(plot$data)

models = lapply(levels(results$melted$regform),function(verb) {
  f = lm(preference ~ age,results$melted[results$melted$regform==verb,])
  c(slope = f$coefficients[2],p = summary(f)$coefficients[2,4])
})
names(models) = names(ngramsusage)
slope = sapply(models,'[',1)

newframe = data.frame(ngramchange = log(ngramsusage),ngramsslope = ngramsslope,modelchange = slope,word = names(ngramsusage))
newframe = newframe[!is.infinite(newframe[,1]),]
newframe = newframe[newframe$word != 'forbidded',]
ggplot(newframe,aes(x=-ngramsslope,y=-modelchange,label=word)) + 
  geom_text() + 
   ylab("Slope of fitted model to age data") +
   xlab("slope of fitted model to ngrams set") + 
   opts(title=
   "The age predictions from the internet usage panel correlate
(R=.61) with the direction of ngrams change\n(positive is regularizing, negative irregularizing)")

cor(newframe[,2],newframe[,3])

length(models)
length(ngramsusage)
f = ngramsusage[[1]]
sapply(ngramsusage,function(f) {
  log(sum(head(f))/sum(tail(f)))
})
f = models[[1]]

f$age
names()
summary(f)$coefficients


answers$age = age
answers = answers[!is.na(answers$age),]

ggplot(answers,aes(x=age,fill=sneaked)) + geom_density(beside=T)



?substr
subsr(f,)