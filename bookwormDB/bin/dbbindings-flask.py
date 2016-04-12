#!/usr/bin/env python

# So we load in the terms that allow the API implementation to happen for now.
from bookwormDB.general_API import SQLAPIcall as SQLAPIcall
from flask import Flask, request, Response, jsonify
import json
import os

app = Flask(__name__)


@app.route('/')
def index():
    JSONinput = request.args.get('queryTerms') or request.args.get('query')
    if not JSONinput:
        return "Need query or queryTerms argument"
    return main(JSONinput)


@app.route('/debug/query')
def debug_query():
    JSONinput = request.args.get('queryTerms') or request.args.get('query')
    return JSONinput


def main(JSONinput):

    query = json.loads(JSONinput)

    p = SQLAPIcall(query)
    result = p.execute()

    if (query['method'] == 'data' and 'format' in query and
            query['format'] == 'json'):
        # New format for response
        jresp = json.loads(result)
        resp = jsonify(jresp)
        if jresp['status'] == 'error':
            resp.status_code = jresp['code'] if 'code' in jresp else 500
    else:
        resp = Response(result)

    if query['method'] == "return_tsv":
        resp.headers['Content-Type'] = "text; charset=utf-8"
        resp.headers["Content-Disposition"] = "filename=Bookworm-data.txt"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = 0
    elif query['method'] in ['return_json', 'return_pickle']:
        resp.headers['Content-Type'] = "text/html"

    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, '\
        'Content-Type, X-Requested-With, X-CSRF-Token'

    return resp

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
