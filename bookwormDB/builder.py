from ducksauce import from_files
import duckdb
import numpy as np
from base64 import b64encode, b64decode
import pyarrow as pa
from nonconsumptive import Corpus
from nonconsumptive.metadata import Catalog
from pathlib import Path
import logging
from pyarrow import feather, parquet
logger = logging.getLogger("bookworm")

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
        for batch in self.encoded_wordcounts():
            yield batch
            
    def bookworm_name(self):

        return self.db_location.with_suffix("").name
    
    def create_unigrams(self):
        self.cache_set.add("ncid_wordid")
        for i in self.encoded_wordcounts():
            pass
        
    def sort_unigrams(self, block_size = 5_000_000):
        from_files((self.root / "ncid_wordid").glob("*"), ['wordid', '_ncid'], self.root / 'unigram__ncid.parquet', block_size = block_size)

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
    

    def ingest_wordids(self):
        con = self.con
        fin = self.root / 'wordids.feather'
        word_table = pa.feather.read_table(fin)
        pa.parquet.write_table(word_table, fin.with_suffix(".parquet"))
        logger.debug("INGESTING INTO words")
        con.execute(f"CREATE TABLE words AS SELECT * FROM parquet_scan('{self.root / 'wordids.parquet'}')")
        logger.debug("INGESTING INTO wordsheap")
        con.execute(f"CREATE TABLE wordsheap AS SELECT wordid, token as word, lower(token) as lowercase FROM words")

    def ingest_unigram__ncid(self):
        con = self.con
        wordids = self.root / 'unigram__ncid.parquet'
        con.execute(f"CREATE TABLE IF NOT EXISTS unigram__ncid AS SELECT * FROM parquet_scan('{wordids}')")
        
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

        for tab in [*self.flat_tabs()] + [self.root / Path("unigram__ncid.parquet"), self.root / 'wordids.parquet']:
            tabname = tab.with_suffix("").name
            if tabname in ["sorted", "wordids"]:
                continue
            con.execute(insertion, 
                        (tabname, b64encode(pa.parquet.ParquetFile(tab).schema_arrow.serialize().to_pybytes()), 
                        "table"))

    def create_slow_catalog(self):
        con = self.con
        catcols = set(con.execute("DESCRIBE TABLE catalog").df()['Field'])
        fastcols = set(con.execute("DESCRIBE TABLE fastcat").df()['Field'])
        unique = ["_ncid"]
        for col in catcols:
            if col in fastcols or f"{col}__id" in fastcols:
                continue
            unique.append(f'"{col}"')
        con.execute(f"CREATE VIEW slowcat AS SELECT {','.join(unique)} FROM catalog")

    def ingest_wordcounts(self):
        self.con.execute('CREATE TABLE nwords ("@id" STRING, "nwords" INTEGER)')
        logger.info("Creating nwords")
        seen_a_word = False
        for batch in self.iter_over('document_lengths', ids = "@id"):
            seen_a_word = True
            tb = pa.Table.from_batches([batch])
            self.con.register_arrow("t", tb)
            self.con.execute('INSERT INTO nwords ("@id", nwords) SELECT * FROM t')
            self.con.unregister("t")
        if not seen_a_word:
            raise FileNotFoundError("No document lengths for corpus.")
        logger.info("Creating nwords on `catalog`")
        self.con.execute("ALTER TABLE catalog ADD nwords INTEGER")
        logger.info("Updating nwords on `catalog` from nwords table.")
        self.con.execute('UPDATE catalog SET nwords = nwords.nwords FROM nwords WHERE "catalog"."@id" = "nwords"."@id"')
        logger.info("Creating nwords on `fastcat`.")
        self.con.execute("ALTER TABLE fastcat ADD nwords INTEGER")
        logger.info("Updating nwords on `fastcat` from catalog table.")
        self.con.execute('UPDATE fastcat SET nwords = catalog.nwords FROM catalog WHERE fastcat._ncid = catalog._ncid')

    def build(self):
        logger.info("Preparing metadata")
        self.prepare_metadata()
        logger.info("Sorting unigrams for duck ingest")
        self.create_unigrams()
        self.sort_unigrams()
        logger.info("Ingesting unigrams")
        self.ingest_wordids()
        self.ingest_unigram__ncid()
#        logger.warning("Ingesting bigrams")
        logger.info("Ingesting metadata")

        self.ingest_metadata()
        logger.info("Creating schemas for load")

        self.ingest_wordcounts()

        self.create_table_schemas()

        logger.info("Building slow catalog view")
        self.create_slow_catalog()
        self.con.close()
        self._connection = duckdb.connect(str(self.db_location), read_only = True)

RESERVED_NAMES = ["slowcat", "fastcat", "catalog", "my_nwords", "unigram__ncid"]