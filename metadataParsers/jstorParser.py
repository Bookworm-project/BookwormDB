#!/usr/bin/py

import re
import codecs
from xml.dom.minidom import parse,parseString

metadata_fields = ['month','day','year','journalabbrv','journalid','headid','title','languages','type','journaltitle','volume','authors','issueid','issn','fpage','lpage']


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
            working = jstorID(p)
            working.writeText()
            working.writeMetadata()
            
class jstorID:
    def __init__(self,string):
        self.id = string
        self.open_xml()
        self.get_metadata()
    def open_xml(self):
        self.dom = parse('../../raw/' + self.id + '.xml')
        self.text = self.dom.getElementsByTagName('text')
        self.textstring = "\n".join([t.childNodes[0].nodeValue for t in self.text])
        self.textstring = self.textstring.encode('utf-8')
    def get_metadata(self):
        self.metadata = dict()
        for item in metadata_fields:
            try:
                self.metadata[item] = self.dom.getElementsByTagName(item)[0].childNodes[0].nodeValue
            except:
                self.metadata[item] = ''
    def writeText(self):
        output = open('../../texts/' + self.id + '.txt','w')
        output.write(self.textstring)
        output.close()
    def writeMetadata(self):
        self.get_metadata()
        metadata = open ('../../metadata/main.txt','a')
        metadata.write(self.id + '\t' + self.metadata['year'])     

Export().exportall()
