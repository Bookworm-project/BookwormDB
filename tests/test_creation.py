import pytest
from pathlib import Path
from bookwormDB.builder import BookwormCorpus

class TestCreation():
    def test_ascii_creation(self, tmpdir):
        corp = BookwormCorpus(
            f"{tmpdir}/federalist.duckdb",
            texts = Path('tests/test_bookworm_files/input.txt'),
            metadata = "tests/test_bookworm_files/jsoncatalog.txt",
            dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})
        corp.build()

    def test_unicode_creation(self, tmpdir):
        corp = BookwormCorpus(
            f"{tmpdir}/unicode.duckdb",
            texts = Path('tests/test_bookworm_files_unicode/input.txt'),
            metadata = "tests/test_bookworm_files_unicode/jsoncatalog.txt",
            dir = tmpdir, cache_set = {"tokenization", "token_counts", "wordids"})
        corp.build()