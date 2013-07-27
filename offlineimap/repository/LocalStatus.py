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

from offlineimap.folder.LocalStatus import LocalStatusFolder
from offlineimap.folder.LocalStatusSQLite import LocalStatusSQLiteFolder
from offlineimap.repository.Base import BaseRepository
import os
import re

class LocalStatusRepository(BaseRepository):
    def __init__(self, reposname, account):
        BaseRepository.__init__(self, reposname, account)
        # Root directory in which the LocalStatus folders reside
        self.root = os.path.join(account.getaccountmeta(), 'LocalStatus')
        # statusbackend can be 'plain' or 'sqlite'
        backend = self.account.getconf('status_backend', 'plain')
        if backend == 'sqlite':
            self._backend = 'sqlite'
            self.LocalStatusFolderClass = LocalStatusSQLiteFolder
            self.root += '-sqlite'
        elif backend == 'plain':
            self._backend = 'plain'
            self.LocalStatusFolderClass = LocalStatusFolder
        else:
            raise SyntaxWarning("Unknown status_backend '%s' for account '%s'" \
                                % (backend, account.name))

        if not os.path.exists(self.root):
            os.mkdir(self.root, 0o700)

        # self._folders is a dict of name:LocalStatusFolders()
        self._folders = {}

    def getsep(self):
        return '.'

    def makefolder(self, foldername):
        """Create a LocalStatus Folder

        Empty Folder for plain backend. NoOp for sqlite backend as those
        are created on demand."""
        if self._backend == 'sqlite':
            return # noop for sqlite which creates on-demand

        if self.account.dryrun:
            return # bail out in dry-run mode

        # Create an empty StatusFolder
        folder = self.LocalStatusFolderClass(foldername, self)
        folder.save()

        # Invalidate the cache.
        self._folders = {}

    def getfolder(self, foldername):
        """Return the Folder() object for a foldername"""
        if foldername in self._folders:
            return self._folders[foldername]

        folder = self.LocalStatusFolderClass(foldername, self)
        self._folders[foldername] = folder
        return folder

    def getfolders(self):
        """Returns a list of all cached folders.

        Does nothing for this backend. We mangle the folder file names
        (see getfolderfilename) so we can not derive folder names from
        the file names that we have available. TODO: need to store a
        list of folder names somehow?"""
        pass

    def forgetfolders(self):
        """Forgets the cached list of folders, if any.  Useful to run
        after a sync run."""
        self._folders = {}
