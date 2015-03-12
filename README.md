## Bookworm API

This is an implementation of the API for Bookworm, written in Python. It primarily implements the API on a MySQL database now, but includes classes for more easily implementing it on top of other platforms (such as Solr).

It is used with the [Bookworm GUI](https://github.com/Bookworm-project/BookwormGUI) and can also be used as a standalone tool to query data from your database created by [the BookwormDB repo](https://github.com/Bookworm-project/BookwormDB).
For a more interactive explanation of how the GUI works, see the [D3 bookworm browser](http://benschmidt.org/beta/APISandbox)

### General Description

A file, currently at `dbbindings.py`, calls the script `bookworm/general_API.py`; that implements a general purpose API, and then further modules may implement the API on specific backends. Currently, the only backend is the one for the MySQL databases create by [the database repo](http://github.com/bookworm-project/BookwormDB).


### Installation

Currently, you should just clone this repo into your cgi-bin directory, and make sure that `dbbindings.py` is executable.

#### OS X caveat.

If using homebrew, the shebang at the beginning of `dbbindings.py` is incorrect. (It will not load your installed python modules). Change it from `#!/usr/bin/env python` to `#!/usr/local/bin/python`, and it should work.

### Usage

If the bookworm is located on your server, there is no need to do anything--it should be drag-and-drop. (Although on anything but debian, settings might require a small amount of tweaking.

If you want to have the webserver and database server on different machines, that needs to be specified in the configuration file for mysql that this reads: if you want to have multiple mysql servers, you may need to get fancy.

This tells the API where to look for the data for a particular bookworm. The benefit of this setup is that you can have your webserver on one server and the database on another server.

