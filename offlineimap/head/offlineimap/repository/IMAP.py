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
import re, types
from threading import *

class IMAPRepository(BaseRepository):
    def __init__(self, config, localeval, accountname, imapserver):
        """Initialize an IMAPRepository object.  Takes an IMAPServer
        object."""
        self.imapserver = imapserver
        self.config = config
        self.accountname = accountname
        self.folders = None
        self.nametrans = lambda foldername: foldername
        self.folderfilter = lambda foldername: 1
        self.folderincludes = []
        self.foldersort = cmp
        if config.has_option(accountname, 'nametrans'):
            self.nametrans = localeval.eval(config.get(accountname, 'nametrans'), {'re': re})
        if config.has_option(accountname, 'folderfilter'):
            self.folderfilter = localeval.eval(config.get(accountname, 'folderfilter'), {'re': re})
        if config.has_option(accountname, 'folderincludes'):
            self.folderincludes = localeval.eval(config.get(accountname, 'folderincludes'), {'re': re})
        if config.has_option(accountname, 'foldersort'):
            self.foldersort = localeval.eval(config.get(accountname, 'foldersort'), {'re': re})

    def getsep(self):
        return self.imapserver.delim

    def getfolder(self, foldername):
        return folder.IMAP.IMAPFolder(self.imapserver, foldername,
                                      self.nametrans(foldername),
                                      accountname, self)

    def getfolders(self):
        if self.folders != None:
            return self.folders
        retval = []
        imapobj = self.imapserver.acquireconnection()
        try:
            listresult = imapobj.list(directory = self.imapserver.reference)[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        for string in listresult:
            if type(string) == types.StringType and string == '':
                # Bug in imaplib: empty strings in results from
                # literals.
                continue
            flags, delim, name = imaputil.imapsplit(string)
            flaglist = [x.lower() for x in imaputil.flagsplit(flags)]
            if '\\noselect' in flaglist:
                continue
            foldername = imaputil.dequote(name)
            if not self.folderfilter(foldername):
                continue
            retval.append(folder.IMAP.IMAPFolder(self.imapserver, foldername,
                                                 self.nametrans(foldername),
                                                 self.accountname, self))
        for foldername in self.folderincludes:
            retval.append(folder.IMAP.IMAPFolder(self.imapserver, foldername,
                                                 self.nametrans(foldername),
                                                 self.accountname, self))
        retval.sort(lambda x, y: self.foldersort(x.getvisiblename(), y.getvisiblename()))
        self.folders = retval
        return retval
