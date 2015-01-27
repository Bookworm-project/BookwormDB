#!/usr/bin/python

import ConfigParser

my = ConfigParser.SafeConfigParser(allow_no_value=True)

systemFile = "/etc/mysql/my.cnf"

if not my.read([systemFile]):
    systemFile = "/etc/my.cnf" #OS X location, for me.
    if not my.read([systemFile]):
        print "Unable to find a working file, just writing to /etc/my.cnf"

if not my.has_section("mysqld"):
    my.add_section("mysqld")

mysqldoptions = {"max_allowed_packet":"512M","sort_buffer_size":"8M","read_buffer_size":"4M","read_rnd_buffer_size":"8M","bulk_insert_buffer_size":"512M","myisam_sort_buffer_size":"512M","myisam_max_sort_file_size":"1500G","key_buffer_size":"1500M","query_cache_size":"32M","tmp_table_size":"1024M","max_heap_table_size":"1024M","character_set_server":"utf8","query_cache_type":"1","query_cache_limit":"2M"}

for option in mysqldoptions.keys():
    if not my.has_option("mysqld",option):
        my.set("mysqld",option,mysqldoptions[option])

my.write(open(systemFile,"w"))
