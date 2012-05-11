#!/usr/bin/py

import re
#Needs codecs to work with unicode characters properly
import codecs
from xml.dom.minidom import parse,parseString
import json

<<<<<<< HEAD
metadata_fields = ['year','month','day','journalabbrv','journalid','headid','title','languages','type','journaltitle','volume','authors','issueid','issn','fpage','lpage']
=======

#These are the names of the metadata fields that it will look for.
metadata_fields = ['month','day','year','journalabbrv','journalid','headid','title','languages','type','journaltitle','volume','authors','issueid','issn','fpage','lpage']
>>>>>>> 6ea30f6424ac968b1a033f9fc7d20ec2af29daff

metadatafile = open ('../../metadata/jsoncatalog.txt','a')


class Export:
    def __init__(self):
        self.filenames = []
        #You have to to feed it a list of files---this could also be retrieved by getting a directory listing.
        filehandle = open('../../filenames.txt')
        for p in filehandle.readlines():
            mystring = p.split('\t')[0]
            mystring = re.sub('.xml\n*','',mystring)
            self.filenames.append(mystring)
    def exportall(self):
        for p in self.filenames:
<<<<<<< HEAD
            working = jstorID(p,metadatafile)
            #working.writeText()
            working.writeMetadata()
            
class jstorID():
    def __init__(self,string,metadatafile):
=======
            #first it cues up the object below by reading in the data:
            working = jstorID(p)
            #This is where it calls the attributes of the jstorID object to write things out.
            #To avoid writing all the texts, you'd just need to an 'if' here: for exmle
            #if working.metadata['journalabbrv']=='royalsocietyjournal'
            working.writeText()
            working.writeMetadata()

#A jstorid is used as an object to iterate over. This clss is called thousands of times by the one "Export" instance you run.
class jstorID:
    def __init__(self,string):
>>>>>>> 6ea30f6424ac968b1a033f9fc7d20ec2af29daff
        self.id = string
        self.metadatafile=metadatafile
        self.open_xml()
        self.get_metadata()
    def open_xml(self):
        self.dom = parse('../../raw/' + self.id + '.xml')
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
<<<<<<< HEAD
                self.metadata[item] = ""
=======
                #If it doesn't have that metadata field, we just take a blank line instead.
                self.metadata[item] = ''
>>>>>>> 6ea30f6424ac968b1a033f9fc7d20ec2af29daff
    def writeText(self):
        #Here it opens a new file in a specified text to write the place.
        output = open('../../texts/' + self.id + '.txt','w')
        output.write(self.textstring)
        output.close()
    def writeMetadata(self):
        self.get_metadata()
        self.metadata["id"] = str(self.id)
        self.metadata["searchstring"] = self.metadata["title"] + "," + self.metadata["journaltitle"] + "<a href=www.jstor.org/" + re.sub("_","/",self.id) + ">" + read + "</a>"
        self.metadatafile.write(json.dumps(self.metadata))
        self.metadatafile.write("\n")

#Finally, the line that actually runs everything.
Export().exportall()
