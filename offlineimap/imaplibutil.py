# imaplib utilities
# Copyright (C) 2002-2007 John Goerzen <jgoerzen@complete.org>
#                    2010 Sebastian Spaeth <Sebastian@SSpaeth.de>
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

import re, socket, time, subprocess
from offlineimap.ui import getglobalui
from imaplib import *

# Import the symbols we need that aren't exported by default
from imaplib import IMAP4_PORT, IMAP4_SSL_PORT, InternalDate, Mon2num

try:
    import ssl
except ImportError:
    #fails on python <2.6
    pass

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


def new_mesg(self, s, secs=None):
            if secs is None:
                secs = time.time()
            tm = time.strftime('%M:%S', time.localtime(secs))
            getglobalui().debug('imap', '  %s.%02d %s' % (tm, (secs*100)%100, s))

class WrappedIMAP4_SSL(IMAP4_SSL):
    """Provides an improved version of the standard IMAP4_SSL

    It provides a better readline() implementation as impaplib's
    readline() is extremly inefficient. It can also connect to IPv6
    addresses."""
    def __init__(self, *args, **kwargs):
        self._readbuf = ''
        self._cacertfile = kwargs.get('cacertfile', None)
        if kwargs.has_key('cacertfile'):
            del kwargs['cacertfile']
        IMAP4_SSL.__init__(self, *args, **kwargs)

    def open(self, host = '', port = IMAP4_SSL_PORT):
        """Do whatever IMAP4_SSL would do in open, but call sslwrap
        with cert verification"""
        #IMAP4_SSL.open(self, host, port) uses the below 2 lines:
        self.host = host
        self.port = port

        #rather than just self.sock = socket.create_connection((host, port))
        #we use the below part to be able to connect to ipv6 addresses too
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

        #connected to socket, now wrap it in SSL
        try:
            if self._cacertfile:
                requirecert = ssl.CERT_REQUIRED
            else:
                requirecert = ssl.CERT_NONE

            self.sslobj = ssl.wrap_socket(self.sock, self.keyfile,
                                          self.certfile,
                                          ca_certs = self._cacertfile,
                                          cert_reqs = requirecert)
        except NameError:
            #Python 2.4/2.5 don't have the ssl module, we need to
            #socket.ssl() here but that doesn't allow cert
            #verification!!!
            if self._cacertfile:
                #user configured a CA certificate, but python 2.4/5 doesn't
                #allow us to easily check it. So bail out here.
                raise Exception("SSL CA Certificates cannot be checked with python <=2.6. Abort")
            self.sslobj = socket.ssl(self.sock, self.keyfile,
                                     self.certfile)

        else:
            #ssl.wrap_socket worked and cert is verified (if configured),
            #now check that hostnames also match if we have a CA cert.
            if self._cacertfile:
                error = self._verifycert(self.sslobj.getpeercert(), host)
                if error:
                    raise ssl.SSLError("SSL Certificate host name mismatch: %s" % error)

        #TODO: Done for now. We should implement a mutt-like behavior
        #that offers the users to accept a certificate (presenting a
        #fingerprint of it) (get via self.sslobj.getpeercert()), and
        #save that, and compare on future connects, rather than having
        #to trust what the CA certs say.

    def _verifycert(self, cert, hostname):
        '''Verify that cert (in socket.getpeercert() format) matches hostname.
        CRLs and subjectAltName are not handled.
        
        Returns error message if any problems are found and None on success.
        '''
        if not cert:
            return ('no certificate received')
        dnsname = hostname.lower()
        for s in cert.get('subject', []):
            key, value = s[0]
            if key == 'commonName':
                certname = value.lower()
                if (certname == dnsname or
                    '.' in dnsname and certname == '*.' + dnsname.split('.', 1)[1]):
                    return None
                return ('certificate is for %s') % certname
        return ('no commonName found in certificate')

    def _read_upto (self, n):
        """Read up to n bytes, emptying existing _readbuffer first"""
        bytesfrombuf = min(n, len(self._readbuf))
        if bytesfrombuf:
            # Return the stuff in readbuf, even if less than n.
            # It might contain the rest of the line, and if we try to
            # read more, might block waiting for data that is not
            # coming to arrive.
            retval = self._readbuf[:bytesfrombuf]
            self._readbuf = self._readbuf[bytesfrombuf:]
            return retval
        return self.sslobj.read(min(n, 16384))

    def read(self, n):
        """Read exactly n bytes

        As done in IMAP4_SSL.read() API. If read returns less than n
        bytes, things break left and right."""
        chunks = []
        read = 0
        while read < n:
            data = self._read_upto (n-read)
            read += len(data)
            chunks.append(data)

        return ''.join(chunks)

    def readline(self):
        """Get the next line. This implementation is more efficient
        than IMAP4_SSL.readline() which reads one char at a time and
        reassembles the string by appending those chars. Uggh."""
        retval = ''
        while 1:
            linebuf = self._read_upto(1024)
            nlindex = linebuf.find("\n")
            if nlindex != -1:
                retval += linebuf[:nlindex + 1]
                self._readbuf = linebuf[nlindex + 1:] + self._readbuf
                return retval
            else:
                retval += linebuf


class WrappedIMAP4(IMAP4):
    """Improved version of imaplib.IMAP4 that can also connect to IPv6"""

    def open(self, host = '', port = IMAP4_PORT):
        """Setup connection to remote server on "host:port"
            (default: localhost:standard IMAP4 port).
        """
        #self.host and self.port are needed by the parent IMAP4 class
        self.host = host
        self.port = port
        res = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM)

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
