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
from offlineimap import folder, imaputil
from mailbox import Maildir
import os

class MaildirRepository(BaseRepository):
    def __init__(self, root, accountname, config):
        """Initialize a MaildirRepository object.  Takes a path name
        to the directory holding all the Maildir directories."""

        self.root = root
        self.folders = None
        self.accountname = accountname
        self.config = config

    def getsep(self):
        if self.config.has_option(self.accountname, 'sep'):
            return self.config.get(self.accountname, 'sep').strip()
        else:
            return '.'

    def makefolder(self, foldername):
        # Do the chdir thing so the call to makedirs does not make the
        # self.root directory (we'd prefer to raise an error in that case),
        # but will make the (relative) paths underneath it.  Need to use
        # makedirs to support a / separator.
        if self.getsep() == '/':
            for invalid in ['new', 'cur', 'tmp', 'offlineimap.uidvalidity']:
                for component in foldername.split('/'):
                    assert component != invalid, "When using nested folders (/ as a separator in the account config), your folder names may not contain 'new', 'cur', 'tmp', or 'offlineimap.uidvalidity'."

        assert oldername.find('./') == -1, "Folder names may not contain ../"
        assert not foldername.startswith('/'), "Folder names may not begin with /"
        oldcwd = os.getcwd()
        os.chdir(self.root)
        os.makedirs(foldername, 0700)
        for subdir in ['cur', 'new', 'tmp']:
            os.mkdir(os.path.join(foldername, subdir), 0700)
        # Invalidate the cache
        self.folders = None
        os.chdir(oldcwd)

    def deletefolder(self, foldername):
        print "NOT YET IMPLEMENTED: DELETE FOLDER %s" % foldername

    def getfolder(self, foldername):
        return folder.Maildir.MaildirFolder(self.root, foldername,
                                            self.getsep())
    
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
            retval.append(folder.Maildir.MaildirFolder(self.root, dirname,
                                                       self.getsep()))
        self.folders = retval
        return retval
    
