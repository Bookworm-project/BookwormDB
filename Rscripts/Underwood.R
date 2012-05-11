rm(list=ls())

#This uses the API to Bookworm to build a data.frame with metadata for all the books matching
#the query. The list structure is so ugly because the API uses dictionary structures
#extensively, and R is one of the less JSON-friendly languages out there.
#This Bookworm API lets all sorts of fun questions get asked; the reason we don't expose it,
#oddly, is because it's _too_ powerful; it's easy to accidentally submit a query that can hang the server
#for hours.

#I"m not showing all the code here: for instance, "Rbindings.R" is a 
source("Rbindings.R")
con=dbConnect(MySQL())
booklist = dbGetQuery(con,
  APIcall(
  list("method" = "counts_query",
       #Groups is the most important term here: it says that we want a data.frame with years, Library of
       #Congress subject headings, and unique identifiers for all the books matching the search limits.
       #We'll also get the numbers of words in each book--that's what counts_query does.
       groups = list('year',"lc1",'catalog.bookid as id'),
       "search_limits" = list(
         "lc0"=list("B"),
         aLanguage=list("eng")
        )
    )
  )
)

names(booklist)[2] = "LCSubjectHeading"
#As it turns out, the database results are a little buggy, so we have to clean them
#to make them work completely consistently. (This is MySQL's fault, mostly)
booklist$LCSubjectHeading = gsub(",.*","",booklist$LCSubjectHeading)
booklist$LCSubjectHeading = tolower(booklist$LCSubjectHeading)
booklist$LCSubjectHeading = gsub(" ","",booklist$LCSubjectHeading)
booklist$LCSubjectHeading = factor(booklist$LCSubjectHeading)
booklist = booklist[!duplicated(booklist$id),]

#Now that we know what the books are, we just set a couple variables:

#Rather than require a book for the year "1850" be written in 1850 exactly, we'll do a moving window, set at
#5 years on either side.
smoothing = 1 #
#Ted says 1,000,000 words per set works well, so I'll do that.
wordsPerSet = 1000000
#Ted just takes one sample of 1,000,000 books for year, but I want to be able to check the distance of
#(for example) history from itself, so I'm going to take two.
samplesPerYear = 2

genrecounts = table(booklist$LCSubjectHeading)
genres = names(genrecounts[genrecounts>1000])
booklist = booklist[booklist$LCSubjectHeading %in% genres,]
booklist$LCSubjectHeading = factor(booklist$LCSubjectHeading)
#And here's the beginning of the meat, where we decide which books we'll be looking at.
#ddply is a beautiful function that iterates over the categories in a data frame to produce a list
#It's part of Hadley Wickham's 'plyr' package: the 'dl' at the beginning means 
#'dataframe'->'list', and there are lots of other ways to use it.
require(plyr)
LCSHframe = booklist[booklist$LCSubjectHeading=="bf",]

