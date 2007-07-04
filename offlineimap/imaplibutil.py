# imaplib utilities
# Copyright (C) 2002-2007 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import re, string, types, binascii, socket, time, random, subprocess, sys, os
from offlineimap.ui import UIBase
from imaplib import *

class IMAP4_Tunnel(IMAP4):
    """IMAP4 client class over a tunnel

    Instantiate with: IMAP4_Tunnel(tunnelcmd)

    tunnelcmd -- shell command to generate the tunnel.
    The result will be in PREAUTH stage."""

    def __init__(self, tunnelcmd):
        IMAP4.__init__(self, tunnelcmd)

    def open(self, host, port):
        """The tunnelcmd comes in on host!"""
        self.process = subprocess.Popen(host, shell=True, close_fds=True,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (self.outfd, self.infd) = (self.process.stdin, self.process.stdout)

    def read(self, size):
        retval = ''
        while len(retval) < size:
            retval += self.infd.read(size - len(retval))
        return retval

    def readline(self):
        return self.infd.readline()

    def send(self, data):
        self.outfd.write(data)

    def shutdown(self):
        self.infd.close()
        self.outfd.close()
        self.process.wait()
        
class sslwrapper:
    def __init__(self, sslsock):
        self.sslsock = sslsock
        self.readbuf = ''

    def write(self, s):
        return self.sslsock.write(s)

    def _read(self, n):
        return self.sslsock.read(n)

    def read(self, n):
        if len(self.readbuf):
            # Return the stuff in readbuf, even if less than n.
            # It might contain the rest of the line, and if we try to
            # read more, might block waiting for data that is not
            # coming to arrive.
            bytesfrombuf = min(n, len(self.readbuf))
            retval = self.readbuf[:bytesfrombuf]
            self.readbuf = self.readbuf[bytesfrombuf:]
            return retval
        retval = self._read(n)
        if len(retval) > n:
            self.readbuf = retval[n:]
            return retval[:n]
        return retval

    def readline(self):
        retval = ''
        while 1:
            linebuf = self.read(1024)
            nlindex = linebuf.find("\n")
            if nlindex != -1:
                retval += linebuf[:nlindex + 1]
                self.readbuf = linebuf[nlindex + 1:] + self.readbuf
                return retval
            else:
                retval += linebuf

def new_mesg(self, s, secs=None):
            if secs is None:
                secs = time.time()
            tm = time.strftime('%M:%S', time.localtime(secs))
            UIBase.getglobalui().debug('imap', '  %s.%02d %s' % (tm, (secs*100)%100, s))

def new_open(self, host = '', port = IMAP4_PORT):
        """Setup connection to remote server on "host:port"
            (default: localhost:standard IMAP4 port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        res = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM)
        self.sock = socket.socket(af, socktype, proto)

        # Try each address returned by getaddrinfo in turn until we
        # manage to connect to one.
        # Try all the addresses in turn until we connect()
        last_error = 0
        for remote in res:
            af, socktype, proto, canonname, sa = remote
            self.sock = socket.socket(af, socktype, proto)
            last_error = self.sock.connect_ex(sa)
            if last_error == 0:
                break
            else:
                self.sock.close()
        if last_error != 0:
            # FIXME
            raise socket.error(last_error)
        self.file = self.sock.makefile('rb')

def new_open_ssl(self, host = '', port = IMAP4_SSL_PORT):
        """Setup connection to remote server on "host:port".
            (default: localhost:standard IMAP4 SSL port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        #This connects to the first ip found ipv4/ipv6
        #Added by Adriaan Peeters <apeeters@lashout.net> based on a socket
        #example from the python documentation:
        #http://www.python.org/doc/lib/socket-example.html
        res = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM)
        # Try all the addresses in turn until we connect()
        last_error = 0
        for remote in res:
            af, socktype, proto, canonname, sa = remote
            self.sock = socket.socket(af, socktype, proto)
            last_error = self.sock.connect_ex(sa)
            if last_error == 0:
                break
            else:
                self.sock.close()
        if last_error != 0:
            # FIXME
            raise socket.error(last_error)
        if sys.version_info[0] <= 2 and sys.version_info[1] <= 2:
            self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)
        else:
            self.sslobj = socket.ssl(self.sock._sock, self.keyfile, self.certfile)
        self.sslobj = sslwrapper(self.sslobj)

mustquote = re.compile(r"[^\w!#$%&'+,.:;<=>?^`|~-]")

def Internaldate2epoch(resp):
    """Convert IMAP4 INTERNALDATE to UT.

    Returns seconds since the epoch.
    """

    mo = InternalDate.match(resp)
    if not mo:
        return None

    mon = Mon2num[mo.group('mon')]
    zonen = mo.group('zonen')

    day = int(mo.group('day'))
    year = int(mo.group('year'))
    hour = int(mo.group('hour'))
    min = int(mo.group('min'))
    sec = int(mo.group('sec'))
    zoneh = int(mo.group('zoneh'))
    zonem = int(mo.group('zonem'))

    # INTERNALDATE timezone must be subtracted to get UT

    zone = (zoneh*60 + zonem)*60
    if zonen == '-':
        zone = -zone

    tt = (year, mon, day, hour, min, sec, -1, -1, -1)

    return time.mktime(tt)
