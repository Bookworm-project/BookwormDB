#newerAPI
require(RJSONIO)
require(RMySQL)
require(ggplot2)
require(reshape)
require(plyr)

if (!exists("con")) {con = dbConnect(MySQL(),db="presidio")}

bookworm = function(
  #query may also be a list that will be coerced to JSON
  query = '
  {"method": "return_tsv",
  "database": "arxiv",
  "groups":["mld"],
  "search_limits":{
  "word":"graphene",
  "tld":["cn","edu","se"],
  "month":{"$gte":731640}}}',
  host = "melville.seas.harvard.edu"
  ) {
  if (length(query)==1){
    query = fromJSON(query)
  }
  if (is.null(length(query[['method']]))) {
    query[['method']] = 'return_tsv'
    }
  query=toJSON(query)
  #This requires curl installed, and write accessto /tmp
  silent = system(cat(
    "curl --data 'queryTerms=",
    query,
    "' ",
    host,
    "/cgi-bin/dbbindings.py > /tmp/tmpR.txt",
    sep=""),intern=T,ignore.stderr=T)
  data = read.table("/tmp/tmpR.txt",sep="\t",row.names=F)
  ?read.table
  if (query[['method']]!="return_tsv") {
    data = data[2,]
  }
  data
}