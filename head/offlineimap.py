#!/usr/bin/python2.2

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

from offlineimap import imaplib, imaputil, imapserver, repository, folder, mbnames, threadutil
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
import re, os, os.path, offlineimap, sys
from ConfigParser import ConfigParser
from threading import *


if '-d' in sys.argv:
    imaplib.Debug = 5

config = ConfigParser()
configfilename = os.path.expanduser("~/.offlineimaprc")
if not os.path.exists(configfilename):
    sys.stderr.write(" *** Config file %s does not exist; aborting!\n" % configfilename)
    sys.exit(1)
    
config.read(configfilename)

ui = offlineimap.ui.detector.findUI(config)
ui.init_banner()


metadatadir = os.path.expanduser(config.get("general", "metadata"))
if not os.path.exists(metadatadir):
    os.mkdir(metadatadir, 0700)

accounts = config.get("general", "accounts")
accounts = accounts.replace(" ", "")
accounts = accounts.split(",")

server = None
remoterepos = None
localrepos = None
passwords = {}
tunnels = {}

threadutil.initInstanceLimit("ACCOUNTLIMIT", config.getint("general",
                                                           "maxsyncaccounts"))

# We have to gather passwords here -- don't want to have two threads
# asking for passwords simultaneously.

for account in accounts:
    if config.has_option(account, "preauthtunnel"):
        tunnels[account] = config.get(account, "preauthtunnel")
    elif config.has_option(account, "remotepass"):
        passwords[account] = config.get(account, "remotepass")
    elif config.has_option(account, "remotepassfile"):
        passfile = os.path.expanduser(config.get(account, "remotepassfile"))
        passwords[account] = passfile.readline().strip()
        passfile.close()
    else:
        passwords[account] = ui.getpass(account, config)
    for instancename in ["FOLDER_" + account, "MSGCOPY_" + account]:
        threadutil.initInstanceLimit(instancename,
                                     config.getint(account, "maxconnections"))

mailboxes = []
mailboxlock = Lock()
servers = {}

def addmailbox(accountname, remotefolder):
    mailboxlock.acquire()
    mailboxes.append({'accountname' : accountname,
                      'foldername': remotefolder.getvisiblename()})
    mailboxlock.release()    
    
def syncaccount(accountname, *args):
    # We don't need an account lock because syncitall() goes through
    # each account once, then waits for all to finish.
    try:
        ui.acct(accountname)
        accountmetadata = os.path.join(metadatadir, accountname)
        if not os.path.exists(accountmetadata):
            os.mkdir(accountmetadata, 0700)

        server = None
        if accountname in servers:
            server = servers[accountname]
        else:
            server = imapserver.ConfigedIMAPServer(config, accountname, passwords)
            servers[accountname] = server
            
        remoterepos = repository.IMAP.IMAPRepository(config, accountname, server)

        # Connect to the Maildirs.
        localrepos = repository.Maildir.MaildirRepository(os.path.expanduser(config.get(accountname, "localfolders")))

        # Connect to the local cache.
        statusrepos = repository.LocalStatus.LocalStatusRepository(accountmetadata)

        ui.syncfolders(remoterepos, localrepos)
        remoterepos.syncfoldersto(localrepos)

        folderthreads = []
        for remotefolder in remoterepos.getfolders():
            thread = InstanceLimitedThread(\
                instancename = 'FOLDER_' + accountname,
                target = syncfolder,
                name = "Folder sync %s[%s]" % \
                (accountname, remotefolder.getvisiblename()),
                args = (accountname, remoterepos, remotefolder, localrepos,
                        statusrepos))
            thread.setDaemon(1)
            thread.start()
            folderthreads.append(thread)
        threadutil.threadsreset(folderthreads)
        if not (config.has_option(accountname, 'holdconnectionopen') and \
           config.getboolean(accountname, 'holdconnectionopen')):
            server.close()
    finally:
        pass

