import pyarrow as pa
from base64 import b64decode
import logging
import pandas as pd
logger = logging.getLogger("bookworm")

class DuckSchema(object):
    """
    This class stores information about the database setup that is used to 
    optimize query creation query
    and so that queries know what tables to include.
    It's broken off like this because it might be usefully wrapped around some of
    the backend features,
    because it shouldn't be run multiple times in a single query 
    (that spawns two instances of itself),
    as was happening before.
    """

    def __init__(self, db):
        # XXXX
        self.db = db

        # hash of what table each variable is in
        self.tableToLookIn = {
            '_ncid': 'fastcat',
            '@id': "slowcat",
            'wordid': "wordsheap",
            'nwords': 'fastcat'}

        # hash of what the root variable for each search term is (eg,
        # 'author_birth' might be crosswalked to 'authorid' in the
        # main catalog.)
        self.anchorFields = {
            '_ncid': '_ncid',
            '@id': "slowcat",
            'wordid': "wordid",
            'word': "wordid",
            'nwords': '_ncid'
        }

        # aliases: a hash showing internal identifications codes that
        # dramatically speed up query time, but which shouldn't be
        # exposed.  So you can run a search for "state," say, and the
        # database will group on a 50-element integer code instead of
        # a VARCHAR that has to be long enough to support
        # "Massachusetts" and "North Carolina."  A couple are
        # hard-coded in, but most are derived by looking for fields
        # that end in the suffix "__id" later.

        # The aliases starts with a dummy alias for fully grouped queries.
        self.aliases = {}

        tables = db.execute("SELECT name, schema FROM arrow_schemas WHERE type='table'").fetchall()
        schema = dict(tables)

        current_anchor = None
        self.fields = []
        for tablename, tab in schema.items():
            sch = pa.ipc.read_schema(pa.py_buffer(b64decode(tab)))
            if tablename in ["catalog"]:
                continue
            for i, field in enumerate(sch):
                self.fields.append(field)
                if i == 0:
                    current_anchor = field.name
                else:
                    self.tableToLookIn[field.name] = tablename
                    self.anchorFields[field.name] = current_anchor
                    if current_anchor.endswith("__id"):
                        self.aliases[field.name] = current_anchor
            tables = db.execute("SELECT name, schema FROM arrow_schemas WHERE type='table'").fetchall()
        # A few columns are kept in the 'slowcat' view for historical reasons.
        slowcols = set(db.execute("DESCRIBE TABLE slowcat").df()['Field'])
        current_anchor = "_ncid"
        for i, field in enumerate(slowcols):
            if i > 0:
                self.tableToLookIn[field] = "slowcat"
                self.anchorFields[field] = "_ncid"

    def to_pandas(self):
        """
        Return a JSON representation of the schema.
        """
        fields = []
        for field in self.fields:
            name = field.name
            if name.endswith("__id"):
                continue
            elif name in { 'count', 'wordid', '_ncid' }: 
                continue
            elif str(field.type) == 'old_string':
                continue
            else:        
                fields.append({'dbname': name, 'dtype': str(field.type)})
        return pd.DataFrame(fields)
    
    def tables_for_variable(self, variable, depth = 0):
        """
        Returns the tables needed to look up a variable, back up to 'fastcat' or 'wordsheap'
        """
        if variable == '_ncid' or variable == 'wordid':
            return []
        vals = []
        try:
            tabs = [
                (depth, self.tableToLookIn[variable]),
                *self.tables_for_variable(self.anchorFields[variable], depth - 1)
                ]
        except KeyError:
            print("\n\n", variable, "\n\n")
            print(self.anchorFields)
            print("\n\n", self.tableToLookIn, "\n\n")
            raise
        return tabs

    def tables_for_variables(self, variables):
        lookups = []
        for variable in variables:
            lookups = lookups + self.tables_for_variable(variable)
        lookups.sort()
        tables = []
        for depth, tablename in lookups:
            if not tablename in tables:
                tables.append(tablename)
        return tables