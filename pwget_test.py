#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-
"""Description"""

__author__ = 'Pedro Larroy'

import os
import sys
import shutil
import io

import pwget
import unittest
import doctest


class CrawlerTest(unittest.TestCase):
    def setUp(self):
        self.assertFalse(os.path.isdir("google.com"))

    def test_simple(self):
        crawler = pwget.Crawler(['http://google.com'])
        crawler()
        self.assertTrue(os.path.isdir("google.com"))
        self.assertTrue(os.path.isfile("google.com/_root_"))

    def tearDown(self):
        shutil.rmtree("google.com")

class parse_cookie_fileTest(unittest.TestCase):
    def test(self):
        self.assertEqual(pwget.parse_cookie_file(".youtube.com\tTRUE\t/\tFALSE\t1687629793\tPREF\tfv=11.2.202&al=en&f1=50000000"), {'.youtube.com': {'PREF': 'fv=11.2.202&al=en&f1=50000000'}})

class NormalizeTest(unittest.TestCase):
    def test(self):
        self.assertEqual(pwget.normalize('http://host/a/b/..'), 'http://host/a/')
        self.assertEqual(pwget.normalize('http://host/a/..'), 'http://host/')
        self.assertEqual(pwget.normalize('http://host'), 'http://host')
        self.assertEqual(pwget.normalize('http://host/'), 'http://host/')


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(pwget))
    return tests

if __name__ == '__main__':
    unittest.main()


