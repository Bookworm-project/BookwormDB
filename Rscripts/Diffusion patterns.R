source("Rbindings.R")
source('Word Spread.R')
source('Age Spread.R')
genres =genreplot(list("awareness"),
          grouping='lc1',
          groupings_to_use = 30,
          counttype = 'Percentage_of_Books',
          ordering=NULL,
          years=c(1830,1922),
          smoothing=.4,
          comparison_words = list(),
          words_collation='All_Words_with_Same_Stem')

p = xtabs(value~year+groupingVariable,genres$data)
myframe = data.frame(year = rownames(p),deviation = apply(p,1,function(row) {abs(sd(row)/mean(row))}))

variance = ggplot(myframe,aes(x=as.numeric(as.character(year)),y=deviation))+geom_line(aes(color=deviation))+ylim(0,5) + ylab('') + xlab('') + scale_x_continuous(expand=c(0,0)) +
  scale_y_continuous(expand=c(0,0)) + scale_color_gradient('metric of\nspreadedness')
grid.arrange(genres,variance,heights = c(4,1)) 

#ageplot("nationwide")