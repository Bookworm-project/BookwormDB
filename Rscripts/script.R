source("Rbindings.R")
source("Dating tools.R")
total = dbGetQuery(con,"SELECT words,year FROM presidio.1grams WHERE word1='the'")

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

pandp = c("http://scriptline.livejournal.com/449.html")

#html = readLines(url("http://www.weeklyscript.com/Duck%20Soup.txt"))
#html = paste(html,collapse = " ")
#html = gsub("  +"," ",html)
#script = html


dcounts = lapply(downton,tokenize)
dcounts = do.call(rbind,dcounts)
  
dcounts = counts(dcounts)
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

loc = change[change$late > 1e-7,]; loc =change
loc[order(loc$change),][1:25,]
change[change$early > 1e-06,]


if (FALSE) {
  wharton = scan("~/wharton.txt",what='raw')
  wharton = paste(script,collapse="\n")
  tok = tokenize(wharton)
  source("Dating tools.R")
  cnts = counts(tok)
  cnts[1:5,]
  scores = apply(cnts,1,modernityCheck,compareYear=1875,baseyear=1921)
  scores = do.call(rbind,scores)
  rownames(scores) = apply(cnts[,1:2],1,paste,collapse=" ")
  scores[,1][scores[,1] < 1e-15] = 1e-15
  change = data.frame(change = scores[,1]/scores[,2],early=scores[,1],late=scores[,2])
  change = change[change$early!=1,]
  change = change[change$late!=1,]
  change$isNew = change$change<1
  change$abslog = abs(log(change$change))
  qplot(change$abslog)
  change$freq = cut(change$early,breaks=quantile(change$early),include.lowest=T)
  ggplot(change[change$change > 0 & cnts[,3] > 1,],aes(x=change)) + 
    geom_histogram(binwidth=.1) + scale_x_continuous(trans='log10',limits = c(.01,100)) +
    facet_wrap(~freq) + scale_y_sqrt()
  ggplot(change[change$abslog<10,],aes(x=abslog,fill=isNew)) + geom_density(alpha=.5)
  f = lm(log(early) ~ log(late),change[change$early > 0 & change$late > 0,])
  sort(f$residuals)[1:55]
  word = "stole secrets";cat(readable[(grep(word,readable)-7):(grep(word,readable)+7)],sep="\n")
}

