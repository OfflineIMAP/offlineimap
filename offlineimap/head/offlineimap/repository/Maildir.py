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
import __main__

class MaildirRepository(BaseRepository):
    def __init__(self, root, accountname, config):
        """Initialize a MaildirRepository object.  Takes a path name
        to the directory holding all the Maildir directories."""

        self.root = root
        self.folders = None
        self.accountname = accountname
        self.config = config
        self.ui = __main__.ui
        self.debug("MaildirRepository initialized, sep is " + repr(self.getsep()))

    def debug(self, msg):
        self.ui.debug('maildir', msg)

    def getsep(self):
        if self.config.has_option(self.accountname, 'sep'):
            return self.config.get(self.accountname, 'sep').strip()
        else:
            return '.'

    def makefolder(self, foldername):
        self.debug("makefolder called with arg " + repr(foldername))
        # Do the chdir thing so the call to makedirs does not make the
        # self.root directory (we'd prefer to raise an error in that case),
        # but will make the (relative) paths underneath it.  Need to use
        # makedirs to support a / separator.
        if self.getsep() == '/':
            for invalid in ['new', 'cur', 'tmp', 'offlineimap.uidvalidity']:
                for component in foldername.split('/'):
                    assert component != invalid, "When using nested folders (/ as a separator in the account config), your folder names may not contain 'new', 'cur', 'tmp', or 'offlineimap.uidvalidity'."

        assert foldername.find('./') == -1, "Folder names may not contain ../"
        assert not foldername.startswith('/'), "Folder names may not begin with /"

        oldcwd = os.getcwd()
        os.chdir(self.root)

        # If we're using hierarchical folders, it's possible that sub-folders
        # may be created before higher-up ones.  If this is the case,
        # makedirs will fail because the higher-up dir already exists.
        # So, check to see if this is indeed the case.

        if self.getsep() == '/' and os.path.isdir(foldername):
            self.debug("makefolder: %s already is a directory" % foldername)
            # Already exists.  Sanity-check that it's not a Maildir.
            for subdir in ['cur', 'new', 'tmp']:
                assert not os.path.isdir(os.path.join(foldername, subdir)), \
                       "Tried to create folder %s but it already had dir %s" %\
                       (foldername, subdir)
        else:
            self.debug("makefolder: calling makedirs %s" % foldername)
            os.makedirs(foldername, 0700)
        self.debug("makefolder: creating cur, new, tmp")
        for subdir in ['cur', 'new', 'tmp']:
            os.mkdir(os.path.join(foldername, subdir), 0700)
        # Invalidate the cache
        self.folders = None
        os.chdir(oldcwd)

    def deletefolder(self, foldername):
        self.ui.warn("NOT YET IMPLEMENTED: DELETE FOLDER %s" % foldername)

    def getfolder(self, foldername):
        return folder.Maildir.MaildirFolder(self.root, foldername,
                                            self.getsep())
    
    def _getfolders_scandir(self, root, extension = None):
        self.debug("_GETFOLDERS_SCANDIR STARTING. root = %s, extension = %s" \
                   % (root, extension))
        # extension willl only be non-None when called recursively when
        # getsep() returns '/'.
        retval = []

        # Configure the full path to this repository -- "toppath"

        if extension == None:
            toppath = root
        else:
            toppath = os.path.join(root, extension)

        self.debug("  toppath = %s" % toppath)

        # Iterate over directories in top.
        for dirname in os.listdir(toppath):
            self.debug("  *** top of loop")
            self.debug("  dirname = %s" % dirname)
            if dirname in ['cur', 'new', 'tmp', 'offlineimap.uidvalidity']:
                self.debug("  skipping this dir (Maildir special)")
                # Bypass special files.
                continue
            fullname = os.path.join(toppath, dirname)
            self.debug("  fullname = %s" % fullname)
            if not os.path.isdir(fullname):
                self.debug("  skipping this entry (not a directory)")
                # Not a directory -- not a folder.
                continue
            if not (os.path.isdir(os.path.join(fullname, 'cur')) and
                    os.path.isdir(os.path.join(fullname, 'new')) and
                    os.path.isdir(os.path.join(fullname, 'tmp'))):
                # Doesn't have maildir stuff -- not a folder.
                self.debug("  skipping this entry (doesn't have cur, new, tmp)")
                continue
            
            foldername = dirname
            if extension != None:
                foldername = os.path.join(extension, dirname)

            self.debug("  foldername = %s" % foldername)

            retval.append(folder.Maildir.MaildirFolder(self.root, foldername,
                                                       self.getsep()))
            if self.getsep() == '/':
                # Check sub-directories for folders.
                retval.extend(self._getfolders_scandir(root, foldername))
        self.debug("_GETFOLDERS_SCANDIR RETURNING %s" % \
                   repr([x.getname() for x in retval]))
        return retval
    
    def getfolders(self):
        if self.folders == None:
            self.folders = self._getfolders_scandir(self.root)
        return self.folders
    
