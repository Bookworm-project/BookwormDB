#!/usr/bin/python

import ConfigParser
import os
import re

print("""Welcome to Bookworm.
~~~~~~~~~~~~~~~~~~~~
First off, let's build a configuration file. This will live
at bookworm.cnf in the current directory: if you mistype anything,
or want to change settings, edit it directly in that location.

For each of the following entries, type the value you want, or hit
enter to accept the default:

""")


"""
First, we go to great efforts to find some sensible defaults
"""

systemConfigFile = ConfigParser.ConfigParser(allow_no_value=True)

#It checks each of these files for defaults in turn

systemConfigFile.read(["/.my.cnf","~/my.cnf","/etc/mysql/my.cnf","/etc/my.cnf","bookworm.cnf"]);

defaults = dict()
#The default bookwormname is just the current location
defaults['database'] = os.path.relpath(".","..")
defaults["user"] = ""
defaults["password"] = ""

for field in ["user","password"]:
    print systemConfigFile.get("client",field)
    defaults[field] = systemConfigFile.get("client",field)

config = ConfigParser.ConfigParser()

for section in ["client"]:
    config.add_section(section)

database = raw_input("What is the name of the bookworm [" + defaults['database'] + "]: ")
if database=="":
    database = defaults['database']

user = raw_input("What is the *client* username for MySQL [" + defaults["user"] + "]: ")
if user=="":
    user = defaults["user"]

password = raw_input("What is the *client* password for MySQL [" + defaults["password"] + "]: ")
if password =="":
    password = defaults["password"]


config.set("client","database",re.sub(" ","_",database))
config.set("client","password",password)
config.set("client","user",user)

config.write(open("bookworm.cnf","w"))
