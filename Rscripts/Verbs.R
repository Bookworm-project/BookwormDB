require(RCurl)
setwd("/presidio/Rscripts")
source("Rbindings.R")
myCsv <- getURL("https://docs.google.com/spreadsheet/pub?hl=en_US&hl=en_US&key=0AjMccO2n_mi6dDlPVm16U2tBM2kydFlQQ2JyemkwOVE&single=true&gid=0&output=csv")
verbs = read.csv(textConnection(myCsv))
verbs = verbs
verbs=verbs[verbs$Include,]
summary(verbs)

flagWordids(verbs$IrrPreterit,"lowercase",1)
flagWordids(verbs$IrrPart,"lowercase",1,preclear=F)
flagWordids(verbs$RegPreterit,"lowercase",2,preclear=F)

pos = 22
irregular = list(unique(
  unlist(strsplit(
    c(
      as.character(verbs$IrrPreterit[pos]),
      as.character(verbs$IrrPart[pos])
      ),", "))))
regular = list(as.character(verbs$RegPreterit[pos]))
flagWordids(unlist(irregular),"word",1)
flagWordids(unlist(regular),"word",2,preclear=F)
    

core_search = list(
    method = 'frequency_query',
    words_collation = "All_Words_with_Same_Stem",
    groups=list('lc1'),      
    search_limits = 
      list(
        list(
          'word' = list("pay attention"),
          'year' = as.list(1880:2000)
          )
  )
  )  
  dbGetQuery(con,APIcall(core_search))
}


