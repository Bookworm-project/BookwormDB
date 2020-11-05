
from .schema_primitives import *

base_schema = {
    "definitions": {

    },
    "type": "object",
    "title": "Bookworm Query Schema",
    "required": [
        "database",
        "method",
        "format",
        "search_limits",
        "groups",
        "counttype"
    ],
    "properties": {
        "method": method_schema,
        "format": format_schema,
        "database": {
            "type": "string",
            "title": "The Database Schema",
            "description": "The name of the database to search in.",
            "examples": [
                "federalist_bookworm",
                "hathipd"
            ],
            "pattern": "^([^ ]+)$"
        },
        "search_limits": {
            "$id": "#/properties/search_limits",
            "type": "object",
            "description": "A set of constraints to create a corpus. If an array, each will be treated as a grouping field for results and a new key, 'Search,' will be returned."
        },
        "compare_limits": {
            "$id": "#/properties/compare_limits",
            "type": "object",
            "description": "The definition of a full corpus against which to run comparisons. In general, this will be automatically inferred from the search_limits field by dropping the 'word' limit.",
        },
        "groups": {
            "$id": "#/properties/groups",
            "type": "array",
            "items": {
                "$id": "#/properties/groups/items",
                "type": "string",
                "default": "",
                "examples": [
                    "author",
                    "date_day_year"
                ],
                "pattern": "^(.*)$"
            }
        },
        "counttype": counts_schema
    }
}

class DataQuerySchema(dict):
    """
    A JSON schema for valid queries.
    """
    def __init__(self, con):
        """
        Initialize a schema.

        Args:
            self: (todo): write your description
            con: (todo): write your description
        """
        dict.__init__(self, base_schema)
        self.set_base_elements()

    def set_base_elements(self):
        """
        Sets the base elements.

        Args:
            self: (todo): write your description
        """
        pass

    def validate(self, query):
        """
        Validate a query.

        Args:
            self: (todo): write your description
            query: (str): write your description
        """
        pass
