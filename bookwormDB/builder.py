from nonconsumptive.ducksauce import quacksort
import duckdb
import numpy as np
from base64 import b64encode, b64decode
import pyarrow as pa
from nonconsumptive import Corpus
from nonconsumptive.metadata import Catalog
from pathlib import Path

class BookwormCorpus(Corpus):
    """
    Create a Bookworm corpus. Uses write db locations, so should 
    not be used to managed existing ones or in a multi-threaded context.
    """

    def __init__(self, db_location, *args, **kwargs):
        self.db_location = Path(db_location)
        self._connection = None
        super().__init__(*args, **kwargs)
        
    def encoded_batches(self):
        for batch in self.encoded_wordcounts:
            yield batch
            
    def bookworm_name(self):
        return self.db_location.with_suffix("").name
    
    def prepare_parquet_ingest_file(self):
        quacksort(self.encoded_batches(), ['wordid', 'bookid'], self.root / 'unigram_bookid.parquet', block_size = 1_000_000_000)

    def prepare_metadata(self):
        self.metadata.to_flat_catalog()
        
    def flat_tabs(self):
        """
        Level-3 normalized database tables with integer keys for faster grouping and selection.
        """
        return (self.root / "metadata" / "flat_catalog").glob("*.parquet")
    
    @property
    def con(self):
        if self._connection is not None:
            return self._connection
        self._connection = duckdb.connect(str(self.db_location))
        return self._connection
    
    def ingest_unigrams(self):
        con = self.con
        wordids = self.root / 'unigram_bookid.parquet'
        con.execute(f"CREATE TABLE IF NOT EXISTS unigram_bookid AS SELECT * FROM parquet_scan('{wordids}')")
        con.execute(f"CREATE TABLE words AS SELECT * FROM parquet_scan('{self.root / 'wordids.parquet'}')")
        con.execute(f"CREATE TABLE wordsheap AS SELECT wordid, token as word, lower(token) as lowercase FROM words")
        
    def ingest_metadata(self):
        for tabpath in self.flat_tabs():
            name = tabpath.with_suffix("").name
            self.con.execute(f"CREATE TABLE {name} AS SELECT * FROM parquet_scan('{tabpath}')")

    def create_table_schemas(self):
        con = self.con
        con.execute('DROP TABLE IF EXISTS arrow_schemas')
        con.execute('CREATE TABLE arrow_schemas (name VARCHAR, schema VARCHAR, type VARCHAR)')
        insertion = 'INSERT INTO arrow_schemas VALUES (?, ?, ?)'

        rich = self.metadata.tb
        con.execute(insertion, ("catalog_ld", b64encode(rich.schema.serialize().to_pybytes()), "resource"))

        ## Insert schemas into the database for later retrieval to understand the db structure
        # Stash as base64 b/c
        # DuckDB can't yet handle blob inserts from python.
        # https://github.com/duckdb/duckdb/issues/1703

        for tab in [*self.flat_tabs()] + [self.root / Path("unigram_bookid.parquet"), self.root / 'wordids.parquet']:
            tabname = tab.with_suffix("").name
            if tabname in ["sorted", "wordids"]:
                continue
            con.execute(insertion, 
                        (tabname, b64encode(pa.parquet.ParquetFile(tab).schema_arrow.serialize().to_pybytes()), 
                        "table"))

    def update_wordcounts(self):
        rel = self.con.register_arrow("my_nwords", self.document_wordcounts(key='bookid'))
        self.con.execute("ALTER TABLE fastcat ADD nwords INT32")
        rel.execute("UPDATE fastcat SET nwords = s.nwords FROM my_nwords as s WHERE s.bookid = fastcat.bookid")
        rel.unregister_arrow("my_nwords")
    
    def create_slow_catalog(self):
        con = self.con
        catcols = set(con.execute("DESCRIBE TABLE catalog").df()['Field'])
        fastcols = set(con.execute("DESCRIBE TABLE fastcat").df()['Field'])
        unique = ["bookid"]
        for col in catcols:
            if col in fastcols or f"{col}__id" in fastcols:
                continue
            unique.append(f'"{col}"')
        con.execute(f"CREATE VIEW slowcat AS SELECT {','.join(unique)} FROM catalog")

    def build(self):
        self.prepare_parquet_ingest_file()
        self.prepare_metadata()
        self.ingest_unigrams()
        self.ingest_metadata()
        self.create_table_schemas()
        self.update_wordcounts()
        self.create_slow_catalog()


RESERVED_NAMES = ["slowcat", "fastcat", "catalog", "my_nwords", "unigram_bookid"]