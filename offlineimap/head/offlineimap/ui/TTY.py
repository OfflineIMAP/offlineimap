# TTY UI
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

from UIBase import UIBase
from getpass import getpass
import select, sys
from threading import *

class TTYUI(UIBase):
    def __init__(s, config, verbose = 0):
        UIBase.__init__(s, config, verbose)
        s.iswaiting = 0
        s.outputlock = Lock()

    def isusable(s):
        return sys.stdout.isatty() and sys.stdin.isatty()
        
    def _msg(s, msg):
        s.outputlock.acquire()
        try:
            if (currentThread().getName() == 'MainThread'):
                print msg
            else:
                print "%s:\n   %s" % (currentThread().getName(), msg)
            sys.stdout.flush()
        finally:
            s.outputlock.release()

    def getpass(s, accountname, config, errmsg = None):
        if errmsg:
            s._msg("%s: %s" % (accountname, errmsg))
        s.outputlock.acquire()
        try:
            return getpass("%s: Enter password for %s on %s: " %
                           (accountname, config.get(accountname, "remoteuser"),
                            config.get(accountname, "remotehost")))
        finally:
            s.outputlock.release()

    def sleep(s, sleepsecs):
        s.iswaiting = 1
        try:
            UIBase.sleep(s, sleepsecs)
        finally:
            s.iswaiting = 0

    def mainException(s):
        if isinstance(sys.exc_info()[1], KeyboardInterrupt) and \
           s.iswaiting:
            sys.stdout.write("Timer interrupted at user request; program terminating.             \n")
            s.terminate()
        else:
            UIBase.mainException(s)

    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs > 0:
            sys.stdout.write("Next sync in %d:%02d (press Enter to sync now, Ctrl-C to abort)   \r" % \
                             (remainingsecs / 60, remainingsecs % 60))
            sys.stdout.flush()
        else:
            sys.stdout.write("Wait done, proceeding with sync....                                \n")

        if sleepsecs > 0:
            if len(select.select([sys.stdin], [], [], sleepsecs)[0]):
                sys.stdin.readline()
                return 1
        return 0
            
            
