# Copyright (C) 2003 John Goerzen
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

from offlineimap import repository, threadutil, mbnames, CustomConfig
from offlineimap.ui import UIBase
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
from threading import Event
import os

def getaccountlist(customconfig):
    return customconfig.getsectionlist('Account')

def AccountListGenerator(customconfig):
    return [Account(customconfig, accountname)
            for accountname in getaccountlist(customconfig)]

def AccountHashGenerator(customconfig):
    retval = {}
    for item in AccountListGenerator(customconfig):
        retval[item.getname()] = item
    return retval

mailboxes = []

class Account(CustomConfig.ConfigHelperMixin):
    def __init__(self, config, name):
        self.config = config
        self.name = name
        self.metadatadir = config.getmetadatadir()
        self.localeval = config.getlocaleval()
        self.ui = UIBase.getglobalui()
        self.refreshperiod = self.getconffloat('autorefresh', 0.0)
        if self.refreshperiod == 0.0:
            self.refreshperiod = None

    def getlocaleval(self):
        return self.localeval

    def getconfig(self):
        return self.config

    def getname(self):
        return self.name

    def getsection(self):
        return 'Account ' + self.getname()

    def sleeper(self):
        """Sleep handler.  Returns same value as UIBase.sleep:
        0 if timeout expired, 1 if there was a request to cancel the timer,
        and 2 if there is a request to abort the program.

        Also, returns 100 if configured to not sleep at all."""
        
        if not self.refreshperiod:
            return 100

        kaobjs = []

        if hasattr(self, 'localrepos'):
            kaobjs.append(self.localrepos)
        if hasattr(self, 'remoterepos'):
            kaobjs.append(self.remoterepos)

        for item in kaobjs:
            item.startkeepalive()
        
        refreshperiod = int(self.refreshperiod * 60)
        sleepresult = self.ui.sleep(refreshperiod)
        if sleepresult == 2:
            # Cancel keep-alive, but don't bother terminating threads
            for item in kaobjs:
                item.stopkeepalive(abrupt = 1)
            return sleepresult
        else:
            # Cancel keep-alive and wait for thread to terminate.
            for item in kaobjs:
                item.stopkeepalive(abrupt = 0)
            return sleepresult
            
class AccountSynchronizationMixin:
    def syncrunner(self):
        self.ui.registerthread(self.name)
        self.ui.acct(self.name)
        accountmetadata = self.getaccountmeta()
        if not os.path.exists(accountmetadata):
            os.mkdir(accountmetadata, 0700)            

        self.remoterepos = repository.Base.LoadRepository(self.getconf('remoterepository'), self, 'remote')

        # Connect to the local repository.
        self.localrepos = repository.Base.LoadRepository(self.getconf('localrepository'), self, 'local')

        # Connect to the local cache.
        self.statusrepos = repository.LocalStatus.LocalStatusRepository(self.getconf('localrepository'), self)
            
        if not self.refreshperiod:
            self.sync()
            self.ui.acctdone(self.name)
            return
        looping = 1
        while looping:
            self.sync()
            looping = self.sleeper() != 2
        self.ui.acctdone(self.name)

    def getaccountmeta(self):
        return os.path.join(self.metadatadir, 'Account-' + self.name)

    def sync(self):
        # We don't need an account lock because syncitall() goes through
        # each account once, then waits for all to finish.
        try:
            remoterepos = self.remoterepos
            localrepos = self.localrepos
            statusrepos = self.statusrepos
            self.ui.syncfolders(remoterepos, localrepos)
            remoterepos.syncfoldersto(localrepos)

            folderthreads = []
            for remotefolder in remoterepos.getfolders():
                thread = InstanceLimitedThread(\
                    instancename = 'FOLDER_' + self.remoterepos.getname(),
                    target = syncfolder,
                    name = "Folder sync %s[%s]" % \
                    (self.name, remotefolder.getvisiblename()),
                    args = (self.name, remoterepos, remotefolder, localrepos,
                            statusrepos))
                thread.setDaemon(1)
                thread.start()
                folderthreads.append(thread)
            threadutil.threadsreset(folderthreads)
            mbnames.write()
            localrepos.holdordropconnections()
            remoterepos.holdordropconnections()
        finally:
            pass
    
class SyncableAccount(Account, AccountSynchronizationMixin):
    pass

def syncfolder(accountname, remoterepos, remotefolder, localrepos,
               statusrepos):
    global mailboxes
    ui = UIBase.getglobalui()
    ui.registerthread(accountname)
    # Load local folder.
    localfolder = localrepos.\
                  getfolder(remotefolder.getvisiblename().\
                            replace(remoterepos.getsep(), localrepos.getsep()))
    # Write the mailboxes
    mbnames.add(accountname, localfolder.getvisiblename())
    # Load local folder
    ui.syncingfolder(remoterepos, remotefolder, localrepos, localfolder)
    ui.loadmessagelist(localrepos, localfolder)
    localfolder.cachemessagelist()
    ui.messagelistloaded(localrepos, localfolder, len(localfolder.getmessagelist().keys()))


    # Load status folder.
    statusfolder = statusrepos.getfolder(remotefolder.getvisiblename().\
                                         replace(remoterepos.getsep(),
                                                 statusrepos.getsep()))
    if localfolder.getuidvalidity() == None:
        # This is a new folder, so delete the status cache to be sure
        # we don't have a conflict.
        statusfolder.deletemessagelist()
        
    statusfolder.cachemessagelist()

    # If either the local or the status folder has messages and there is a UID
    # validity problem, warn and abort.  If there are no messages, UW IMAPd
    # loses UIDVALIDITY.  But we don't really need it if both local folders are
    # empty.  So, in that case, just save it off.
    if len(localfolder.getmessagelist()) or len(statusfolder.getmessagelist()):
        if not localfolder.isuidvalidityok():
            ui.validityproblem(localfolder, localfolder.getsaveduidvalidity(),
                               localfolder.getuidvalidity())
            return
        if not remotefolder.isuidvalidityok():
            ui.validityproblem(remotefolder, remotefolder.getsaveduidvalidity(),
                               remotefolder.getuidvalidity())
            return
    else:
        localfolder.saveuidvalidity()
        remotefolder.saveuidvalidity()

    # Load remote folder.
    ui.loadmessagelist(remoterepos, remotefolder)
    remotefolder.cachemessagelist()
    ui.messagelistloaded(remoterepos, remotefolder,
                         len(remotefolder.getmessagelist().keys()))


    #

    if not statusfolder.isnewfolder():
        # Delete local copies of remote messages.  This way,
        # if a message's flag is modified locally but it has been
        # deleted remotely, we'll delete it locally.  Otherwise, we
        # try to modify a deleted message's flags!  This step
        # need only be taken if a statusfolder is present; otherwise,
        # there is no action taken *to* the remote repository.

        remotefolder.syncmessagesto_delete(localfolder, [localfolder,
                                                         statusfolder])
        ui.syncingmessages(localrepos, localfolder, remoterepos, remotefolder)
        localfolder.syncmessagesto(statusfolder, [remotefolder, statusfolder])

    # Synchronize remote changes.
    ui.syncingmessages(remoterepos, remotefolder, localrepos, localfolder)
    remotefolder.syncmessagesto(localfolder, [localfolder, statusfolder])

    # Make sure the status folder is up-to-date.
    ui.syncingmessages(localrepos, localfolder, statusrepos, statusfolder)
    localfolder.syncmessagesto(statusfolder)
    statusfolder.save()

