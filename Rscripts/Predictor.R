melville = dbConnect(MySQL(),
                host="melville.seas.harvard.edu",
                password="oldPassword",
                user="oldUser",
                db="presidio")
setwd("/presidio/Rscripts")
source("Rbindings.R")
predictors = c("Australian", "Buddhist", "Conservative", "Democratic", "Educational", 
"Engineering", "Geol", "Hegel", "Hong", "Industrial", "Iowa", 
"Kashmir", "Melbourne", "Muhammad", "Oregon", "Peking", "Psychology", 
"Railroad", "Railway", "Strauss", "Technology", "Texas", "Toronto", 
"Wisconsin", "aesthetic", "ammonium", "anode", "antagonism", 
"artistic", "basic", "cab", "category", "cathode", "cognitive", 
"competitive", "conservative", "constituency", "educational", 
"electrode", "electrodes", "embodiment", "embryonic", "enlightenment", 
"epithelium", "exceptional", "exhaustive", "fauna", "gradient", 
"hydrochloric", "hypertrophy", "immigrant", "immigration", "industrial", 
"mammals", "mediaeval", "monetary", "mythical", "myths", "organism", 
"outbreak", "ovarian", "phenomenal", "polarization", "policeman", 
"psychology", "railroad", "railroads", "resonance", "restaurant", 
"restaurants", "steamer", "steamers", "suggestive", "systemic", 
"tertiary", "tidal", "traveled", "traveler", "travelers", "traveling", 
"trousers", "Democracy", "Democrat", "Muslim", "Republicans", 
"Socialism", "Socialists", "Viet", "abnormal", "centralized", 
"dynamic", "pelvic", "photographic", "quantitative", "spores", 
"symbolism", "ventricular", "Dewey", "Dickens", "antagonistic", 
"environment", "myth", "organisms", "ovary", "Carlyle", "Gladstone", 
"Herr", "Jimmy", "cognition", "emotional", "medieval", "normally", 
"peripheral", "pleafure", "qualitative", "socialism", "unmistakable", 
"Handbook", "Houfe", "Muslims", "Shanghai", "counselor", "epithelial", 
"individualism", "protein", "sunlight", "Renaissance", "Socialist", 
"caufes", "clofe", "corpuscles", "fertilizer", "obferved", "plasma", 
"prestige", "queftion", "reafon", "reliable", "themfelves", "Annie", 
"Chrift", "Milwaukee", "Singh", "circumftances", "courfe", "eafily", 
"efpecially", "exprefs", "fats", "feems", "fenfe", "fhort", "fimple", 
"fmall", "fomething", "fpeak", "fpirit", "ftrength", "fubject", 
"fuch", "fuperior", "lofs", "myfelf", "neceflary", "ourfelves", 
"rhythmic", "thefe", "ufeful", "underftood", "Tennyson", "Thefe", 
"Utah", "almoft", "anfwer", "bourgeoisie", "cellulose", "climatic", 
"confiderable", "defenses", "eafy", "feem", "feldom", "fometimes", 
"foon", "glacial", "increafe", "intereft", "leaft", "lefs", "meafure", 
"muft", "obferve", "pafs", "perfons", "photography", "progrefs", 
"raife", "socialist", "tensile", "thofe", "unlefs", "Englifh", 
"Kong", "befides", "characterization", "defign", "feen", "fenfible", 
"feveral", "fingle", "fociety", "fuppofe", "fuppofed", "fupport", 
"fyftem", "genetic", "glucose", "happinefs", "hiftory", "inftance", 
"inftead", "itfelf", "juft", "purpofe", "reafoning", "reagent", 
"realistic", "refpect", "residues", "theater", "ufual", "univerfal", 
"whilft", "whofe", "Biology", "Communism", "carcinoma", "chloroform", 
"communism", "exiftence", "experimentation", "nuclei", "transitional", 
"tuberculosis", "urea", "Reafon", "Victorian", "amongft", "autonomy", 
"availability", "axial", "communist", "defense", "diftance", 
"faying", "feemed", "feven", "fick", "fouls", "fpecies", "ftate", 
"ftill", "herfelf", "himfelf", "houfe", "intensified", "nationalities", 
"postal", "reactionary", "sewage", "skillful", "sulphide", "thoufand", 
"ufe", "California", "Communist", "Communists", "Nebraska", "Sacramento", 
"againft", "autonomous", "becaufe", "confequence", "confider", 
"exceptionally", "felf", "ferve", "fervice", "firft", "ftand", 
"ftrong", "fufficient", "greateft", "ignoring", "juftice", "moft", 
"neceffary", "neural", "otherwife", "photograph", "poffible", 
"raifed", "sanitary", "ufed", "Atlanta", "Dakota", "Minnesota", 
"Nevada", "Percentage", "Ruskin", "concepts", "developmental", 
"solidarity", "standpoint", "surroundings", "Aspects", "Sociology", 
"biological", "fibers", "filver", "linguistic", "methyl", "nuclear", 
"Cuban", "Exhibition", "Tork", "environments", "ignore", "leadership", 
"reliability", "biology", "bureaucratic", "cigarettes", "differentiation", 
"hygiene", "photographs", "plow", "sociological", "Vols", "concept", 
"constants", "ignored", "protoplasm", "syphilis", "Fio", "Kansas", 
"Nerve", "detective", "rainfall", "retinal", "aluminium", "cigarette", 
"differentiated", "percentage", "sociology", "Aryan", "Denver", 
"chemicals", "formulated", "Arizona", "noteworthy", "percentages", 
"photo", "telegram", "utilized", "Industries", "Photo", "alignment", 
"stresses", "supplemented", "utilization", "utilize", "Confederates", 
"Seward", "downstairs", "ethnic", "parameters", "Confederacy", 
"Confederate", "Reagan", "conductivity", "Idaho", "Potomac", 
"Rebel", "Run", "imperialism", "prehistoric", "raids", "utilizing", 
"Headquarters", "Sanskrit", "Volunteers", "anyone", "formulate", 
"proliferation", "raid", "Reconstruction", "albumin", "investors", 
"Bismarck", "Minneapolis", "kinship", "summarized", "Corps", 
"Evolution", "dioxide", "unification", "kinetic", "neurotic", 
"racial", "Alaska", "Montana", "Petroleum", "bacteria", "heredity", 
"integrated", "scientist", "selective", "someone", "spectacular", 
"survival", "ooo", "psychic", "scientists", "specialists", "specialization", 
"Symphony", "industries", "interviewed", "outcome", "proletariat", 
"stenosis", "Macmillan", "calories", "connective", "evolutionary", 
"Someone", "abnormalities", "grams", "specialist", "spectra", 
"wavelength", "cortex", "metabolic", "skeletal", "hydroxide", 
"mobilization", "output", "potentials", "Symposium", "Telephone", 
"formulation", "frequencies", "mucosa", "optimistic", "telephone", 
"volts", "Ballance", "Burma", "bacilli", "carbohydrate", "dissociation", 
"handicapped", "metabolism", "Marx", "bacillus", "bacterial", 
"reflexes", "technique", "trauma", "dosage", "oriented", "negligible", 
"standardized", "vectors", "Biol", "Environment", "conceptual", 
"capitalism", "dimensional", "micro", "Economics", "Korean", 
"intravenous", "minimize", "interstate", "spatial", "Housing", 
"Oklahoma", "baseball", "cultures", "shortage", "economics", 
"perceptual", "voltage", "Seattle", "Tokyo", "transformer", "Sudan", 
"hydrolysis", "impedance", "motors", "awareness", "immune", "toxicity", 
"chromosomes", "coastal", "enzyme", "enzymes", "golf", "programs", 
"Ltd", "complexes", "environmental", "torque", "Korea", "functioning", 
"program", "edema", "lymphocytes", "sulfate", "sulfur", "Nietzsche", 
"chromosome", "gasoline", "involvement", "neurons", "Argentina", 
"adrenal", "anemia", "input", "stressed", "unemployment", "infections", 
"nearby", "proteins", "Kenya", "Manila", "Nigeria", "Philippines", 
"Rico", "automobile", "electrons", "interface", "supposedly", 
"Philippine", "anesthesia", "automobiles", "ecological", "myocardial", 
"overseas", "syndrome", "viewpoint", "Aires", "Computer", "Manchuria", 
"Shri", "amino", "electron", "financed", "questionnaire", "Roosevelt", 
"normative", "radioactive", "receptors", "vocational", "Radio", 
"antibodies", "cholesterol", "concentrations", "insofar", "ions", 
"radio", "receptor", "Marxism", "Therapy", "antibody", "hypertension", 
"layout", "occupational", "regulatory", "asset", "electronic", 
"intellectuals", "psychotherapy", "therapy", "Taft", "turbine", 
"activated", "activation", "antigen", "catalyst", "financing", 
"intake", "motivation", "literacy", "motivated", "antigens", 
"feminist", "Freud", "hormone", "hormones", "aircraft", "optimal", 
"pragmatic", "Inc", "appraisal", "cinema", "movies", "Planning", 
"amplifier", "bombing", "movie", "vitamin", "Allies", "basically", 
"bombs", "container", "meaningful", "Marketing", "Soviet", "Soviets", 
"coverage", "submarine", "viruses", "wartime", "Allied", "Czechoslovakia", 
"Lenin", "airplane", "gel", "genes", "industrialization", "manpower", 
"nationalism", "placement", "sector", "Gandhi", "Iraq", "executives", 
"grid", "postwar", "processing", "sponsored", "turnover", "Personnel", 
"Yugoslavia", "skills", "Czech", "Hoover", "broadcasting", "psychiatric", 
"Evaluation", "creativity", "insulin", "ratings", "television", 
"Hitler", "Hollywood", "Indonesia", "Score", "livestock", "objectives", 
"organizational", "techniques", "Stalin", "factual", "operational", 
"outcomes", "trends", "quantum", "semantic", "Nazi", "airport", 
"beft", "Reich", "behaviors", "documentation", "gene", "global", 
"Nazis", "counseling", "implemented", "behavioral", "conditioning", 
"feedback", "monitoring", "therapist", "ideology", "implementation", 
"technological", "Deal", "Marxist", "ideological", "businessmen", 
"nonetheless", "Thailand", "polymer", "Pakistan", "Axis", "Eisenhower", 
"interpersonal", "processed", "priorities", "inputs", "computer", 
"programming", "Truman", "Vietnam", "rocket", "reactor", "video", 
"Vietnamese", "Israeli", "uranium", "Mao", "computers", "hon", 
"structured", "Asian", "Taiwan", "Nuclear", "infrastructure", 
"digital", "Eds", "algorithm", "strategies", "caufe", "laser", 
"software", "alfo", "guidelines", "confidered", "fuck", "simulation", 
"Castro", "likewife", "prefent", "Kennedy", "constraints", "fince", 
"fome", "confequently", "confrontation", "defire", "expertise", 
"faid", "falfe", "fecond", "fhall", "fhould", "fituation", "fliould", 
"laft", "occafion", "perfon", "pleafe", "elfe", "fays", "fent", 
"Perfon", "Perfons", "caft", "faw", "lofe", "paft", "fettled", 
"blacks", "database", "Environmental", "Senfe", "funding", "pollution", 
"technologies", "options", "Lett", "Internet", "gender", "imaging", 
"menu")

