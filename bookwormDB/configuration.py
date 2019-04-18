#!/usr/bin/python

from __future__ import print_function
import configparser
import os
import sys
import re
import MySQLdb
import argparse
import getpass
import subprocess
import logging
import uuid

def update():
    ## Assemble list of all bookworms on the system.
    
    bookworms = [] ### ...
    
    ## Create on-disk versions of memory tables if 'fastcat_' does not exists.

    pass

    ## Allow "'bookworm'@'localhost' IDENTIFIED BY ''" to have select access on each bookworm.

    pass

    ## Print a message about enabling access.

    pass
    
    
def create(ask_about_defaults=True, database=None):
    """
    Through interactive prompts at the command line, builds up a file at
    bookworm.cnf that can be used to set preferences for the installation.
    """
 
    if ask_about_defaults:
        print("""
    Welcome to Bookworm.
    ~~~~~~~~~~~~~~~~~~~~
    First off, let's build a configuration file. This will live
    at bookworm.cnf in the current directory: if you mistype anything,
    or want to change settings, edit it directly in that location.

    For each of the following entries, type the value you want, or hit
    enter to accept the default:

    """)
    else:
        logging.info("Auto-generating config file.")
    
    """
    First, we go to great efforts to find some sensible defaults
    Usually the user can just hit enter.
    """

    systemConfigFile = configparser.SafeConfigParser(allow_no_value=True)
    
    defaults = dict()
    # The default bookwormname is just the current location

    if database is None:
        defaults['database'] = os.path.relpath(".", "..")
    else:
        defaults['database'] = database

    defaults["user"] = "bookworm"
    defaults["password"] = ""
    
    config = configparser.ConfigParser()

    for section in ["client"]:
        config.add_section(section)

    if ask_about_defaults:
        database = input("What is the name of the bookworm [" + defaults['database'] + "]: ")
    else:
        database = defaults['database']

    config.set("client", "database", re.sub(" ","_",database))
    config.write(open("bookworm.cnf", "w"))

class Configfile(object):
    def __init__(self, usertype, possible_locations=None, default=None, ask_about_defaults=True):
        """
        Initialize with the type of the user. The last encountered file on
        the list is the one that will be used.
        If default is set, a file will be created at that location if none
        of the files in possible_locations exist.
        
        If ask_about_defaults is false, it will do a force installation.
        """
        
        if not usertype in ['read_only', 'admin']:
            raise NotImplementedError("Only read_only and admin supported")
        
        self.ask_about_defaults = ask_about_defaults
        
        logging.info("Creating configuration as " + usertype)
        
        self.usertype = usertype

        if possible_locations is None:
            possible_locations = self.default_locations_from_type(usertype)
            
        self.location = None
        
        self.config = configparser.ConfigParser(allow_no_value=True)

        if usertype=="admin":
            
            self.ensure_section("client")
            self.ensure_section("mysqld")
            
            self.config.set("client", "host", "localhost")        
            self.config.set("client", "user", "root")
            self.config.set("client", "password", "")
            
        else:
            self.ensure_section("client")
            self.config.set("client", "host", "localhost")        
            self.config.set("client", "user", "bookworm")
            self.config.set("client", "password", "")

        self.read_config_files(possible_locations)

        for string in possible_locations:
            if os.path.exists(string):
                self.location = string
        

    def read_config_files(self, used_files):
        
        try:
            self.config.read(used_files)
        except configparser.MissingSectionHeaderError:
            """
            Some files throw this error if you have an empty
            my.cnf. This throws those out of the list, and tries again.
            """
            for file in used_files:
                try:
                    self.config.read(file)
                except configparser.MissingSectionHeaderError:
                    used_files.remove(file)
            successes = self.config.read(used_files)

        

    def default_locations_from_type(self,usertype):
        """
        The default locations for each usertype.
        Note that these are in ascending order of importance:
        so the preferred location for admin and read_only configuration
        is in /etc/bookworm/admin.cnf
        and /etc/bookworm/client.cnf
        """

        if usertype=="admin":
            return [os.path.abspath(os.path.expanduser("~/.my.cnf")),
                    os.path.abspath(os.path.expanduser("~/my.cnf")),
                    "/etc/bookworm/admin.cnf"]
        if usertype == "read_only":
            return ["/etc/bookworm/client.cnf"]
        else:
            return []

    def ensure_section(self,section):
        if not self.config.has_section(section):
            self.config.add_section(section)

    def set_bookworm_options(self):
        """
        A number of specific MySQL changes to ensure fast queries on Bookworm.
        """
        self.ensure_section("mysqld")
        
        mysqldoptions = {"### = =": "THIS FILE SHOULD GENERALLY BE PLACED AT /etc/mysql/my.cnf = = = ###", "max_allowed_packet":"512M","sort_buffer_size":"8M","read_buffer_size":"8M","read_rnd_buffer_size":"8M","bulk_insert_buffer_size":"512M","myisam_sort_buffer_size":"5512M","myisam_max_sort_file_size":"5500G","key_buffer_size":"2500M","query_cache_size":"32M","tmp_table_size":"1024M","max_heap_table_size":"2048M","character_set_server":"utf8","query_cache_type":"1","query_cache_limit":"8M"}

        for option in list(mysqldoptions.keys()):
            if not self.config.has_option("mysqld",option):
                self.config.set("mysqld", option, mysqldoptions[option])
            else:
                if mysqldoptions[option] != self.config.get("mysqld",option):
                    choice = input("Do you want to change the value for " + option + " from " + self.config.get("mysqld",option) + " to the bookworm-recommended " + mysqldoptions[option] + "? (y/N): ")
                    if choice=="y":
                        self.config.set("mysqld",option,mysqldoptions[option])
                                       
    def write_out(self):
        """
        Write out a new version of the configfile to stdout. 
        The user is responsible for putting this somewhere it will
        affect the MySQL preferences
        """
        self.config.write(sys.stdout)
        
def recommend_my_cnf(known_loc = None):
    if known_loc is None:
        for loc in ["/usr/etc/my.cnf","/etc/mysql/my.cnf","/etc/my.cnf"]:
            if os.path.exists(loc):
                known_loc = loc
    if known_loc is None:
        raise FileNotFoundError("Could not find MySQL folder: pass one.")
    cnf = Configfile(usertype = 'admin', possible_locations = [known_loc])
    cnf.set_bookworm_options()
    cnf.write_out()
                    

        
def apache(self):
    print("""
    Instructions for Apache:


    First: Serve the Bookworm API over port 10012. (`bookworm serve`).

    Then: Install an Apache host on port 80.

    Then: enable proxy servers and turn off any existing cgi.

    # If you were previously using the CGI bookworm.
    `sudo a2dismod cgi`
    
    `sudo a2enmod proxy proxy_ajp proxy_http rewrite deflate headers proxy_balancer proxy_connect proxy_html`

    Then: Add the following to your '/etc/apache2/sites-available/000-default.conf'
    (or whatever site from which you run your apache.

    ~~~~~~~~~~~~~~~~

    <Proxy *>
      Order deny,allow
      Allow from all
    </Proxy>
      ProxyPreserveHost On
    <Location "/cgi-bin">
      ProxyPass "http://127.0.0.1:10012/"
      ProxyPassReverse "http://127.0.0.1:10012/"
    </Location>

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


""")
