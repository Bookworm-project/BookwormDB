#!/usr/bin/R

#Testing for fictiveness.
flagRandomBooks(7,1)
flagRandomBooks(97,2,preclear=F)

p = list(
    method = 'allwords_query',
    smoothingType="None",
    groupings="stem",
    search_limits = list(
      list(
        'bflag' = list(1),
        'alanguage' = list("PZ")
        ),
      list(
        'bflag' = list(2),
        'alanguage' = list("QA")
      )
     )
    )

counts = compare_groups(p)

p[["search_limits"]][[1]][['lc1']] = list()
baseline = dbGetQuery(con,APIcall(p))

comparison = dun.with.merge(counts,baseline)
stopwords = dbGetQuery(con,"SELECT word FROM words WHERE stopword =1")[,1]

sort(-comparison[!(names(comparison)) %in% stopwords])[1:25]
    
usewords = names(sort(-comparison[!(names(comparison)) %in% stopwords])[1:96])

flagWordids(usewords,field="stem")
flagRandomBooks(10,1,preclear=T)

results = vapply(usewords,function (word) {
  words= list(word)
  cat(word,"\n")
  p = list(
      method = 'ratio_query',
      smoothingType="None",
      words_collation = "All_Words_with_Same_Stem",
      search_limits = list(
        list(
          'lc1'=list("PZ"),
          'word' = words,
          'alanguage' = list("eng")
          ),
        list(
          'word' = words,
          'alanguage' = list("eng")
          )
      ))   
  frames = lapply(APIcall(p),function(query) {dbGetQuery(con,query)})
  merged = merge(frames[[1]],frames[[2]],by="year",all=T)
  merged = merge(merged,data.frame(year=1823:1922),all.y=T,by="year")
  merged$value.x/merged$value.y
},(1823:1922)/2
)    
rownames(results) = 1823:1922
    covarians = cor(results)
melted = melt(results)
names(melted) = c("year","stem","ratio")
p = kmeans(covarians,12)
melted$cluster = p$cluster[match(melted$stem,names(p$cluster))]
summary(melted)    
    
a = lapply(1:12,function(num) {
my_data = melted[num==melted$cluster,]
my_data$stem = factor(my_data$stem)
ggplot(
  my_data,
  aes(x=year,y=ratio,color=stem)) +  
    geom_line(size=.1) + ylim(1,7)+
    geom_smooth(span=.4,size = 1,se=F,fullrange=T) 
})
search_terms[['groupings']] = "words1.stem,catalog.bookid"
require(gridExtra)
a[[2]]
do.call(grid.arrange,a)

    my_data = melted[melted$stem=="glance",]
    