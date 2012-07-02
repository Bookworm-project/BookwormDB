#!/usr/bin/python

def update_Porter_stemming(): #We use stems occasionally.                                        
    print "Updating stems from Porter algorithm..."
    from nltk import PorterStemmer
    stemmer = PorterStemmer()
    cursor.execute("""SELECT word FROM words""")
    words = cursor.fetchall()
    for local in words:
        word = ''.join(local)
        #Apostrophes have the save stem as the word, if they're included
        word = re.sub("'s","",word)
        if re.match("^[A-Za-z]+$",word):
            query = """UPDATE words SET stem='""" + stemmer.stem(''.join(local)) + """' WHERE word='""" + ''.join(local) + """';"""
            z = cursor.execute(query)
