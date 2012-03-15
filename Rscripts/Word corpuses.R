  
dbGetQuery(con,APIcall(constraints = 
     list(counttype = "Percentage_of_Books",method = 'counts_query', 
      groups = list("year"),                           
      search_limits = 
         list(
          'word'=list('Charles Darwin'),
          'hasword'=list("evolution")
     ))))
