import os
from distutils.core import setup

def figure_out_cgi_directory():
    """
    Try to place the cgi-scripts in a cgi dir; if that fails, bomb out to the current directory.
    """
    for dir in ["/usr/lib/cgi-bin","/Library/WebServer/CGI-Executables/","var/www/cgi-bin","/tmp","."]:
        if os.path.exists(dir):
            return dir

setup(name='bookwormDB',
      packages=["bookwormDB"],
      version='1.0.0a',
      scripts=["bookwormDB/bin/bookworm"],
      description="Create, deploy, and serve a Bookworm instance.",
      package_data={'bookwormDB':['etc/*']},
      # Copy the cgi-executable to a cgi-dir.
      data_files = [(cgi_directory,["dbbindings.py"])]
)
