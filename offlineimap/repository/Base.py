# Base repository support
# Copyright (C) 2002-2007 John Goerzen
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

from offlineimap import CustomConfig
from offlineimap.ui import UIBase
import os.path

def LoadRepository(name, account, reqtype):
    from offlineimap.repository.Gmail import GmailRepository
    from offlineimap.repository.IMAP import IMAPRepository, MappedIMAPRepository
    from offlineimap.repository.Maildir import MaildirRepository
    if reqtype == 'remote':
        # For now, we don't support Maildirs on the remote side.
        typemap = {'IMAP': IMAPRepository,
                   'Gmail': GmailRepository}
    elif reqtype == 'local':
        typemap = {'IMAP': MappedIMAPRepository,
                   'Maildir': MaildirRepository}
    else:
        raise ValueError, "Request type %s not supported" % reqtype
    config = account.getconfig()
    repostype = config.get('Repository ' + name, 'type').strip()
    return typemap[repostype](name, account)

class BaseRepository(CustomConfig.ConfigHelperMixin):
    def __init__(self, reposname, account):
        self.account = account
        self.config = account.getconfig()
        self.name = reposname
        self.localeval = account.getlocaleval()
        self.accountname = self.account.getname()
        self.uiddir = os.path.join(self.config.getmetadatadir(), 'Repository-' + self.name)
        if not os.path.exists(self.uiddir):
            os.mkdir(self.uiddir, 0700)
        self.mapdir = os.path.join(self.uiddir, 'UIDMapping')
        if not os.path.exists(self.mapdir):
            os.mkdir(self.mapdir, 0700)
        self.uiddir = os.path.join(self.uiddir, 'FolderValidity')
        if not os.path.exists(self.uiddir):
            os.mkdir(self.uiddir, 0700)

    # The 'restoreatime' config parameter only applies to local Maildir
    # mailboxes.
    def restore_atime(self):
	if self.config.get('Repository ' + self.name, 'type').strip() != \
		'Maildir':
	    return

	if not self.config.has_option('Repository ' + self.name, 'restoreatime') or not self.config.getboolean('Repository ' + self.name, 'restoreatime'):
	    return

	return self.restore_folder_atimes()

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

    def getuiddir(self):
        return self.uiddir

    def getmapdir(self):
        return self.mapdir

    def getaccountname(self):
        return self.accountname

    def getsection(self):
        return 'Repository ' + self.name

    def getconfig(self):
        return self.config

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

    def makefolder(self, foldername):
        raise NotImplementedError

    def deletefolder(self, foldername):
        raise NotImplementedError

    def getfolder(self, foldername):
        raise NotImplementedError
    
    def syncfoldersto(self, dest, copyfolders):
        """Syncs the folders in this repository to those in dest.
        It does NOT sync the contents of those folders.

        For every time dest.makefolder() is called, also call makefolder()
        on each folder in copyfolders."""
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
                for copyfolder in copyfolders:
                    copyfolder.makefolder(key.replace(dest.getsep(), copyfolder.getsep()))

        #
        # Find deleted folders.
        #
        # We don't delete folders right now.

        #for key in desthash.keys():
        #    if not key in srchash:
        #        dest.deletefolder(key)


        ##### Find any folders that aren't being synced
        ignoredfolders = []
        for key in desthash.keys():
            if not key in srchash:
                ignoredfolders.append(key)

        ignoredfolders.sort()
        if ignoredfolders != []:
            UIBase.getglobalui().warn("Found local folders that are not being synced: %s" % (", ".join(ignoredfolders)))
        
    ##### Keepalive

    def startkeepalive(self):
        """The default implementation will do nothing."""
        pass

    def stopkeepalive(self, abrupt = 0):
        """Stop keep alive.  If abrupt is 1, stop it but don't bother waiting
        for the threads to terminate."""
        pass
    
