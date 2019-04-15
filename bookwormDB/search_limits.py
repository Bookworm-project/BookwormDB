import MySQLdb

def where_from_hash(myhash, joiner=None, comp = " = ", escapeStrings=True, list_joiner = " OR "):
    whereterm = []
    # The general idea here is that we try to break everything in search_limits down to a list, and then create a whereterm on that joined by whatever the 'joiner' is ("AND" or "OR"), with the comparison as whatever comp is ("=",">=",etc.).
    # For more complicated bits, it gets all recursive until the bits are all in terms of list.
    if joiner is None:
        joiner = " AND "
    for key in list(myhash.keys()):
        values = myhash[key]
        if isinstance(values, (str, bytes)) or isinstance(values, int) or isinstance(values, float):
            # This is just human-being handling. You can pass a single value instead of a list if you like, and it will just convert it
            # to a list for you.
            values = [values]
        # Or queries are special, since the default is "AND". This toggles that around for a subportion.

        if key == "$or" or key == "$OR":
            local_set = []
            for comparison in values:
                local_set.append(where_from_hash(comparison, comp=comp))
            whereterm.append(" ( " + " OR ".join(local_set) + " )")
        elif key == '$and' or key == "$AND":
            for comparison in values:
                whereterm.append(where_from_hash(comparison, joiner=" AND ", comp=comp))                
        elif isinstance(values, dict):
            if joiner is None:
                joiner = " AND "
            # Certain function operators can use MySQL terms.
            # These are the only cases that a dict can be passed as a limitations
            operations = {"$gt":">", "$ne":"!=", "$lt":"<",
                          "$grep":" REGEXP ", "$gte":">=",
                          "$lte":"<=", "$eq":"="}
            
            for operation in list(values.keys()):
                if operation == "$ne":
                    # If you pass a lot of ne values, they must *all* be false.
                    subjoiner = " AND "
                else:
                    subjoiner = " OR "
                whereterm.append(where_from_hash({key:values[operation]}, comp=operations[operation], list_joiner=subjoiner))
        elif isinstance(values, list):
            # and this is where the magic actually happens:
            # the cases where the key is a string, and the target is a list.
            if isinstance(values[0], dict):
                # If it's a list of dicts, then there's one thing that happens.
                # Currently all types are assumed to be the same:
                # you couldn't pass in, say {"year":[{"$gte":1900}, 1898]} to
                # catch post-1898 years except for 1899. Not that you
                # should need to.
                for entry in values:
                    whereterm.append(where_from_hash(entry))
            else:
                # Note that about a third of the code is spent on escaping strings.
                if escapeStrings:
                    if isinstance(values[0], (str, bytes)):
                        quotesep = "'"
                    else:
                        quotesep = ""

                    def escape(value):
                        # NOTE: stringifying the escape from MySQL; hopefully doesn't break too much.                        
                        return str(MySQLdb.escape_string(to_unicode(value)), 'utf-8')
                else:
                    def escape(value):
                        return to_unicode(value)
                    quotesep = ""

                joined = list_joiner.join([" ({}{}{}{}{}) ".format(key, comp, quotesep, escape(value), quotesep) for value in values])
                whereterm.append(" ( {} ) ".format(joined))

    if len(whereterm) > 1:
        return "(" + joiner.join(whereterm) + ")"
    else:
        return whereterm[0]
    # This works pretty well, except that it requires very specific sorts of terms going in, I think.

    
class Search_limits(dict):
    def to_sql(self):
        return where_from_hash(self)
    def rkeys(self):
        # Recursively return the SQL keys so we know what fields to work with.
        keys = []
        for k, v in self.iteritems():
            if not k.starts_with("$"):
                keys.append(k)
            elif isinstance(v, dict):
                for k in Search_limits(v).rkeys():
                    keys.append(k)
        return keys
    def validate(self):
        # Some tests to see if a query is valid
        for k in self.keys():
            pass
            
