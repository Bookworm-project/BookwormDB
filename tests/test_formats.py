# -*- coding: utf-8 -*-

from builtins import range
from builtins import object
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
from pyarrow import feather

class Bookworm_Return_Formats(unittest.TestCase):

    def test_feather(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        query = {
                "database":"federalist_bookworm",
                "search_limits":{},
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data",
                 "format":"feather"
        }
        
        feather_file = SQLAPIcall(query).execute()
        f = io.BytesIO(feather_file)
        f.seek(0)
        m = feather.read_feather(f)
        self.assertEqual(m.shape[0],5)
        self.assertEqual(m.shape[1],2)


    def test_proxy_API(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{},
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data",
                "format":"json"
        }
        
        m = json.loads(SQLAPIcall(query).execute())['data']
        self.assertEqual(len(m),5)
        
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
