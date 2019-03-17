from __future__ import print_function
import bookwormDB
import bookwormDB.CreateDatabase
from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
import logging
import os
from subprocess import call as call
import sys
import json
from shutil import rmtree

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
    rmtree(".bookworm", ignore_errors = True)
    
    bookwormDB.configuration.create(ask_about_defaults=False, database="federalist_bookworm")

    db = bookwormDB.CreateDatabase.DB(dbname="mysql")
    
    try:
        db.query("DROP DATABASE IF EXISTS federalist_bookworm")
    except MySQLdb.OperationalError as e:
        if e[0]==1008:
            pass
        else:
            print(e)
            raise
    except Exception as e:
        """
        This is some weird MariaDB exception. It sucks that I'm compensating for it here.
        """
        if e[0]=="Cannot load from mysql.proc. The table is probably corrupted":
            pass
        else:
            print(e)
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
    rmtree(".bookworm", ignore_errors = True)
    
    bookwormDB.configuration.create(ask_about_defaults=False,database="unicode_test_bookworm")
    
    db = bookwormDB.CreateDatabase.DB(dbname="mysql")
    
    try:
        db.query("DROP DATABASE IF EXISTS unicode_test_bookworm")
    except MySQLdb.OperationalError as e:
        if e[0]==1008:
            pass
        else:
            print(e)
            raise
    except Exception as e:
        """
        This is some weird MariaDB exception. It sucks that I'm compensating for it here.
        """
        if e[0]=="Cannot load from mysql.proc. The table is probably corrupted":
            pass
        else:
            logging.warning("Some mysterious error in attempting to drop previous iterations: just try running it again?")
            
    call(["bookworm --log-level warning build all"],shell=True,cwd=sys.path[0] + "/test_bookworm_files_unicode")


if __name__=="__main__":
    setup_bookworm()
    setup_bookworm_unicode()

