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

from offlineimap.threadutil import threadlist, InstanceLimitedThread
from offlineimap.accounts import SyncableAccount
from threading import currentThread

def syncaccount(threads, config, accountname):
    account = SyncableAccount(config, accountname)
    thread = InstanceLimitedThread(instancename = 'ACCOUNTLIMIT',
                                   target = account.syncrunner,
                                   name = "Account sync %s" % accountname)
    thread.setDaemon(True)
    thread.start()
    threads.add(thread)

def syncitall(accounts, config):
    # Special exit message for SyncRunner thread, so main thread can exit
    currentThread().exit_message = 'SYNCRUNNER_EXITED_NORMALLY'
    threads = threadlist()
    for accountname in accounts:
        syncaccount(threads, config, accountname)
    # Wait for the threads to finish.
    threads.reset()
