dbGetQuery(con,
           "UPDATE wordsheap as t1 SET t1.wflag = 0 ")
           
dbGetQuery(con,"
UPDATE wordsheap as t1 
LEFT JOIN wordsheap as t2 
ON (t1.lowercase=t2.lowercase) 
SET t1.wflag = 1 
WHERE
 t1.casesens != t1.lowercase 
 AND t1.stem is not null
 AND t1.wordid < t2.wordid
 AND t2.casesens=t2.lowercase
 AND NOT t1.casesens=t2.casesens
")
           
dbGetQuery(con,
           "
           UPDATE wordsheap as t1
           LEFT JOIN wordsheap as t2
           ON t1.lowercase=t2.casesens SET t1.wflag = 1
           WHERE t2.casesens is null AND t1.stem is not null;"   
)           
dbGetQuery(con,"UPDATE wordsheap as t1 
SET t1.wflag = 0 WHERE t1.wflag=1 AND CHAR_LENGTH(word)=1 ")

dbGetQuery ( con, "UPDATE wordsheap as t1 SET wflag=0 WHERE wflag=1 AND
           word='Sir' OR word='East' OR word='Miss'
           OR word = 'University' OR word = 'American' OR 
           word = 'English' OR word = 'College'
           OR word = 'Catholic' OR word = 'Christ' OR 
           word = 'San' OR word = 'United' OR word = 'God'
           "
           )