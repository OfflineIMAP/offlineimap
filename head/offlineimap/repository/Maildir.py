# Maildir repository support
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
from mailbox import Maildir
import os

class MaildirRepository(BaseRepository):
    def __init__(self, root):
        """Initialize a MaildirRepository object.  Takes a path name
        to the directory holding all the Maildir directories."""

        self.root = root
        self.folders = None

    def getsep(self):
        return '.'

    def getfolders(self):
        if self.folders != None:
            return self.folders

        retval = []
        for dirname in os.listdir(self.root):
            fullname = os.path.join(self.root, dirname)
            if not os.path.isdir(fullname):
                continue
            if not (os.path.isdir(os.path.join(fullname, 'cur')) and
                    os.path.isdir(os.path.join(fullname, 'new')) and
                    os.path.isdir(os.path.join(fullname, 'tmp'))):
                continue
            retval.append(MaildirFolder(self.root, dirname))
        self.folders = retval
        return retval
    
