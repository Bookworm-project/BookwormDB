# About #
[Presidio](https://github.com/bmschmidt/Presidio "Presidio") is the code repository for building the database and tables used with a Bookworm [web app](https://github.com/econpy/BookwormGUI "GUI") and [API](https://github.com/bmschmidt/BookwormAPI "Bookworm API").

# Files to Start With #
* A MySQL database you are authorized to edit and a *my.cnf* file that python can load with your permissions.
*  **../metadata/jsoncatalog.txt**: A file with one JSON object per line. All JSON objects should have the same keys. There should be no new line or tab characters in this file. A sample set of lines in jsoncatalog.txt may look something like this:

```
{"title":"Adventures of Huckleberry Finn", "author":"Mark Twain", "pubyear":"1885", "authorbirth":"1835", "authorsex":"Male"}
{"title":"The Great Gatsby", "author":"F. Scott Fitzgerald", "pubyear":"1925", "authorbirth":"1896", "authorsex":"Male"}
{"title":"Moby-Dick", "author":"Herman Melville", "pubyear":"1851", "authorbirth":"1819", "authorsex":"Male"}
{"title":"Harry Potter and the Philosopher's Stone", "author":"J. K. Rowling", "pubyear":"1997", "authorbirth":"1965", "authorsex":"Female"}
```
*  **../texts/raw**: This folder should contain a uniquely named *.txt* file for every item in your collection that you want to build a bookworm around. If the example *jsoncatalog.txt* file above was the one we were using, then the *../texts/raw* directory should contain 4 *.txt* files, each with the full text of a book.

# Running #
Once everything described above is in place, building the database is done via a command like this:

```python
python OneClick.py dbname dbuser dbpassword
```
 * **dbname**: Will create if it doesn't exist.
 * **dbuser** & **dbpassword**: These need to be setup with the database ahead of time.
