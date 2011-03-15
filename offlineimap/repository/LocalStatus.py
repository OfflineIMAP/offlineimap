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
from offlineimap import folder
import offlineimap.folder.LocalStatus
import os
import re

class LocalStatusRepository(BaseRepository):
    def __init__(self, reposname, account):
        BaseRepository.__init__(self, reposname, account)
        self.directory = os.path.join(account.getaccountmeta(), 'LocalStatus')
        if not os.path.exists(self.directory):
            os.mkdir(self.directory, 0700)
        self.folders = None

    def getsep(self):
        return '.'

    def getfolderfilename(self, foldername):
        foldername = re.sub('/\.$', '/dot', foldername)
        foldername = re.sub('^\.$', 'dot', foldername)
        return os.path.join(self.directory, foldername)

    def makefolder(self, foldername):
        # "touch" the file, truncating it.
        filename = self.getfolderfilename(foldername)
        file = open(filename + ".tmp", "wt")
        file.write(offlineimap.folder.LocalStatus.magicline + '\n')
        file.flush()
        os.fsync(file.fileno())
        file.close()
        os.rename(filename + ".tmp", filename)
        
        # Invalidate the cache.
        self.folders = None

    def getfolders(self):
        retval = []
        for folder in os.listdir(self.directory):
            retval.append(folder.LocalStatus.LocalStatusFolder(self.directory,
                                                               folder, self, self.accountname, 
                                                               self.config))
        return retval

    def getfolder(self, foldername):
        return folder.LocalStatus.LocalStatusFolder(self.directory, foldername,
                                                    self, self.accountname,
                                                    self.config)


    

    
