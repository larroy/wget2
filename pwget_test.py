#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Description"""

__author__ = 'Pedro Larroy'

import os
import sys

import pwget
import unittest


class CrawlerTest(unittest.TestCase):
    def setUp(self):
        self.assertFalse(os.path.isdir("google.com"))

    def test_simple(self):
        crawler = pwget.Crawler(['http://google.com'], None, True)
        crawler()
        self.assertTrue(os.path.isdir("google.com"))

if __name__ == '__main__':
    unittest.main()

