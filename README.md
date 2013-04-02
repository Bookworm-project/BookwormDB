[Presidio](https://github.com/bmschmidt/Presidio "Presidio") is the code repository for building the database and tables used with a Bookworm web app and [API](https://github.com/bmschmidt/BookwormAPI "Bookworm API").

# Bookworms #
Here are a couple of Bookworm web apps that are already built using [Presidio](https://github.com/bmschmidt/Presidio "Presidio"):

1. [Open Library](http://bookworm.culturomics.org/ "Open Library")
2. [ArXiv](http://arxiv.culturomics.org/ "ArXiv")
3. [Chronicling America](http://arxiv.culturomics.org/ChronAm/ "Chronicling America")
4. [SSRN](http://steinbeck.seas.harvard.edu/bookworm/ssrn/ "SSRN: Social Science Research Network")
5. [US Congress](http://steinbeck.seas.harvard.edu/bookworm/congress/ "Bills in US Congress")


# Getting Started #
Before you can build the database with this library, there are a couple things that need to be setup.


### Required Files ###
*  **../metadata/jsoncatalog.txt**: A file with one JSON object per line. All JSON objects must have the same keys. There should be no new line or tab characters in this file.
*  **../texts/raw**: This folder should contain a uniquely named .txt file for every item in your collection that you want to build a bookworm around. If the example `jsoncatalog.txt` file above was the one we were using, then the `../texts/raw` directory should contain 4 .txt files, each with the full text of a book.
* **MySQL Database**: Your user must be authorized to edit the database and there must be a `my.cnf` file that Python can load with your permissions. More info about setting up the database and permissions will be added soon.

Assuming a running MySQL database, we'll set up a user `bookwormuser` on the database and give them the access they'll need.

```sql
CREATE USER 'bookwormuser'@'localhost' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON *.* TO 'bookwormuser'@'localhost';
FLUSH PRIVILEGES;
```


# Demo #
Here we'll look at how to use Presidio by going through a demo where we will look at [text from the summaries of bills](https://github.com/unitedstates/congress/wiki "text from the summaries of bills") introduced in the US Congress from 1973 to the present day. The goal is to provide everything needed to build a Bookworm using publically available data.

## Data ##
First we need to download the latest data. I've put together a script in another repo that will download everything you'll need. Start by cloning that repo:

```bash
git clone git://github.com/econpy/congress_api
```

Now run the `get_and_unzip_data.py` script to fetch the data and unzip the zip files:

```bash
cd congress_api
python get_and_unzip_data.py
```

This will take a few minutes depending on your Internet connection and the speed of your computer. The script downloads and unzips all the files in parallel using [multiprocessing](http://docs.python.org/2/library/multiprocessing.html "multiprocessing") to make this as fast as possible. Note that once fully unzipped, the files will take up just under 3GB of disk space.

Once all the files have finished downloading we'll clone this repo and begin to build the metadata for the Bookworm.

## Prep to Build Bookworm ##
Now create some directories and clone Presidio:

```bash
cd ..
mkdir metadata
mkdir texts
mkdir texts/raw
git clone git://github.com/econpy/Presidio
```

We first need to fill `texts/raw/` with .txt files containing the summary of bills introduced into Congress. Each .txt file will be uniquely named and will contain the text from the summary of a bill. Then, we will create the `metadata/jsoncatalog.txt` file which will hold metadata for each bill, including a field that links each JSON object to a .txt file in `texts/raw/`.

Included in the `congress_api` repo is a script titled `congress_parser.py` which we'll run to create the jsoncatalog.txt file and all the .txt files.

```bash
cd congress_api
python congress_parser.py
```

Now we just need to create the `metadata/field_descriptions.json` file which is used to define the type of variable for each variable in `jsoncatalog.txt`. Copy the following JSON object into `metadata/field_descriptions.json`:

```json
[
    {"field":"date","datatype":"time","type":"numeric","unique":true,"derived":[{"resolution":"month"}]},
    {"field":"searchstring","datatype":"searchstring","type":"text","unique":true},
    {"field":"enacted","datatype":"categorical","type":"text","unique":false},
    {"field":"sponsor_state","datatype":"categorical","type":"text","unique":false},
    {"field":"cosponsors_state","datatype":"categorical","type":"text","unique":false},
    {"field":"chamber","datatype":"categorical","type":"text","unique":false}
    ]
```

Everything should now be in place and we are ready to build the database.

## Running ##
Building the database for a Bookworm is done via a command like this:

```python
python OneClick.py dbname dbuser dbpassword
```

 * **dbname**: If the database doesn't exist, the script will create it for you.
 * **dbuser** and **dbpassword**: These need to be setup with the database ahead of time.

Assuming our MySQL username is `bookwormuser` with password `mypassword`, we'll create a database named `congress` by running:

```python
python OneClick.py congress bookwormuser mypassword
```

This will take a while to run. Sit back and relax.

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
