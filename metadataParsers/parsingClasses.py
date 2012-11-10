#!/usr/bin/python

import re
import os

"""
These are classes that define types of strings we might want to use with Bookworm objects.
For all of them, there are various different formats that the data might come in:
for instance, a [name] may have a 'first' and a 'last' characteristic that would be nice to get.
This stuff must exist out there somewhat, but I'm bad about generally creating things from scratch.
Some aspects (like to pull the gender for a name) are pretty original, although it's something
to build them out.
"""


class ocaid():
    #An id from the Internet Archive.
    #Might be extended to work with other things we want to coerce to a pairtree structure and back.
    #The class is to make it easy to switch between a directory-oriented, pairtree structure (basically)
    #and the raw names we might use with that.

    def __init__(self,obj):
        #This lets you put in a file structure with or without the slashes.
        obj = re.sub("/","",obj)
        obj = re.sub("\.txt","",obj)
        self.raw = obj

    def fileLocation(self, length=2):
        return "/".join([self.raw[i:i+length] for i in range(0, len(self.raw), length)]) + ".txt"

    def onlineLocation(self):
        return "http://archive.org/download/" + self.raw + "/" + self.raw + "_djvu.txt"

    def raw(self):
        #Probably not necessary, but just for constancy of methods
        return(self.raw)

    def homeDirectory(self):
        return re.sub("/[^/]*txt$","",self.fileLocation())


class LCClass():
    def __init__(self, string):
        self.string = string
    def lcSplit(self):
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
class date():
    def __init__(self,string):
        self.string = string
    def extract_date(self):
        years = re.findall("\d\d\d\d",self.string)
        if(years):
            return years[0]
        else:
      return "NULL"

#name inherits from string, but lets you pull first or last names off.                                                                              
class name():
  def __init__(self,string):
    self.string = string
  def firstName(self):
    pass
  def lastName(self):
    pass
  def genderize(self):
    first = self.firstName()
    pass