samples = ddply(booklist,.(LCSubjectHeading),function(LCSHframe) {
  #This goes by each of the subject headings, and creates a new frame only consisting 
  #of books with that heading. We'll create the samples from those.
  genreSamples = ldply(seq(1870,1922,by=1+smoothing*2),function(year) {
    #Now we're going to create some sample years. I just put them in by hand here.
    myframe = LCSHframe[LCSHframe$year >= year - smoothing & LCSHframe$year <= year + smoothing,
                        c('id','count')]
    #No point even considering the large books.
    myframe = myframe[myframe$count<2*wordsPerSet,]
    if (nrow(myframe)==0) {return(data.frame())}

    possibleSamples = llply(1:100,function(setber) {
      #So, 100 times we randomly reorder these books. No reason for 100 in particular; but a hundred simulations
      #to get 2 book sets it should be pretty good.
      #We're going to randomly assign those books into subcorpuses. I am confident this is a pretty bad way to do it.
      #First determine how the corpuses can be: they can range from a single book to twice the average number required to get 
      #up to the target
      corpusSizes = 1:((wordsPerSet*2)%/%mean(myframe$count))
      #Then assign group numbers to individual books based on some random sampling.
      group = unlist(lapply(1:100,function(n) rep(n,times = sample(corpusSizes,1))))
      #Only a few of these are actually needed.
      myframe$set = group[1:nrow(myframe)]
      #Now ddply can easily tell us 
      counts = ddply(myframe,.(set),function(frame) data.frame(setcount = sum(frame$count)))
      #We want to figure out how close the first 3 books is to 1,000,000 words, how
      #close the first four books are, etc. The absolute value of the difference tells
      #us that, neatly vectorized across the whole set. Then I just remove all but the top two sets.
      counts=counts[order(abs(wordsPerSet-counts$setcount)),][1:2,]
      #and then a merge returns a data.frame with the bookids and counts.
      distance = sqrt(sum(wordsPerSet-counts$setcount)^2)
      corpus = myframe[myframe$set %in% counts$set,]
      #Now we rename those two sets as '1' and '2':
      corpus$set = as.numeric(factor(corpus$set))
      list(corpus = corpus[,c('id','set')],distance=distance)
      })
    #OK, so we have 100 lists of book pairs of about 1,000,000 words. Let's narrow it down.
    #you can use "[[" as a function in an apply statement to pull out just one element
    #of a list--this is frequently handy. Here I create two new vectors: one the number of 
    #in each of the booklists we've created, and one the actual books in that list.
    corpusgoodness = sapply(possibleSamples,'[[',"distance") #sapply returns a vector, not a list.
    corpuses = lapply(possibleSamples,'[[',"corpus") #lapply returns a list, which we need 
      #because there can be varying numbers of bookids in each group here.
    #Some of these simulations produce corpuses with only 40 or 50K words; I take the 
    #two that are closest to 1,000,000 words in length. This will probably bias us towards
    #shorter texts: I don't know that that's a problem, but it could be.
    
    topSamples = corpuses[[which(corpusgoodness==min(corpusgoodness))[1]]]
    topSamples$year = year

    #if the mean distance is more than 10% of the whole, just scrap the whole thing.
    if (min(corpusgoodness,na.rm=T)>wordsPerSet/10) {return(data.frame())}
    #We now add a column to the frame that lets us know what year the sample
    #is for.   
    #And then we return the set back out. These will get aggregated across subject headings by ddply 
    #automatically
    topSamples
  },.progress = "text")
})

#So now we have a data.frame with four columns: bookid,year,genre,and set.

