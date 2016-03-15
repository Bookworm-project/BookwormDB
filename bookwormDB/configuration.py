#!/usr/bin/python

import ConfigParser
import os
import re


def create():
    """
    Through interactive prompts at the command line, builds up a file at 
    bookworm.cnf that can be used to set preferences for the installation.
    """

    
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
    Usually the user can just hit enter.
    """

    systemConfigFile = ConfigParser.ConfigParser(allow_no_value=True)

    #It checks each of these files for defaults in turn

    systemConfigFile.read(["/.my.cnf",os.path.expanduser("~/my.cnf"),os.path.expanduser("~/.my.cnf"),"/etc/mysql/my.cnf","/etc/my.cnf","/root/.my.cnf","bookworm.cnf"]);

    defaults = dict()
    #The default bookwormname is just the current location
    defaults['database'] = os.path.relpath(".","..")
    defaults["user"] = ""
    defaults["password"] = ""



    for field in ["user","password"]:
        try:
            print systemConfigFile.get("client",field)
            defaults[field] = systemConfigFile.get("client",field)
        except ConfigParser.NoSectionError:
            print systemConfigFile.get("mysql",field)
            defaults[field] = systemConfigFile.get("mysql",field)

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


import ConfigParser
import os
import MySQLdb
import sys
import argparse
import getpass
import subprocess
import logging

class Configfile:
    def __init__(self,usertype,possible_locations=None,default=None):
        """
        Initialize with the location of the file. The last encountered file on the list is the one that will be used.
        If default is set, a file will be created at that location if none of the files in possible_locations exist.
        """

        self.usertype = usertype

        if possible_locations is None:
            possible_locations = self.default_locations_from_type(usertype)
        self.location = None
        
        self.config = ConfigParser.ConfigParser(allow_no_value=True)
        
        for string in possible_locations:
            if os.path.exists(string):
                self.location=string

        if self.location is None:
            if default is None:
                raise IOError("No mysql configuration file could be found for the %s user, and no default to create" %usertype)
            else:
                self.location=default
                logging.info("No configuration files at at any of [%s]. Creating a new configuration file for %s at %s" %(",".join(possible_locations),self.usertype,self.location))
        else:
            logging.info("Reading configuration file for %s from %s" %(self.usertype,self.location))
        
    def meta_locations_from_type(self):
        """
        Set the local ConfigParser to contain values from an appropriate stack 
        of configuration files for MySQL.

        For 'local' access, for example, it uses a local file at "bookworm.cnf", 
        and then looks for global (select-only) settings, and finally uses 
        administrative settings for values that exist nowhere else.

        They appear front-to-back in the arrays below because 

        For sanity sake, only admin has any chance at getting root access.
        """
        admin = self.default_locations_from_type("admin")
        glob = self.default_locations_from_type("global")
        root = self.default_locations_from_type("root")
        local = self.default_locations_from_type("local")
        if self.usertype=="admin":
            return glob + root + admin
        if self.usertype=="global":
            return admin + local + glob
        if self.usertype=="local":
            return admin + glob + local

    def read_config_files(self):
        used_files = self.meta_locations_from_type()
        try:
            self.config.read(used_files)
        except ConfigParser.MissingSectionHeaderError:
            """
            Some files throw this error if you have an empty
            my.cnf. This throws those out of the list, and tries again.
            """
            for file in used_files:
                try:
                    self.config.read(file)
                except ConfigParser.MissingSectionHeaderError:
                    used_files.remove(file)
            successes = self.config.read(used_files)
            print successes
            
    def default_locations_from_type(self,usertype):
        if usertype == "root":
            return ["/root/.my.cnf"]
        if usertype=="admin":
            return [os.path.abspath(os.path.expanduser("~/.my.cnf"))
                    ,os.path.abspath(os.path.expanduser("~/my.cnf"))]
        if usertype=="global":
            return ["/usr/etc/my.cnf","/etc/mysql/my.cnf","/etc/my.cnf","/etc/mysql/conf.d/mysql.cnf","/etc/bookworm/my.cnf"]
        if usertype=="local":
            # look for a bookworm.cnf file in or above the current directory.
            # Max out at 20 directory levels deep because let's be reasonable.
            return ["../"*i + "bookworm.cnf" for i in range(20,-1,-1)]
        else:
            return []

    def ensure_section(self,section):
        if not self.config.has_section(section):
            self.config.add_section(section)

    def change_client_password(self):
        """
        Changes the client password in the config file AND updates the MySQL server with the new password at the same time.
        """
        try:
            db = MySQLdb.connect(read_default_file="~/.my.cnf")
            db.cursor().execute("GRANT SELECT ON *.* to root@localhost")
        except MySQLdb.OperationalError, message:
            user = raw_input("Can't log in automatically: Please enter an *administrative* username for your mysql with grant privileges: ")
            password = raw_input("Now enter the password for that user: ")
            db = MySQLdb.connect(user=user,passwd=password)
            
        cur = db.cursor()
        self.ensure_section("client")
        try:
            user = self.config.get("client","user")
        except ConfigParser.NoOptionError:
            if self.usertype=="root":
                user = "root"
                self.config.set("client","user","root")
            else:
                user = raw_input("No username found for the user in the %s role.\nPlease enter the name for the %s user: " %(self.usertype,self.usertype))
                self.config.set("client","user",user)

        confirmation = 1
        new_password = 0

        while not confirmation == new_password:
            new_password = raw_input("Please enter a new password for user " + user + ", or hit enter to keep the current password: ")
            if new_password=="":
                new_password=self.config.get("client","password")
                break
            confirmation = raw_input("Please re-enter the new password for " + user + ": ")
        try:
            cur.execute("SET PASSWORD FOR '%s'@'localhost'=PASSWORD('%s')" % (user.strip('"').strip("'"),new_password.strip('"').strip("'")))
        except MySQLdb.OperationalError, message:	# handle trouble
            errorcode = message[0]
            if errorcode==1133:
                logging.info("creating a new %s user called %s" %(self.usertype,user))
                if self.usertype=="admin":
                    cur.execute("GRANT ALL ON *.* TO '%s'@'localhost' IDENTIFIED BY '%s' WITH GRANT OPTION" % (user,new_password))
                if self.usertype=="global":
                    cur.execute("GRANT SELECT ON *.* TO '%s'@'localhost' IDENTIFIED BY '%s'" % (user,new_password))
            else:
                raise
        self.config.set("client","password",new_password)

    def set_bookworm_options(self):
        """
        A number of specific MySQL changes to ensure fast queries on Bookworm.
        """
        self.ensure_section("mysqld")
        
        mysqldoptions = {"max_allowed_packet":"512M","sort_buffer_size":"8M","read_buffer_size":"4M","read_rnd_buffer_size":"8M","bulk_insert_buffer_size":"512M","myisam_sort_buffer_size":"512M","myisam_max_sort_file_size":"1500G","key_buffer_size":"1500M","query_cache_size":"32M","tmp_table_size":"1024M","max_heap_table_size":"1024M","character_set_server":"utf8","query_cache_type":"1","query_cache_limit":"2M"}

        for option in mysqldoptions.keys():
            if not self.config.has_option("mysqld",option):
                self.config.set("mysqld",option,mysqldoptions[option])
            else:
                if mysqldoptions[option] != self.config.get("mysqld",option):
                    choice = raw_input("Do you want to change the value for " + option + " from " + self.config.get("mysqld",option) + " to the bookworm-recommended " + mysqldoptions[option] + "? (y/N): ")
                    if choice=="y":
                        self.config.set("mysqld",option,mysqldoptions[option])
                                       
    def write_out(self):
        self.config.write(open(self.location,"w"))

def change_root_password_if_necessary():
    """
    The root password should not be "root". So we change it if it is.
    """
    try:
        db = MySQLdb.connect(user="root",passwd="root",host="localhost")
        print "'root' is an insecure root password for MySQL: starting a process to change it. You can just re-enter 'root' if you want."
    except:
        try:
            db = MySQLdb.connect(user="root",passwd="",host="localhost")
            print "Your root MySQL password is blank; starting a process to change it. You can just hit return at the prompts to keep it blank if you want."
        except:
            print "Root mysql password is neither blank nor 'root', so it's up to you to change it."
            return

    root = Configfile("root",default="/root/.my.cnf")
    root.change_client_password()
    root.write_out()
    print """
    root .my.cnf file updated with password at %s; delete that file if you don't want the root password anywhere on your server.
    """ % root.location
  
def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("--sub","-s",help="run as subprocess")
    parser.add_argument("--force","-f",help="run as subprocess",action="store_true",default=False)
    parser.add_argument("users",nargs="+",choices=["admin","global","root"])
    return parser.parse_args()

def update_settings_for(name):
    """
    There are three roles: different things need to be changed for each.
    """
    if name=="root":
        change_root_password_if_necessary()
    if name=="admin":
        default_cnf_file_location = raw_input("Please enter the full path (no tildes) for the home directory of the user who will be the administrator.\nFor example, if your username is 'mrubio', on OS X it might be /Users/mrubio/: ")
        admin = Configfile("admin",[default_cnf_file_location + "/" + ".my.cnf"],default=default_cnf_file_location + ".my.cnf")
        admin.change_client_password()
        admin.write_out()
    if name=="global":
        system = Configfile("global",default="/etc/my.cnf")
        system.change_client_password()
        system.set_bookworm_options()
        system.write_out()
        

def reconfigure_passwords(names_to_parse,force=False):
    """
    Takes a list of roles to reset passwords for, and
    then

    force indicates that it will go ahead and reset the admin role
    while logged in as root, or other strange situations that arise
    that seem like a bad idea.

    """
    names_to_parse = set(names_to_parse)
    whoami = getpass.getuser()

    # Some names need to be run as root. Here we disentangle, and launch
    # a subprocess as root for those that do.
    privileged_names = names_to_parse.intersection(['global','root'])
    unprivileged_names = names_to_parse.intersection(['admin'])

    if len(privileged_names) > 0 and whoami != "root":
        # Some of these can only be automatically upgraded as root, probably.
        # We could try-catch this, I guess, but it's such a tiny set right now.
        print "Using sudo to process password change(s) for " + " and ".join(list(privileged_names)) + ". The system may now request your root password." 
        subprocess.call(["sudo","bookworm","config","mysql","--users"] + list(privileged_names))
        names_to_parse = unprivileged_names

    if "admin" in names_to_parse and whoami=="root":
        if not args.force:
            print "You're trying to update the admin user while logged in as root (using sudo?)" 
            print "That's confusing to me; if you're only going to run admin operations as root,"
            print "just set the root password."

    for name in names_to_parse:
        update_settings_for(name)
