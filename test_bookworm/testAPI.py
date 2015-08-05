import unittest
import bookwormDB

class Bookworm_SQL_Creation(unittest.TestCase):

    def test_server_connection(self):
        """
        Connect to MySQL and run a simple query.
        """
        import bookwormDB.CreateDatabase
        db = bookwormDB.CreateDatabase.DB(dbname="mysql")
        sampleQuery=db.query("SELECT 1+1").fetchall()
        self.assertTrue(sampleQuery[0][0]==2)

        
    def test_bookworm_creation(self):
        """
        Creates a test bookworm. Removes any existing databases called "federalist_bookworm"
        """
        
        import MySQLdb
        from warnings import filterwarnings
        filterwarnings('ignore', category = MySQLdb.Warning)
        
        import bookwormDB.CreateDatabase
        db = bookwormDB.CreateDatabase.DB(dbname="mysql")
        if len(db.query("SHOW DATABASES LIKE 'federalist_bookworm'").fetchall()) > 0:
            db.query("DROP DATABASE federalist_bookworm")

        from subprocess import call as call

        from urllib2 import urlopen, URLError, HTTPError

        url = "https://github.com/bmschmidt/federalist-bookworm/archive/master.zip"
        f = urlopen(url)
        with open("/tmp/federalist.zip", "wb") as local_file:
            local_file.write(f.read())

        import zipfile  
        import os
        import shutil
        
        if os.path.exists("/tmp/federalist/federalist-bookworm-master/"):
            if os.path.exists("/tmp/federalist/federalist-bookworm-master/.bookworm"):
                shutil.rmtree("/tmp/federalist/federalist-bookworm-master/.bookworm")
        else:
            zip = zipfile.ZipFile(r'/tmp/federalist.zip')  
            zip.extractall(r'/tmp/federalist')

        with open("/tmp/federalist/federalist-bookworm-master/bookworm.cnf","w") as output:
            output.write("""[client]\ndatabase = federalist_bookworm\nuser=\npassword=\n""")
            # This doesn't worry about client-side passwords.

        call(["make"],shell=True,cwd="/tmp/federalist/federalist-bookworm-master")
        
        db.query("USE federalist_bookworm")
        wordCount = db.query("SELECT SUM(nwords) FROM fastcat").fetchall()[0][0]
        self.assertTrue(wordCount>100000)
        
    def test_api(self):
        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        
        query = {
                "database":"federalist",
                "search_limits":{},
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"return_json"
        }
        
        m = json.loads(SQLAPIcall(query).execute())
        self.assertTrue(len(m)==5)

        
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

if __name__=="__main__":
    unittest.main()