predictors = as.character(1760:2000)

flagWordids(predictors)

date()
z = dbGetQuery(
  melville,
  "SELECT word1,year,books from 1grams JOIN wordsheap ON 1grams.word1 = wordsheap.casesens 
  WHERE year > 1800 AND year <= 2000 and wflag=1"
  )
date()
totals = dbGetQuery(
  melville,
  "SELECT year,books from 1grams WHERE word1='the'"
  )  

z$books = as.numeric(z$books)

tabbed = xtabs(books~year+word1,z)

tabbed = tabbed/totals$books[match(rownames(tabbed),totals$year)]

  
#density = apply(tabbed,2,function(col) {col/sum(col)})
smoothed = apply(tabbed,2,function(col) {loess(col~as.numeric(rownames(tabbed)),span=.5)$fitted})
smoothed[smoothed<=0.001] = 0.001
rownames(smoothed) = rownames(tabbed)

plot(rownames(smoothed),smoothed[,200],type='l')
year = sample(1800:2000,1)
dbGetQuery(melville,"UPDATE catalog SET bflag=0")
dbGetQuery(melville,paste("UPDATE catalog  SET bflag=1 WHERE alanguage='eng' AND nwords > 25000 AND year=",
  year," 
  ORDER BY RAND() LIMIT 1"))
core_search = list(
      method = 'counts_query',
      words_collation = 'Flagged',
      groups=list('words1.word as w1'),      
      search_limits = 
        list(
          list(
            'word' = list('Kennedy'),
            'bflag' = list(1)
            )
    )
  )  
exampleBook = dbGetQuery(melville,APIcall(core_search))
test = smoothed[,tolower(colnames(smoothed))==colnames(smoothed)]
missing = as.numeric(!colnames(test) %in% exampleBook$w1)
likelihood = t(abs(t(test)-missing))

plot(rownames(likelihood),apply(likelihood,1,prod),type='l',xlim=c(1800,2000))
p = dbGetQuery(melville,"SELECT author,authorbirth,workyear,title,year,ocaid FROM open_editions WHERE bookid = (SELECT bookid FROM catalog WHERE bflag=1)")
abline(v=p$year,col='red',lwd=3,lty=2)  
p
  require(zoo)

  
  
edit(as.vector(changes[!duplicated(changes$word),]$word))
  