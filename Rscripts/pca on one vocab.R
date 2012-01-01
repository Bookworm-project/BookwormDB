Word spread

rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")
groupeds = list("lc1 as genre","words1.stem as w1")
years = c(1880,1881)
core_search = list(
    method = 'counts_query',
    words_collation = "Case_Sensitive",
    groups=groupeds,      
    search_limits = 
      list(
        list(
          'word2' = list("are"),
          'alanguage' = list('eng'),
          'bflag' = list(1)
          )
  )
)  

values=dbGetQuery(con,APIcall(core_search))

values = values[!is.na(values$w1) & !is.na(values$genre),]
#Set some cutoffs
words = xtabs(count~w1,values)
words = names(words)[words>100]

genres = xtabs(count~genre,values)
genres = names(sort(-genres)[1:75])

usable = values[values$w1 %in% words & values$genre %in% genres,]
usable$w1 = factor(usable$w1)
usable$genre = factor(usable$genre)
tabulated = xtabs(count ~ genre+w1,usable)
tabulated = tabulated/rowSums(tabulated)
x = tabulated[rownames(tabulated)=='FB',] + tabulated[rownames(tabulated)=='LA',]
x = tabulated[rownames(tabulated)=='PZ',]
plot(hclust(dist(results)))

results = apply(tabulated,1,function(x) {apply(tabulated,1,function(y) {x %*% y / sqrt(x%*%x * y%*%y)} )})
melted = melt(results)
levels(melted$Var.1)=levels(melted$genre) = c(levels(melted$Var.1),"NA")
melted$Var.1[is.na(melted$Var.1)]=as.character("NA")
melted$genre[is.na(melted$genre)]="NA"

sorted_levels = rev(sort(unique(as.character(melted$genre))))
sorted_levels = names(sort(prcomp(results)$x[,2]))
sorted_levels = names(sort(results[rownames(results)=='BF',]))
melted$genre = factor(melted$genre,levels= sorted_levels)
melted$Var.1 = factor(melted$Var.1,levels = rev(levels(melted$genre)))
melted$value = as.numeric(melted$value)

none=theme_blank()
ggplot(melted,aes(x=Var.1,y=genre,fill=value)) + geom_tile(aes(fill=.83)) +
  geom_tile() + 
  scale_fill_gradient2(midpoint = median(melted$value),limits=c(.83,1),high=muted("green")) +
  scale_x_discrete(expand=c(0,0)) +
  scale_y_discrete(expand=c(0,0))  +
  opts(title = "cosine similarity among LC classifications",
       panel.background = theme_rect(fill=muted("red")),axis.ticks = theme_blank(),
       panel.grid.major = none,
       panel.grid.major = none,
       axis.text.x = theme_text(
         angle = 90, hjust = 1,colour = "grey50")) + 
           labs(fill="score",x="",y="") 
          

 

z = matrix(1:16,ncol=4)
z
sweep(z,2,)

x = c(1,2,3)
y = c(1,2,4)

sort(values)

normed = tabulated/rowSums(tabulated)
#normed = t(t(normed)/colSums(normed))
z = prcomp(normed)
plot(normed %*% z$rotation[,c(1,2)],type='n')
text(normed %*% z$rotation[,c(1,2)],rownames(tabulated),col=rgb(0,0,0,.6))
points(normed %*% z$rotation[,1:2],pch=16,
     col=rgb(1,0,0,tabulated[,colnames(tabulated)=='call']/max(tabulated[,colnames(tabulated)=='call'])*.75))

tabulated[1:5,1:5]