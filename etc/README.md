This folder contains files


Setup
=====

The "Bookworm" directory assumes that you already have a customized version of a LAMP stack in place to run a Bookworm server.
For computers that have not been previously configured, this will not be the case.

The scripts here help to set up a computer as a Bookworm server.
Currently, they are partially completely for Ubuntu and for CentOS; OS X is probably the next logical candidate.

**These files will overwrite your existing my.cnf file**. They will also make some generous assumptions about the amount of RAM and disk space you have available.
It may be necessary to fine-tune your mysql installation after running the script. (For example, you may not want to store your databases files on your main hard drive at /var/lib/mysql.

MetadataParsers
===============

This is code that helps to parse individual files into metadata. Since most 