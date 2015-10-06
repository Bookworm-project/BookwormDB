import os
from setuptools import setup


def figure_out_cgi_directory():
    """
    Try to place the cgi-scripts in a cgi dir; if that fails, bomb out to the current directory.
    """
    for dir in ["/usr/lib/cgi-bin","/Library/WebServer/CGI-Executables/","/var/www/cgi-bin","/tmp","."]:
        if os.path.exists(dir):
            return dir

setup(name='bookwormDB',
      packages=["bookwormDB"],
      version='0.4.0',
      entry_points={
            'console_scripts': [
                'bookworm = bookwormDB.manager:run_arguments'
            ],
      },
      data_files = [(figure_out_cgi_directory(),["bookwormDB/bin/dbbindings.py"])],
      description="Create, deploy, and serve a Bookworm instance.",
      long_description = open("README.rst").readlines(),
      package_data={'bookwormDB':['etc/*','bin/*']},
      url="http://github.com/Bookworm-Project",
      author="Benjamin Schmidt",
      author_email="b.schmidt@neu.edu",
      license="MIT",
      # Copy the cgi-executable to a cgi-dir.
      classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        "Natural Language :: English",
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',
        "Operating System :: Unix",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        "Topic :: Sociology :: History",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Text Processing :: Linguistic"
        ],
      install_requires= ["numpy","regex","nltk","numpy","pandas","mysql-python","python-dateutil"]
      
)
