#Dating tools

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

counts = function(dcounts) {
  #This is separate so we can paste together some serialized works.
  counts = table(paste(dcounts[,1],dcounts[,2]))
  words = as.data.frame(do.call(rbind,strsplit(names(counts)," ")))
  words$count = counts
  words = words[!grepl("[B-HJ-Z]",apply(words,1,paste,collapse=" "),perl=T),]
}

modernityCheck = function(row,compareYear=1921,baseyear=2000,yearlim=c(1800,2008)) {
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
    c(merged$smoothed[merged$year==compareYear],merged$smoothed[merged$year==baseyear])
    } else {1}
}