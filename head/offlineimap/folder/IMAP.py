# IMAP folder support
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

from Base import BaseFolder
from imapsync import imaputil

class IMAPFolder(BaseFolder):
    def __init__(self, imapserver, name):
        self.name = imaputil.dequote(name)
        self.root = imapserver.root
        self.sep = imapserver.delim
        self.imapserver = imapserver
        self.imapobj = self.imapserver.makeconnection()
        self.messagelist = None

    def getuidvalidity(self):
        x = self.imapobj.status(self.getfullname(), ('UIDVALIDITY'))[1][0]
        uidstring = imaputil.imapsplit(x)[1]
        return int(imaputil.flagsplit(x)[1])
    
    def cachemessagelist(self):
        assert(self.imapobj.select(self.getfullname())[0] == 'OK')
        self.messagelist = {}
        response = self.imapobj.status(self.getfullname(), ('MESSAGES'))[1][0]
        result = imaputil.imapsplit(response)[1]
        maxmsgid = int(imaputil.flags2hash(result)['MESSAGES'])

        # Now, get the flags and UIDs for these.
        response = self.imapobj.fetch('1:%d' % maxmsgid, '(FLAGS UID)')[1]
        for messagestr in response:
            # Discard the message number.
            messagestr = imaputil.imapsplit(messagestr)[1]
            options = imaputil.flags2hash(messagestr)
            
        
