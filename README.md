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

The General Workflow
====================
*  Run python Oneclick.py $project $username $password", which builds the database for you, assuming your my.cnf file is working,
*  Set up a bookworm installation with the Bookworm code and the API implementation: the file at WebsiteCreate.pl will do this locally on Chaucer, but details will be different for different servers.
*  Ensure that the user you specified in the create call has select permissions on the MySQL database, and that its password is specified in /etc/mysql/my.cnf.
*  Plug the settings in the API_SETTINGS table that has been create at the end of the hash at the beginning of 
(I know this is a pain--at some point we'll have to think of a way to update this automatically. The problem is that we need to explicitly tell the website what database to query, and it can't just pull that from the database. Probably this file should live somewhere in the web directory, or even the options settings, but that would make API calls much more complicated, and that's an extremely bad thing in my mind. (Far worse than a more circuitous set-up).

Adding new files is not currently supported--you just have to rebuild the database. We'll have to write a couple new methods to take care of that.
