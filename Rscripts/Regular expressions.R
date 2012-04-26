con=dbConnect(MySQL())
core_search = list(
      method = 'counts_query',
      groups=list("year","words1.word as w1","words2.word as w2"),
      search_limits = 
        list(
            'word' = "focus attention,"
            'year' = list("$gte"=list(1900),"$lte"=list(1911)),
            'alanguage' = list('eng'),
            'lc1'='BF'
    )
  )  
search = APIcall(core_search)
dbGetQuery(con,search)