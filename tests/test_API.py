# -*- coding: utf-8 -*-

import unittest
import bookwormDB
import bookwormDB.CreateDatabase
from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
import logging
import os
from subprocess import call as call
import sys
import json
from setup import setup_bookworm, setup_bookworm_unicode

class Bookworm_SQL_Creation(unittest.TestCase):

    def test_bookworm_files_exist(self):
        bookworm = bookwormDB.CreateDatabase.BookwormSQLDatabase("federalist_bookworm")
        db = bookworm.db
        db.query("USE federalist_bookworm")
        wordCount = db.query("SELECT SUM(nwords) FROM fastcat").fetchall()[0][0]
        # This should be 212,081, but I don't want the tests to start failing when
        # we change the tokenization rules or miscellaneous things about encoding.
        self.assertTrue(wordCount>100000)
        """
        Then we test whether the API can make queries on that bookworm.
        """
        
    def test_API(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{},
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"return_json"
        }
        
        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==5)

    def test_adding_metadata_to_bookworm(self):
        """
        Build out some dummy metadata: label the difference
        between even and odd paragrahs.
        """
        
        from bookwormDB.manager import BookwormManager
        manager = BookwormManager(database="federalist_bookworm")

        # Create a phony derived field to test metadata supplementing
        newMetadata = open("/tmp/test_bookworm_metadata.tsv","w")
        newMetadata.write("paragraphNumber\toddness\n")
        def even_even(number):
            if number % 2 == 0:
                return "even"
            return "odd"
                
        for n in range(500):
            newMetadata.write("%d\t%s\n" %(n,even_even(n)))

        class Dummy:
            """
            Just quickly create a namespace to stand in for the command-line args.
            """
            key = "paragraphNumber"
            format = "tsv"
            file = "/tmp/test_bookworm_metadata.tsv"
            field_descriptions = None # Test the guessing at field_descriptions while we're at it

        import os
        manager.add_metadata(Dummy)

        """
        And then we test if that can be retrieved
        """

        query = {
                "database":"federalist_bookworm",
                "search_limits":{},
                "counttype":"TextCount",
                "groups":["oddness"],
                "method":"return_json"
        }
        
        SQLAPIcall(query)
        m = json.loads(SQLAPIcall(query).execute())
        # Even or odd is one of two things.
        self.assertTrue(len(m)==2)
        
        # Since the first paragraph is odd,
        # there should be more of those.
        
        self.assertTrue(m['odd'][0]>=m['even'][0])
        
    def test_case_sensitivity(self):
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["the"]},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Sensitive",
                "method":"return_json"
        }

        SQLAPIcall(query)
        val1 = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(val1[0] > 0)

        query["words_collation"] = "Case_Insensitive"        

        SQLAPIcall(query)        
        val2 = json.loads(SQLAPIcall(query).execute())
        # The words ('The','the') appear more often than ('the') alone.
        self.assertTrue(val2[0] > val1[0])


    def test_case_insensitivity_works_without_search_term(self):
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["hOwEvEr"]},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Insensitive",
                "method":"return_json"
        }
        SQLAPIcall(query)
        val1 = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(val1[0] > 0)

    def test_unicode_search_term(self):
        query = {
                "database":"unicode_test_bookworm",
                "search_limits":{"word":[u"ᎾᏍᎩ"]},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Insensitive",
                "method":"return_json"
        }
        SQLAPIcall(query)
        val1 = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(val1[0] > 0)

    def test_various_unicode_cases(self):
        # There's a 'description_' for each individual item.
        catalog_location = sys.path[0] + "/test_bookworm_files_unicode/jsoncatalog.txt"
        cases = [json.loads(line)["description_"] for line in open(catalog_location)]       
        for case in cases:
            query = {
                "database":"unicode_test_bookworm",
                "search_limits":{"description_":case},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Insensitive",
                "method":"return_json"
                }
            SQLAPIcall(query)
            val1 = json.loads(SQLAPIcall(query).execute())
            self.assertTrue(val1[0] > 0)

    def test_asterisks_in_search_limits(self):
        """
        The following two queries should, by definition, produce the same result.
        """
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["on"],"author":["HAMILTON"]},
                "compare_limits":{"word":["on"]},                
                "counttype":"WordsPerMillion",
                "groups":[],
                "method":"return_json"
        }        
        val1 = json.loads(SQLAPIcall(query).execute())

        query = {
            "database":"federalist_bookworm",
            "search_limits":{"word":["on"],"*author":["HAMILTON"]},
            "counttype":"WordsPerMillion",
            "groups":[],
            "method":"return_json"
            }
        val2 = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(val1[0] == val2[0])        

        
"""        
class SQLConnections(unittest.TestCase):
    
        

    def test_dunning(self):
        query = {
            "database":"federalist",
            "search_limits":{"author":"Hamilton"},
            "compare_limits":{"author":"Madison"},
            "counttype":"Dunning",
            "groups":["unigram"],
            "method":"return_json"
        }
        

        try:
            #dbbindings.main(query)
            worked = True
        except:
            worked = False

        self.assertTrue(worked)
"""

        
if __name__=="__main__":
    # The setup is done without verbose logging; any failure
    # causes it to try again.
    logging.basicConfig(level=40)
    try:
        setup_bookworm()
        setup_bookworm_unicode()
    except:
        logging.basicConfig(level=10)
        setup_bookworm()
        setup_bookworm_unicode()        
    logging.basicConfig(level=10)    
    unittest.main()
