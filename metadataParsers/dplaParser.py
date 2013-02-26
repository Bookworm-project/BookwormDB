#!/usr/bin/python
import json
import re
import os
from random import random

class dplaFile:
    """
    This is initialized with the location of a DPLA mongoDB dump file.
    """

    def __init__(self,fileloc):
        self.file = open(fileloc,'r')

    def getTopKeys(self,max=100000,sampling = .01):
        """
        Just debugging: sees what metadatafields are being generated
        that we'll have to work with. stops after looking at 10000 out of the first 1000000 files
        """
        counts = dict()
        i = 0
        while i<max:
            if random() < sampling:
                i += 1
                myline = dplaLine(self.file.readline())
                myline.makeOutput()
                for key in myline.output.keys():
                    try: counts[key] = counts[key] + 1
                    except: counts[key] = 1
        countKeys = counts.keys()
        countKeys.sort()
        for count in countKeys:
            print str(count) + "\t" + str(counts[count])

    def writeOutputs(self,output="../../metadata/jsoncatalog.txt",max=(2**8)**3):
        """
        Iterate through and pull out the top keys
        """


        dir = os.path.dirname(output)

        if not os.path.exists(dir):
            os.makedirs(dir)
        print output

        output = open(output,'w')

        i = 0
        for line in self.file:
            i = i+1
            """
            Write the output metadata
            """
            imported = dplaLine(line)
            dumpt = json.dumps(imported.makeOutput())
            output.write(dumpt+"\n")

            """
            Genereate some phony text to use the basis for the Bookworm.
            """
            filename = "../../texts/raw/" + imported.output['filename'] + ".txt"
            try:
                fileout = open(filename,'w')
            except:
                dir = os.path.dirname(filename)
                os.makedirs(dir)
                fileout = open(filename,'w')
            fileout.write(imported.fakeText())
            if i % 10000==0:
                print i
            if i >= max:
                break
        output.close()

        
class dplaLine:
    """
    This parses out a single line of a DPLA mongodb export into a flatter JSON object to load into Bookworm.
    It might lose something valuable: that's to check with the DPLA people about.
    """
    def __init__(self,string):
        myjson = json.loads(string.decode('utf-8'))
        self.id = myjson['_id']
        self.dpla = myjson['dpla']
        #self.local = myjson['local']

    def makeOutput(self):
        self.output = dict()
        for key in self.dpla.keys():
            vals = breakDownDplaField(key,self.dpla[key])
            self.output = dict(self.output.items() + vals.items())

        id = self.output['dpla_id']
        self.output['filename'] = "/".join([id[:2],id[2:4],id])
        self.output['searchstring'] = self.output.get('title','')

        lookups = {'call_number_LC_call_number_value':"lcClassification", 'contributor_id':'contributor_id', 'contributor_name':'contributor_name', 'contributor_record_id':'contributor_record_id', 'creator_creator_name':"author", 'dataset_id':"dataset_id", 'date_publication_date_expression':"publication", 'description':"description", 'dpla_id':"dpla_id", 'identifier_ISBN_id':"ISBN", 'identifier_LCCN_id':"LCCN", 'identifier_OCLC_id':'OCLC', 'language':'language', 'location_place_of_publication_name':"publicationPlace", 'location_place_of_publication_relationship':"placeType", 'publisher':'publisher', 'resource_type':'type', 'subject':'subject', 'title':'title',"filename":"filename","searchstring":"searchstring"}

        returnValue = dict()
        for lookup in lookups.keys():
            try:
                returnValue[lookups[lookup]] = self.output[lookup]
            except KeyError:
                pass
 
        for shouldBeSoloValue in ['publication','LCCN','OCLC']:
            try:
                returnValue[shouldBeSoloValue] = returnValue[shouldBeSoloValue][0]
            except KeyError:
                pass

        return(returnValue)
            
    def fakeText(self):
        """
        we don't have full text files, but we can make them out of the keywords
        self.makeOutput() must be run first.
        """

        keywords = ""
        for field in ["title","creator_creator_name"]: #Currently only searching titles
            try:
                keywords = keywords + " " + self.output[field]
            except KeyError:
                pass
            except TypeError:
                for item in self.output[field]:
                    keywords = keywords + " " + item
        return keywords.encode("UTF-8")
    
def breakDownDplaField(key,field):
    #to flatten the hierarchy for database purposes, I'm just collapsing the various keys into '_' separated identifiers
    returnVal = dict()
    if isinstance(field,basestring):
        returnVal[key] = field
    if isinstance(field,dict):
        for subfield in field.keys():
            returnVal[key+"_"+subfield] = field[subfield]
    if isinstance (field,list) and len(field) > 0:
        if isinstance (field[0],basestring):
            returnVal[key] = [item for item in field]
        if isinstance (field[0],dict):
            for subfield in field:
                for classifierType in ["type",'relationship','place of publication']:
                    try:
                        descriptor = re.sub("_","",subfield[classifierType])
                    except KeyError:
                        pass
                try:
                    m = descriptor    
                except:
                    raise
                for subfieldkey in subfield.keys():
                    if subfieldkey not in ['type','relationship','place of publication']:
                        try:
                            returnVal[re.sub(" ","_",'_'.join([key,descriptor,subfieldkey]))].append(subfield[subfieldkey])
                        except KeyError:
                            returnVal[re.sub(" " ,"_",'_'.join([key,descriptor,subfieldkey]))] = [subfield[subfieldkey]]
    return returnVal


if __name__=='__main__':
    file = dplaFile("../../mongoexport_dpla_item.harvard_edu")
    file.writeOutputs(max=10000000000)
