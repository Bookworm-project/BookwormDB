from ducksauce import from_files
import duckdb
import numpy as np
from base64 import b64encode, b64decode
import pyarrow as pa
from nonconsumptive import Corpus
from nonconsumptive.metadata import Catalog
from pathlib import Path
import logging
from pyarrow import feather, parquet, dataset
from ducksauce import from_files
logger = logging.getLogger("bookworm")

class BookwormCorpus(Corpus):
    """
    Create a Bookworm corpus. Uses write db locations, so should 
    not be used to managed existing ones or in a multi-threaded context.
    """

    def __init__(self, db_location, ngrams, *args, **kwargs):
        self.db_location = Path(db_location)
        self._connection = None
        self.ngrams = ngrams
        super().__init__(*args, **kwargs)
        
    def encoded_batches(self):
        for batch in self.encoded_wordcounts():
            yield batch
            
    def bookworm_name(self):
        return self.db_location.with_suffix("").name
            
    """
    def ingest_ngrams_ncid(self, levels = ['bigram'], block_size = 2_500_000_000):
        con = self.con
        for i, f in enumerate(levels):
            con.execute(f"DROP TABLE IF EXISTS {f}__ncid")
            ngrams = i + 1
            logging.info(f"Creating {f} table.")
            sort_order = [f"word{i + 1}" for i in range(ngrams)] + ["_ncid"] 
            ingest_file = self.root / f"{f}__ncid.parquet"
            inputs = [*(self.root / f"encoded_{f}s").glob("*")]
            print(inputs)
            from_files(inputs, sort_order, ingest_file, block_size = block_size)
            con.execute(f"CREATE TABLE {f}__ncid AS SELECT {} FROM parquet_scan('{ingest_file}')")
    """
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

    def create_sorted_ngram_ncid(self, ngrams : int, force : bool = False):
        lookup = [
            None,
            "unigram",
            "bigram",
            "trigram",
            "quadgram",
            "quintgram"
        ]
        name = lookup[ngrams]

        path = self.root / f'{name}__ncid.parquet'
        inputs : List[Path]= [*(self.root / f'encoded_{name}s').glob("*.feather")]
        columns : List[str] = [] # Defined below.
        if path.exists():
            last_time = max([p.stat().st_mtime for p in inputs])
            if path.stat().st_mtime < last_time or force:
                path.unlink()
            else:
                return
        if ngrams > 1:
            columns = [f'word{i + 1}' for i in range(ngrams)]
        else:
            columns = ['wordid']
        logging.getLogger("ducksauce").setLevel(logging.getLogger("bookworm").level)
        from_files(inputs, [*columns, '_ncid'], path, block_size = 1_000_000_000)

    def ingest_unigram__ncid(self):
        con = self.con
        self.create_sorted_ngram_ncid(ngrams = 1)
        wordids = self.root / 'unigram__ncid.parquet'
        con.execute(f"CREATE TABLE IF NOT EXISTS unigram__ncid AS SELECT * FROM parquet_scan('{wordids}')")
        schema = parquet.ParquetFile(wordids).schema_arrow
        self.insert_table_schema("unigram__ncid", schema)

