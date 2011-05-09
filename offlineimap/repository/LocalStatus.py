# Local status cache repository support
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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from Base import BaseRepository
from offlineimap.folder.LocalStatus import LocalStatusFolder
from offlineimap.folder.LocalStatusSQLite import LocalStatusSQLiteFolder
import os
import re

class LocalStatusRepository(BaseRepository):
    def __init__(self, reposname, account):
        BaseRepository.__init__(self, reposname, account)
        self.directory = os.path.join(account.getaccountmeta(), 'LocalStatus')

        #statusbackend can be 'plain' or 'sqlite'
        backend = self.account.getconf('status_backend', 'plain')
        if backend == 'sqlite':
            self._backend = 'sqlite'
            self.LocalStatusFolderClass = LocalStatusSQLiteFolder
            self.directory += '-sqlite'
        elif backend == 'plain':
            self._backend = 'plain'
            self.LocalStatusFolderClass = LocalStatusFolder
        else:
            raise SyntaxWarning("Unknown status_backend '%s' for account '%s'" \
                                % (backend, account.name))

        if not os.path.exists(self.directory):
            os.mkdir(self.directory, 0700)

        # self._folders is a list of LocalStatusFolders()
        self._folders = None

    def getsep(self):
        return '.'

    def getfolderfilename(self, foldername):
        """Return the full path of the status file"""
        # replace with 'dot' if final path name is '.'
        foldername = re.sub('(^|\/)\.$','\\1dot', foldername)
        return os.path.join(self.directory, foldername)

    def makefolder(self, foldername):
        """Create a LocalStatus Folder

        Empty Folder for plain backend. NoOp for sqlite backend as those
        are created on demand."""
        # Invalidate the cache.
        self._folders = None
        if self._backend == 'sqlite':
            return

        filename = self.getfolderfilename(foldername)
        file = open(filename + ".tmp", "wt")
        file.write(offlineimap.folder.LocalStatus.magicline + '\n')
        file.close()
        os.rename(filename + ".tmp", filename)
        # Invalidate the cache.
        self._folders = None

    def getfolder(self, foldername):
        """Return the Folder() object for a foldername"""
        return self.LocalStatusFolderClass(self.directory, foldername,
                                           self, self.accountname,
                                           self.config)

    def getfolders(self):
        """Returns a list of ALL folders on this server.

        This is currently nowhere used in the code."""
        if self._folders != None:
            return self._folders

        for folder in os.listdir(self.directory):
            self._folders = retval.append(self.getfolder(folder))
        return self._folders

    def forgetfolders(self):
        """Forgets the cached list of folders, if any.  Useful to run
        after a sync run."""
        self._folders = None