#I'll fill those in with the actual top 5K words for every comparison we'd like to make by doing a ddply call that fills in the words with actual
#examples from the database.
#To keep it quick(er), I'm only going to use results from years divisible by 5.
words = ddply(samples,.(year),function(yearsample) {
  #Dividing by 'year' has ggplot create a frame for each year with a list of the books in each sample 
  yearResults = ddply(yearsample,.(LCSubjectHeading),function(subjectSample) {
    #Then--and this is the most time-consuming step--we pull out the full word counts, again using
    #the Bookworm API, for every set of bookids in each year-subject heading-set combo
    ddply(subjectSample,.(set),function(myframe) {
       words = dbGetQuery(
          con,
          APIcall(
            list("method" = "counts_query",
              #This 'groups' term is where I specify what's getting returned. I like to use stems in
              #situations like this, so that differences in verb tenses don't affect the results.
              groups = list('words1.stem as w1'),
              "search_limits" = list(
                #This is where I place limitations on the words returned: myframe$bookid is a vector
                #that contains all the bookids in the 1,000,000 word sample we're looking at.
                #This as.list(as.integer()) stuff is ugly.
                catalog.bookid=as.list(as.integer(myframe$id))
                #To test this out, I only count words that appear immediately before the word "are"
                #word2=list("are")
              ))
            )
          )
        #RMySQL tends to return character vectors, but factors are much more efficient. So we change it.
        words$w1 = factor(words$w1)
        words
          })
  })
  #Here's a random problem: I select on stems, but some words don't have stems in my database
  #(Arabic numerals, for instance). So we have to drop all those.
  yearResults=yearResults[!is.na(yearResults$w1),]
  #And here's where it gets a little ugly. We want to have a data.frame that has information on each
  #of the combinations that we can look at. One line for fiction subset 1 compared to poetry subset 2,
  #one for biography 2 to fiction 1, and so on down the chain. expand.grid does this in one function call.
  variable_combinations = expand.grid(
    genre=levels(samples$LCSubjectHeading),
    comparedTo=levels(samples$LCSubjectHeading),
    group1 = unique(samples$set),
    group2 = unique(samples$set))
  #And now the ugliest line in this script.
  #We don't want both fiction 1<->poetry 2 AND poetry2<->fiction 1 comparisons: 
  #It's the same thing in a different order. There's probably a function for this,
  #but I just sort, paste, and drop.
  variable_combinations = variable_combinations[!duplicated(
    apply(variable_combinations,1,function(row) paste(sort(c(paste(row[1],row[3]),paste(row[2],row[4]))),collapse="") )),]
  #less importantly, we don't want to compare fiction 1 to fiction 1; we know they're identical.
  #So we can drop those all out.
  variable_combinations = variable_combinations[!(variable_combinations[,1]==variable_combinations[,2] & variable_combinations[,3]==variable_combinations[,4]),]
  #Then, using merge() we wrap in the word counts for every possible genre and group category.
  comparisons = merge(
    variable_combinations,
    yearResults,by.x=c("genre","group1"),
    by.y=c("LCSubjectHeading","set"),all=T)
  #But that's not all: we merge again to get every comparison of genre and group. This produces a big data.frame
  comparisons = merge(
    comparisons,
    yearResults,by.x=c("comparedTo","group2","w1"),
    by.y=c("LCSubjectHeading","set","w1"),all=T)
  #Now, it would be nice to just return this comparisons set as a whole. But it's too big for that.
  #Instead, I'm just going to reduce it down to the top 5000 words in each set. ddply works for this, too.
  topwords = ddply(comparisons,.(comparedTo,group2,genre,group1),function(frame){
    #Note that I order on a negative result--that's often easier.
    frame = frame[order(-(frame$count.x+frame$count.y)),][1:5000,]
  })
  #again, some NAs creep in, I know not how. Drop them all out.
  topwords = topwords[!is.na(topwords$count.x),]
  #I'd actually like to just return this as it is, but that's impractical with sufficiently large sets.
  #So we reduce it down to a single score--similarity--instead
  ddply(topwords,.(genre,group1,comparedTo,group2),function(comparison){
    comparison = comparison[!is.na(comparison$count.x),]
    comparison = comparison[!is.na(comparison$count.y),]
    data.frame(similarity = cor(comparison$count.x,comparison$count.y,method='spearman'))
  })
},.progress = "text")
head(words)
#It's very easy to move from this data structure to any other one. To get the Spearman correlations for each group, for example:

similarities = words
similarities = similarities[!is.na(similarities$similarity),]
head(similarities)
#Earlier, we made it so that we didn't have both fiction-poetry and poetry-fiction
#Now I add them back in, to make the plotting make sense:
inverse = similarities
names(inverse)[match(c("comparedTo","group2","genre","group1"),names(inverse))] = c("genre","group1","comparedTo","group2")
#Basically, we just switch the names around, and rbind knows to keep them together
similarities = rbind(similarities,inverse)
#Using two sets gets two different samples. I want these to be as different as possible, so I only compare 1 to 1 and 2 to 2, except within a single genre.
similarities = similarities[similarities$group1 == similarities$group2 | similarities$genre == similarities$comparedTo,]
#"Recast" lets us treat "distance from fiction" as a variable, basically, which makes plotting work better.

#And then I'll just average the results of simulations using another ddply call.
summarysims = ddply(similarities,.(genre,comparedTo,year),function(localframe) {
  data.frame(similarity = mean(localframe$similarity))
})

#I'm going to make a bunch of plots at once using lapply here:for each of the types of genres.
plots = lapply(levels(summarysims$genre),function(genre) {
  #The 1800 data is terrible, so I'm just dropping it. 
  ggplot(summarysims[summarysims$comparedTo==genre,],aes(x=year,y=similarity,color=genre )) + 
    geom_smooth(se=F) + geom_point() + opts(title=paste("Similarity to",genre))
})

#do.call(grid.arrange,plots)
  
#The 1800 data is terrible, so I'm just dropping it. Partly this may be labeling by libraries of 18xx as 1800, it may be
#may be typesetting mistakes.
plots2 = lapply(levels(summarysims$genre),function(genre) {
  ggplot(summarysims[summarysims$comparedTo==genre & summarysims$year != 1800,],aes(x=year,y=similarity,color=genre )) + 
    geom_smooth(se=F) + geom_point() + opts(title=paste("Similarity to",genre))
})

do.call(grid.arrange,plots2)
