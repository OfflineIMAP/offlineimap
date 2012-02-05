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

import os
import fcntl
import re
import socket
import time
import subprocess
import threading
from hashlib import sha1

from offlineimap.ui import getglobalui
from offlineimap import OfflineImapError
from offlineimap.imaplib2 import IMAP4, IMAP4_SSL, zlib, IMAP4_PORT, InternalDate, Mon2num

try:
    import ssl
except ImportError:
    #fails on python <2.6
    pass

class UsefulIMAPMixIn(object):
    def getselectedfolder(self):
        if self.state == 'SELECTED':
            return self.mailbox
        return None

    def select(self, mailbox='INBOX', readonly=False, force = False):
        """Selects a mailbox on the IMAP server

        :returns: 'OK' on success, nothing if the folder was already
        selected or raises an :exc:`OfflineImapError`"""
        if self.getselectedfolder() == mailbox and self.is_readonly == readonly \
                and not force:
            # No change; return.
            return
        # Wipe out all old responses, to maintain semantics with old imaplib2
        del self.untagged_responses[:]
        try:
            result = super(UsefulIMAPMixIn, self).select(mailbox, readonly)
        except self.abort as e:
            # self.abort is raised when we are supposed to retry
            errstr = "Server '%s' closed connection, error on SELECT '%s'. Ser"\
                "ver said: %s" % (self.host, mailbox, e.args[0])
            severity = OfflineImapError.ERROR.FOLDER_RETRY
            raise OfflineImapError(errstr, severity)
        if result[0] != 'OK':
            #in case of error, bail out with OfflineImapError
            errstr = "Error SELECTing mailbox '%s', server reply:\n%s" %\
                (mailbox, result)
            severity = OfflineImapError.ERROR.FOLDER
            raise OfflineImapError(errstr, severity)
        return result

    def _mesg(self, s, tn=None, secs=None):
        new_mesg(self, s, tn, secs)

class IMAP4_Tunnel(UsefulIMAPMixIn, IMAP4):
    """IMAP4 client class over a tunnel

    Instantiate with: IMAP4_Tunnel(tunnelcmd)

    tunnelcmd -- shell command to generate the tunnel.
    The result will be in PREAUTH stage."""

    def __init__(self, tunnelcmd, **kwargs):
        IMAP4.__init__(self, tunnelcmd, **kwargs)

    def open(self, host, port):
        """The tunnelcmd comes in on host!"""
        self.host = host
        self.process = subprocess.Popen(host, shell=True, close_fds=True,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (self.outfd, self.infd) = (self.process.stdin, self.process.stdout)
        # imaplib2 polls on this fd
        self.read_fd = self.infd.fileno()

        self.set_nonblocking(self.read_fd)

    def set_nonblocking(self, fd):
        "Mark fd as nonblocking"
        # get the file's current flag settings
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        # clear non-blocking mode from flags
        fl = fl & ~os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, fl)

    def read(self, size):
        """data = read(size)
        Read at most 'size' bytes from remote."""

        if self.decompressor is None:
            return os.read(self.read_fd, size)

        if self.decompressor.unconsumed_tail:
            data = self.decompressor.unconsumed_tail
        else:
            data = os.read(self.read_fd, 8192)

        return self.decompressor.decompress(data, size)

    def send(self, data):
        if self.compressor is not None:
            data = self.compressor.compress(data)
            data += self.compressor.flush(zlib.Z_SYNC_FLUSH)

        self.outfd.write(data)


    def shutdown(self):
        self.infd.close()
        self.outfd.close()
        self.process.wait()


def new_mesg(self, s, tn=None, secs=None):
            if secs is None:
                secs = time.time()
            if tn is None:
                tn = threading.currentThread().getName()
            tm = time.strftime('%M:%S', time.localtime(secs))
            getglobalui().debug('imap', '  %s.%02d %s %s' % (tm, (secs*100)%100, tn, s))


class WrappedIMAP4_SSL(UsefulIMAPMixIn, IMAP4_SSL):
    """Improved version of imaplib.IMAP4_SSL overriding select()"""
    def __init__(self, *args, **kwargs):
        self._fingerprint = kwargs.get('fingerprint', None)
        if kwargs.has_key('fingerprint'):
            del kwargs['fingerprint']
        super(WrappedIMAP4_SSL, self).__init__(*args, **kwargs)

    def open(self, host=None, port=None):
        super(WrappedIMAP4_SSL, self).open(host, port)
        if (self._fingerprint or not self.ca_certs) and\
                'ssl' in locals(): # <--disable for python 2.5
            # compare fingerprints
            fingerprint = sha1(self.sock.getpeercert(True)).hexdigest()
            if fingerprint != self._fingerprint:
                raise OfflineImapError("Server SSL fingerprint '%s' for hostnam"
                      "e '%s' does not match configured fingerprint. Please ver"
                      "ify and set 'cert_fingerprint' accordingly if not set ye"
                      "t." % (fingerprint, host),
                                       OfflineImapError.ERROR.REPO)


class WrappedIMAP4(UsefulIMAPMixIn, IMAP4):
    """Improved version of imaplib.IMAP4 overriding select()"""
    pass


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
