import pandas
import json
import copy
import threading
import time
from collections import defaultdict

def hostlist(dblist):
    #This could do something fancier, but for now we look by default only on localhost.
    return ["localhost"]*len(dblist)

class childQuery(threading.Thread):
    def __init__(self,dictJSON,host):
        super(SummingThread, self).__init__()
        self.dict = json.dumps(dict)
        self.host = host
        
    def runQuery(self):
        #make a webquery, assign it to self.data
        url = self.host + "/cgi-bin/bookwormAPI?query=" + self.dict

    def parseResults(self):
        pass
        #return json.loads(self.data)

    def run(self):
        self.runQuery()

def flatten(dictOfdicts):
    """
    Recursive function: transforms a dict with nested entries like
    foo["a"]["b"]["c"] = 3
    to one with tuple entries like
    fooPrime[("a","b","c")] = 3
    """
    output = []
    for (key,value) in dictOfdicts.iteritems():
        if isinstance(value,dict):
            output.append([(key),value])
        else:
            children = flatten(value)
            for child in children:
                output.append([(key,) + child[0],child[1]])
    return output

def animate(dictOfTuples):
    """
    opposite of flatten
    """

    def tree():
        return defaultdict(tree)

    output = defaultdict(tree)

    

def combineDicts(master,new):
    """
    instead of a dict of dicts of arbitrary depth, use a dict of tuples to store.
    """

    for (keysequence, valuesequence) in flatten(new):
        try:
            master[keysequence] = map(sum,zip(master[keysequence],valuesequence))
        except KeyError:
            master[keysequence] = valuesequence
    return dict1
        
class MetaQuery(object):
    def __init__(self,dictJSON):
        self.outside_outdictionary = json.dumps(dictJSON)
        
    def setDefaults(self):
        for specialKey in ["database","host"]:
            try:
                if isinstance(self.outside_dictionary[specialKey],basestring):
                    #coerce strings to list:
                    self.outside_dictionary[specialKey] = [self.outside_dictionary[specialKey]]
            except KeyError:
                #It's OK not to define host.
                if specialKey=="host":
                    pass
            
        if 'host' not in self.outside_dictionary:
            #Build a hostlist: usually just localhost a bunch of times.
            self.outside_dictionary['host']  = hostlist(self.outside_dictionary['database'])

        for (target, dest) in [("database","host"),("host","database")]:
            #Expand out so you can search for the same database on multiple databases, or multiple databases on the same host.
            if len(self.outside_dictionary[target])==1 and len(self.outside_dictionary[dest]) != 1:
                self.outside_dictionary[target] = self.outside_dictionary[target] * len(self.outside_dictionary[dest])
            

    def buildChildren(self):
        desiredCounts = []
        for (host,dbname) in zip(self.outside_dictionary["host"],self.outside_dictionary["database"]):
            query = copy.deepcopy(self.outside_dictionary)
            del(query['host'])
            query['database'] = dbname
            
            desiredCounts.append(childQuery(query,host))
        self.children = desiredCounts

    def runChildren(self):
        for child in self.children:
            child.start()

    def combineChildren(self):
        complete = dict()
        while (threading.enumerate()):
            for child in self.children:
                if not child.is_alive():
                    complete=combineDicts(complete,child.parseResult())
            time.sleep(.05)

    def return_json(self):
        pass


    
