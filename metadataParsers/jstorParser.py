#!/usr/bin/py

import re
import codecs
from xml.dom.minidom import parse,parseString
import json

metadata_fields = ['year','month','day','journalabbrv','journalid','headid','title','languages','type','journaltitle','volume','authors','issueid','issn','fpage','lpage']

metadatafile = open ('../../metadata/jsoncatalog.txt','a')

class Export:
    def __init__(self):
        self.filenames = []
        filehandle = open('../../filenames.txt')
        for p in filehandle.readlines():
            mystring = p.split('\t')[0]
            mystring = re.sub('.xml\n*','',mystring)
            self.filenames.append(mystring)
    def exportall(self):
        for p in self.filenames:
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
        self.dom = parse('../../raw/' + self.id + '.xml')
        self.text = self.dom.getElementsByTagName('text')
        self.textstring = "\n".join([t.childNodes[0].nodeValue for t in self.text])
        #self.textstring = self.textstring.encode('utf-8')
    def get_metadata(self):
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
                self.metadata[item] = ""
    def writeText(self):
        output = open('../../texts/' + self.id + '.txt','w')
        output.write(self.textstring)
        output.close()
    def writeMetadata(self):
        self.get_metadata()
        self.metadata["id"] = str(self.id)
        self.metadata["searchstring"] = self.metadata["title"] + "," + self.metadata["journaltitle"] + "<a href=www.jstor.org/" + re.sub("_","/",self.id) + ">" + read + "</a>"
        self.metadatafile.write(json.dumps(self.metadata))
        self.metadatafile.write("\n")

Export().exportall()
