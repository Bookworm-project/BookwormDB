# -*- coding: utf-8 -*-

from bookwormDB.manager import BookwormManager
import unittest
import logging
import os
import sys

class Bookworm_Configuration(unittest.TestCase):

    def test_config(self):
        """
        Çķłæīĳåıĸåįĸĩä»¶

        Args:
            self: (todo): write your description
        """
        bookworm = BookwormManager(None, "federalist_bookworm")        

        
if __name__=="__main__":
    # The setup is done without verbose logging; any failure
    # causes it to try again.
    unittest.main()
