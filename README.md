About
=====
[Presidio](https://github.com/bmschmidt/Presidio "Presidio") is the code repository for building the database and tables used with a Bookworm web app and [API](https://github.com/bmschmidt/BookwormAPI "Bookworm API").


Files to Start With
===================
1. A MySQL database you are authorized to edit and a *my.cnf* file that python can load with your permissions.
2.  **../texts/raw**: This is where the actual texts are going to live, all at the same depth.They will have arbitrary, unique names. You'll have to create. 
3.  **../metadata/jsoncatalog.txt**: A file with one JSON object per line. All JSON objects should have the same keys. There should be no new line or tab characters in this file. A sample line may look something like this:
```
{"title": "Ulysses", "author": "James Joyce", "authorbirth": "1880", "authorsex": "Male"}
```  

Running
=======
Once all the settings described below are accounted for, building the database is done via a command like this:

```python
python OneClick.py dbname dbuser dbpassword
```
 * **dbname**: Will create if it doesn't exist.
 * **dbuser** & **dbpassword**: These need to be setup with the database ahead of time.
