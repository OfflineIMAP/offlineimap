# IMAP repository support
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

from Base import BaseRepository
from imapsync import folder, imaputil

class IMAPRepository(BaseRepository):
    def __init__(self, imapserver):
        """Initialize an IMAPRepository object.  Takes an IMAPServer
        object."""
        self.imapserver = imapserver
        self.imapobj = imapserver.makeconnection()

    def getfolders(self):
        retval = []
        for string in self.imapobj.list(self.imapserver.root)[1]:
            flags, delim, name = imaputil.imapsplit(string)
            if '\\Noselect' in imaputil.flagsplit(flags):
                continue
            retval.append(folder.IMAP.IMAPFolder(self.imapserver, name))
        return retval
