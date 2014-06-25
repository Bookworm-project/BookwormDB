#!/usr/bin/python
import roman
from xml.dom.minidom import parseString
import re
import json
import sys
import time
import os 

def parse(paper):
    out = dict()
    for metadataField in ["title","author"]:
        out[metadataField] = paper.getElementsByTagName(metadataField)[0].childNodes[0].data
    out["paragraphs"] = [n.firstChild.data for n in paper.getElementsByTagName("text")[0].getElementsByTagName("p")]
    out["words"] = words(out["paragraphs"])
    return out


def descend(thisNode,stackOfTags=[],seenSoFar=dict(),depth=1):
    """
    A recursive function to go down the XML tree.
    The tricky part is that some metadata is stored in the text: in particular, 
    the speaker of a speech and the title of an act. So what's complication

    """
    if thisNode.nodeType==1:
        if thisNode.nodeName in ["TITLE","SPEAKER"]:
            lastSeen = stackOfTags[-1]
            key = stackOfTags[-1].keys()[0]
            try:
                stackOfTags[-1] = {key:thisNode.childNodes[0].data}
            except:
                pass
        elif thisNode.nodeName in ["#text"]:
            pass
        else:
            stackOfTags.append({thisNode.nodeName:thisNode.firstChild.nodeValue})

    if thisNode.nodeType in [1,9]:
        # 1 is an element node: 9, also covered, is the main document root here.
        children = thisNode.childNodes
        for child in children:
            seenSoFar = descend(child,stackOfTags,seenSoFar,depth+1)

    if thisNode.nodeType==3:
        #3 is a text node: that's when we really dump out some text.
        thisDocument = {}
        for element in stackOfTags:
            for key in element.keys():
                #This should only be one deep ever....
                thisDocument[key] = element[key]

        thisDocument["textType"]   = stackOfTags[-1].keys()[0]

        # A tuple gives a stable way to represent this dict
        
        try:
            del(thisDocument["LINE"])
        except KeyError:
            pass
        
        key = tuple(sorted(thisDocument.iteritems()))

        try:
            seenSoFar[key] = seenSoFar[key] + " " + thisNode.data
        except KeyError:
            seenSoFar[key] = thisNode.data

    return seenSoFar

class xmlParser(object):
    def __init__(self,filename):
        self.filename=filename
        self.string = open(filename).read()
        self.dom = parseString(self.string)

    def markup(self):
        all = descend(self.dom,stackOfTags=[],seenSoFar=dict(),depth=1)
        returnable = []
        for key in all:
            line = dict(key)
            line["textString"] = all[key]
            if re.search(r"\w+",line["textString"]):
                try:
                    line["actNumber"] = roman.fromRoman(re.findall(r"(?:ACT|Act) +(\w+)",line["ACT"])[0])
                except KeyError:
                    pass
                try: 
                    line["sceneNumber"] = roman.fromRoman(re.findall(r"(?:SCENE|Scene) +([IXVL]+)",line["SCENE"])[0])
                except KeyError:
                    pass
                except:
                    pass
                returnable.append(line)
        return returnable
        
    def printOut(self):
        jsonout = open("../../../files/metadata/jsoncatalog.txt","a")
        textout = open("../../../files/texts/input.txt","a")
        i=1
        for item in self.markup():
            ID = filename+"-" + str(i)
            item["filename"] = ID
            jsonout.write(json.dumps(item) + "\n")
            textout.write(ID + "\t" + re.sub("[\n\r]","",item["textString"]) + "\n")
            i += 1
        jsonout.close()
        textout.close()

if __name__=="__main__":
    jsonout = open("../../../files/metadata/jsoncatalog.txt","w")
    textout = open("../../../files/texts/input.txt","w")
    jsonout.close()
    textout.close()

    for filename in os.listdir("../../../files/raw"):
        print filename
        dom = xmlParser("../../../files/raw/" + filename)
        dom.printOut()
