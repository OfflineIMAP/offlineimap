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
from offlineimap import folder, imaputil
import re
from threading import *

class IMAPRepository(BaseRepository):
    def __init__(self, config, accountname, imapserver):
        """Initialize an IMAPRepository object.  Takes an IMAPServer
        object."""
        self.imapserver = imapserver
        self.config = config
        self.accountname = accountname
        self.folders = None
        self.nametrans = lambda foldername: foldername
        if config.has_option(accountname, 'nametrans'):
            self.nametrans = eval(config.get(accountname, 'nametrans'))

    def getsep(self):
        return self.imapserver.delim

    def getfolder(self, foldername):
        return folder.IMAP.IMAPFolder(self.imapserver, foldername,
                                      self.nametrans(foldername))

    def getfolders(self):
        if self.folders != None:
            return self.folders
        retval = []
        imapobj = self.imapserver.acquireconnection()
        try:
            listresult = imapobj.list()[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        for string in listresult:
            flags, delim, name = imaputil.imapsplit(string)
            if '\\Noselect' in imaputil.flagsplit(flags):
                continue
            retval.append(folder.IMAP.IMAPFolder(self.imapserver, name,
                                                 self.nametrans(imaputil.dequote(name))))
        retval.sort(lambda x, y: cmp(x.getvisiblename(), y.getvisiblename()))
        self.folders = retval
        return retval
