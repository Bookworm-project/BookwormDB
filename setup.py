import os
from distutils.core import setup



setup(name='bookwormDB',
      packages=["bookwormDB"],
      version='1.0.0a',
      scripts=["bookworm"],
      description="Create, deploy, and serve a Bookworm instance.",
      package_data={'bookwormDB':['etc/*']}
)
