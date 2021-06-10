from nonconsumptive.ducksauce import quacksort
import duckdb
import numpy as np
from base64 import b64encode, b64decode
import pyarrow as pa
from nonconsumptive import Corpus
from nonconsumptive.metadata import Catalog
from pathlib import Path
import logging
from pyarrow import feather
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
        for batch in self.encoded_wordcounts:
            yield batch
            
    def bookworm_name(self):
        return self.db_location.with_suffix("").name
    
    def sort_parquet_unigrams(self):
        dest = self.root / 'unigram__ncid.parquet'
        if dest.exists():
            logger.warning(f"Using existed sorted unigrams at {dest} without checking if they're out of date.")
            return
        quacksort(self.encoded_batches(), ['wordid', '_ncid'], self.root / 'unigram__ncid.parquet', block_size = 5_000_000_000)

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
        wordids = self.root / 'unigram__ncid.parquet'
        con.execute(f"CREATE TABLE IF NOT EXISTS unigram__ncid AS SELECT * FROM parquet_scan('{wordids}')")
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
        self.con.execute('CREATE TABLE nwords ("_ncid" INTEGER, "nwords" INTEGER)')

        for p in (self.root / "document_lengths").glob("*.feather"):
            tb = feather.read_table(p)
            indices = feather.read_table(self.root / "build/batch_indices" / p.name, columns = ["_ncid"])
            zipped = pa.table([indices['_ncid'], tb['count']], ["_ncid", "nwords"])
            self.con.register_arrow("t", zipped)
            self.con.execute("INSERT INTO nwords (_ncid, nwords) SELECT * FROM t")
            self.con.unregister("t")

        self.con.execute("ALTER TABLE catalog ADD nwords INTEGER")
        self.con.execute('UPDATE catalog SET nwords = nwords.nwords FROM nwords WHERE "catalog"."_ncid" = "nwords"."_ncid"')
        self.con.execute("ALTER TABLE fastcat ADD nwords INTEGER")
        self.con.execute('UPDATE fastcat SET nwords = nwords.nwords FROM nwords WHERE fastcat._ncid = nwords._ncid')

    def build(self):
        logger.info("Preparing metadata")
        self.prepare_metadata()
        logger.info("Sorting unigrams for duck ingest")
        self.sort_parquet_unigrams()
        logger.info("Ingesting unigrams")
        self.ingest_unigrams()
#        logger.warning("Ingesting bigrams")
        logger.info("Ingesting metadata")

        self.ingest_metadata()
        logger.info("Creating schemas for load")

        self.ingest_wordcounts()

        self.create_table_schemas()

        logger.info("Building slow catalog view")
        self.create_slow_catalog()
        self.con.close()


RESERVED_NAMES = ["slowcat", "fastcat", "catalog", "my_nwords", "unigram__ncid"]