#        wordids.unlink()
        """
        encoded = dataset.dataset(self.root / 'encoded_unigrams', format = "feather")
        con.register_arrow("unigrams_dataset", encoded)
        con.execute("CREATE TABLE IF NOT EXISTS unigram__ncid AS SELECT wordid, _ncid, count FROM unigrams_dataset ORDER BY wordid, _ncid")
        """

    def ingest_ngram__ncid(self, ngrams = 2):
        con = self.con
        lookup = [
            None,
            None,
            "bigram",
            "trigram",
            "quadgram",
            "quintgram"
        ]
        name = lookup[ngrams]
        
        wordids = self.root / f'{name}__ncid.parquet'
        self.create_sorted_ngram_ncid(ngrams)
        con.execute(f"CREATE TABLE IF NOT EXISTS {name}__ncid AS SELECT * FROM parquet_scan('{wordids}')")
        schema = parquet.ParquetFile(wordids).schema_arrow
        self.insert_table_schema(f"{name}__ncid", schema)

        """
        encoded = dataset.dataset(self.root / f'encoded_{name}s', format = "feather")
        con.register_arrow("dataset", encoded)
        word_cols = ", ".join([f"word{i + 1}" for i in range(ngrams)])

        con.execute(f"DROP TABLE IF EXISTS {name}__ncid")
        con.execute(f"CREATE TABLE IF NOT EXISTS {name}__ncid AS SELECT {word_cols}, _ncid, count "
                    f"FROM dataset order by {word_cols}, _ncid")
        self.insert_table_schema(name + "__ncid", encoded.schema)
        """

    def ingest_metadata(self) -> None:
        for tabpath in self.flat_tabs():
            name = tabpath.with_suffix("").name
            self.con.execute(f"CREATE TABLE {name} AS SELECT * FROM parquet_scan('{tabpath}')")

    def create_table_schemas(self):
        con = self.con
        insertion = 'INSERT INTO arrow_schemas VALUES (?, ?, ?)'

        rich = self.metadata.tb
        con.execute(insertion, ("catalog_ld", b64encode(rich.schema.serialize().to_pybytes()), "resource"))

        ## Insert schemas into the database for later retrieval to understand the db structure
        # Stash as base64 b/c
        # DuckDB can't yet handle blob inserts from python.
        # https://github.com/duckdb/duckdb/issues/1703

        for tab in [*self.flat_tabs()] + [self.root / 'wordids.parquet']:
            tabname = tab.with_suffix("").name
            if tabname in ["sorted", "wordids"]:
                continue
            con.execute(insertion, 
                        (tabname, b64encode(pa.parquet.ParquetFile(tab).schema_arrow.serialize().to_pybytes()), 
                        "table"))
    
    def insert_table_schema(self, tabname, schema):
        con = self.con
        insertion = 'INSERT INTO arrow_schemas VALUES (?, ?, ?)'
        con.execute(insertion, (tabname, b64encode(schema.serialize().to_pybytes()), "table"))

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
        """
        The total wordcounts for each document.
        """
        self.con.execute('DROP TABLE IF EXISTS nwords')
        self.con.execute('CREATE TABLE nwords ("@id" STRING, "nwords" INTEGER)')
        logger.info("Creating nwords")
        seen_a_word = False
        for batch in self.iter_over('document_lengths', ids = "@id"):
            seen_a_word = True
            tb = pa.Table.from_batches([batch])
            self.con.register("t", tb.to_pandas())
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

        logger.info("Creating unigrams for duck ingest")
        for k in ["token_counts", "tokenization"]:
            if k in self.cache_set:
                self.multiprocess(k)
        self.total_wordcounts # To cache it
        self.multiprocess("encoded_unigrams")
        ngrams = self.ngrams
        if ngrams > 1:
           self.multiprocess("encoded_bigrams")
        if ngrams > 2:
           self.multiprocess("encoded_trigrams")
        if ngrams > 3:
           self.multiprocess("encoded_quadgrams")
        if ngrams > 4:
           self.multiprocess("encoded_quintgrams")

        con = self.con
        con.execute('CREATE TABLE IF NOT EXISTS arrow_schemas (name VARCHAR, schema VARCHAR, type VARCHAR)')

        self.ingest_wordids()
        logger.info("Sorting and ingesting unigrams")
        self.ingest_unigram__ncid()
        logger.info("Ingesting metadata")
        self.ingest_metadata()
        logger.info("Creating schemas for load")

        self.ingest_wordcounts()
        for i in range(ngrams):
            grams = i + 1
            if i == 0:
                continue
            logger.info(f"Ingesting {i}grams")
            self.ingest_ngram__ncid(grams)

        self.create_table_schemas()

        logger.info("Building slow catalog view")
        self.create_slow_catalog()
        self.con.close()
        self._connection = duckdb.connect(str(self.db_location), read_only = True)

RESERVED_NAMES = ["slowcat", "fastcat", "catalog", "my_nwords", "unigram__ncid"]