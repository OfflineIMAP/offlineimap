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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from offlineimap import threadutil, mbnames, CustomConfig
import offlineimap.repository.Base, offlineimap.repository.LocalStatus
from offlineimap.ui import UIBase
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
from subprocess import Popen, PIPE
from threading import Event, Lock
import os
from Queue import Queue, Empty

class SigListener(Queue):
    def __init__(self):
        self.folderlock = Lock()
        self.folders = None
        Queue.__init__(self, 20)
    def put_nowait(self, sig):
        self.folderlock.acquire()
        try:
            if sig == 1:
                if self.folders is None or not self.autorefreshes:
                    # folders haven't yet been added, or this account is once-only; drop signal
                    return
                elif self.folders:
                    for foldernr in range(len(self.folders)):
                        # requeue folder
                        self.folders[foldernr][1] = True
                    self.quick = False
                    return
                # else folders have already been cleared, put signal...
        finally:
            self.folderlock.release()
        Queue.put_nowait(self, sig)
    def addfolders(self, remotefolders, autorefreshes, quick):
        self.folderlock.acquire()
        try:
            self.folders = []
            self.quick = quick
            self.autorefreshes = autorefreshes
            for folder in remotefolders:
                # new folders are queued
                self.folders.append([folder, True])
        finally:
            self.folderlock.release()
    def clearfolders(self):
        self.folderlock.acquire()
        try:
            for folder, queued in self.folders:
                if queued:
                    # some folders still in queue
                    return False
            self.folders[:] = []
            return True
        finally:
            self.folderlock.release()
    def queuedfolders(self):
        self.folderlock.acquire()
        try:
            dirty = True
            while dirty:
                dirty = False
                for foldernr, (folder, queued) in enumerate(self.folders):
                    if queued:
                        # mark folder as no longer queued
                        self.folders[foldernr][1] = False
                        dirty = True
                        quick = self.quick
                        self.folderlock.release()
                        yield (folder, quick)
                        self.folderlock.acquire()
        finally:
            self.folderlock.release()

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
        self.quicknum = 0
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

    def sleeper(self, siglistener):
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
#         try:
#             sleepresult = siglistener.get_nowait()
#             # retrieved signal before sleep started
#             if sleepresult == 1:
#                 # catching signal 1 here means folders were cleared before signal was posted
#                 pass
#         except Empty:
#             sleepresult = self.ui.sleep(refreshperiod, siglistener)
        sleepresult = self.ui.sleep(refreshperiod, siglistener)
        if sleepresult == 1:
            self.quicknum = 0

        # Cancel keepalive
        for item in kaobjs:
            item.stopkeepalive()
        return sleepresult
            
