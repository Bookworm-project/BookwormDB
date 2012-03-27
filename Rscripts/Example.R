#Examples

head(locframe)

p = ggplot(locframe[locframe$ep==1,],aes(x=(y2+y1)/2,y=y2/y1))
p + geom_point()
p = p + scale_y_log10() + scale_x_log10()
p+geom_point() 
p+geom_hex()
p+geom_text(aes(label=word1),size=3)

ggplot(locframe)+geom_density(aes(x=y2/y1)) + scale_x_log10()

  scale_y_continuous(
    "Ratio of modern use to period use",
    trans='log10',lim=c(1/3,35)) + 
  scale_x_continuous("Overall Frequency",labels = c("1 in 10M","1 in 1K","1 in 100K","1 in 1B"),
                     breaks = c(1/100000,1/10,1/1000,1/10000000),
                     trans='log10')+
        geom_text(data=subset(plottable[plottable$y1*plottable$y2!=0,]), 
                  size=2.5,alpha=.15) + 
        geom_text(data=subset(plottable[plottable$y1==0 & plottable$y2 != 0,]),
                  size=2.5,color='red',aes(y=500),position=position_jitter(width=0)) + 
        geom_hline(yint=1,color='black',alpha=.7,lwd=3,lty=2)