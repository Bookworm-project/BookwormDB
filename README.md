[![Travis Build Status](https://travis-ci.org/Bookworm-project/BookwormDB.svg?branch=master)](https://travis-ci.org/Bookworm-project/BookwormDB)

[BookwormDB](https://github.com/bookworm-project/BookwormDB "BookwormDB") is the main code repository for the Bookworm project. Given simply formatted files and metadata, it creates an efficient and easily queryable MySQL database that can make full use of all the metadata and lexical data in the original source. It also includes a powerful API for asking a variety of unigrammatic queries about that data.

A quick walkthrough is included below: other documentation is at [bookworm.culturomics.org]() and in a [Bookworm Manual](http://bookworm-project.github.io/Docs) on this repository (editable at the repo [here](https://github.com/Bookworm-project/Docs)).

# Installation

Installation is tested on Ubuntu and OS X. It may work on other Unixes, but will not work on Windows.

1. Install some dependencies; mysql or mariadb for databases, and GNU parallel for parallel processing.
2. Download the latest release, either by cloning this git repo or downloading a zip.
3. Navigate to the folder in the terminal, and type `pip install .`.
   * If `/usr/lib/cgi-bin` is not writeable by your account,
     you may need to type `sudo pip install .` 
4. Type `bookworm --help` to confirm the executable has worked. If this doesn't work, file
   a bug report.
5. Type `bookworm config mysql` for some interactive prompts to allow Bookworm to edit MySQL databases on your server. (Note that this makes some other changes to your mysql configuration files; you may want to copy them first if you're using it for other things.)

## Releases

The `master` branch is regularly tested on Travis; you are generally best off installing the latest version.

## Related projects

This builds a database and implements the Bookworm API on particular set of texts.

Some basic, widely appealing visualizations of the data are possible with the Bookworm [web app](https://github.com/bookworm-project/BookwormGUI "Bookworm web app"), which runs on top of the API. 

A more wide-ranging set of visualizations is available built on top of D3 in the [Bookworm D3 package](http://github.com/bmschmidt/BookwormD3).
If you're looking to develop on top of Bookworm, that presents a much more flexible set of tools.

## Bookworms ##
Here are a couple of Bookworms built using [BookwormDB](https://github.com/bookworm-project/BookwormDB "Bookworm"):

1. [Open Library](http://bookworm.culturomics.org/OL/ "Open Library")
2. [ArXiv](http://bookworm.culturomics.org/arxiv/ "ArXiv")
3. [Chronicling America](http://arxiv.culturomics.org/ChronAm/ "Chronicling America")
4. [SSRN](http://bookworm.culturomics.org/ssrn/ "SSRN: Social Science Research Network")
5. [US Congress](http://bookworm.culturomics.org/congress/ "Bills in US Congress")
6. [Rate My Professor Gendered Language](http://benschmidt.org/profGender)


## Getting Started ##

### Required MySQL Database ###

The hardest part about setting up Bookworm is properly configuring the MySQL installation.
The easiest way to test out Bookworm on your home computer may be to use a VM running Ubuntu; installation is realtively easy using OS X, as well.

At the very least, there must be a MySQL user with permissions to insert + select data from all databases.
The easiest way to handle this is to have a user with root access defined in your system-wide MySQL configuration files.

This creates a bit of a security risk, though, so we recommend 2 MySQL users: an admin user with the ability to create new databases (i.e. GRANT ALL) and a second user that is only able to select data from databases (i.e. GRANT SELECT). This is for security: your data is safer if the web user can't modify it at all.

#### Setting up databases automatically

Running `bookworm config mysql` will take care of most of these tasks through an interactive prompt; `bookworm config --force mysql` will come up with automatic answers for all questions, and is suitable in a scripting situation (like setting up a variety of VMs). The configuration script will ask for a variety of different passwords, and may request an administrative password from the machine.

Restart your MySQL server after the configuration script has run.

If you encounter problems in the config script, please feel free to post issues to the project github repo.

#### Setting up databases manually

If you have an existing MySQL configuration you do not want to risk hurting, you may want to proceed by hand. 

First, create an admin user:

For example, create a user `foobar` with password `mysecret` and full access to all databases from `localhost`:

```mysql
CREATE USER 'foobar'@'localhost' IDENTIFIED BY 'mysecret';
GRANT ALL PRIVILEGES ON *.* TO 'foobar'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

Then put the credentials for that user in a file that will be automatically read when you start up MySQL. The best place for this is at `~/.my.cnf`. If multiple users on your machine will be administering the bookworm, another recommended location is `/etc/bookworm/admin.cnf`. In this example, that file would look like this:

```
[client]
user = 'foobar'
password = 'mysecret'
```


The second user would be the user that the API uses to get data for queries over the web. Note that this user has only "select" rights.

```mysql
GRANT SELECT ON *.* TO 'bookworm_client'@'localhost' IDENTIFIED BY 'otherpassword';
FLUSH PRIVILEGES;
```

Then add a section your **systemwide** `my.cnf` file (usually at `/etc/mysql/my.cnf`, `/etc/my.cnf`, or a similar location). 

```
[client]
user = 'bookworm_client'
password = 'otherpassword'
```

With these settings in place, you're ready to begin building a Bookworm. See [the walkthrough](#walkthrough) for a fuller example.


## The query API

This distribution also includes two files, general_api.py and SQLapi.py, which together constitute an implementation of the API for Bookworm, written in Python. It primarily implements the API on a MySQL database now, but includes classes for more easily implementing it on top of other platforms (such as Solr).

It is used with the [Bookworm GUI](https://github.com/Bookworm-project/BookwormGUI) and can also be used as a standalone tool to query data from your database. To run the API in its most basic form, type `bookworm query $string`, where $string is a json-formatted query.

An executable is bundled in the distro at `bookwormdb/bin/dbbindings.py` that, when placed in your cgi-bin folder, will serve the API over to and from the web; when you install bookworm, it attempts to move this into a web directory for you.

While the point of the command-line tool `bookworm` is generally to *create* a Bookworm, the point of the query API is to retrieve results from it.

For a more interactive explanation of how the GUI works, see the [D3 bookworm browser](http://benschmidt.org/D3/APISandbox) (Sorry, this is broken for the moment).

### Installing the API.

On most systems, `pip install .` in the `bookwormDB` dir should deposit a copy in an appropriate location on your system (such as `/usr/lib/cgi-bin`).

If that doesn't work, just run `cp bookwormDB/bin/dbbindings.py /usr/lib/cgi-bin` (exact locations may vary) to place it in the correct place.

If using homebrew on OS X, the shebang at the beginning of `dbbindings.py` may be incorrect. (It will not load your installed python modules). Change it from `#!/usr/bin/env python` to `#!/usr/local/bin/python`, and it should work. (Or you can fix the PYTHONPATH that apache uses as [described here](https://github.com/Bookworm-project/BookwormDB/issues/81), but that is considerably harder than just changing the bookworm code.


Walkthrough
===========

These are some instructions on how to build a bookworm. 

> Indented bits tell you how to build on specific bookworm using [text from the summaries of bills](https://github.com/unitedstates/congress/wiki "text from the summaries of bills") introduced in the US Congress from 1973 to the present day.
> The goal is to provide everything needed to build a Bookworm using publically available data.

## Get the Data ##

First off, you need a collection of texts to analyze. Ideally this should be more than 1000 individual texts, with some year (or other time) description.

> To download the congress data, Matt Nicklay has put together a script in another repo that will download everything you'll need. Clone that repo and run `get_and_unzip_data.py` to fetch and unzip the data:

> ```
> git clone git://github.com/bmschmidt/congress_api
> cd congress_api
> python get_and_unzip_data.py
> ```

> This will take a few minutes depending on your Internet connection and the speed of your computer. The `get_and_unzip_data.py` script simply downloads and unzips all the files in parallel using [multiprocessing](http://docs.python.org/2/library/multiprocessing.html "multiprocessing"). NOTE: Once fully unzipped, the files will take up just under 3GB of disk space.


## Prep to Build Bookworm ##

If you haven't already, install this repo on your system.

```
git clone git://github.com/Bookworm-project/BookwormDB
cd BookwormDB
python setup.py install
```

### Required Files ###

To build a bookworm, you need to build three files in the directory you plan to use. You can have whatever other files you want in the root directory. But these three names are reserved for bookworm use.

```
congress/
  | input.txt
  | jsoncatalog.txt
  | field_descriptions.json
```

#### Required files 1: input.txt:

The first is slightly more complicated than it appears.
It contains the various files you'll be reading in as unicode text.
These can be input in one of three ways.

The first, which will be faster in most cases, is as a *single file*.

* `input.txt`

In this format, each line consists of the file's unique identifier, followed by a tab, followed by the **full text** of that file. Note that you'll have to strip out all newlines and returns from original documents. In the event that an identifier is used twice, behavior is undefined.

By changing the makefile, you can also do some more complex substitutions. (See the metadata parsers for an example of a Bookworm that directly reads hierarchical, bzipped directories without decompressing first).

**Format 2** is as a directory of files:

*  `input/`

This folder should contain a uniquely named .txt file for every item in your collection of texts that you want to build a bookworm around. The files may be stored in subdirectories: if so, their identifier key should include the full path to the file (but not the trailing '.txt'). (NOTE: this is currently unimplemented)


**Format 3** is as a shell script named

*  `input_script`

That script when executed, should out a stream formatted the same as input.txt. In some cases, this will allow you to save a lot disk space and/or time. It must be executable and have a shebang on the first line designating the interpreter. (NOTE: currently unimplemented). 

> To build the congress API, we must create an `input.txt` file with raw text from summaries of bills introduced into Congress. Each line contains a unique ID and the text from the summary of a single bill. Then, we will create the `jsoncatalog.txt` file which will hold metadata for each bill, including a field that links each JSON object to a line in input.txt. Included in the [congress_api](http://github.com/bmschmidt/congress_api) repo is a script `congress_parser.py` which we'll run to create `jsoncatalog.txt` and the `input.txt` file.

> ```
> cd congress_api
> python congress_parser.py
> ```

#### Required files 2: Metadata about each file.

*  `jsoncatalog.txt` with one JSON object per line. The keys represent shared metadata for each file: the values represent the entry for that particular document. There should be no new line or tab characters in this file.

In addition to the metadata you choose, two fields are required:

1. A `searchstring` field that contains valid HTML which will be served to the user to identify the text.
   * This can be a link, or simply a description of the field. If you have a URL where the text can be read, it's best to include it inside an <a> tag: otherwise, you can just put in any text field you want in the process of creating the jsoncatalog.txt file: something like author and title is good.
  
2. A `filename` field that includes a unique identifier for the document (linked to the filename or the identifier, depending on your input format).

> Congress users have already created this file in the previous step.

#### Required Files 3: Metadata about the metadata.

Now create a file in the `field_descriptions.json` which is used to define the type of variable for each variable in `jsoncatalog.txt`.

Currently, you **do** have to include a `searchstring` definition in this, but **should not** include a filename definition.

> For the Congress demo, copy the following JSON object into `field_descriptions.json`:

> ```json
> [
>    {"field":"date","datatype":"time","type":"numeric","unique":true,"derived":[{"resolution":"month"}]},
>    {"field":"searchstring","datatype":"searchstring","type":"text","unique":true},
>    {"field":"enacted","datatype":"categorical","type":"text","unique":false},
>    {"field":"sponsor_state","datatype":"categorical","type":"text","unique":false},
>    {"field":"cosponsors_state","datatype":"categorical","type":"text","unique":false},
>    {"field":"chamber","datatype":"categorical","type":"text","unique":false}
>    ]
> ```

> Everything should now be in place and we are ready to build the database.

## Running ##

For a first run, you just want to use `bookworm init` to create the entire database (if you want to rebuild parts of a large bookworm--the metadata, for example--that is also possible.)

```
bookworm init
```

This will walk you through the process of choosing a name for your database.

Then to build the bookworm, type

```
bookworm build all
```

Depending on the total number and average size of your texts, this could take a while. Sit back and relax.

Finally, you may want to set up a GUI.

To test a local one over a python webserver, type

```
bookworm serve
```

Otherwise, you can type

```
bookworm build linechartGUI
```



### General Workflow ###
For reference, the general workflow of the Makefile is the following:

5. Build the directory structure in `files/texts/`.
1. Derive `.bookworm/metadata/field_descriptions_derived.json` from `.bookworm/metadata/field_descriptions.txt`.
2. Derive `.bookworm/metadata/jsoncatalog_derived.txt` from `.bookworm/metadata/jsoncatalog.json`, respectively.
4. Create metadata catalog files in `.bookworm/metadata/`.
7. Create a table with all words from the text files, and save the million most common for regular use.
8. Encode unigrams and bigrams from the texts into `.bookworm/encoded`
9. Load data into MySQL database.
10. Create temporary MySQL table and .json file that will be used by the web app.
11. Create API settings.


# Dependencies #

* python 2.7 (with modules):
 * ntlk (recommended, to be required)
 * numpy
 * regex (to handle complicated Unicode regular expressions for tokenization: `easy_install regex`)
 * pandas (used by the API, not this precise, set of scripts)
* parallel (GNU parallel, in versions available from apt-get or homebrew)
* MySQL v. 5.6 (will work with 5.5, but future versions may require 5.6 for some functionality; MariaDB 10.0+ is also actively supported. Some people have reported that it largely works with MySQL 5.1)
* Apache or other webserver (for front end, if you don't just want to run the simple version through `bookworm serve` that uses an obscure port.)
 


