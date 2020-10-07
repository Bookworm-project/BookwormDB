import os
from setuptools import setup


setup(
    name='bookwormDB',
    packages=["bookwormDB"],
    version='0.5',
    entry_points={
        'console_scripts': [
            'bookworm = bookwormDB.manager:run_arguments'
        ],
    },
    description="Create, deploy, and serve a Bookworm instance.",
    long_description="\n".join(open("README.rst").readlines()),
    package_data={'bookwormDB':['etc/*','bin/*']},
    url="http://github.com/Bookworm-Project",
    author="Benjamin Schmidt",
    author_email="bmschmidt@gmail.com",
    license="MIT",
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Topic :: Sociology :: History",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Text Processing :: Linguistic"
    ],
    install_requires=["numpy","pandas","mysqlclient",
                      "python-dateutil", "psutil", "bounter",
                      "gunicorn"
    ]
)
