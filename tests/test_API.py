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

def setup_bookworm():
    """
    Creates a test bookworm. Removes any existing databases called "federalist_bookworm"
    """
    logging.info("\n\nTESTING BOOKWORM CREATION\n\n")
    import MySQLdb
    from warnings import filterwarnings
    filterwarnings('ignore', category = MySQLdb.Warning)

    import bookwormDB.configuration
    os.chdir(sys.path[0] + "/test_bookworm_files")
    bookwormDB.configuration.create(ask_about_defaults=False,database="federalist_bookworm")

    try:
        db.query("DROP DATABASE federalist_bookworm")
    except MySQLdb.OperationalError as e:
        if e[0]==1008:
            pass
        else:
            raise
    except Exception, e:
        """
        This is some weird MariaDB exception. It sucks that I'm compensating for it here.
        """
        if e[0]=="Cannot load from mysql.proc. The table is probably corrupted":
            pass
        else:
            logging.warning("Some mysterious error in attempting to drop previous iterations: just try running it again?")
            
    call(["bookworm --log-level warning build all"],shell=True,cwd=sys.path[0] + "/test_bookworm_files")

def setup_bookworm_unicode():
    """
    Creates a test bookworm. Removes any existing databases called "unicode_test_bookworm"
    """
    logging.info("\n\nTESTING BOOKWORM CREATION\n\n")
    import MySQLdb
    from warnings import filterwarnings
    filterwarnings('ignore', category = MySQLdb.Warning)

    import bookwormDB.configuration
    os.chdir(sys.path[0] + "/test_bookworm_files_unicode")
    bookwormDB.configuration.create(ask_about_defaults=False,database="unicode_test_bookworm")

    try:
        db.query("DROP DATABASE unicode_test_bookworm")
    except MySQLdb.OperationalError as e:
        if e[0]==1008:
            pass
        else:
            raise
    except Exception, e:
        """
        This is some weird MariaDB exception. It sucks that I'm compensating for it here.
        """
        if e[0]=="Cannot load from mysql.proc. The table is probably corrupted":
            pass
        else:
            logging.warning("Some mysterious error in attempting to drop previous iterations: just try running it again?")
            
    call(["bookworm --log-level warning build all"],shell=True,cwd=sys.path[0] + "/test_bookworm_files_unicode")
    

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
        self.assertEqual(len(m),5)


    def test_multiword_search(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["on","upon"]},
                "counttype":"TextPercent",
                "method":"return_json",
                "groups": []
        }
        
        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(m[0] > 33)

    def test_ne_with_one_entry(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"return_json"
        }
        
        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==4)

    def test_ne_with_two_entries(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON","DISPUTED"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"return_json"
        }

        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==3)


    def test_ne_with_two_entries(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON","DISPUTED"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"return_json"
        }

        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==3)


    def test_or_with_two_entries(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "$or": [
                        {"author": ["HAMILTON"]},
                        {"author": ["DISPUTED"]}
                    ]
                },
                "counttype":"TextCount",
                "groups":["author"],
                "method":"return_json"
        }

        m = json.loads(SQLAPIcall(query).execute())
        self.assertEqual(len(m),2)

    def test_lte_and_gte(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "fedNumber":{"$lte":10,"$gte":5}
                },
                "counttype":"TextCount",
                "groups":["fedNumber"],
                "method":"return_json"
        }

        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==6)
        
    def test_and_with_two_entries(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "$and": [
                        {"author": ["HAMILTON"]},
                        {"fedNumber":[40]}
                    ]
                },
                "counttype":"TextCount",
                "groups":["author"],
                "method":"return_json"
        }

        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==0)
        
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
