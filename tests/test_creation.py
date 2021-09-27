import pytest
from pathlib import Path
from bookwormDB.builder import BookwormCorpus
import duckdb

class TestCreation():
    def test_ascii_creation(self, tmpdir):
        path = Path(f"{tmpdir}/federalist.duckdb")

        corp = BookwormCorpus(
            path,
            ngrams = 2,
            texts = Path('tests/test_bookworm_files/input.txt'),
            metadata = "tests/test_bookworm_files/jsoncatalog.txt",
            dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})
        corp.build()
        con = duckdb.connect(str(path))
        ts = con.execute("""SELECT sum(nwords) as 'WordCount' FROM "fastcat" """).fetchall()[0][0]
        assert ts > 20

    def test_unicode_creation(self, tmpdir):
        path = Path(f"{tmpdir}/unicode.duckdb")
        if path.exists(): path.unlink()
        corp = BookwormCorpus(
           path,
           ngrams = 2,
           texts = Path('tests/test_bookworm_files_unicode/input.txt'),
           metadata = "tests/test_bookworm_files_unicode/jsoncatalog.txt",
           dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})
        corp.build()
        con = duckdb.connect(str(path))
        # There's a 'description_' for each individual item.
        ts = con.execute("""SELECT sum(nwords) as 'WordCount'
        FROM "slowcat" NATURAL JOIN "fastcat" """).fetchall()[0][0]
        assert ts > 20
        