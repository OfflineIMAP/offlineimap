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

from imapsync import imaplib

class IMAPServer:
    def __init__(self, username, password, hostname, port = None, ssl = 1):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.usessl = ssl
        if port == None:
            if ssl:
                self.port = 993
            else:
                self.port = 143

    def makeconnection(self):
        """Opens a connection to the server and returns an appropriate
        object."""

        imapobj = None
        if self.usessl:
            imapobj = imaplib.IMAP4_SSL(self.hostname, self.port)
        else:
            imapobj = imaplib.IMAP4(self.hostname, self.port)

        imapobj.login(self.username, self.password)
        return imapobj
    
        
