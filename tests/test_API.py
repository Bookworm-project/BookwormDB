# -*- coding: utf-8 -*-

import pytest
import bookwormDB
from bookwormDB.general_API import DuckDBCall as DuckDBCall
from bookwormDB.builder import BookwormCorpus
from pathlib import Path
import logging
import os
import duckdb
from subprocess import call as call
import sys
import json
import pytest

@pytest.fixture(scope="session")
def federalist_bookworm(tmpdir_factory):
    path = tmpdir_factory.mktemp("ascii").join("federalist.duckdb")
    tmpdir = tmpdir_factory.mktemp("tmpdir")
    corp = BookwormCorpus(
        f"{path}",
        texts = Path('tests/test_bookworm_files/input.txt'),
        metadata = "tests/test_bookworm_files/jsoncatalog.txt",
        dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})    
    corp.build()
    con = duckdb.connect(str(path), read_only = True)
    return con

@pytest.fixture(scope="session")
def unicode_bookworm(tmpdir_factory):
    path = tmpdir_factory.mktemp("unicode").join("unicode.duckdb")
    tmpdir = tmpdir_factory.mktemp("tmpdir")
    corp = BookwormCorpus(
        f"{path}",
        texts = Path('tests/test_bookworm_files_unicode/input.txt'),
        metadata = "tests/test_bookworm_files_unicode/jsoncatalog.txt",
        dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})
    corp.build()
    con = duckdb.connect(str(path), read_only = True)
    return con

class Test_Bookworm_SQL_Creation():
    def test_nwords_populated(self, federalist_bookworm):
        wordCount = federalist_bookworm.query('SELECT SUM(nwords) FROM fastcat').fetchall()[0][0]
        # This should be about 212,081, but I don't want the tests to start failing when
        # we change the tokenization rules or miscellaneous things about encoding.
        assert wordCount > 200000
        """
        Then we test whether the API can make queries on that bookworm.
        """
        
    def test_fastcat_populated(self, federalist_bookworm):
        textCount = federalist_bookworm.query('SELECT COUNT(*) FROM fastcat').fetchall()[0][0]
        # This should be 212,081, but I don't want the tests to start failing when
        # we change the tokenization rules or miscellaneous things about encoding.
        assert textCount == 1333
        """
        Then we test whether the API can make queries on that bookworm.
        """
        
    def test_groups(self, federalist_bookworm):
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{},
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data", "format":"json"
        }
        
        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert len(m) == 5

    def test_multiword_search(self, federalist_bookworm):
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["on","upon"]},
                "counttype":"TextPercent",
                "method":"data", "format":"json",
                "groups": []
        }
        
        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert m[0] > 33

    def test_ne_with_one_entry(self, federalist_bookworm):
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data", "format":"json"
        }
        
        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert len(m)==4

    def test_ne_with_two_entries(self, federalist_bookworm):
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON","DISPUTED"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data", "format":"json"
        }

        m = json.loads(DuckDBCall(federalist_bookworm, query= query).execute())['data']
        assert len(m)==3


    def test_ne_with_two_entries(self, federalist_bookworm):
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON","DISPUTED"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data", "format":"json"
        }

        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert len(m)==3


    def test_or_with_two_entries(self, federalist_bookworm):
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
                "method":"data", "format":"json"
        }

        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert len(m) == 2

    def test_lte_and_gte(self, federalist_bookworm):
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "fedNumber":{"$lte":10,"$gte":5}
                },
                "counttype":"TextCount",
                "groups":["fedNumber"],
                "method":"data", "format":"json"
        }

        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())
        print(m)
        assert len(m['data'])==6
        
    def test_and_with_two_entries(self, federalist_bookworm):
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
                "method":"data", "format":"json"
        }

        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert len(m)==0
        
    def ftest_adding_metadata_to_bookworm(self):
        """
        Build out some dummy metadata: label the difference
        between even and odd paragrahs.
        """
        
        from bookwormDB.manager import BookwormManager
        manager = BookwormManager(database="federalist_bookworm")

        # Create a phony derived field to test metadata supplementing

        
        def even_even(number):
            if number % 2 == 0:
                return "even"
            return "odd"

        tmp_file = "{}/test_bookworm_metadata.tsv".format(sys.path[0])
        
        with open(tmp_file,"w") as newMetadata:
            newMetadata.write("paragraphNumber\toddness\n")                
            for n in range(500):
                newMetadata.write("%d\t%s\n" %(n,even_even(n)))
                
        class Dummy(object):
            """
            Just quickly create a namespace to stand in for the command-line args.
            """
            key = "paragraphNumber"
            format = "tsv"
            file = tmp_file
            # Test the guessing at field_descriptions while we're at it
            field_descriptions = None

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
                "method":"data", "format":"json"
        }
        
