# -*- coding: utf-8 -*-

import pytest
import bookwormDB
from bookwormDB.general_API import DuckDBCall as DuckDBCall
from bookwormDB.builder import BookwormCorpus
from pathlib import Path
import logging
logger = logging.getLogger("bookworm")

import os
import duckdb
from subprocess import call as call
import sys
import json
import pytest

@pytest.fixture(scope="session")
def federalist_bookworm(tmpdir_factory):
    path = tmpdir_factory.mktemp("ascii").join("federalist.duckdb")
    tmpdir = tmpdir_factory.mktemp("tmpdir")
    corp = BookwormCorpus(
        f"{path}",
        texts = Path('tests/test_bookworm_files/input.txt'),
        metadata = "tests/test_bookworm_files/jsoncatalog.txt",
        dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})    
    corp.build()
    con = duckdb.connect(str(path), read_only = True)
    return con

@pytest.fixture(scope="session")
def unicode_bookworm(tmpdir_factory):
    path = tmpdir_factory.mktemp("unicode").join("unicode.duckdb")
    tmpdir = tmpdir_factory.mktemp("tmpdir")

    corp = BookwormCorpus(
        f"{path}",
        texts = Path('tests/test_bookworm_files_unicode/input.txt'),
        metadata = "tests/test_bookworm_files_unicode/jsoncatalog.txt",
        dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})

    corp.build()
    con = duckdb.connect(str(path), read_only = True)
    return con

class Test_Bookworm_SQL_Creation():
   
    def test_ne_with_one_entry(self, federalist_bookworm):
        import json
        
        query = {
                "database":"federalist_bookworm",
                "search_limits":{
                    "author": {"$ne": ["HAMILTON"]}
                },
                "counttype":"TextPercent",
                "groups":["author"],
                "method":"data", "format":"json"
        }
        
        m = json.loads(DuckDBCall(federalist_bookworm, query = query).execute())['data']
        assert len(m)==4