class AccountSynchronizationMixin:
    def syncrunner(self, siglistener):
        self.ui.registerthread(self.name)
        self.ui.acct(self.name)
        accountmetadata = self.getaccountmeta()
        if not os.path.exists(accountmetadata):
            os.mkdir(accountmetadata, 0700)            

        self.remoterepos = offlineimap.repository.Base.LoadRepository(self.getconf('remoterepository'), self, 'remote')

        # Connect to the local repository.
        self.localrepos = offlineimap.repository.Base.LoadRepository(self.getconf('localrepository'), self, 'local')

        # Connect to the local cache.
        self.statusrepos = offlineimap.repository.LocalStatus.LocalStatusRepository(self.getconf('localrepository'), self)
            
        if not self.refreshperiod:
            self.sync(siglistener)
            self.ui.acctdone(self.name)
            return
        looping = 1
        while looping:
            self.sync(siglistener)
            looping = self.sleeper(siglistener) != 2
        self.ui.acctdone(self.name)

    def getaccountmeta(self):
        return os.path.join(self.metadatadir, 'Account-' + self.name)

    def sync(self, siglistener):
        # We don't need an account lock because syncitall() goes through
        # each account once, then waits for all to finish.

        hook = self.getconf('presynchook', '')
        self.callhook(hook)

        quickconfig = self.getconfint('quick', 0)
        if quickconfig < 0:
            quick = True
        elif quickconfig > 0:
            if self.quicknum == 0 or self.quicknum > quickconfig:
                self.quicknum = 1
                quick = False
            else:
                self.quicknum = self.quicknum + 1
                quick = True
        else:
            quick = False

        try:
            remoterepos = self.remoterepos
            localrepos = self.localrepos
            statusrepos = self.statusrepos
            self.ui.syncfolders(remoterepos, localrepos)
            remoterepos.syncfoldersto(localrepos, [statusrepos])

            siglistener.addfolders(remoterepos.getfolders(), bool(self.refreshperiod), quick)

            while True:
                folderthreads = []
                for remotefolder, quick in siglistener.queuedfolders():
                    thread = InstanceLimitedThread(\
                        instancename = 'FOLDER_' + self.remoterepos.getname(),
                        target = syncfolder,
                        name = "Folder sync %s[%s]" % \
                        (self.name, remotefolder.getvisiblename()),
                        args = (self.name, remoterepos, remotefolder, localrepos,
                                statusrepos, quick))
                    thread.setDaemon(1)
                    thread.start()
                    folderthreads.append(thread)
                threadutil.threadsreset(folderthreads)
                if siglistener.clearfolders():
                    break
            mbnames.write()
            localrepos.forgetfolders()
            remoterepos.forgetfolders()
            localrepos.holdordropconnections()
            remoterepos.holdordropconnections()
        finally:
            pass

        hook = self.getconf('postsynchook', '')
        self.callhook(hook)

    def callhook(self, cmd):
        if not cmd:
            return
        try:
            self.ui.callhook("Calling hook: " + cmd)
            p = Popen(cmd, shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE,
                      close_fds=True)
            r = p.communicate()
            self.ui.callhook("Hook stdout: %s\nHook stderr:%s\n" % r)
            self.ui.callhook("Hook return code: %d" % p.returncode)
        except:
            self.ui.warn("Exception occured while calling hook")
    
class SyncableAccount(Account, AccountSynchronizationMixin):
    pass

def syncfolder(accountname, remoterepos, remotefolder, localrepos,
               statusrepos, quick):
    global mailboxes
    ui = UIBase.getglobalui()
    ui.registerthread(accountname)
    # Load local folder.
    localfolder = localrepos.\
                  getfolder(remotefolder.getvisiblename().\
                            replace(remoterepos.getsep(), localrepos.getsep()))
    # Write the mailboxes
    mbnames.add(accountname, localfolder.getvisiblename())

    # Load status folder.
    statusfolder = statusrepos.getfolder(remotefolder.getvisiblename().\
                                         replace(remoterepos.getsep(),
                                                 statusrepos.getsep()))
    if localfolder.getuidvalidity() == None:
        # This is a new folder, so delete the status cache to be sure
        # we don't have a conflict.
        statusfolder.deletemessagelist()
        
    statusfolder.cachemessagelist()

    if quick:
        if not localfolder.quickchanged(statusfolder) \
               and not remotefolder.quickchanged(statusfolder):
            ui.skippingfolder(remotefolder)
            localrepos.restore_atime()
            return

    # Load local folder
    ui.syncingfolder(remoterepos, remotefolder, localrepos, localfolder)
    ui.loadmessagelist(localrepos, localfolder)
    localfolder.cachemessagelist()
    ui.messagelistloaded(localrepos, localfolder, len(localfolder.getmessagelist().keys()))

    # If either the local or the status folder has messages and there is a UID
    # validity problem, warn and abort.  If there are no messages, UW IMAPd
    # loses UIDVALIDITY.  But we don't really need it if both local folders are
    # empty.  So, in that case, just save it off.
    if len(localfolder.getmessagelist()) or len(statusfolder.getmessagelist()):
        if not localfolder.isuidvalidityok():
            ui.validityproblem(localfolder)
            localrepos.restore_atime()
            return
        if not remotefolder.isuidvalidityok():
            ui.validityproblem(remotefolder)
            localrepos.restore_atime()
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
    localrepos.restore_atime()

