# Maildir repository support
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

from offlineimap import folder
from offlineimap.ui import getglobalui
from offlineimap.error import OfflineImapError
from offlineimap.repository.Base import BaseRepository
import os
from stat import *

class MaildirRepository(BaseRepository):
    def __init__(self, reposname, account):
        """Initialize a MaildirRepository object.  Takes a path name
        to the directory holding all the Maildir directories."""

        BaseRepository.__init__(self, reposname, account)

        self.root = self.getlocalroot()
        self.folders = None
        self.ui = getglobalui()
        self.debug("MaildirRepository initialized, sep is %s"% repr(self.getsep()))
        self.folder_atimes = []

        # Create the top-level folder if it doesn't exist
        if not os.path.isdir(self.root):
            os.mkdir(self.root, 0o700)

        # Create the keyword->char mapping
        self.keyword2char = dict()
        for c in 'abcdefghijklmnopqrstuvwxyz':
            confkey = 'customflag_' + c
            keyword = self.getconf(confkey, None)
            if keyword is not None:
                self.keyword2char[keyword] = c

    def _append_folder_atimes(self, foldername):
        """Store the atimes of a folder's new|cur in self.folder_atimes"""

        p = os.path.join(self.root, foldername)
        new = os.path.join(p, 'new')
        cur = os.path.join(p, 'cur')
        atimes = (p, os.path.getatime(new), os.path.getatime(cur))
        self.folder_atimes.append(atimes)

    def restore_atime(self):
        """Sets folders' atime back to their values after a sync

        Controlled by the 'restoreatime' config parameter."""

        if not self.getconfboolean('restoreatime', False):
            return # not configured to restore

        for (dirpath, new_atime, cur_atime) in self.folder_atimes:
            new_dir = os.path.join(dirpath, 'new')
            cur_dir = os.path.join(dirpath, 'cur')
            os.utime(new_dir, (new_atime, os.path.getmtime(new_dir)))
            os.utime(cur_dir, (cur_atime, os.path.getmtime(cur_dir)))

    def getlocalroot(self):
        xforms = [os.path.expanduser]
        return self.getconf_xform('localfolders', xforms)

    def debug(self, msg):
        self.ui.debug('maildir', msg)

    def getsep(self):
        return self.getconf('sep', '.').strip()

    def getkeywordmap(self):
        return self.keyword2char if len(self.keyword2char) > 0 else None

    def makefolder(self, foldername):
        """Create new Maildir folder if necessary

        This will not update the list cached in getfolders(). You will
        need to invoke :meth:`forgetfolders` to force new caching when
        you are done creating folders yourself.

        :param foldername: A relative mailbox name. The maildir will be
            created in self.root+'/'+foldername. All intermediate folder
            levels will be created if they do not exist yet. 'cur',
            'tmp', and 'new' subfolders will be created in the maildir.
        """

        self.ui.makefolder(self, foldername)
        if self.account.dryrun:
            return
        full_path = os.path.abspath(os.path.join(self.root, foldername))

        # sanity tests
        if self.getsep() == '/':
            for component in foldername.split('/'):
                assert not component in ['new', 'cur', 'tmp'],\
                    "When using nested folders (/ as a Maildir separator), "\
                    "folder names may not contain 'new', 'cur', 'tmp'."
        assert foldername.find('../') == -1, "Folder names may not contain ../"
        assert not foldername.startswith('/'), "Folder names may not begin with /"

        # If we're using hierarchical folders, it's possible that
        # sub-folders may be created before higher-up ones.
        self.debug("makefolder: calling makedirs '%s'"% full_path)
        try:
            os.makedirs(full_path, 0o700)
        except OSError as e:
            if e.errno == 17 and os.path.isdir(full_path):
                self.debug("makefolder: '%s' already a directory"% foldername)
            else:
                raise
        for subdir in ['cur', 'new', 'tmp']:
            try:
                os.mkdir(os.path.join(full_path, subdir), 0o700)
            except OSError as e:
                if e.errno == 17 and os.path.isdir(full_path):
                    self.debug("makefolder: '%s' already has subdir %s"%
                        (foldername, subdir))
                else:
                    raise

    def deletefolder(self, foldername):
        self.ui.warn("NOT YET IMPLEMENTED: DELETE FOLDER %s"% foldername)

    def getfolder(self, foldername):
        """Return a Folder instance of this Maildir

        If necessary, scan and cache all foldernames to make sure that
        we only return existing folders and that 2 calls with the same
        name will return the same object."""

        # getfolders() will scan and cache the values *if* necessary
        folders = self.getfolders()
        for f in folders:
            if foldername == f.name:
                return f
        raise OfflineImapError("getfolder() asked for a nonexisting "
                               "folder '%s'."% foldername,
                               OfflineImapError.ERROR.FOLDER)

    def _getfolders_scandir(self, root, extension=None):
        """Recursively scan folder 'root'; return a list of MailDirFolder

        :param root: (absolute) path to Maildir root
        :param extension: (relative) subfolder to examine within root"""

        self.debug("_GETFOLDERS_SCANDIR STARTING. root = %s, extension = %s"%
                   (root, extension))
        retval = []

        # Configure the full path to this repository -- "toppath"
        if extension:
            toppath = os.path.join(root, extension)
        else:
            toppath = root
        self.debug("  toppath = %s"% toppath)

        # Iterate over directories in top & top itself.
        for dirname in os.listdir(toppath) + ['']:
            self.debug("  dirname = %s"% dirname)
            if dirname == '' and extension is not None:
                self.debug('  skip this entry (already scanned)')
                continue
            if dirname in ['cur', 'new', 'tmp']:
                self.debug("  skip this entry (Maildir special)")
                # Bypass special files.
                continue
            fullname = os.path.join(toppath, dirname)
            if not os.path.isdir(fullname):
                self.debug("  skip this entry (not a directory)")
                # Not a directory -- not a folder.
                continue
            # extension can be None.
            if extension:
                foldername = os.path.join(extension, dirname)
            else:
                foldername = dirname

            if (os.path.isdir(os.path.join(fullname, 'cur')) and
                os.path.isdir(os.path.join(fullname, 'new')) and
                os.path.isdir(os.path.join(fullname, 'tmp'))):
                # This directory has maildir stuff -- process
                self.debug("  This is maildir folder '%s'."% foldername)
                if self.getconfboolean('restoreatime', False):
                    self._append_folder_atimes(foldername)
                fd = self.getfoldertype()(self.root, foldername,
                                          self.getsep(), self)
                retval.append(fd)

            if self.getsep() == '/' and dirname != '':
                # Recursively check sub-directories for folders too.
                retval.extend(self._getfolders_scandir(root, foldername))
        self.debug("_GETFOLDERS_SCANDIR RETURNING %s"% \
                   repr([x.getname() for x in retval]))
        return retval

    def getfolders(self):
        if self.folders == None:
            self.folders = self._getfolders_scandir(self.root)
        return self.folders

    def getfoldertype(self):
        return folder.Maildir.MaildirFolder

    def forgetfolders(self):
        """Forgets the cached list of folders, if any.  Useful to run
        after a sync run."""

        self.folders = None
