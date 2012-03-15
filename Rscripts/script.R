setwd("/presidio/Rscripts")
source("Rbindings.R")
source("Rbindings.R")
source("Dating tools.R")
source("Trendspotting.R")


#Don't always load the files, so commented out
#bleh = lapply(downtons,function(string) {readLines(url(string)})
#save(bleh,file = "~/Downtoneps.R")
load("~/Downtoneps.R")
downtonscripts=lapply(bleh,parseScriptline)

#scripts = lapply(PandPs,function(string) {readLines(url(string)})
#save(scripts,file = "~/PandPeps.R")
load("~/PandPeps.R")
PandPs = lapply(scripts,parseScriptline)


source("Dating tools.R")

#example(downtonscripts,'rationing')


WharParts = split(tok,rep(1:10,1,each=4000)[1:nrow(tok)])
WharScores = lapply(WharParts,function(script) {
  fullGrid(MakeNgramCounts(tokenize(script)),comps=c(1877,1921),weighted=T,
           smoothing=9)})


example(downtonscripts,'moral high ground')

do.call(rbind,lapply(downtonScores,function(score) {dat = score[[2]]$data; dat = dat[dat$y1==1e-09,];dat[order(dat$y2),]}))->dat; dat[order(-dat$y2),1]
do.call(rbind,lapply(downtonScores,function(score) {dat = score[[2]]$data; dat = dat[dat$y1!=1e-09,];dat[dat$y1/dat$y2<1e-02,]}))->dat; dat=dat[!duplicated(dat$word1)&dat$word1!="clicking on",]; dat[order(-dat$y2),1]
do.call(rbind,lapply(downtonScores,function(score) {dat = score[[2]]$data; dat = dat[dat$y1!=1e-09,];dat[dat$y1/dat$y2>6,]}))->dat; dat=dat[!duplicated(dat$word1)&dat$word1!="clicking on",]; dat[order(-dat$y1),1]
do.call(rbind,lapply(downtonScores,function(score) {dat = score[[2]]$data; dat}))->dat; dat=dat[!duplicated(dat$word1)&dat$word1!="clicking on",]; dat[order(-dat$y2),1]


summary(testing$data)
mat = xtabs(value ~ year+word1,testing$data)
qplot(as.numeric(rownames(mat)),rowSums(changefrom(-10,mat)>1,na.rm=T)/ncol(mat),geom='line')
crossmat = apply(mat,1,function(row) {apply(mat,1,function(locrow) {
  sum(row>=locrow)/sum(locrow>=row)
  })})
    
crossmat[rownames(crossmat)=='1917',colnames(crossmat)=='1990']
f = melt(crossmat)
f = f[f[,1]<f[,2],]
f = f[f$year < 1997,]

ggplot(f,aes(x=Var.1,y=year,fill=log(value))) + geom_tile() +
scale_fill_gradient2(mid='white') +ylim(1900,1990) + xlim(1900,2000)

plots = lapply(downtonScores,'[[',2)
plots[[1]] + ylim(-2,2) + geom_hex()
plots[[2]]$data[plots[[2]]$data$word1=='need to',]

MM2 = list("6"="http://movie.subtitlr.com/subtitle/show/89832",
           "4" = "http://movie.subtitlr.com/subtitle/show/440303",
            "8" = "http://movie.subtitlr.com/subtitle/show/232916")
MM1 = list("1" = "http://movie.subtitlr.com/subtitle/show/193933",
           "10" = "http://movie.subtitlr.com/subtitle/show/193942")
MM3 = list("12" = "http://movie.subtitlr.com/subtitle/show/583320")
MM = as.list(unlist(list(MM1,MM2,MM3)))

MMScores[[1]][[2]]
MMScores[[2]]
p[[2]] + 
ylim(0,3) + geom_point(size=7,alpha=.1,aes(color='red'))
example(men,"up having")
downtonScores[[2]][[2]]
#scripts = lapply(pandp,function(string) {readLines(url(string))}
#save(scripts,file = "~/PandPeps.R")
#load("~/PandPeps.R")
#MarxScores = sdfdfsfd(tokenize(Marx))




