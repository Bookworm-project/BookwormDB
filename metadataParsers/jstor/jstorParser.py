#!/usr/bin/py

import re
#Needs codecs to work with unicode characters properly
import codecs
from xml.dom.minidom import parse,parseString
import json

#These are the names of the metadata fields that it will look for.
metadata_fields = ['month','day','year','journalabbrv','journalid','headid','title','languages','type','journaltitle','volume','authors','issueid','issn','fpage','lpage']
metadatafile = open ('../../../metadata/jsoncatalog.txt','a')

class journals(dict):
    def load(self):
        reading = open("JournalData.txt")
        for line in reading:
            line = re.sub("\n","",line)
            splitted = line.split("\t")
            splitted = [re.sub("'$","",split) for split in splitted]
            splitted = [re.sub("^'","",split) for split in splitted]
            self[splitted[11]] = splitted[18].split(";")


class Export:
    def __init__(self):
        self.filenames = []
        #You have to to feed it a list of files---this could also be retrieved by getting a directory listing.
        filehandle = open('../../../filenames.txt')
        for p in filehandle.readlines():
            mystring = p.split('\t')[0]
            mystring = re.sub('.xml\n*','',mystring)
            self.filenames.append(mystring)
    def exportall(self):
        for p in self.filenames:
            #first it cues up the object below by reading in the data:
            #This is where it calls the attributes of the jstorID object to write things out.
            #To avoid writing all the texts, you'd just need to an 'if' here: for example
            #if working.metadata['journalabbrv']=='royalsocietyjournal'
            working = jstorID(p,metadatafile)
            #working.writeText()
            working.writeMetadata()
            
class jstorID():
    def __init__(self,string,metadatafile):
        self.id = string
        self.metadatafile=metadatafile
        self.open_xml()
        self.get_metadata()
    def open_xml(self):
        self.dom = parse('../../../raw/' + self.id + '.xml')
        #Here's where the text comes from--it reads in the XML node stored under 'text', and then writes that into
        #an attribute 'textstring' of this object that can be exported.
        self.text = self.dom.getElementsByTagName('text')
        self.textstring = "\n".join([t.childNodes[0].nodeValue for t in self.text])
        #self.textstring = self.textstring.encode('utf-8')
    def get_metadata(self):
        #Here's where the metadata comes out.
        self.metadata = dict()
        for item in metadata_fields:
            try:
                self.metadata[item] = self.dom.getElementsByTagName(item)[0].childNodes[0].nodeValue
                #self.metadata[item] = self.metadata[item].encode('utf-8')
                self.metadata[item] = re.sub("\n$","",self.metadata[item])
                self.metadata[item] = re.sub(" +$","",self.metadata[item])
                self.metadata[item] = re.sub("\n","",self.metadata[item])
                self.metadata[item] = re.sub("\t","",self.metadata[item])
            except:
                #If it doesn't have that metadata field, we just take a blank line instead.
                self.metadata[item] = ''
        try:
            self.metadata['discipline'] = disciplines[self.metadata['journalabbrv']]
        except KeyError:
            pass
    def writeText(self):
        #Here it opens a new file in a specified text to write the place.
        output = open('../../../texts/raw/' + self.id + '.txt','w')
        output.write(self.textstring)
        output.close()
    def writeMetadata(self):
        self.get_metadata()
        self.metadata["id"] = str(self.id)
        self.metadata["filename"] = str(self.id)
        #There's no avoiding this sort of messiness, I think. It doesn't have to be buried so deep, though.
        self.metadata["searchstring"] = self.metadata["title"] + ", <i>" + self.metadata["journaltitle"] + "</i> <a href=www.jstor.org/" + re.sub("_","/",self.id) + ">read online</a>"
        self.metadatafile.write(json.dumps(self.metadata))
        self.metadatafile.write("\n")

#Finally, the line that actually runs everything.
disciplines=journals()
disciplines.load()
Export().exportall()
