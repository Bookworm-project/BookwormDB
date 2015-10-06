import unittest
import bookwormDB
import logging

logging.basicConfig(level=10)

class Bookworm_SQL_Creation(unittest.TestCase):

    def test_server_connection(self):
        logging.info("\n\nTESTING SERVER CONNECTION\n\n")
        """
        Connect to MySQL and run a simple query.
        """
        import bookwormDB.CreateDatabase
        db = bookwormDB.CreateDatabase.DB(dbname="mysql")
        sampleQuery=db.query("SELECT 1+1").fetchall()
        self.assertTrue(sampleQuery[0][0]==2)

    """
    To properly test things, we actually build some bookworms.
    This assumes that the directory '/tmp' is writeable,
    which isn't strictly necessary for a bookworm to be built.
    """

    def test_config_files(self):
        logging.info("\n\nTESTING CONFIG FILE ACCESS\n\n")
        def test_config_file(conf):
            user = conf.get("client","user")
            pw = conf.get("client","password")

        global_configuration_file = bookwormDB.configuration.Configfile("global").config
        admin_configuration_file = bookwormDB.configuration.Configfile("admin").config

        test_config_file(global_configuration_file)
        test_config_file(admin_configuration_file)


    def test_bookworm_creation(self):
        """
        Creates a test bookworm. Removes any existing databases called "federalist_bookworm"
        """
        logging.info("\n\nTESTING BOOKWORM CREATION\n\n")
        import MySQLdb
        from warnings import filterwarnings
        filterwarnings('ignore', category = MySQLdb.Warning)
        
        import bookwormDB.CreateDatabase
        db = bookwormDB.CreateDatabase.DB(dbname="mysql")
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

        import bookwormDB.configuration
            
        globalc = bookwormDB.configuration.Configfile("global").config
        password = globalc.get("client","password")
        user = globalc.get("client","user")

        with open("/tmp/federalist/federalist-bookworm-master/bookworm.cnf","w") as output:
            output.write("""[client]\ndatabase = federalist_bookworm\nuser=%s\npassword=%s\n""" % (user,password))
            # This doesn't worry about client-side passwords.

        call(["make"],shell=True,cwd="/tmp/federalist/federalist-bookworm-master")
        
        db.query("USE federalist_bookworm")
        wordCount = db.query("SELECT SUM(nwords) FROM fastcat").fetchall()[0][0]
        # This should be 212,081, but I don't want the tests to start failing when
        # we change the tokenization rules or miscellaneous things about encoding.
        self.assertTrue(wordCount>100000)

        """
        Then we test whether the API can make queries on that bookworm.
        """

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

        """
        And then we test if we can add metadata to the bookworm.
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
        os.chdir("/tmp/federalist/federalist-bookworm-master")
        manager.add_metadata(Dummy)

        """
        And then we test if that can be retrieved
        """

        from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
        import json
        import os
                
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
        # Since the first paragraph is even,
        # there should be more of those.
        
        self.assertTrue(m['odd'][0]>=m['even'][0])

        
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
    unittest.main()
