source("Rbindings.R")
html = readLines(url("http://scriptline.livejournal.com/45325.html"))
downtons = c("http://scriptline.livejournal.com/41950.html",
             "http://scriptline.livejournal.com/42491.html",
             "http://scriptline.livejournal.com/42876.html",
             "http://scriptline.livejournal.com/43317.html",
             "http://scriptline.livejournal.com/43860.html",
             "http://scriptline.livejournal.com/45325.html",
             "http://scriptline.livejournal.com/45845.html",
             "http://scriptline.livejournal.com/46091.html"
             )
#Don't always load the files
#scripts = lapply(downtons,function(string) {readLines(url(string)})
#save(scripts,file = "~/Downtoneps.R")
load("~/Downtoneps.R")
downton = scripts

downton = lapply(downton,parseScriptline)
names(downton) = c(1:length(downton))
readable = lapply(downton,strsplit,"\n")
readable = unlist(readable)
pp1 = readLines(url("http://scriptline.livejournal.com/449.html"))
#html = readLines(url("http://www.weeklyscript.com/Duck%20Soup.txt"))
#html = paste(html,collapse = " ")
#html = gsub("  +"," ",html)
#script = html
parseScriptline = function(html) {
  script = html[grep('entry-content',html)]
  script = gsub("<[^>]+>","\n",script,perl=T)
  script = gsub("\\[.*\\]"," ",script,perl=T)
  #script = gsub("\\n[A-Z ,]+\\n"," ",script,perl=T)
}

tokenize = function(script,grams=2) {
  script = gsub("\n",' ',script)
  script = gsub("([.,!?\\[])"," \\1",script)
  splitted = strsplit(script," ")
  splitted = unlist(splitted)
  splitted = splitted[grep("^$",splitted,perl=T,invert=T)]
  words = cbind(splitted[-length(splitted)],splitted[-1])
  words = words[grepl("^\\w+$",words[,1],perl=T) & grepl("^\\w+$",words[,2],perl=T),]
  words
}
  
total = dbGetQuery(con,"SELECT words,year FROM presidio.1grams WHERE word1='the'")

dcounts = lapply(downton,tokenize)
dcounts = do.call(rbind,dcounts)

counts = function(dcounts) {
  counts = table(paste(dcounts[,1],dcounts[,2]))
  words = as.data.frame(do.call(rbind,strsplit(names(counts)," ")))
  words$count = counts
  words = words[!grepl("[B-HJ-Z]",apply(words,1,paste,collapse=" "),perl=T),]
}

dcounts = counts(dcounts)

modernityCheck = function(row,compareYear=1921,baseyear=2000) {
  cat(row,"\n")
  word1 = row[1]
  word2 = row[2]
  local = dbGetQuery(con,paste(
    "SELECT words,year FROM ngrams.2grams WHERE word1='",word1,"' AND word2='",word2,"'",sep=""
                       ))
    if(dim(local)[1]) {
    merged = merge(total,local,by='year',all.x=T)
    merged$words.y[is.na(merged$words.y)]=0
    merged$ratio = merged$words.y/merged$words.x
    require(zoo)
    merged$smoothed = rollapply(merged$ratio,14,mean,fill=NA)
    merged = merged[merged$year > 1800,]
    c(merged$smoothed[merged$year==compareYear],merged$smoothed[merged$year==baseyear])
    } else {1}
}

  modernityCheck(c("got","shafted"))
scores = apply(dcounts,1,modernityCheck,compareYear=1918)
scores = do.call(rbind,scores)
rownames(scores) = apply(dcounts,1,paste,collapse=" ")
scores[,1][scores[,1] < 1e-11] = 1e-11

change = data.frame(change = scores[,1]/scores[,2],early=scores[,1],late=scores[,2])
change = change[change$early!=1,]
change$freq = cut(change$early,breaks=quantile(change$early),include.lowest=T)
ggplot(change[change$change > 0,],aes(x=change)) + 
  geom_histogram(binwidth=.1) + scale_x_continuous(trans='log10',limits = c(.001,1000)) +
  facet_wrap(~freq) + scale_y_sqrt()
f = lm(log(early) ~ log(late),change)
sort(f$residuals)[1:55]
word = "stole secrets";cat(readable[(grep(word,readable)-7):(grep(word,readable)+7)],sep="\n")

readable[grep("cow pie",readable)]

 l oc = change[change$late > 1e-7,]; loc =change
loc[order(loc$change),][1:25,]
change[change$early > 1e-06,]
