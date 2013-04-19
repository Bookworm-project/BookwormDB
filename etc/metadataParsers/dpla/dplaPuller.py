#!/usr/bin/python

import json

def APIcall(dictOfParams,key):
    """
    This takes a url, and returns the json object from the request
    """
    #Convert dictOfParams to a string

    #build a url

    #post the request

    #handle the results

    return json.dumps(returnvalues)

class initialQuery:
    """
    The Query is a dict with keys corresponding to = limits on the search
    parameters for the API.
    """

    def __init__(self,query):
        self.query = query

    def pullResults(self,maxhits = 1):
        query  = self.updateQueryToNextPage(self.query)
        allEntries = []
        for i in xrange(maxhits):
            set = resultSet(APIcall(query))
            for entry in set:
                allEntries.append(entry)
            if set < 100:
                break

    def updateQueryToNextPage(self,query):
        if thishasnopagelimit:
            addapagelimit()
        else:
            incrementpagelimitby100()

class resultSet:
    """
    a grouping returned through an API call
    This is 100 items at a time, so many of these will
    be spawned by a single query.
    """
    def __init__(self,jsonvariables):
        self.apireturn = jsonvariables

    def separateEntries(self):
        self.items = []
        #entry will be more complicated than this.
        for entry in self.apireturn:
            self.items.append(entry)

class dplaField:
    def __init__(self,string):
        self.fieldname = string

    def translate(self):
        """
        Take the string 
        """
        pass

