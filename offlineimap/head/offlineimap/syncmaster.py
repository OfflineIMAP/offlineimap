# OfflineIMAP synchronization master code
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

from offlineimap import imaplib, imapserver, repository, folder, mbnames, threadutil, version
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
from offlineimap.ui import UIBase
import re, os, os.path, offlineimap, sys
from ConfigParser import ConfigParser
from threading import *

def syncaccount(accountname, metadatadir, servers, config, passwords,
                localeval, *args):
    ui = UIBase.getglobalui()
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
            
        remoterepos = repository.IMAP.IMAPRepository(config, localeval, accountname, server)

        # Connect to the Maildirs.
        localrepos = repository.Maildir.MaildirRepository(os.path.expanduser(config.get(accountname, "localfolders")), accountname, config)

        # Connect to the local cache.
        statusrepos = repository.LocalStatus.LocalStatusRepository(accountmetadata)

        ui.syncfolders(remoterepos, localrepos)
        remoterepos.syncfoldersto(localrepos)
        ui.acct(accountname)

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
    ui = UIBase.getglobalui()
    # Load local folder.
    localfolder = localrepos.\
                  getfolder(remotefolder.getvisiblename().\
                            replace(remoterepos.getsep(), localrepos.getsep()))
    # Write the mailboxes
    mailboxes.append({'accountname': accountname,
                      'foldername': localfolder.getvisiblename()})
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

    
    # If either the local or the status folder has messages and
    # there is a UID validity problem, warn and abort.
    # If there are no messages, UW IMAPd loses UIDVALIDITY.
    # But we don't really need it if both local folders are empty.
    # So, in that case, save it off.
    if (len(localfolder.getmessagelist()) or \
        len(statusfolder.getmessagelist())) and \
        not localfolder.isuidvalidityok(remotefolder):
        ui.validityproblem(remotefolder)
        return
    else:
        localfolder.saveuidvalidity(remotefolder.getuidvalidity())

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
    remotefolder.syncmessagesto(localfolder)

    # Make sure the status folder is up-to-date.
    ui.syncingmessages(localrepos, localfolder, statusrepos, statusfolder)
    localfolder.syncmessagesto(statusfolder)
    statusfolder.save()

    

def syncitall(accounts, metadatadir, servers, config, passwords, localeval):
    ui = UIBase.getglobalui()
    global mailboxes
    mailboxes = []                      # Reset.
    threads = []
    for accountname in accounts:
        thread = InstanceLimitedThread(instancename = 'ACCOUNTLIMIT',
                                       target = syncaccount,
                                       name = "Account sync %s" % accountname,
                                       args = (accountname, metadatadir,
                                               servers, config, passwords,
                                               localeval))
        thread.setDaemon(1)
        thread.start()
        threads.append(thread)
    # Wait for the threads to finish.
    threadutil.threadsreset(threads)
    mbnames.genmbnames(config, localeval, mailboxes)

def sync_with_timer(accounts, metadatadir, servers, config, passwords,
                    localeval):
    ui = UIBase.getglobalui()
    currentThread().setExitMessage('SYNC_WITH_TIMER_TERMINATE')
    syncitall(accounts, metadatadir, servers, config, passwords, localeval)
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
                syncitall(accounts, metadatadir, servers, config, passwords,
                          localeval)
