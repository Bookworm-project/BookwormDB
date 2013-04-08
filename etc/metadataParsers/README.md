Different files have different metadata. But some of the code will be adaptable, so they're all being saved here. These work from whatever native metadata format is being stored to create a parseable, neat little json file that the CreateDatabase python program can work with easily.

This directory also stores json definitions for different databases. These are used to control what and how metadata is acceded into the database: and they are used to create an options file that the Bookworm website can run a basic version some. (Those files may require some tweaking to produce pretty results.

Each project should have a subdirectory here to build its own metadata parsers: grander schemes (MARC-XML, DPLA data) may be placed in the main file for cross-project use. We save them here a) to backup the code--the metadata parser will be the most intensive part of most projects; and b) because that code may be generally useful. Although they're called metadataParsers, they frequently will also be pulling and configuring the raw texts themselves. Any code that preps for the main import, basically, should live here.

field_descriptions.json
-----------------------

In addition to all that specific code, there will be one other file REQUIRED by the main import. It is the json definition. See existing ones for examples. It is an array of dictionaries. Each dictionary corresponds to a single metadata field we have collected for each text. (eg, 'title' or 'year of publication'). The possible keys for that 

"field"
----------
The name of the metadata field. "Title", "Author", etc.


"type"
------
the RAW DATA TYPE of the field--primarily used for MySQL. Options are:
1. 'character': stored as a VARCHAR field. HARD LIMIT 255 characters. Anything
2. 'text': stored as a text field--soft limit of 5000 characters, though this could be changed. Useful for things like title. *Text fields cannot be stored as categorical data* in the datatype field.
3. 'integer': stored as an int.
4. 'decimal': stored as a decimal, allowing 5 before the point and 4 digits after. Currently we use this for latitude and longitude.
   ('float','logical', and other types haven't been supported yet--for now, they can generally be coerced to one of these types. For example,
  storing 'T' and 'F' as one-byte characters is not any worse for performance than storing them as logical integers.)

"datatype"
---------
###1. time
It's a time field, to be grouped by and displayed on X axes. (Note--if you want time rounding, you'll have to do the grouping beforehand, not in the database.)
*Time fields can have an additional key,"derived". For example, in the ChronAm Bookworm, you'll find this line:

``` {javascript}
 {"field":"date","datatype":"time","type":"character","unique":true,"derived":
     [
         {"resolution":"year"}, {"resolution":"month"},
         {"resolution":"day"},    
         {"resolution":"day", "aggregate":"year"}
     ]
    }
```
That means the time will be rounded to four primary resolutions (year,month, and day), along with one aggregated resolution (day of year: a number from 1 to 365.)
For large bookworms, this should be done with care: time fields each take up 4 bytes, so in a Bookworm with 10 million documents, five different time resolutions will consume about 200 MB of RAM on their own. Actually, that's not so bad.


###2. categorical
It has several options, and should display as a grouping option in the search dialogue. If you choose this, it will be converted to an integer lookup table, which can take some time but will give much faster returns on any given search.
###3. etc
It won't be used in the public Bookworm, but we keep it in the database for more specialized analysis.
###4. searchstring
It's the REQUIRED field that will display when the user clicks for search results. This will be an ugly HTML string with a link, etc. Formats are too diverse to construct this on the fly, so if you want anything to show up, it needs to be defined here.

REQUIRED FIELDS:
(it will break if you haven't defined these):

"searchstring"
"filename" (which DOESN'T include '.txt' at the end)
--at least one "time" field