# About #
[Presidio](https://github.com/bmschmidt/Presidio "Presidio") is the code repository for building the database and tables used with a Bookworm [web app](https://github.com/econpy/BookwormGUI "GUI") and [API](https://github.com/bmschmidt/BookwormAPI "Bookworm API").

# Getting Started #
Before you can build the database with this library, there are a couple things that need to be setup.

### Required Files ###
*  **../metadata/jsoncatalog.txt**: A file with one JSON object per line. All JSON objects must have the same keys. There should be no new line or tab characters in this file. A sample set of lines in `jsoncatalog.txt` may look something like this:

```
{"title":"Adventures of Huckleberry Finn", "author":"Mark Twain", "pubyear":"1885", "authorbirth":"1835", "authorsex":"Male"}
{"title":"The Great Gatsby", "author":"F. Scott Fitzgerald", "pubyear":"1925", "authorbirth":"1896", "authorsex":"Male"}
{"title":"Moby-Dick", "author":"Herman Melville", "pubyear":"1851", "authorbirth":"1819", "authorsex":"Male"}
{"title":"Harry Potter and the Philosopher's Stone", "author":"J. K. Rowling", "pubyear":"1997", "authorbirth":"1965", "authorsex":"Female"}
```
*  **../texts/raw**: This folder should contain a uniquely named .txt file for every item in your collection that you want to build a bookworm around. If the example `jsoncatalog.txt` file above was the one we were using, then the `../texts/raw` directory should contain 4 .txt files, each with the full text of a book.

### MySQL Database ###
Your user must be authorized to edit the database and there must be a `my.cnf` file that Python can load with your permissions.

# Running #
Once everything described above is in place, building the database is done via a command like this:

```python
python OneClick.py dbname dbuser dbpassword
```
 * **dbname**: If the database doesn't exist, the script will create it for you.
 * **dbuser** and **dbpassword**: These need to be setup with the database ahead of time.

### General Workflow ###
The general workflow of OneClick.py is the following:

1. Derive `../metadata/field_descriptions_derived.json` and `../metadata/jsoncatalog_derived.json` from `../metadata/field_descriptions.json` and `../metadata/jsoncatalog.json`, respectively.
2. Initialize connection to the MySQL database.
3. Create metadata catalog files in `../metadata/`.
4. Copy directory structure of files in `../texts/`.
5. Clean and tokenize unigrams and bigrams.
6. Create a table with all words.
7. Encode unigrams and bigrams.
8. Load data into MySQL database.
9. Create temporary MySQL table and .json file that will be used by the web app.
10. Create other API settings.

# Demos #
Here are a couple of Bookworm web apps that are already built using [Presidio](https://github.com/bmschmidt/Presidio "Presidio"):

1. [Open Library](http://bookworm.culturomics.org/ "Open Library")
2. [ArXiv](http://arxiv.culturomics.org/ "ArXiv")
3. [Chronicling America](http://arxiv.culturomics.org/ChronAm/ "Chronicling America")
