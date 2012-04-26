#Oceans2

#Preprocessing is done by downloading the files, and then this:
#
if (FALSE) {
awk '
BEGIN{
  ORS="\n";
  OFS="\t";
  FIELDWIDTHS = "4 2 2 4 5 6 2 1 1 1 1 1 2 2 9 2"
  OS = "\t"}
{print $1,$2,$3,$5,$6,$14,$15,$16}' downloads/* >> all.txt 
}
require(ggplot2)
data = read.delim(
  "~/ICOADS/all.txt",sep="\t",fill=T,header=F,
  col.names = c("Year","Month","Day","lat","long","II","ID","country","blank"),
  colClasses = c("integer","integer","integer","integer","integer","integer","factor","factor"),
                  comment.char="",quote="",flush=T)

data$long = as.numeric(data$long)/100
data$long[data$long>180] = data$long[data$long>180] -360
data$lat = as.numeric(data$lat)/100

data$century = cut(
  data$Year,quantile(unique(data$Year)),include.lowest=T)
data$voyageid = factor(paste(data$ID,data$II))
head(data)

tmp = data[data$Year==1830,]
tmp$voyageid = factor(tmp$voyageid)
ggplot(tmp,aes(y=lat,x=long,group=voyageid,color=country)) + 
  geom_path(alpha=.15) 
