import unittest
import json
from test_API import setup_bookworm
import urllib2
import logging

class Bookworm_apacheserver_works(unittest.TestCase):
    def test_apache_server_exists(self):
        """
        Request the number of words in the test server.
        """
        files = urllib2.urlopen('http://localhost/cgi-bin/dbbindings.py/?query={"database":"federalist_bookworm","method":"return_json","counttype":["WordCount"],"groups":[]}').readlines()
        val = json.loads(files[0])
        self.assertTrue(val[0]>150000)

if __name__ == "__main__":
    # The setup is done without verbose logging; any failure
    # causes it to try again.
    logging.basicConfig(level=100)
    try:
        setup_bookworm()
    except:
        logging.basicConfig(level=10)
        setup_bookworm()
    logging.basicConfig(level=10)    
    unittest.main()
