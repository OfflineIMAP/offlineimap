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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Base import BaseRepository
from offlineimap import folder
import os

class LocalStatusRepository(BaseRepository):
    def __init__(self, directory):
        self.directory = directory
        self.folders = None

    def getsep(self):
        return '.'

    def getfolderfilename(self, foldername):
        return os.path.join(self.directory, foldername)

    def makefolder(self, foldername):
        # "touch" the file.
        file = open(self.getfolderfilename(foldername), "ab")
        file.close()
        # Invalidate the cache.
        self.folders = None

    def getfolders(self):
        retval = []
        for folder in os.listdir(self.directory):
            retval.append(folder.LocalStatus.LocalStatusFolder(self.directory,
                                                               folder, self))
        return retval

    def getfolder(self, foldername):
        return folder.LocalStatus.LocalStatusFolder(self.directory, foldername,
                                                    self)


    

    
