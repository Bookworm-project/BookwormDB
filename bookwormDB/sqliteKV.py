# Copyright © 2018 Sylvain PULICANI <picani@laposte.net>
# Super heavily changed by Ben Schmidt; the old version was a true
# kv store, this one just autoincrements a lookup table.

# This should generally be thread safe for reads, but not for writes.
# If multip

# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See the COPYING file for more details.

# sqlite_kv.py
#
# Python implementation of the SQLiteKV store.

import sqlite3


class KV:
    """
    Python implementation of the SQLiteKV store, with additionnal methods
    to make it more pythonic.
    ..Warning::
      * The `close` method has to be called after use.
      * The `delete` method is not yet implemented.
    """
    def __init__(self, dbfile):
        """
        Open a connection to the SQLite file. If it doesn't exists, create it
        and add the needed tables.
        """
        self.conn = None
        self.conn = sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row

        tables = [dict(r)['name'] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]

        if 'keys' not in tables:
            self.conn.execute("""CREATE TABLE keys(
                              ID INTEGER PRIMARY KEY ASC,
                              key TEXT UNIQUE NOT NULL)""")
            
            self.conn.execute("CREATE UNIQUE INDEX idx_keys ON keys(key)")


    def close(self):
        """
        Properly close the database.
        """
        self.conn.commit()
        self.conn.close()
                       
    def __getitem__(self, key):
        rows = self.conn.execute("""SELECT ID FROM keys 
                               WHERE keys.key=(?)""", (key, ))
        row = rows.fetchone()
        if row is None:
            raise KeyError(key)
        return row['ID']

    def register(self, key):
        self.conn.execute("INSERT INTO keys(key) VALUES (?)",
                          (key, ))

