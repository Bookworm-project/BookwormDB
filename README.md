[Presidio](https://github.com/bmschmidt/Presidio "Presidio") is the code repository for transforming a large
set of files and their metadata into an efficient and easily queryable database that can make full use of all the
metadata and lexical data in the original source.

Technically, it is a set of Python and Perl scripts that leaves behind a MySQL database.

## Related projects

This is closely tied to two other projects. 

To query the database created here programatically, you should use the Bookworm [API](https://github.com/bmschmidt/BookwormAPI "Bookworm API").

Some basic, widely appealing visualizations of the data are possible with the Bookworm [web app](https://github.com/econpy/BookwormGUI "Bookworm web app"), which runs
on top of the API. 


The "master" branch is more backwards-compatible, but the "dev" branch tends to be significantly faster both for creation and
for querying. "Master" exists primarily as an internal scheme to support legacy installations; there has not been a "stable" 
release to date, so neither is guaranteed to be more stable than the other. Most new installations should use "dev."


## Bookworms ##
Here are a couple of [our](http://www.culturomics.org "Culturomics") Bookworms built using [Presidio](https://github.com/bmschmidt/Presidio "Presidio"):

1. [Open Library](http://bookworm.culturomics.org/OL/ "Open Library")
2. [ArXiv](http://bookworm.culturomics.org/arxiv/ "ArXiv")
3. [Chronicling America](http://arxiv.culturomics.org/ChronAm/ "Chronicling America")
4. [SSRN](http://bookworm.culturomics.org/ssrn/ "SSRN: Social Science Research Network")
5. [US Congress](http://bookworm.culturomics.org/congress/ "Bills in US Congress")


## Getting Started ##
### Required MySQL Database ###
At the very least, there must be a MySQL user with permissions to insert + select data from all databases.

For example, create a user `foobar` with password `mysecret` and full access to all databases from `localhost`:

```mysql
CREATE USER 'foobar'@'localhost' IDENTIFIED BY 'mysecret';
GRANT ALL PRIVILEGES ON *.* TO 'foobar'@'localhost';
FLUSH PRIVILEGES;
```

However, ideally there should be 2 MySQL users. The first user would have the ability to create new databases (i.e. GRANT ALL) and the second would only be able to select data from databases (i.e. GRANT SELECT).

The first user would be the one defined above. The second user would be the user that the API uses to get data to push to the bookworm GUI. The easiest way to configure this user is to just let the Apache user handle getting the data. On Ubuntu, you would do: 

```mysql
GRANT SELECT PRIVILEGES ON *.* TO 'www-data'@'localhost';
FLUSH PRIVILEGES;
```

If you're using a Mac, the Apache user is `_www`, so replace `www-data` with `_www` above. Otherwise, you can get it from your `httpd.conf` file (located in this example at `/etc/apache2/httpd.conf`) by doing:

```bash
cat /etc/apache2/httpd.conf | grep ^User | cut -d" " -f 2
```

Finally, there must also be a file at `~/.my.cnf` that Python can load with your MySQL user/pass (this prevents having to store any sensitive information in the Python scripts). Here is an example of what the `~/.my.cnf` file would look like for the user/pass created above:

```
[client]
user = foobar
password = 'mysecret'
```
With these settings in place, you're ready to begin building a Bookworm.

# Demo #
Here we'll look at how to use Presidio by going through a demo where we will look at [text from the summaries of bills](https://github.com/unitedstates/congress/wiki "text from the summaries of bills") introduced in the US Congress from 1973 to the present day. The goal is to provide everything needed to build a Bookworm using publically available data.

## Get the Data ##
First we need to download the latest data. I've put together a script in another repo that will download everything you'll need. Clone that repo and run `get_and_unzip_data.py` to fetch and unzip the data:

```
git clone git://github.com/econpy/congress_api
cd congress_api
python get_and_unzip_data.py
```

This will take a few minutes depending on your Internet connection and the speed of your computer. The `get_and_unzip_data.py` script simply downloads and unzips all the files in parallel using [multiprocessing](http://docs.python.org/2/library/multiprocessing.html "multiprocessing"). NOTE: Once fully unzipped, the files will take up just under 3GB of disk space.

## Prep to Build Bookworm ##
Now clone this repo and make a few directories where we'll put some files:

```
git clone git://github.com/bmschmidt/Presidio
cd Presidio
mkdir files && mkdir files/{metadata,texts,texts/raw}
```

### Required Files ###

To build a bookworm, files are required in three places. Relative to the root directory (which will be called `Presidio` 
if you clone this repo directly), they are all in a subdirectory called `files`.

```
Presidio/
 -- files/
  | -- texts/
  |  | raw  <--- contains texts files or a folder of text files
  |  | input.txt <----- (alternate method: a single file with all texts, preceded by their id.)
  | -- metadata/
  |  | -- jsoncatalog.txt
  |  | -- field_descriptions.json

```


#### Raw Text files:

These can be input in one of two ways.
The first is as a directory of files:

*  `files/texts/raw`
This folder should contain a uniquely named .txt file for every item in your collection of texts 
that you want to build a bookworm around. The files may be stored in subdirectories: if so, their identifier key
should include the full path to the file.

The second, which will be faster in most cases, is as a *single file*. In this format, each line consists of the file's unique identifier, followed by a tab, followed by the **full text** of that file. Note that you'll have to strip out all newlines and returns from original documents. In the event that an identifier is used twice, behavior is undefined.

#### Metadata about each file.

*  `files/metadata/jsoncatalog.txt` with one JSON object per line. All JSON objects must have the same keys. There should be no new line or tab characters in this file.

Fill `files/texts/raw/` with .txt files containing the raw text from summaries of bills introduced into Congress. Each .txt file must be uniquely named and contain the text from the summary of a single bill. Then, we will create the `files/metadata/jsoncatalog.txt` file which will hold metadata for each bill, including a field that links each JSON object to a .txt file in `files/texts/raw/`.

Included in the [congress_api](http://github.com/econpy/congress_api) repo is a script `congress_parser.py` which we'll run to create `jsoncatalog.txt` and all the .txt files.

```
cd ../congress_api
python congress_parser.py
```

#### Metadata about the metadata!

Now create a file in the `files/metadata/` folder called `field_descriptions.json` which is used to define the type of variable for each variable in `jsoncatalog.txt`. For this demo, copy the following JSON object into `field_descriptions.json`:

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
The structure of the arguments needed by `OneClick.py` to build the database are the following:

```
python OneClick.py dbname dbuser dbpassword
```

Here, that would look like this:

```
python OneClick.py bookwormcongress foobar mysecret
```

The database **bookwormcongress** will be created if it does not exist. Both **dbuser** and **dbpassword** should have been defined [earlier](https://github.com/bmschmidt/Presidio#required-mysql-database) in this tutorial.

Depending on the total number and average size of your texts, this could take a while. Sit back and relax.

### General Workflow ###
For reference, the general workflow of OneClick.py is the following:

1. Derive `files/metadata/field_descriptions_derived.json` from `files/metadata/field_descriptions.txt`.
2. Derive `files/metadata/jsoncatalog_derived.txt` from `files/metadata/jsoncatalog.json`, respectively.
3. Initialize connection to the MySQL database.
4. Create metadata catalog files in `files/metadata/`.
5. Build the directory structure in `files/texts/`.
6. Clean and tokenize unigrams and bigrams.
7. Create a table with all words.
8. Encode unigrams and bigrams.
9. Load data into MySQL database.
10. Create temporary MySQL table and .json file that will be used by the web app.
11. Create API settings.
