#!/usr/bin/perl

$database = shift @ARGV or die "Must specify dbname";

`echo $database > WORKS.txt`;
`cp -r /var/www/OL /var/www/$database`;
`cp -r ../$database.json /var/www/$database/static/$database.json`;
`cp -r /var/www/$database/default.html /var/www/$database/$database.html`;
`cd /var/www/$database; perl setVersion.pl $database`;