data.frame
setwd("/presidio/Rscripts")

filename = "Downton Abbey - 02x10 - Christmas Special.FoV.English.C.orig.Addic7ed.com.srt"
text = scan(paste("~/tv/",filename,sep=""),what='raw',sep="\n") 
newEp = fullGrid(MakeNgramCounts(tokenize(text)),comps=c(1920,1995),weighted=T,
           smoothing=9)
length(scores[['Downton Abbey']])




filename = "Heartbreak.txt"
text = scan(paste("~/tv/",filename,sep=""),what='raw',sep="\n")
tok = tokenize(text)
shawparts = split(tok,rep(1:10,1,each=6000)[1:nrow(tok)])
shawparts = lapply(shawparts,MakeNgramCounts)

scores[['Heartbreak House']][[3]][[2]] + ylim(-2,3.5) + geom_smooth() + scale_x_continuous(limits = c(1.5e-06,10e00),trans='log10')

scores[['Heartbreak House']] = lapply(shawparts,fullGrid,comps=c(1920,1995),weighted=T,smoothing=9)

tscores[["Remains of the Day"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/38477",
                                                    comps=c(1938,1995),smoothing=7,weighted=T))
scores[["Gone With the Wind"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/178290",
                                                    comps=c(1859,1939),smoothing=7,weighted=T))
scores[["The Apartment"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/527308",
                                               comps=c(1960,1995),smoothing=7,weighted=T))
scores[["Gosford Park"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/496590",
                                               comps=c(1932,1995),smoothing=7,weighted=T))
scores[["There Will Be Blood"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/123334",
                                               comps=c(1911,1995),smoothing=7,weighted=T))

scores[["Mad Men"]] = lapply(MM,subtitlrScore,
                             comps=c(1960,1995),smoothing=7,weighted=T)
scores[["Downton Abbey"]] = lapply(downtonscripts,
                                   function(script) {
  fullGrid(MakeNgramCounts(tokenize(script)),comps=c(1917,1995),weighted=T,
           smoothing=9)})
scores[["Pride and Prejudice"]] = lapply(PandPs,
                                         function(script) {
  fullGrid(MakeNgramCounts(tokenize(script)),comps=c(1815,1995),weighted=T,
           smoothing=9)})
