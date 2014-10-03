import dbbindings
import unittest
import bookworm.general_API as general_API
import bookworm.SQLAPI as SQLAPI

class SQLfunction(unittest.TestCase):

    def test1(self):

        query = {
            "database": "movies",
            "method": "return_json",
            "search_limits": {"MovieYear":1900},
            "counttype": "WordCount",
            "groups": ["TV_show"]
        }

    
        f = SQLAPI.userquery(query).query()
        print f
    

class SQLConnections(unittest.TestCase):
    def dbConnectorsWork(self):
        from general_API import prefs as prefs
        connection = general_API.dbConnect(prefs,"federalist")
        tables = connection.cursor.execute("SHOW TABLES")
        self.assertTrue(connection.dbname=="federalist")

    def test1(self):
        query = {
                "database":"federalist",
                "search_limits":{},
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"return_json"
        }
        
        try:
            dbbindings.main(query)
            worked = True
        except:
            worked = False

        self.assertTrue(worked)

    def test2(self):
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

if __name__=="__main__":
    unittest.main()