#        m = json.loads(SQLAPIcall(query).execute())['data']
        # Even or odd is one of two things.
        self.assertTrue(len(m)==2)
        
        # Since the first paragraph is odd,
        # there should be more of those.
        
        self.assertTrue(m['odd'][0]>=m['even'][0])
        
    def test_case_sensitivity(self, federalist_bookworm):
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["the"]},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Sensitive",
                "method":"data", "format":"json"
        }

        val1 = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert(val1[0] > 0)

        query["words_collation"] = "Case_Insensitive"        

        val2= json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        # The words ('The','the') appear more often than ('the') alone.
        assert (val2[0] > val1[0])


    def test_case_insensitivity_works_without_search_term_existing(self, federalist_bookworm):
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["hOwEvEr"]},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Insensitive",
                "method":"data", "format":"json"
        }
        val = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert (val[0] > 0)

    def test_unicode_search_term(self, unicode_bookworm):
        query = {
                "database":"unicode_test_bookworm",
                "search_limits":{"word":["ᎾᏍᎩ"]},
                "counttype":"WordCount",
                "groups":[],
                "words_collation":"Case_Insensitive",
                "method":"data", "format":"json"
        }
        val = json.loads(DuckDBCall(unicode_bookworm, query = query).execute())['data']
        assert (val[0] > 0)

    def test_various_unicode_cases(self, unicode_bookworm):
        # There's a 'description_' for each individual item.
        catalog_location = "tests/test_bookworm_files_unicode/jsoncatalog.txt"
        cases = [json.loads(line)["description_"] for line in open(catalog_location)]
        wordcounts = unicode_bookworm.query("SELECT * FROM nwords").df()['nwords']
        fastcounts = unicode_bookworm.query("SELECT * FROM fastcat").df()['nwords']
        assert (wordcounts > 0).all()
        assert (fastcounts > 0).all()
        for case in cases:
            query = {
                "database":"unicode_test_bookworm",
                "search_limits": {"description_": case},
                "counttype": "WordCount",
                "groups": [],
                "words_collation": "Case_Insensitive",
                "method": "data", "format": "json"
                }
            try:
                val = json.loads(DuckDBCall(unicode_bookworm, query = query).execute())['data']
            except KeyError:
                print(DuckDBCall(unicode_bookworm, query = query).execute())
                raise
            assert(val[0] > 0)

    def test_asterisks_in_search_limits(self, federalist_bookworm):
        """
        The following two queries should, by definition, produce the same result.
        """
        query = {
                "database":"federalist_bookworm",
                "search_limits":{"word":["on"],"author":["HAMILTON"]},
                "compare_limits":{"word":["on"]},                
                "counttype":"WordsPerMillion",
                "groups":[],
                "method":"data", "format":"json"
        }

        val1 = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']

        query = {
            "database":"federalist_bookworm",
            "search_limits":{"word":["on"],"*author":["HAMILTON"]},
            "counttype":"WordsPerMillion",
            "groups":[],
            "method":"data", "format":"json"
            }
        val2 = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert(val1[0] == val2[0])        

        