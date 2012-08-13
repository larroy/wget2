pwget
=====

A wget replacement written in Python3


Running
-------

To download recursively urls matching a regex do:


For example:

./pwget.py -r http://slashdot.org/tag/microsoft http://slashdot.org

Will download http://slashdot.org, and recursed links matching 'http://slashdot.org/tag/microsoft'