def syncfolder(accountname, remoterepos, remotefolder, localrepos,
               statusrepos):
    mailboxes.append({'accountname': accountname,
                      'foldername': remotefolder.getvisiblename()})
    # Load local folder.
    localfolder = localrepos.\
                  getfolder(remotefolder.getvisiblename().\
                            replace(remoterepos.getsep(), localrepos.getsep()))
    if not localfolder.isuidvalidityok(remotefolder):
        ui.validityproblem(remotefolder)
        return
    ui.syncingfolder(remoterepos, remotefolder, localrepos, localfolder)
    ui.loadmessagelist(localrepos, localfolder)
    localfolder.cachemessagelist()
    ui.messagelistloaded(localrepos, localfolder, len(localfolder.getmessagelist().keys()))

    # Load remote folder.
    ui.loadmessagelist(remoterepos, remotefolder)
    remotefolder.cachemessagelist()
    ui.messagelistloaded(remoterepos, remotefolder,
                         len(remotefolder.getmessagelist().keys()))

    # Load status folder.
    statusfolder = statusrepos.getfolder(remotefolder.getvisiblename().\
                                         replace(remoterepos.getsep(),
                                                 statusrepos.getsep()))
    statusfolder.cachemessagelist()

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
    remotefolder.syncmessagesto(localfolder)

    # Make sure the status folder is up-to-date.
    ui.syncingmessages(localrepos, localfolder, statusrepos, statusfolder)
    localfolder.syncmessagesto(statusfolder)
    statusfolder.save()
    

def syncitall():
    global mailboxes
    mailboxes = []                      # Reset.
    threads = []
    for accountname in accounts:
        thread = InstanceLimitedThread(instancename = 'ACCOUNTLIMIT',
                                       target = syncaccount,
                                       name = "Account sync %s" % accountname,
                                       args = (accountname,))
        thread.setDaemon(1)
        thread.start()
        threads.append(thread)
    # Wait for the threads to finish.
    threadutil.threadsreset(threads)
    mbnames.genmbnames(config, mailboxes)

def sync_with_timer():
    currentThread().setExitMessage('SYNC_WITH_TIMER_TERMINATE')
    syncitall()
    if config.has_option('general', 'autorefresh'):
        refreshperiod = config.getint('general', 'autorefresh') * 60
        while 1:
            # Set up keep-alives.
            kaevents = {}
            kathreads = {}
            for accountname in accounts:
                if config.has_option(accountname, 'holdconnectionopen') and \
                   config.getboolean(accountname, 'holdconnectionopen') and \
                   config.has_option(accountname, 'keepalive'):
                    event = Event()
                    kaevents[accountname] = event
                    thread = ExitNotifyThread(target = servers[accountname].keepalive,
                                              name = "Keep alive " + accountname,
                                              args = (config.getint(accountname, 'keepalive'), event))
                    thread.setDaemon(1)
                    thread.start()
                    kathreads[accountname] = thread
            if ui.sleep(refreshperiod) == 2:
                # Cancel keep-alives, but don't bother terminating threads
                for event in kaevents.values():
                    event.set()
                break
            else:
                # Cancel keep-alives and wait for threads to terminate.
                for event in kaevents.values():
                    event.set()
                for thread in kathreads.values():
                    thread.join()
                syncitall()
        
def threadexited(thread):
    if thread.getExitCause() == 'EXCEPTION':
        if isinstance(thread.getExitException(), SystemExit):
            # Bring a SystemExit into the main thread.
            # Do not send it back to UI layer right now.
            # Maybe later send it to ui.terminate?
            raise SystemExit
        ui.threadException(thread)      # Expected to terminate
        sys.exit(100)                   # Just in case...
        os._exit(100)
    elif thread.getExitMessage() == 'SYNC_WITH_TIMER_TERMINATE':
        ui.terminate()
        # Just in case...
        sys.exit(100)
        os._exit(100)
    else:
        ui.threadExited(thread)

threadutil.initexitnotify()
t = ExitNotifyThread(target=sync_with_timer,
                     name='Sync Runner')
t.setDaemon(1)
t.start()
try:
    threadutil.exitnotifymonitorloop(threadexited)
except SystemExit:
    raise
except:
    ui.mainException()                  # Also expected to terminate.
