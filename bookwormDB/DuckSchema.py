import pyarrow as pa
from base64 import b64decode
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
            'bookid': 'fastcat',
            'filename': "catalog",
            'wordid': "wordsheap"}

        # hash of what the root variable for each search term is (eg,
        # 'author_birth' might be crosswalked to 'authorid' in the
        # main catalog.)
        self.anchorFields = {
            'bookid': 'bookid',
            'filename': "bookid",
            'wordid': "wordid",
            'word': "wordid"
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
        for tablename, tab in schema.items():
            sch = pa.ipc.read_schema(pa.py_buffer(b64decode(tab)))
            if tablename in ["catalog"]:
                continue
            for i, field in enumerate(sch):
                if i == 0:
                    current_anchor = field.name
                else:
                    self.tableToLookIn[field.name] = tablename
                    self.anchorFields[field.name] = current_anchor
                    if current_anchor.endswith("__id"):
                        self.aliases[field.name] = current_anchor
            
    def tables_for_variables(self, variables, tables = []):
        lookups = []
        for variable in variables:
            stack_here = []
            lookup_table = self.tableToLookIn[variable]
            if lookup_table in tables:
                continue
            stack_here.append(lookup_table)
            while True:
                anchor = self.anchorFields[variable]
                parent_tab = self.tableToLookIn[anchor]
                if anchor in stack_here or anchor in lookups:
                    break
                else:
                    # Must go first in duck or other postgres parsers.
                    stack_here.append(parent_tab)
                lookup_table = anchor
                # Look for the parent of the parent.
                if variable == 'bookid' or anchor == 'wordid':
                    break
                variable = anchor                

            stack_here.reverse()
            for variable in stack_here:
              if not variable in lookups:
                lookups.append(variable)
        return list(lookups)
