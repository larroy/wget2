#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-
# Copyright (C) 2012, Pedro Larroy Tovar
"""A wget replacement in Python, downloads urls recursively matching a regexp"""


__author__ = 'Pedro Larroy'
__version__ = '0.1'

import sys
import re
import urllib.request
import urllib.parse
import logging
import io
import getopt
import os


def usage():
    print('Recursively downloads from http urls matching a regexp:\n')
    print('{0} [-r url_regexp] url1 [url2] ... [urln]'.format(sys.argv[0]))
    print()
    print('''Options:
    -v:         verbose execution
    -h:         this help''')



def url_to_localpath(u):
    res = os.path.join(u.netloc,u.path[1:])
    if u.query:
        res += '?{0}'.format(u.query)

    if u.fragment:
        res += '#{0}'.format(u.fragment)
    return res


def normalize(url):
    x = urllib.parse.urlsplit(url)
    return urllib.parse.urlunparse((x[0],x[1].lower(),x[2],'', x[3],x[4]))


def xmkdir(d):
    rev_path_list = list()
    head = d
    while len(head) and head != os.sep:
        rev_path_list.append(head)
        (head, tail) = os.path.split(head)

    rev_path_list.reverse()
    for p in rev_path_list:
        try:
            os.mkdir(p)
        except OSError as e:
            if e.errno != 17:
                raise



class Crawler(object):

    linkregex = re.compile('<a\s(?:.*?\s)*?href=[\'"](.*?)[\'"].*?>')
    def __init__(self, urls, urlre):
        self.tocrawl = set(urls)
        self.urlre = re.compile(urlre) if urlre else None
        self.crawled = set([])

    @staticmethod
    def save_local(url, response, parsed_url, verbose=None):
        localpath = url_to_localpath(parsed_url)
        print('save_local:',localpath)
        (localdir, localfile) = os.path.split(localpath)
        if not localfile:
            localfile = '_root_'

        new_localpath = os.path.join(localdir, localfile)
        xmkdir(localdir)
        if os.path.exists(new_localpath):
            logging.warn('{0} exists, won\'t overwrite'.format(new_localpath))
            return

        if verbose:
            print()

        with io.open(new_localpath, 'wb') as fd:
            total = 0
            while True:
                s = response.read(8192)
                if verbose:
                    total += len(s)
                    sys.stdout.write('\r')
                    sys.stdout.write('{0} bytes read from {1}'.format(total, url))
                if s:
                    fd.write(s)
                else:
                    return

    @staticmethod
    def get_links(parsed_url, content):
        res = []
        links = Crawler.linkregex.findall(content)
        for link in (links.pop(0) for _ in range(len(links))):
            if link.startswith('/'):
                link = parsed_url.scheme + '://' + parsed_url.netloc + link
                res.append(link)
            elif link.startswith('#'):
                link = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path + link
                res.append(link)
            elif link.startswith('http://'):
                res.append(link)
            elif not re.match('^\w+://', link):
                link = parsed_url.scheme + '://' + parsed_url.netloc + '/' + link
                res.append(link)
            else:
                pass
        return res

    def __call__(self, verbose=False):
        while True:
            try:
                current_url = self.tocrawl.pop()

            except KeyError:
                print('All finished.')
                return

            parsed_url = urllib.parse.urlparse(current_url)
            try:
                print('GET {0}'.format(current_url))
                response = urllib.request.urlopen(current_url)
            except KeyboardInterrupt:
                raise
            except:
                logging.error('urlopen failed: {0}'.format(current_url))
                continue

            headers = dict(response.getheaders())
            if re.match('^text/html', headers['Content-Type']):
                encoding = 'utf-8'
                m = re.match('charset=(\w+)', headers['Content-Type'])
                if m:
                    encoding = m.group(0)

                content = response.read()
                self.crawled.add(normalize(current_url))
                try:
                    links = Crawler.get_links(parsed_url, content.decode(encoding))
                    for link in links:
                        link = normalize(link)
                        if link not in self.crawled:
                            if self.urlre and self.urlre.match(link):
                                print('Recursing link {0}'.format(link))
                                self.tocrawl.add(normalize(link))
                            else:
                                if verbose:
                                    print('Not recursing link {0}'.format(link))
                except UnicodeDecodeError as e:
                    logging.error('Failed decoding "{0}" with charset "{1}": {2}'.format(current_url, encoding, str(e)))
                    pass

                Crawler.save_local(current_url, io.BytesIO(content), parsed_url, verbose)

            else:
                print('Saving {0} to disk'.format(current_url))
                Crawler.save_local(current_url, response, parsed_url, verbose)
                self.crawled.add(normalize(current_url))
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhr:", ["help", "regex="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        return(1)

    options = dict()
    for o, a in opts:
        if o in ("-r", "--regex"):
            options['regex'] = a

        elif o == '-v':
            options['verbose'] = True

        elif o in ("-h", "--help"):
            usage()
            return(1)

        else:
            assert False, "unhandled option"

    if not len(args):
        usage()
        return(1)

    c = Crawler(args, options.get('regex',None))
    c(verbose=options.get('verbose',False))

if __name__ == '__main__':
    sys.exit(main())
