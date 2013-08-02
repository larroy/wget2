pwget
=====

A wget replacement written in Python3

Recursively downloads from http urls matching a regexp:

./pwget.py [-r url_regex] url1 [url2] ... [urln]

Options:
    -v --verbose:       verbose execution
    -h --help:          this help
    -r --regex:         regex for urls to download
    -c --cokiefile:     specify a cookie file to use
    -o --overwrite:     force overwritting of files
    -m --mirror:        only download if size differs
    -t --time:          time to sleep between requests in seconds (float)



Running
-------

To download recursively urls matching a regex do:


For example:

./pwget.py -r http://slashdot.org/tag/microsoft http://slashdot.org

Will download http://slashdot.org, and recursed links matching 'http://slashdot.org/tag/microsoft'
