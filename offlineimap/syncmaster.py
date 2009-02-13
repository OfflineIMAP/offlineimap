# OfflineIMAP synchronization master code
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

from offlineimap import imaplib2, imapserver, repository, folder, mbnames, threadutil, version
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
import offlineimap.accounts
from offlineimap.accounts import SyncableAccount, SigListener
from offlineimap.ui import UIBase
import re, os, os.path, offlineimap, sys
from ConfigParser import ConfigParser
from threading import *

def syncaccount(threads, config, accountname, siglisteners):
    account = SyncableAccount(config, accountname)
    siglistener = SigListener()
    thread = InstanceLimitedThread(instancename = 'ACCOUNTLIMIT',
                                   target = account.syncrunner,
                                   name = "Account sync %s" % accountname,
                                   kwargs = {'siglistener': siglistener} )
    # the Sync Runner thread is the only one that will mutate siglisteners
    siglisteners.append(siglistener)
    thread.setDaemon(1)
    thread.start()
    threads.add(thread)
    
def syncitall(accounts, config, siglisteners):
    currentThread().setExitMessage('SYNC_WITH_TIMER_TERMINATE')
    ui = UIBase.getglobalui()
    threads = threadutil.threadlist()
    mbnames.init(config, accounts)
    for accountname in accounts:
        syncaccount(threads, config, accountname, siglisteners)
    # Wait for the threads to finish.
    threads.reset()
