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
import datetime
import http


def usage():
    print('Recursively downloads from http urls matching a regexp:\n')
    print('{0} [-r url_regex] url1 [url2] ... [urln]'.format(sys.argv[0]))
    print()
    print('''Options:
    -v --verbose:       verbose execution
    -h --help:          this help
    -r --regex:         regex for urls to download
    -c --cokiefile:     specify a cookie file to use
    ''')


def est_finish(started, done, total):
    '''Return a datetime object estimating date of finishing. @param started is a datetime object when the job started, @param done is the number of currently done elements and @total is the remaining elements to do work on.'''
    if not total or total <= 0 or done <= 0:
        return datetime.datetime.now()
    delta = datetime.datetime.now() - started
    remaining = (delta.total_seconds() * total) / done
    res = datetime.datetime.now() + datetime.timedelta(seconds=remaining)
    return res.strftime('%Y-%m-%d %H:%M')

def getTerminalSize():
    '''returns terminal size as a tuple (x,y)'''
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (25, 80)
    return int(cr[1]), int(cr[0])



class ProgressBar:
    def __init__(self, minValue = 0, maxValue = 10, totalWidth=getTerminalSize()[0]):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = int(minValue)
        self.max = int(maxValue)
        self.span = self.max - self.min
        self.width = totalWidth
        self.done = 0
        self.percentDone_last = -1
        self.percentDone = 0
        self.updateAmount(0)  # Build progress bar string
        self.lastMsg = ''

    def updateAmount(self, done = 0, msg=''):
        if done < self.min:
            done = self.min

        if done > self.max:
            done = self.max

        self.done = done

        if self.span == 0:
            self.percentDone = 100
        else:
            self.percentDone = int(((self.done - self.min) * 100) / self.span)

        if self.percentDone == self.percentDone_last and self.lastMsg == msg:
            return False
        else:
            self.percentDone_last = self.percentDone

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (self.percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

        # figure out where to put the percentage, roughly centered
        if not msg:
            percentString = str(self.percentDone) + "%"
        else:
            percentString = str(self.percentDone) + "%" + ' ' + msg

        percentString = '{0}% {1}'.format(str(self.percentDone),msg)

        percentPlace = len(self.progBar)//2 - len(percentString)//2
        if percentPlace < 0:
            percentPlace = 0

        # slice the percentage into the bar
        self.progBar = self.progBar[0:percentPlace] + percentString[:allFull] + self.progBar[percentPlace+len(percentString):]
        return True

    def __call__(self, amt, msg='', force=False):
        if self.updateAmount(amt, msg):
            sys.stdout.write(str(self))
            if sys.stdout.isatty():
                sys.stdout.write("\r")
            else:
                sys.stdout.write("\n")
            sys.stdout.flush()


    def __str__(self):
        return str(self.progBar)


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

def humansize(nbytes):
    if nbytes:
        nbytes = int(nbytes)
        p = [('TiB', 40), ('GiB', 30), ('MiB', 20), ('KiB', 10), ('B', 0)]
        for (pk,pv) in p:
            if nbytes > (1<<pv):
                return '{0:.1f} {1}'.format(nbytes / (1<<pv), pk)
        return '0 B'
    return nbytes

class Rate(object):
    def __init__(self, min_delta_t = 1):
        self.nbytes_last = 0
        self.min_delta_t = min_delta_t
        self.tprev = None
        self.prev_rate = ' - '
        pass

    def __call__(self, nbytes):
        if not self.tprev:
            self.tprev = datetime.datetime.now()
            self.nbytes_last = nbytes
            return self.prev_rate

        delta_t = (datetime.datetime.now() - self.tprev).total_seconds()

        if delta_t > self.min_delta_t:
            delta_b = nbytes - self.nbytes_last
            rate = delta_b / delta_t
            self.prev_rate = humansize(rate) + '/s'
            self.tprev = datetime.datetime.now()

        return self.prev_rate

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


def parse_cookie_file(content):
    """returns a dict of tuples of domain => cookie => value"""
    host_cookies = dict()
    for line in content.decode().split(os.linesep):
        line = line.rstrip()
        if not re.match("^#", line) and line:
            try:
                fields = line.split("\t")
                cookie = host_cookies.get(fields[0], {})
                if len(fields) == 7:
                    cookie[fields[5]] = fields[6]
                else:
                    cookie[fields[5]] = ''
                host_cookies[fields[0]] = cookie
            except IndexError:
                sys.stderr.write("warning: ignoring cookiefile entry with insufficient fields: {0}".format(line))
    return host_cookies

def without_port(netloc):
    colon_pos = netloc.rfind(':')
    if colon_pos > 0:
        return netloc[:colon_pos]
    return netloc

def remove_first_dot(netloc):
    if netloc[0] == '.':
        return netloc[1:]
    return netloc

class Crawler(object):
    ROOTFILENAME = '_root_'

    linkregex = re.compile('<a\s(?:.*?\s)*?href=[\'"](.*?)[\'"].*?>', re.IGNORECASE)
    def __init__(self, urls, **kvargs):
        self.tocrawl = set(urls)
        self.crawled = set([])

        self.urlre = re.compile(kvargs['regex']) if kvargs.get('regex') else None

        for i in ['regex', 'verbose', 'cookiefile']:
            self.__setattr__(i, kvargs.get(i, None))

        self.host_cookies = None
        if self.cookiefile:
            if os.path.isfile(self.cookiefile):
                self.host_cookies = parse_cookie_file(open(self.cookiefile, "rb").read())
            else:
                raise RuntimeError("Crawler error: cookie file {0} not found", self.cookiefile)


    @staticmethod
    def save_local(url, response, parsed_url, verbose=None):
        localpath = url_to_localpath(parsed_url)
        print('Destination:',localpath)
        (localdir, localfile) = os.path.split(localpath)
        if not localfile:
            localfile = Crawler.ROOTFILENAME

        new_localpath = os.path.join(localdir, localfile)
        xmkdir(localdir)
        if os.path.exists(new_localpath):
            logging.warn('{0} exists, won\'t overwrite'.format(new_localpath))
            return

        length = response.getheader('content-length') if isinstance(response, http.client.HTTPResponse) else None
        pb = None
        start = None

        #if verbose:
        print()
        if length:
            length = int(length)
            pb = ProgressBar(0, length)
            start = datetime.datetime.now()

        rate = Rate()
        with io.open(new_localpath, 'wb') as fd:
            total = 0
            while True:
                s = response.read(8192)

                total += len(s)
                if pb:
                    pb(total, humansize(total) + ' @ ' + rate(total) + ' ETA: ' + est_finish(start, total, length))
                elif verbose:
                    sys.stdout.write('\r')
                    sys.stdout.write('{0} bytes read'.format(total))
                if s:
                    fd.write(s)
                else:
                    print('{0} saved'.format(localfile))
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
                link = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path + link
                res.append(link)
            else:
                pass
        return res

    def process_links(self, links):
        for link in links:
            link = normalize(link)
            if link not in self.crawled:
                #if self.verbose:
                #    print('Check {0}'.format(link))
                if self.urlre and self.urlre.match(link):
                    print('Recursing link {0}'.format(link))
                    self.tocrawl.add(normalize(link))
                else:
                    if self.verbose:
                        print('Not recursing link {0}'.format(link))


    def add_cookies(self, url_opener, parsed_url, host_cookies):
        if not host_cookies:
            return

        assert(isinstance(parsed_url, urllib.parse.ParseResult))
        url_host = without_port(parsed_url.netloc)

        # FIXME so far ignoring the port on the cookie file
        for (host, cookies) in host_cookies.items():
            host = without_port(host)
            #print('url_host', url_host)
            if url_host == host or url_host.endswith(remove_first_dot(host)):
                for (k, v) in cookies.items():
                    if self.verbose:
                        print('Using cookie "{0}: {1}" for host {2}'.format(k, v, url_host))
                    url_opener.add_header('Cookie', '{0}={1}'.format(k,v))


    def __call__(self):
        while True:
            try:
                current_url = self.tocrawl.pop()

            except KeyError:
                print('All finished.')
                return

            parsed_url = urllib.parse.urlparse(current_url)
            try:
                print()
                print('GET {0}'.format(current_url))
                request = urllib.request.Request(url = current_url)
                self.add_cookies(request, parsed_url, self.host_cookies)
                response = urllib.request.urlopen(request)

                length = response.getheader('content-length')
                print('-> ', response.getcode(), response.getheader('Content-Type'), humansize(length))
                print()

            except KeyboardInterrupt:
                raise
            except RuntimeError as e:
                logging.error('urlopen failed: {0}, {1}'.format(current_url, e))
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
                    self.process_links(links)

                except UnicodeDecodeError as e:
                    logging.error('Failed decoding "{0}" with charset "{1}": {2}'.format(current_url, encoding, str(e)))
                    pass

                Crawler.save_local(current_url, io.BytesIO(content), parsed_url, self.verbose)

            else:
                Crawler.save_local(current_url, response, parsed_url, self.verbose)
                self.crawled.add(normalize(current_url))
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhr:c:", ["help", "regex=", "cookiefile=", 'verbose'])
    except getopt.GetoptError as err:
        print(err)
        usage()
        return(1)

    options = dict()
    for o, a in opts:
        if o in ("-r", "--regex"):
            options['regex'] = a

        elif o in ("-c", "--cookiefile"):
            options['cookiefile'] = a

        elif o in ('-v', '--verbose'):
            options['verbose'] = True

        elif o in ("-h", "--help"):
            usage()
            return(1)

        else:
            assert False, "unhandled option"

    if not len(args):
        usage()
        return(1)

    crawler = Crawler(args, **options)
    crawler()

if __name__ == '__main__':
    sys.exit(main())
