# Base repository support
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

import re
import os.path
from sys import exc_info

from offlineimap import CustomConfig
from offlineimap.ui import getglobalui
from offlineimap.error import OfflineImapError

class BaseRepository(CustomConfig.ConfigHelperMixin, object):

    def __init__(self, reposname, account):
        self.ui = getglobalui()
        self.account = account
        self.config = account.getconfig()
        self.name = reposname
        self.localeval = account.getlocaleval()
        self._accountname = self.account.getname()
        self._readonly = self.getconfboolean('readonly', False)
        self.uiddir = os.path.join(self.config.getmetadatadir(), 'Repository-' + self.name)
        if not os.path.exists(self.uiddir):
            os.mkdir(self.uiddir, 0o700)
        self.mapdir = os.path.join(self.uiddir, 'UIDMapping')
        if not os.path.exists(self.mapdir):
            os.mkdir(self.mapdir, 0o700)
        # FIXME: self.uiddir variable name is lying about itself.
        self.uiddir = os.path.join(self.uiddir, 'FolderValidity')
        if not os.path.exists(self.uiddir):
            os.mkdir(self.uiddir, 0o700)

        self.nametrans = lambda foldername: foldername
        self.folderfilter = lambda foldername: 1
        self.folderincludes = []
        self.foldersort = None
        self.newmail_hook = None
        if self.config.has_option(self.getsection(), 'nametrans'):
            self.nametrans = self.localeval.eval(
                self.getconf('nametrans'), {'re': re})
        if self.config.has_option(self.getsection(), 'folderfilter'):
            self.folderfilter = self.localeval.eval(
                self.getconf('folderfilter'), {'re': re})
        if self.config.has_option(self.getsection(), 'folderincludes'):
            self.folderincludes = self.localeval.eval(
                self.getconf('folderincludes'), {'re': re})
        if self.config.has_option(self.getsection(), 'foldersort'):
            self.foldersort = self.localeval.eval(
                self.getconf('foldersort'), {'re': re})

    def restore_atime(self):
        """Sets folders' atime back to their values after a sync

        Controlled by the 'restoreatime' config parameter (default
        False), applies only to local Maildir mailboxes and does nothing
        on all other repository types."""
        pass

    def connect(self):
        """Establish a connection to the remote, if necessary.  This exists
        so that IMAP connections can all be established up front, gathering
        passwords as needed.  It was added in order to support the
        error recovery -- we need to connect first outside of the error
        trap in order to validate the password, and that's the point of
        this function."""
        pass

    def holdordropconnections(self):
        pass

    def dropconnections(self):
        pass

    def getaccount(self):
        return self.account

    def getname(self):
        return self.name

    def __str__(self):
        return self.name

    @property
    def accountname(self):
        """Account name as string"""
        return self._accountname

    def getuiddir(self):
        return self.uiddir

    def getmapdir(self):
        return self.mapdir

    # Interface from CustomConfig.ConfigHelperMixin
    def getsection(self):
        return 'Repository ' + self.name

    # Interface from CustomConfig.ConfigHelperMixin
    def getconfig(self):
        return self.config

    @property
    def readonly(self):
        """Is the repository readonly?"""
        return self._readonly

    def getlocaleval(self):
        return self.account.getlocaleval()

    def getfolders(self):
        """Returns a list of ALL folders on this server."""
        return []

    def forgetfolders(self):
        """Forgets the cached list of folders, if any.  Useful to run
        after a sync run."""
        pass

    def getsep(self):
        raise NotImplementedError

    def getkeywordmap(self):
        raise NotImplementedError

    def should_sync_folder(self, fname):
        """Should this folder be synced?"""

        return fname in self.folderincludes or self.folderfilter(fname)

    def get_create_folders(self):
        """Is folder creation enabled on this repository?

        It is disabled by either setting the whole repository
        'readonly' or by using the 'createfolders' setting."""

        return (not self._readonly) and \
            self.getconfboolean('createfolders', True)

    def makefolder(self, foldername):
        """Create a new folder."""
        raise NotImplementedError

    def deletefolder(self, foldername):
        raise NotImplementedError

    def getfolder(self, foldername):
        raise NotImplementedError

    def sync_folder_structure(self, dst_repo, status_repo):
        """Syncs the folders in this repository to those in dest.

        It does NOT sync the contents of those folders. nametrans rules
        in both directions will be honored, but there are NO checks yet
        that forward and backward nametrans actually match up!
        Configuring nametrans on BOTH repositories therefore could lead
        to infinite folder creation cycles."""

        if not self.get_create_folders() and not dst_repo.get_create_folders():
            # Quick exit if no folder creation is enabled on either side.
            return

        src_repo = self
        src_folders = src_repo.getfolders()
        dst_folders = dst_repo.getfolders()
        # Do we need to refresh the folder list afterwards?
        src_haschanged, dst_haschanged = False, False
        # Create hashes with the names, but convert the source folders.
        # to the dest folder's sep.
        src_hash = {}
        for folder in src_folders:
            src_hash[folder.getvisiblename().replace(
                    src_repo.getsep(), dst_repo.getsep())] = folder
        dst_hash = {}
        for folder in dst_folders:
            dst_hash[folder.getvisiblename().replace(
                    dst_repo.getsep(), src_repo.getsep())] = folder

        # Find and create new folders on src_repo.
        for src_name_t, src_folder in src_hash.items():
            # Don't create on dst_repo, if it is readonly.
            if not dst_repo.get_create_folders():
                break

            if src_folder.sync_this and not src_name_t in dst_folders:
                try:
                    dst_repo.makefolder(src_name_t)
                    dst_haschanged = True # Need to refresh list.
                except OfflineImapError as e:
                    self.ui.error(e, exc_info()[2],
                         "Creating folder %s on repository %s"%
                         (src_name_t, dst_repo))
                    raise
                status_repo.makefolder(src_name_t.replace(dst_repo.getsep(),
                                                   status_repo.getsep()))
        # Find and create new folders on dst_repo.
        for dst_name_t, dst_folder in dst_hash.items():
            if not src_repo.get_create_folders():
                # Don't create missing folder on readonly repo.
                break

            if dst_folder.sync_this and not dst_name_t in src_folders:
                # nametrans sanity check!
                # Does nametrans back&forth lead to identical names?
                # 1) would src repo filter out the new folder name? In this
                # case don't create it on it:
                if not self.should_sync_folder(dst_name_t):
                    self.ui.debug('', "Not creating folder '%s' (repository '%s"
                        "') as it would be filtered out on that repository."%
                        (dst_name_t, self))
                    continue
                # get IMAPFolder and see if the reverse nametrans
                # works fine TODO: getfolder() works only because we
                # succeed in getting inexisting folders which I would
                # like to change. Take care!
                folder = self.getfolder(dst_name_t)
                # apply reverse nametrans to see if we end up with the same name
                newdst_name = folder.getvisiblename().replace(
                    src_repo.getsep(), dst_repo.getsep())
                if dst_folder.name != newdst_name:
                    raise OfflineImapError("INFINITE FOLDER CREATION DETECTED! "
                        "Folder '%s' (repository '%s') would be created as fold"
                        "er '%s' (repository '%s'). The latter becomes '%s' in "
                        "return, leading to infinite folder creation cycles.\n "
                        "SOLUTION: 1) Do set your nametrans rules on both repos"
                        "itories so they lead to identical names if applied bac"
                        "k and forth. 2) Use folderfilter settings on a reposit"
                        "ory to prevent some folders from being created on the "
                        "other side." % (dst_folder.name, dst_repo, dst_name_t,
                                         src_repo, newdst_name),
                                           OfflineImapError.ERROR.REPO)
                # end sanity check, actually create the folder
                try:
                    src_repo.makefolder(dst_name_t)
                    src_haschanged = True # Need to refresh list
                except OfflineImapError as e:
                    self.ui.error(e, exc_info()[2], "Creating folder %s on "
                                  "repository %s" % (dst_name_t, src_repo))
                    raise
                status_repo.makefolder(dst_name_t.replace(
                                src_repo.getsep(), status_repo.getsep()))
        # Find deleted folders.
        # TODO: We don't delete folders right now.

        #Forget old list of cached folders so we get new ones if needed
        if src_haschanged:
            self.forgetfolders()
        if dst_haschanged:
            dst_repo.forgetfolders()

    def startkeepalive(self):
        """The default implementation will do nothing."""
        pass

    def stopkeepalive(self):
        """Stop keep alive, but don't bother waiting
        for the threads to terminate."""
        pass

    def getlocalroot(self):
        """ Local root folder for storing messages.
        Will not be set for remote repositories."""
        return None

