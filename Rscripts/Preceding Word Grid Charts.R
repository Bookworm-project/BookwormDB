rm(list=ls())
setwd("/presidio/Rscripts")
source("Rbindings.R")

wordlist = list('attention')
comparelist = list('carriage','language','advantage','passage')

words = wordgrid(wordlist,
         collation='Case_Insensitive',
         flagfield='lowercase',
         fitAgainst='smoothed',
         n=85)


wordgrid(wordlist,
         collation='Case_Insensitive',
         flagfield='stem',
         fitAgainst='smoothed',
         n=85,
         WordsOverride=adunwords,
         freqClasses = 4,trendClasses=3)




  compdunwords = c("free","keen","unfair","fair","active","foreign","fierce","successful",
               "sharp","direct","increased","ruinous","water","industrial",
               "international","intense","open","effective","domestic","destructive",
               "excessive","increasing","potential","severe","healthy",
               "commercial","market","railroad","unlimited","cutthroat",
               "business","American","perfect","friendly","serious","global",
               "unrestrained","restricting","growing","unregulated","economic",
               "local","athletic","honorable","legitimate","wasteful","keener",
               "lively","close","strenuous","unequal","individual")
  adunwords = c("absorbed", "amused", "aroused", "arrest", "arrests", "attract", 
"attracted", "attracting", "attracts", "attracts", "awaken","awake","awakened","call", "called", 
"calling", "calls", "challenge", "claimed", "command", "commanded", 
"commands", "compelled", "compelling", "compels", "concentrate", 
"concentrate", "concentrated", "confine","demand", "demanded", "demanding", "demands",
"devoted", "directed", "directing", "distract", "distracted", 
"diverted", "diverting", "divided", "draw", "drawing", "drawn", 
"draws", "drew", "enforce","engage","engaged", "escape","escaped","excited", "excite", "fix","focus", "gave", 
"giving", "increased", "increase","invite","merit", "need", "needed", "needing", 
"needs", "paid", "pay", "paying", "pays", "received", "receiving", 
"required", "riveted", "startled", "strained", "turn", 
"turn", "turned","wander", "wandering","withdraw")
