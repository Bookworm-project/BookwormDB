setwd("/presidio")
source("Rbindings.R")

p = APIcall(
  list(
    method = 'allwords_query',
    smoothingType="None",
    words_collation="Case_Insensitive",
    search_limits = list(
      list('lc1'=list("BT")),
      list('lc1'=list("BV"))
     )
    )
)

results = lapply(p, function(y) {dbGetQuery(con,y)})
merged = merge(results[[1]],results[[2]],all=T,by=names(results[[1]])[1])
names(merged)[1] = "word"
merged$word = iconv(merged$word)
merged = merged[!is.na(merged$word),]
#merged = merged[merged$word==tolower(merged$word),]
#merged = merged[nchar(merged$word)>1,]
merged[is.na(merged[,2]),2] = 0.5
merged[is.na(merged[,3]),3] = 0.5
#bookids = dbGetQuery(con,"SELECT bookid,year FROM catalog")
dunning = dunning.log(merged)

multiplicative_overage = merged[,2]/merged[,3]
additive_overage = merged[,2]/sum(merged[,2])-merged[,3]/sum(merged[,3])
names(multiplicative_overage) = names(additive_overage) = merged$word
comparison = data.frame(word = merged$word,addition = additive_overage*sum(merged[,2]),multiplication=multiplicative_overage)
comparison = comparison[comparison$addition > 1 & comparison$multiplication > 1 & comparison$mult < Inf,]
plot(comparison$addition,
     comparison$multiplication,
     pch=16,
     col=rgb(.75,0,0,.05),log='xy',main="Same plot, Dunning's Points in Green")
Interesting_words = c(names(rev(sort(multiplicative_overage[multiplicative_overage < Inf]))[1:12]),names(rev(sort(additive_overage))[1:12]))

merged

midpoint = comparison$add[comparison$mult==max(comparison$mult)]
comparison$combined_overage=
  (log(comparison$add)-log(midpoint))/(max(log(comparison$add)-log(midpoint))) + 
  log(comparison$mul)/max(log(comparison$mul))

Interesting_words = comparison$word[comparison$comb >=1]
comparison[rev(order(comparison$combined_overage)),][1:50,]
groupa = abs((sort(dunning))[1:500])
textable = comparison[comparison$word %in% names(groupa[1:100]),]
points(textable$addition,textable$multiplication,pch=16,col=rgb(0,.75,0,1))
textable = comparison[comparison$word %in% Interesting_words,]
text(textable$addition,textable$multiplication,textable$word,cex=.8)

groupa = abs((rev(sort(dunning)))[1:500])
cat(paste(names(groupa),": ",groupa,sep="",collapse="\n"))
#paste(rep(names(groupa),groupa),collapse=" ")

dunning.log = function(wordlist) {
  #takes a data frame with columns "word," "count.x" and "count.y"
	#Formula (whence variable names) taken from http://wordhoard.northwestern.edu/userman/analysis-comparewords.html
  attach(wordlist)
  wordlist[wordlist==0] = .1
  c = sum(count.x); d = sum(count.y); totalWords = c+d
  wordlist$count.total = count.x+count.y
  wordlist$exp.x = c*(wordlist$count.total)/(totalWords)
  wordlist$exp.y = d*(wordlist$count.total)/(totalWords)
  wordlist$over.x = wordlist$count.x - wordlist$exp.x
  wordlist$over.y = wordlist$count.y - wordlist$exp.y
  detach(wordlist)
  attach(wordlist)
  wordlist$score = 2*((count.x*log(count.x/exp.x)) + count.y*log(count.y/exp.y))
  
	dunning = apply(wordlist,1,function(row) {
		a = as.numeric(row[2]); b = as.numeric(row[3])
		E1 = c*(a+b)/(c+d)
		E2 = d*(a+b)/(c+d)
		score = 2*((a*log(a/E1)) + (b*log(b/E2)))
		if (b <= E2) {score = score*-1}
		#This last line makes values negative if the word is overrepresented in the second sample, because otherwise it's non-trivial to tell the two groups apart.
		score
	})
	names(dunning) = wordlist[,1]
	dunning
}	