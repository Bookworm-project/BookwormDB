About
=====
This is the code repository for building the database and tables used with a Bookworm web app and API. Once all the settings described below are accounted for, building the database is done via a command like this:

```python
python OneClick.py dbname dbuser dbpassword
```
Parameters: dbname, dbuser, dbpassword
======================================
 * dbname: Will create if it doesn't exist.
 * dbuser & dbpassword: These need to be setup with the database ahead of time.


Files to Start With
===================
*  ../texts/raw: This is where the actual texts are going to live, all at the same depth. (This can be big--about a million files in a single directory is pretty common.) They will have arbitrary, unique names. You'll have to create. 
*  ../metadata/jsoncatalog.txt: a set of lines with one JSON object per line. Tabs and newlines ARE NOT currently permitted to appear in this file. Each line looks something like this:
```
{"title":"Ulysses","author":"James Joyce","authorbirth":"1880"}
```
*  A MySQL database you are authorized to edit, and a my.cnf file that python can load with your permissions.
