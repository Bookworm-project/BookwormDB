from .general_API import Aggregator

agg_keys = list(Aggregator.__dict__.keys())
agg_keys = [k for k in agg_keys if not k.startswith("_")]
counts_schema = {
            "$id": "#/properties/counttype",
            "type": "array",
            "items": {
                "$id": "#/properties/counttype/items",
                "type": "string",
                "default": "WordCount",
                "enum":  agg_keys,
                "pattern": "^(.*)$"
            }
}

method_schema = {
    "type": "string",
    "title": "Return Method",
    "default": "data",
    "enum": [
        "data",
        "schema",
        "search"
    ],
    "pattern": "^(.*)$"
}

format_schema = {
    "description": "The return format requested from the API.",
    "type": "string",
    "title": "The Format Schema",
    "default": "json_c",
    "enum": [
        "json_c",
        "csv",
        "tsv",
        "feather",
        "json",
        "html"
    ]
}
