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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from UIBase import UIBase
from getpass import getpass
import sys
from threading import *

class TTYUI(UIBase):
    def __init__(s, config, verbose = 0):
        UIBase.__init__(s, config, verbose)
        s.iswaiting = 0
        s.outputlock = Lock()
        s._lastThreaddisplay = None

    def isusable(s):
        return sys.stdout.isatty() and sys.stdin.isatty()
        
    def _display(s, msg):
        s.outputlock.acquire()
        try:
            #if the next output comes from a different thread than our last one
            #add the info.
            #Most look like 'account sync foo' or 'Folder sync foo'.
            try:
                threadname = currentThread().name
            except AttributeError:
                threadname = currentThread().getName()
            if (threadname == s._lastThreaddisplay \
                    or threadname == 'MainThread'):
                print " %s" % msg
            else:
                print "%s:\n %s" % (threadname, msg)
                s._lastThreaddisplay = threadname

            sys.stdout.flush()
        finally:
            s.outputlock.release()

    def getpass(s, accountname, config, errmsg = None):
        if errmsg:
            s._msg("%s: %s" % (accountname, errmsg))
        s.outputlock.acquire()
        try:
            return getpass("%s: Enter password: " % accountname)
        finally:
            s.outputlock.release()

    def mainException(s):
        if isinstance(sys.exc_info()[1], KeyboardInterrupt) and \
           s.iswaiting:
            sys.stdout.write("Timer interrupted at user request; program terminating.             \n")
            s.terminate()
        else:
            UIBase.mainException(s)

