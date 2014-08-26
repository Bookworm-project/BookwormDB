import dbbindings
import unittest
import bookworm.general_API as general_API


class SQLConnections(unittest.TestCase):
    def dbConnectorsWork(self):
        from general_API import prefs as prefs
        print prefs
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

#        self.assertTrue(worked)

if __name__=="__main__":
    unittest.main()
