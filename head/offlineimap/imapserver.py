# IMAP server support
# Copyright (C) 2002 John Goerzen
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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from imapsync import imaplib, imaputil

class IMAPServer:
    def __init__(self, username, password, hostname, port = None, ssl = 1):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.usessl = ssl
        self.delim = None
        self.root = None
        if port == None:
            if ssl:
                self.port = 993
            else:
                self.port = 143
        self.imapobj = None

    def getdelim(self):
        """Returns this server's folder delimiter.  Can only be called
        after one or more calls to makeconnection."""
        return self.delim

    def getroot(self):
        """Returns this server's folder root.  Can only be called after one
        or more calls to makeconnection."""
        return self.root

    def makeconnection(self):
        """Opens a connection to the server and returns an appropriate
        object."""

        if self.imapobj != None:
            return self.imapobj
        imapobj = None
        if self.usessl:
            imapobj = imaplib.IMAP4_SSL(self.hostname, self.port)
        else:
            imapobj = imaplib.IMAP4(self.hostname, self.port)

        imapobj.login(self.username, self.password)

        if self.delim == None:
            self.delim, self.root = \
                        imaputil.imapsplit(imapobj.list('""', '""')[1][0])[1:]
            self.delim = imaputil.dequote(self.delim)
            self.root = imaputil.dequote(self.root)

        self.imapobj = imapobj
        return imapobj
    
    def close(self):
        self.imapobj.logout()
        self.imapobj = None
