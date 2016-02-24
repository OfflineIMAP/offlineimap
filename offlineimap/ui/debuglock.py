# Locking debugging code -- temporary
# Copyright (C) 2003-2015 John Goerzen & contributors
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

from threading import Lock, currentThread
import traceback
logfile = open("/tmp/logfile", "wt")
loglock = Lock()

class DebuggingLock:
    def __init__(self, name):
        self.lock = Lock()
        self.name = name

    def acquire(self, blocking = 1):
        self.print_tb("Acquire lock")
        self.lock.acquire(blocking)
        self.logmsg("===== %s: Thread %s acquired lock\n"%
            (self.name, currentThread().getName()))

    def release(self):
        self.print_tb("Release lock")
        self.lock.release()

    def logmsg(self, msg):
        loglock.acquire()
        logfile.write(msg + "\n")
        logfile.flush()
        loglock.release()

    def print_tb(self, msg):
        self.logmsg(".... %s: Thread %s attempting to %s\n"% \
                    (self.name, currentThread().getName(), msg) + \
                    "\n".join(traceback.format_list(traceback.extract_stack())))


