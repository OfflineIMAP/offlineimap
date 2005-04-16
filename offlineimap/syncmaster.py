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
import offlineimap.accounts
from offlineimap.accounts import SyncableAccount
from offlineimap.ui import UIBase
import re, os, os.path, offlineimap, sys
from ConfigParser import ConfigParser
from threading import *

def syncaccount(threads, config, accountname):
    account = SyncableAccount(config, accountname)
    thread = InstanceLimitedThread(instancename = 'ACCOUNTLIMIT',
                                   target = account.syncrunner,
                                   name = "Account sync %s" % accountname)
    thread.setDaemon(1)
    thread.start()
    threads.add(thread)
    
def syncitall(accounts, config):
    currentThread().setExitMessage('SYNC_WITH_TIMER_TERMINATE')
    ui = UIBase.getglobalui()
    threads = threadutil.threadlist()
    mbnames.init(config, accounts)
    for accountname in accounts:
        syncaccount(threads, config, accountname)
    # Wait for the threads to finish.
    threads.reset()
