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

from offlineimap.threadutil import accountThreads, InstanceLimitedThread, STOP_MONITOR
from offlineimap.accounts import SyncableAccount
from threading import currentThread

def syncaccount(config, accountname):
    """Return a new running thread for this account."""

    account = SyncableAccount(config, accountname)
    thread = InstanceLimitedThread(instancename = 'ACCOUNTLIMIT',
                                   target = account.syncrunner,
                                   name = "Account sync %s" % accountname)
    thread.setDaemon(True)
    thread.start()
    return thread

def syncitall(accounts, config):
    """The target when in multithreading mode for running accounts threads."""

    # Special exit message for the monitor to stop looping so the main thread
    # can exit.
    currentThread().exit_message = STOP_MONITOR
    threads = accountThreads() # The collection of accounts threads.
    for accountname in accounts:
        # Start a new thread per account and store it in the collection.
        threads.add(syncaccount(config, accountname))
    # Wait for the threads to finish.
    threads.wait() # Blocks until all accounts are processed.
