#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-
"""Description"""

__author__ = 'Pedro Larroy'
__version__ = '0.1'

import os
import sys
import subprocess

import re

import shutil
import urllib.parse
import tempfile




def find_files_re(path, regex=None):
    """Find files in path matching regex, returns a list"""
    if not os.path.isdir(path):
        raise RuntimeError('{0}: not a directory'.format(path))

    result = []
    cregex = None
    if regex:
        cregex = re.compile(regex)

    for dirpath, dirnames, filenames in os.walk(path):
        #print dirpath, dirnames, filenames
        if re.search('^\.[^/]', dirpath):
            #sys.stderr.write('Skipping {0}\n'.format(dirpath))
            continue

        for f in filenames:
            #print 'match {0} against {1}'.format(f,sys.argv[2])
            if not cregex or (cregex and cregex.match(f)):
                #print 'match: ',f
                full_file_path = os.path.join(dirpath, f)
                result.append(full_file_path)

    return result


def main():
    if len(sys.argv) != 2:
        return 1
    for f in find_files_re(sys.argv[1], ""):
        #print(f)
        pc = f.split(os.sep)
        fname = pc[-1]
        unscaped_fname = urllib.parse.unquote(fname)

        unscaped_fl = pc[:-1]
        unscaped_fl.append(unscaped_fname)
        unscaped_f = os.sep.join(unscaped_fl)

        if f != unscaped_f:
            print("move('{0}',\n     '{1}')".format(f, unscaped_f))
            shutil.move(f, unscaped_f)

    return 0

if __name__ == '__main__':
    sys.exit(main())

