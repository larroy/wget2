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
    for f in find_files_re(sys.argv[1], "^_root_$"):
        print(f)
        pc = f.split(os.sep)
        tmpfile = tempfile.mktemp()
        shutil.move(f, tmpfile)
        basedir = os.sep.join(pc[:-1])
        shutil.rmtree(basedir)
        shutil.move(tmpfile, basedir)

    return 0

if __name__ == '__main__':
    sys.exit(main())

