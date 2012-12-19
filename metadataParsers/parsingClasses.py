#!/usr/bin/python

import re
import os
import decimal
"""
These are classes that define types of strings we might want to use with Bookworm objects.
For all of them, there are various different formats that the data might come in:
for instance, a [name] may have a 'first' and a 'last' characteristic that would be nice to get.
Where possible, we can use other applications for this (as, example, in the date class).
Some aspects (like to pull the gender for a name) are pretty original, although it's something
to build them out.
"""

def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    if isinstance(obj,int) or isinstance(obj,float) or isinstance(obj,decimal.Decimal):
        obj=unicode(str(obj),encoding)
    return obj


class ocaid():
    #An id from the Internet Archive.
    #Might be extended to work with other things we want to coerce to a pairtree structure and back.
    #The class is to make it easy to switch between a directory-oriented, pairtree structure (basically)
    #and the raw names we might use with that.

    def __init__(self,obj):
        #This lets you put in a file structure with or without the slashes.
        obj = re.sub(".*/","",obj)
        obj = re.sub("\.txt","",obj)
        self.string = obj

    def fileLocation(self, length=2,depth=2):
        return "/".join([self.string[i:i+length] for i in range(0, min([len(self.string),depth*length]), length)]) + "/" + self.string + ".txt"

    def oldfileLocation(self, length=2,depth=92):
        return "/".join([self.string[i:i+length] for i in range(0, min([len(self.string),depth*length]), length)]) + ".txt"

    def onlineLocation(self):
        return "http://archive.org/download/" + self.string + "/" + self.string + "_djvu.txt"

    def readerLocation(self):
        return("http://archive.org/stream/" + self.string)

    def homeDirectory(self):
        return re.sub("/[^/]*txt$","",self.fileLocation())

class LCClass():
    def __init__(self, string):
        self.string = string
    def split(self):
        lcclass = self.string.encode("ascii",'replace')
        #This regex defines an LC classification.
        mymatch = re.match(r"^(?P<lc1>[A-Z]+) ?(?P<lc2>\d+)", lcclass)
        if mymatch:
            returnt = {'lc0':lcclass[0],'lc1':mymatch.group('lc1'),'lc2':mymatch.group('lc2')}
            return returnt
        else:
            return(dict())

"""
This could do better at extracting months, etc, when they are available.
"""

#date lets you convert to the bookworm date format
#maybe build out to allow rounding to happen here? Billy wrote that code for LOC

from dateutil.parser import parse
class date():
    def __init__(self,string):
        self.string = string
    def extract_year(self):
        try:
            year = parse(self.string).year
            return(year)
        except:
            #This is super-kludgy, but it almost always works.
            #The parse function, on the other hand, is clean but
            #fails on things like "c. 1756" or "~1987"

            years = re.findall("\d\d\d\d",self.string)
            if(years):
                return years[0]
        return "NULL"

#name is imported from the parsenames package

