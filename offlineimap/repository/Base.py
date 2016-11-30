""" Base repository support """

# Copyright (C) 2002-2016 John Goerzen & contributors
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


class BaseRepository(CustomConfig.ConfigHelperMixin):
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

    def should_create_folders(self):
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

    def sync_folder_structure(self, local_repo, status_repo):
        """Sync the folders structure.

        It does NOT sync the contents of those folders. nametrans rules
        in both directions will be honored

        Configuring nametrans on BOTH repositories could lead to infinite folder
        creation cycles."""

        if not self.should_create_folders() and not local_repo.should_create_folders():
            # Quick exit if no folder creation is enabled on either side.
            return

        remote_repo = self
        remote_hash, local_hash = {}, {}

        for folder in remote_repo.getfolders():
            remote_hash[folder.getname()] = folder

        for folder in local_repo.getfolders():
            local_hash[folder.getname()] = folder

        # Create new folders from remote to local.
        for remote_name, remote_folder in remote_hash.items():
            # Don't create on local_repo, if it is readonly.
            if not local_repo.should_create_folders():
                break

            # Apply remote nametrans and fix serparator.
            local_name = remote_folder.getvisiblename().replace(
                remote_repo.getsep(), local_repo.getsep())
            if remote_folder.sync_this and not local_name in local_hash.keys():
                try:
                    local_repo.makefolder(local_name)
                    # Need to refresh list.
                    local_repo.forgetfolders()
                except OfflineImapError as e:
                    self.ui.error(e, exc_info()[2],
                         "Creating folder %s on repository %s"%
                         (local_name, local_repo))
                    raise
                status_repo.makefolder(local_name.replace(
                    local_repo.getsep(), status_repo.getsep()))

        # Create new folders from local to remote.
        for local_name, local_folder in local_hash.items():
            if not remote_repo.should_create_folders():
                # Don't create missing folder on readonly repo.
                break

            # Apply reverse nametrans and fix serparator.
            remote_name = local_folder.getvisiblename().replace(
                local_repo.getsep(), remote_repo.getsep())
            if local_folder.sync_this and not remote_name in remote_hash.keys():
                # Would the remote filter out the new folder name? In this case
                # don't create it.
                if not remote_repo.should_sync_folder(remote_name):
                    self.ui.debug('', "Not creating folder '%s' (repository '%s"
                        "') as it would be filtered out on that repository."%
                        (remote_name, self))
                    continue

                # nametrans sanity check! Does remote nametrans lead to the
                # original local name?
                #
                # Apply remote nametrans to see if we end up with the same
                # name. We have:
                #   - remote_name: local_name -> reverse nametrans + separator
                # We want local_name == loop_name from:
                #   - remote_name -> remote (nametrans + separator) -> loop_name
                #
                # Get IMAPFolder and see if the reverse nametrans works fine.
                # TODO: getfolder() works only because we succeed in getting
                # inexisting folders which I would like to change. Take care!
                tmp_remotefolder = remote_repo.getfolder(remote_name)
                loop_name = tmp_remotefolder.getvisiblename().replace(
                    remote_repo.getsep(), local_repo.getsep())
                if local_name != loop_name:
                    raise OfflineImapError("INFINITE FOLDER CREATION DETECTED! "
                        "Folder '%s' (repository '%s') would be created as fold"
                        "er '%s' (repository '%s'). The latter becomes '%s' in "
                        "return, leading to infinite folder creation cycles.\n "
                        "SOLUTION: 1) Do set your nametrans rules on both repos"
                        "itories so they lead to identical names if applied bac"
                        "k and forth. 2) Use folderfilter settings on a reposit"
                        "ory to prevent some folders from being created on the "
                        "other side."%
                        (local_folder.getname(), local_repo, remote_name,
                            remote_repo,
                            loop_name),
                        OfflineImapError.ERROR.REPO)

                # End sanity check, actually create the folder.
                try:
                    remote_repo.makefolder(remote_name)
                    # Need to refresh list.
                    self.forgetfolders()
                except OfflineImapError as e:
                    self.ui.error(e, exc_info()[2], "Creating folder %s on "
                                  "repository %s"% (remote_name, remote_repo))
                    raise
                status_repo.makefolder(local_name.replace(
                    local_repo.getsep(), status_repo.getsep()))

        # Find deleted folders.
        # TODO: We don't delete folders right now.
        return None

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
