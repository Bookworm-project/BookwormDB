from builtins import hex
import unittest
import bookwormDB
import bookwormDB.configuration
import bookwormDB.CreateDatabase
import logging
import MySQLdb
import random

logging.basicConfig(level=10)


"""
Tests of the MySQL configuration.
"""

class Bookworm_MySQL_Configuration(unittest.TestCase):
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
            conf.read_config_files()
            user = conf.config.get("client","user")
            pw = conf.config.get("client","password")
            return (user,pw)

        global_configuration_file = bookwormDB.configuration.Configfile("global")
        admin_configuration_file = bookwormDB.configuration.Configfile("admin")

        (admin_user,admin_pw) = test_config_file(global_configuration_file)
        (client_user,client_pw) = test_config_file(admin_configuration_file)
        logging.info("admin user is {} and password is {}".format(admin_user,admin_pw))
        logging.info("client user is {} and password is {}".format(client_user,client_pw))
        logging.info("Checking that admin and client users are distinct")
        self.assertTrue(admin_user != client_user)
        
    def test_createDB_permission(self):
        logging.info("\nTESTING ABILITY TO CREATE DATABASES\n\n")
        import bookwormDB.configuration
        dbname = "A" + hex(random.getrandbits(128))[2:-1]
        import bookwormDB.CreateDatabase
        db = bookwormDB.CreateDatabase.DB(dbname="mysql")        
        cursor = db.query("CREATE DATABASE {}".format(dbname))
        cursor.execute("DROP DATABASE {}".format(dbname))
        cursor.close()


if __name__=="__main__":
    unittest.main()
