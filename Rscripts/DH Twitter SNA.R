chooseCRANmirror()

#I'm going to lift some code from http://blog.ynada.com/864

#First, we install some R extensions
install.packages("twitteR")
install.packages("sna")
install.packages("ROAuth")
#Then
require("twitteR")
require("sna")
require("ROAuth")

#Set up authorization:
tw<-OAuthFactory$new(consumerKey="OJQLVhd2nYEWKXT1u2hqQ",
        consumerSecret="JHQLIAFDhRrFrZLxzIINQZUo2PhomHOd2l2sd52XU",  
requestURL="http://api.twitter.com/oauth/request_token",
accessURL="http://api.twitter.com/oauth/access_token",
authURL="http://api.twitter.com/oauth/authorize")

tw$handshake()
I used http instead of https because the latter gave me an error of SSL certification fail. Then, I enter a PIN code obtained from a given URL and registered with Twitter:

registerTwitterOAuth(tw)


dhnow = getUser("benmschmidt")
#"dhnow" is now an R object that contains all sorts of information about taht twitter user.
dhnow$location
dhnow$screenName
# Get Friends and Follower names with first fetching IDs (getFollowerIDs(),getFriendIDs()) and then looking up the names (lookupUsers()) 
lookupUsers(dhnow$getFriendIDs(5))

follow = dhnow$getFollowers()
df <- do.call(“rbind”, lapply(follow, as.data.frame))
str(df)
head(df, 3)

df <- do.call(“rbind”, lapply(follow, as.data.frame))
f = dhnow$getFriends(2)
lookupUsers(someIDs[[1]])
users = lapply(someIDs[1],getUser)
friends.object<-lookupUsers()
friends.object
n<-20 
friends <- sapply(friends.object[1:n],name)

# Retrieve the names of your friends and followers from the friend
# and follower objects. You can limit the number of friends and followers by adjusting the 
# size of the selected data with [1:n], where n is the number of followers/friends 
# that you want to visualize. If you do not put in the expression the maximum number of 
# friends and/or followers will be visualized.
 
friends <- sapply(friends.object[1:n],name)
followers <- sapply(followers.object[1:n],name)
 
# Create a data frame that relates friends and followers to you for expression in the graph
relations <- merge(data.frame(User='YOUR_NAME', Follower=friends), 
data.frame(User=followers, Follower='YOUR_NAME'), all=T)
 
# Create graph from relations.
g <- graph.data.frame(relations, directed = T)