# Base repository support
# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

class BaseRepository:
    def getfolders(self):
        """Returns a list of ALL folders on this server."""
        return []

    def getsep(self):
        raise NotImplementedError

    def makefolder(self, foldername):
        raise NotImplementedError

    def deletefolder(self, foldername):
        raise NotImplementedError

    def getfolder(self, foldername):
        raise NotImplementedError
    
    def syncfoldersto(self, dest):
        """Syncs the folders in this repository to those in dest.
        It does NOT sync the contents of those folders."""
        src = self
        srcfolders = src.getfolders()
        destfolders = dest.getfolders()

        # Create hashes with the names, but convert the source folders
        # to the dest folder's sep.

        srchash = {}
        for folder in srcfolders:
            srchash[folder.getvisiblename().replace(src.getsep(), dest.getsep())] = \
                                                           folder
        desthash = {}
        for folder in destfolders:
            desthash[folder.getvisiblename()] = folder

        #
        # Find new folders.
        #
        
        for key in srchash.keys():
            if not key in desthash:
                dest.makefolder(key)

        #
        # Find deleted folders.
        #
        # We don't delete folders right now.

        #for key in desthash.keys():
        #    if not key in srchash:
        #        dest.deletefolder(key)
        
