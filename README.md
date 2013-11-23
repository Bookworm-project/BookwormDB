## Bookworm API

These Python scripts make up the API for Bookworm. 

They are used with the [Bookworm GUI](https://github.com/econpy/BookwormGUI) and can also be used as a standalone tool to query data from your database created by [Presidio](https://github.com/bmschmidt/Presidio).
For a more interactive explanation of how the GUI works, see the [D3 bookworm browser](http://github.com/bmschmidt/Presidio)

### General Description
`dbbindings.py` is called as a CGI script and uses `APIimplementation.py` to construct a database query and return the data to the web client.


### Installation

On Ubuntu, you can simply run the `Makefile` to install dependencies for the API software.

```bash
sudo make ubuntu-install
```

However, you may wish to open the Makefile and see what is going on for yourself. The idea is to move the 3 python scripts to your cgi-bin, make them executable, and make the Apache user the owner of the files.

### Usage

If the bookworm is located on your server, there is no need to do anything--it should be drag-and-drop. (Although on anything but debian, settings might require a small amount of tweaking.
If you want to have the webserver and database server on different machines, that needs to be specified in the knownhosts.py.
This tells the API where to look for the data for a particular bookworm. The benefit of this setup is that you can have your webserver on one server and the database on another server.
