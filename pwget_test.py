#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-
"""Description"""

__author__ = 'Pedro Larroy'

import os
import sys
import shutil

import pwget
import unittest


class CrawlerTest(unittest.TestCase):
    def setUp(self):
        self.assertFalse(os.path.isdir("google.com"))

    def test_simple(self):
        crawler = pwget.Crawler(['http://google.com'], None, True)
        crawler()
        self.assertTrue(os.path.isdir("google.com"))
        self.assertTrue(os.path.isfile("google.com/_root_"))

    def tearDown(self):
        shutil.rmtree("google.com")

if __name__ == '__main__':
    unittest.main()

