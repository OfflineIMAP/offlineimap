# Local status cache repository support
# Copyright (C) 2002-2015 John Goerzen & contributors
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

import os

from offlineimap.folder.LocalStatus import LocalStatusFolder
from offlineimap.folder.LocalStatusSQLite import LocalStatusSQLiteFolder
from offlineimap.repository.Base import BaseRepository

class LocalStatusRepository(BaseRepository):
    def __init__(self, reposname, account):
        BaseRepository.__init__(self, reposname, account)

        # class and root for all backends
        self.backends = {}
        self.backends['sqlite'] = {
            'class': LocalStatusSQLiteFolder,
            'root': os.path.join(account.getaccountmeta(), 'LocalStatus-sqlite')
        }

        self.backends['plain'] = {
            'class': LocalStatusFolder,
            'root': os.path.join(account.getaccountmeta(), 'LocalStatus')
        }

        # Set class and root for the configured backend
        self.setup_backend(self.account.getconf('status_backend', 'sqlite'))

        if not os.path.exists(self.root):
            os.mkdir(self.root, 0o700)

        # self._folders is a dict of name:LocalStatusFolders()
        self._folders = {}

    def _instanciatefolder(self, foldername):
        return self.LocalStatusFolderClass(foldername, self) # Instanciate.

    def setup_backend(self, backend):
        if backend in self.backends.keys():
            self._backend = backend
            self.root = self.backends[backend]['root']
            self.LocalStatusFolderClass = self.backends[backend]['class']

        else:
            raise SyntaxWarning("Unknown status_backend '%s' for account '%s'"%
                (backend, self.account.name))

    def import_other_backend(self, folder):
        for bk, dic in self.backends.items():
            # skip folder's own type
            if dic['class'] == type(folder):
                continue

            repobk = LocalStatusRepository(self.name, self.account)
            repobk.setup_backend(bk)      # fake the backend
            folderbk = dic['class'](folder.name, repobk)

            # if backend contains data, import it to folder.
            if not folderbk.isnewfolder():
                self.ui._msg("Migrating LocalStatus cache from %s to %s "
                    "status folder for %s:%s"%
                    (bk, self._backend, self.name, folder.name))

                folderbk.cachemessagelist()
                folder.messagelist = folderbk.messagelist
                folder.saveall()
                break

    def getsep(self):
        return '.'

    def makefolder(self, foldername):
        """Create a LocalStatus Folder."""

        if self.account.dryrun:
            return # bail out in dry-run mode

        # Create an empty StatusFolder
        folder = self._instanciatefolder(foldername)
        folder.save()
        folder.closefiles()

        # Invalidate the cache.
        self.forgetfolders()

    def getfolder(self, foldername):
        """Return the Folder() object for a foldername.

        Caller must call closefiles() on the folder when done."""

        if foldername in self._folders:
            return self._folders[foldername]

        folder = self._instanciatefolder(foldername)

        # If folder is empty, try to import data from an other backend.
        if folder.isnewfolder():
            self.import_other_backend(folder)

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