scores[["Duck Soup"]] = weeklyscriptParse("http://www.weeklyscript.com/Duck%20Soup.txt",comps=c(1933,1995),weighted=T,smoothing=9)
#scores[["Age of Innocence (novel)"]] = WharScores,
scores[["Network"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/446082",comps=c(1976,1995),smoothing=7,weighted=T))
scores[["Glory"]] = list(subtitlrScore("http://movie.subtitlr.com/subtitle/show/194967",comps=c(1863,1989),smoothing=7,weighted=T))
scores[["Howard's End"]] = list(
  subtitlrScore("http://movie.subtitlr.com/subtitle/show/355514",comps=c(1905,1992),smoothing=7,weighted=T))
scores[["Lawrence of Arabia"]] = list(
  subtitlrScore("http://movie.subtitlr.com/subtitle/show/281949",comps=c(1917,1962),smoothing=7,weighted=T))
scores[["My Fair Lady"]] = list(
  subtitlrScore("http://movie.subtitlr.com/subtitle/show/36351",comps=c(1914,1956),smoothing=7,weighted=T))
        
scores[["Van Helsing"]] = list(
  subtitlrScore("http://movie.subtitlr.com/subtitle/show/36351",comps=c(1887,2004),smoothing=7,weighted=T))

scores[["Deadwood"]] = lapply(
  list("http://movie.subtitlr.com/subtitle/show/237791"),subtitlrScore,
    comps=c(1875,1995),smoothing=7,weighted=T)

loc = scores[["The Apartment"]][[1]][[1]]$data
summary(loc)
compyears = c(1800,1850,1900,1950,1995)
loc = loc[loc$year %in% compyears,]
words = table(loc$word1)
tabbed = xtabs(value ~ year+word1,loc)
tabbed = tabbed[,!is.na(colSums(log(tabbed)))]
ranks= apply(-tabbed,1,rank)
names(ranks) = names(tabbed)
ranks = melt(ranks)
names(ranks) = c("word1","year","value")
loc = melt(tabbed)
loc = merge(loc,ranks,by=c('word1','year'))
names(loc) = c("phrase","year","frequency","rank")

myframe
ggplot(myframe,aes(y=frequency,x = rank,color=factor(year))) + geom_line()

geom_density(alpha=.4,binwidth=.5,position='dodge') +
     

loc = scores[["Downton Abbey"]][[9]][[2]]
extras = loc
extras$data = loc$data[loc$data$y1==1e-09,]
loc$data = loc$data[loc$data$y1!=1e-09,]
names(extras)
extras$layers[[1]] 
extras$mapping = aes(x=(y1+y2)/2,y=y2*0+3)
loc + geom_text(data = extras$data,aes(y=sample(200:300,nrow(extras$data),replace=T)/100,label=word1),color = 'red',size=2.5)

loc[loc$y1==1e-09,]
summarystats = function(myframe) {
  testing = myframe[[2]]$data
  attach(testing)
  sum1 = sum( (y1==1e-09 & y2 >= 1e-06) | (y1!=1e-09 & y1/y2<=5e-02)) /nrow(testing)
  sum2 = sum(abs(log(y1[y1>y2]/y2[y1>y2])))/sum(abs(log(y1[y1<y2]/y2[y1<y2])))
  newrat = sum(log(y1/y2)>=1.9)/sum(log(y1/y2)<=-1.9)
  detach(testing)
  
  cleandat = testing[testing$y1 != 1e-09 & testing$y2 > 10e-06,]
  attach(cleandat)
  newrat = sum(log(y1/y2)>=1)/sum(log(y1/y2)<=-1)
  detach(cleandat)
  c(sum1,newrat)
}  
#testing = scores[['Duck Soup']][[1]][[2]]$data
SummaryScores = lapply(
  names(scores), function(name) {
    myframe = as.data.frame(t(sapply(scores[[name]],summarystats)))
    myframe$show   = name
    myframe
  })
    
Summaries = lapply(scores, function(mylist) {
    names(mylist) = paste(as.character(1:length(mylist)))
    ret = ldply(mylist,function(myframes) {
      myframes = myframes[[2]]$data
      myframes
      })
    ret
  })
Summaries = ldply(Summaries,function(myframe) {
  names(myframe)[1] = "ep"
  myframe
})
names(Summaries)
?grep
Summaries = Summaries[grep("gonna",Summaries$word1,invert=T),]
Summaries = Summaries[grep("gotta",Summaries$word1,invert=T),]
Summaries = Summaries[grep("anybody",Summaries$word1,invert=T),]
Summaries = Summaries[grep("anyone",Summaries$word1,invert=T),]
Summaries = Summaries[grep("someone",Summaries$word1,invert=T),]
Summaries = Summaries[grep("everyone",Summaries$word1,invert=T),]
Summaries = Summaries[grep("cannot",Summaries$word1,invert=T),]
Summaries = Summaries[grep("shit",Summaries$word1,invert=T),]
Summaries = Summaries[grep("fuck",Summaries$word1,invert=T),]
Summaries = Summaries[grep("piss",Summaries$word1,invert=T),]

Summaries = Summaries[grep("\\d",Summaries$word1,invert=T,perl=T),]

names(Summaries)[1] = "show"
Summaries$haplax = (Summaries$y1==1e-09)
Summaries$real = "Modern"
Summaries$real[Summaries$show %in% c("The Apartment", "Duck Soup", "Network", "Heartbreak House")] = factor("Old")
Summaries$real[Summaries$show %in% c("Pride and Prejudice","Howard's End","Gone with the Wind")] = "Mix"
Summaries$real = factor(Summaries$real)
Summaries$ratio = Summaries$y2/Summaries$y1
Summaries[Summaries$ratio > 3000 & Summaries$haplax==T,]

TransLog10I <- Trans$new("log10I", "log10", function(x) 10^x, function(x) format(10^x, scientific=FALSE)) 
Georgian = c("Remains of the Day", "Downton Abbey", 
"Howard's End", "Heartbreak House", "Gosford Park")

ggplot(subset(Summaries,show =="Gosford Park"),
       aes(x=(y2+y1)/2,y=ratio,label=word1)) + 
        scale_y_continuous("Ratio of modern use to period use",
            breaks=c(1/25,1/10,1/5,1/2.5,1,2,5,10,25,50,100,200,500,1000,2000),
            trans='log10I') + scale_x_continuous(trans='log10') +
        facet_wrap (~show + ep) + 
        #geom_density2d()  + 
        #geom_point(alpha=.1,color = muted('blue')) + 
        geom_text(size=2.5) 
eval("1/2")
       
ggplot(subset(Summaries,show %in% Georgian),# & show %in% c("Mad Men","The Apartment","Downton Abbey","Heartbreak House")),
       aes(x=ratio,label=word1,col=real,lty=show)) + 
         geom_density(window='gaussian',adjust=5) + scale_x_continuous(trans='log10') + 
         scale_y_continuous(trans='sqrt')

summaryScores = ddply(Summaries,.(show,ep),function(frame,xscore = 64) {
  attach(frame)
  densities = density(log(frame$ratio),window='gaussian',adjust=10)
  val = data.frame(
    score1=densities$y[order(abs(1-densities$x))[1]],
    score2= sum(densities$y[densities$x > 1]),
    real=real,
    extreme = sum(ratio>xscore & haplax == F)/length(ratio),
    xhaplax = sum(haplax & ratio > xscore)/length(ratio),
    mhaplax = sum(haplax & ratio < xscore)/length(ratio))
  detach(frame)
  val
})
plotting = summaryScores[summaryScores$show!="Network",]
plotting$extreme[plotting$extreme==0] = min(plotting$extreme[plotting$extreme!=0]/2)
plotting$xhaplax[plotting$xhaplax==0] = min(plotting$xhaplax[plotting$xhaplax!=0]/2)

ggplot(plotting[plotting$show %in% Georgian,],aes(
  x=score2,y=(extreme + xhaplax)*100,color=show,label=ep)) + 
  scale_x_continuous("Score of moderate outliers",lim=c(2.8,5.5)) + 
  scale_y_continuous("Percentage of extreme outliers",lim=c(0,.5)) + 
  geom_text(data = ddply(plotting[plotting$show %in% Georgian,],.(show),
                         function(aframe) data.frame(score2 = mean(aframe$score2),extreme = mean(aframe$extreme),xhaplax = mean(aframe$xhaplax))
            ),aes(label=gsub(" ([A-Z])","\n\\1",show,perl=T)),alpha=.75) + 
  geom_text(data = ddply(plotting[plotting$show %in% Georgian,],.(show,ep),
        function(aframe) data.frame(
          score2 = mean(aframe$score2),
          extreme = mean(aframe$extreme),
          xhaplax = mean(aframe$xhaplax))
            ),alpha=.75,size=3.5) +   
              opts(legend.position="none",
                   title="Georgian Dramas by share of anachronistic language\n(towards the lower left is good:\nHeartbreak House is an actual Georgian Drama)")

ggplot(plotting[plotting$show=="Gosford Park",],aes(x=score2,y=(extreme + xhaplax)*100,color=show)) + 
  scale_x_continuous("Percentage of moderate outliers",trans='log10') + 
  scale_y_continuous("Percentage of extreme outliers",trans='log10')   + 
              geom_text(aes(label=ep)) + 
              opts(legend.position="none")



density(log(Summaries$ratio))$x
?density
?stat_density
head(Summaries)
Summaries[!is.na(Summaries$real) & Summaries$real==T & Summaries$y2/Summaries$y1 >= 100 & Summaries$y2,]
names(scores)
mylist = scores[["Downton Abbey"]]
    ldply(mylist,function(myframes) {
      myframes[[2]]$data[1:2,]
    },.progress = "text")

myframe = do.call(rbind,SummaryScores)
myframe$show = factor(myframe$show)

ggplot(myframe,aes(x=V1,y=V2*100,color=show)) + geom_point() + 
  scale_y_continuous("Percentage of Words more common today than then",trans='log10') + 
  scale_x_continuous("Percentage of extremely anachronistic phrases",trans='log10')+ 
  opts(legend.position = "none") + 
  geom_text(data = ddply(myframe,.(show),function(aframe) c(mean(aframe$V1),mean(aframe$V2))),
            aes(label=show))
ggplot(myframe,aes(y=V1,x=show)) + geom_boxplot() + 
  opts(legend.position = "none") + coord_flip() + scale_y_sqrt()

scores[["Network"]][[1]][[2]] +geom_smooth(model='lm')

m = ldply(names(scores),function(name) {
  dat = scores[[name]][[1]][[2]]$data
  data.frame(strength = summary(lm(log(y2/y1) ~ log(y2),dat))$coefficients[2,1])
})
scores[['Heartbreak House']][[1]][[2]] + geom_hex() + geom_smooth(method='lm')
lapply


?stat_smooth
?geom_smooth
m$show = names(scores)
m[order(m$strength),]

MarxScores = fullGrid(MakeNgramCounts(Marx),comps=c(1933,1995),weighted=T,smoothing=9) 

downton = scripts
downton = lapply(downton,parseScriptline)
names(downton) = c(1:length(downton))
readable = unlist(lapply(downton,strsplit,"\n"))

source("Dating tools.R")

  
PandP = checkCorpus(dcounts)

summary(change$isNew)
sum(change$isNew==T)/sum(change$isNew==F)
change[is.na(change$isNew)],
ggplot(checked,aes(x=change)) + 
  geom_histogram(binwidth=.1) + scale_x_continuous(trans='log10',limits = c(.001,1000)) +
  facet_wrap(~freqClass) + scale_y_sqrt()

ggplot(checked,aes(x=abslog,fill=isNew)) +
  geom_bar(alpha=.5,position='dodge',binwidth=.2) + 
  scale_y_continuous(trans='sqrt')

f = lm(log(early) ~ log(late),change)
-sort(f$residuals)[1:25]
word = "stole secrets";cat(readable[(grep(word,readable)-7):(grep(word,readable)+7)],sep="\n")

readable[grep("cow pie",readable)]

loc = change[change$late > 1e-7,]; loc =change
loc[order(loc$change),][1:25,]
change[change$early > 1e-06,]


if (FALSE) {
  wharton = scan("~/wharton.txt",what='raw',sep="\n")
  wharton = gsub('\\."','"\\.',wharton)
  wharton[(sapply(wharton,nchar))<59] = paste(wharton[(sapply(wharton,nchar))<59],"\n")
  wharton = paste(wharton,collapse=" ")
  wharton = unlist(strsplit(wharton,"\n"))
  quotes = wharton
  quotes = gsub('^[^"]+$','',quotes,perl=T)
  quotes = gsub('^[^"]+"','"',quotes,perl=T)
  quotes = gsub('"[^"]+$','"',quotes,perl=T)  
  comparison = 0
  i = 1
  while (length!=comparison) {
    cat(i)
    i = i+1
    comparison=length
    quotes = sub('("[^"]+")([^"]+)("[^"]+")','\\1\\3',quotes,perl=T)
    length = nchar(paste(quotes,collapse=""))    
    length = nchar(paste(quotes,collapse=""))
  }
  quotes = quotes[quotes!=""]  
  quotes = paste(quotes,collapse="")
  quotes = unlist(strsplit(quotes,'"'))
  quotes = quotes[quotes!=""]
  quotes = gsub("[,\\.!;'\\?:-]"," ",quotes)

  quotes[1:5]
  tok = do.call(rbind,lapply(quotes,function(line) {
    line = unlist(strsplit(line," "))
    cbind(line[-length(line)],line[-1])
  }))
  tok[1:5,]
  tok = tok[tok[,1]!="" &tok[,2]!="",]
  source("Dating tools.R")
  cnts = counts(tok)
  cnts[1:5,]
  wharScores = checkCorpus(cnts,compareYear=1875,baseyear=1921)
  wharPresent = checkCorpus(cnts,compareYear=1921,baseyear=1980)
setwd("/presidio/Rscripts")
source("Rbindings.R")
source("Dating tools.R")  
source("Trendspotting.R")
  
dateBookid = function(bookid,sampling =F ) {
  #We have to flag a single bookid
  dbGetQuery(con,"UPDATE catalog SET bflag=0")
  dbGetQuery(con,paste("UPDATE catalog SET bflag=1 WHERE bookid=",bookid))
  query=APIcall(constraints = 
     list(method = 'ratio_query',
      smoothingType="None",      
      counttype = 'Raw_Counts',
      groups = list(
          "words1.casesens as term1",
          "words2.casesens as term2",
          "catalog.bookid as mid"),                           
      search_limits = 
         list(
          'bflag' = list(1))
     ),internal=T)
  results = dbGetQuery(con,query)
  results = results[,c(1,2,4)]
  results = results[!grepl("'",results[,1]) & !grepl("'",results[,2]),]
  if (sampling) {results = results[sample(nrow(results),sampling),]}
  results = results[!grepl("\\d",results[,1],perl=T) & !grepl("\\d",results[,2],perl=T),]
  results = results[!grepl("\\W",results[,1],perl=T) & !grepl("\\W",results[,2],perl=T),]
  results = results[!grepl("[A-Z]",results[,1],perl=T) & !grepl("[A-Z]",results[,2],perl=T),]
  graph = fullGrid(results)
  graph + 
    geom_vline(col='red',lty=2,lwd=4,xintercept=dbGetQuery(con,paste("SELECT year FROM catalog WHERE bookid=",bookid))[1,1])
}
  
source("Dating tools.R")
f = dbGetQuery(con,"SELECT bookid FROM catalog WHERE aLanguage='eng'")
bookid = sample(f[,1],1)
p = dateBookid(bookid,500)
p
p$layers[[2]]$data
  
  scores = t(scores)
  
  scores = t(apply(cnts[cnts[,3]>1,],1,modernityCheck,compareYear=1921,baseyear=1950))
  dim(scores)  
  change = makeChangeTable(scores,cnts[cnts[,3]>1,])
  qplot(change$abslog)
  ggplot(change[change$change > 0 & cnts[,3] > 1,],aes(x=change)) + 
    geom_histogram(binwidth=.1) + scale_x_continuous(trans='log10',limits = c(.01,100)) +
    facet_wrap(~freq) + scale_y_sqrt()
  ggplot(change[change$abslog<10,],aes(x=abslog,fill=isNew)) + geom_bar(alpha=.5,position='dodge')
  
  f = lm(log(early) ~ log(late),change[change$early > 0 & change$late > 0,])
  sort(f$residuals)[1:55]
  word = "stole secrets";cat(readable[(grep(word,readable)-7):(grep(word,readable)+7)],sep="\n")
}

