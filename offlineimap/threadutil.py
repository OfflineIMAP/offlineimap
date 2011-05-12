# Copyright (C) 2002, 2003 John Goerzen
# Thread support module
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

from threading import Lock, Thread, BoundedSemaphore
from Queue import Queue, Empty
import traceback
from thread import get_ident	# python < 2.6 support
import sys
from offlineimap.ui import getglobalui

profiledir = None

def setprofiledir(newdir):
    global profiledir
    profiledir = newdir

######################################################################
# General utilities
######################################################################

def semaphorereset(semaphore, originalstate):
    """Wait until the semaphore gets back to its original state -- all acquired
    resources released."""
    for i in range(originalstate):
        semaphore.acquire()
    # Now release these.
    for i in range(originalstate):
        semaphore.release()
        
class threadlist:
    def __init__(self):
        self.lock = Lock()
        self.list = []

    def add(self, thread):
        self.lock.acquire()
        try:
            self.list.append(thread)
        finally:
            self.lock.release()

    def remove(self, thread):
        self.lock.acquire()
        try:
            self.list.remove(thread)
        finally:
            self.lock.release()

    def pop(self):
        self.lock.acquire()
        try:
            if not len(self.list):
                return None
            return self.list.pop()
        finally:
            self.lock.release()

    def reset(self):
        while 1:
            thread = self.pop()
            if not thread:
                return
            thread.join()
            

######################################################################
# Exit-notify threads
######################################################################

exitthreads = Queue(100)

def exitnotifymonitorloop(callback):
    """An infinite "monitoring" loop watching for finished ExitNotifyThread's.

    :param callback: the function to call when a thread terminated. That 
                     function is called with a single argument -- the 
                     ExitNotifyThread that has terminated. The monitor will 
                     not continue to monitor for other threads until
                     'callback' returns, so if it intends to perform long
                     calculations, it should start a new thread itself -- but
                     NOT an ExitNotifyThread, or else an infinite loop 
                     may result.
                     Furthermore, the monitor will hold the lock all the 
                     while the other thread is waiting.
    :type callback:  a callable function
    """
    global exitthreads
    while 1:                            
        # Loop forever and call 'callback' for each thread that exited
        try:
            # we need a timeout in the get() call, so that ctrl-c can throw
            # a SIGINT (http://bugs.python.org/issue1360). A timeout with empty
            # Queue will raise `Empty`.
            thrd = exitthreads.get(True, 60)
            callback(thrd)
        except Empty:
            pass

def threadexited(thread):
    """Called when a thread exits."""
    ui = getglobalui()
    if thread.getExitCause() == 'EXCEPTION':
        if isinstance(thread.getExitException(), SystemExit):
            # Bring a SystemExit into the main thread.
            # Do not send it back to UI layer right now.
            # Maybe later send it to ui.terminate?
            raise SystemExit
        ui.threadException(thread)      # Expected to terminate
        sys.exit(100)                   # Just in case...
    elif thread.getExitMessage() == 'SYNC_WITH_TIMER_TERMINATE':
        ui.terminate()
        # Just in case...
        sys.exit(100)
    else:
        ui.threadExited(thread)

class ExitNotifyThread(Thread):
    """This class is designed to alert a "monitor" to the fact that a thread has
    exited and to provide for the ability for it to find out why."""
    def run(self):
        global exitthreads, profiledir
        try:
            if not profiledir:          # normal case
                Thread.run(self)
            else:
                try:
                    import cProfile as profile
                except ImportError:
                    import profile
                prof = profile.Profile()
                try:
                    prof = prof.runctx("Thread.run(self)", globals(), locals())
                except SystemExit:
                    pass
                prof.dump_stats( \
                            profiledir + "/" + str(get_ident()) + "_" + \
                            self.getName() + ".prof")
        except:
            self.setExitCause('EXCEPTION')
            if sys:
                self.setExitException(sys.exc_info()[1])
                tb = traceback.format_exc()
                self.setExitStackTrace(tb)
        else:
            self.setExitCause('NORMAL')
        if not hasattr(self, 'exitmessage'):
            self.setExitMessage(None)

        if exitthreads:
            exitthreads.put(self, True)

    def setExitCause(self, cause):
        self.exitcause = cause
    def getExitCause(self):
        """Returns the cause of the exit, one of:
        'EXCEPTION' -- the thread aborted because of an exception
        'NORMAL' -- normal termination."""
        return self.exitcause
    def setExitException(self, exc):
        self.exitexception = exc
    def getExitException(self):
        """If getExitCause() is 'EXCEPTION', holds the value from
        sys.exc_info()[1] for this exception."""
        return self.exitexception
    def setExitStackTrace(self, st):
        self.exitstacktrace = st
    def getExitStackTrace(self):
        """If getExitCause() is 'EXCEPTION', returns a string representing
        the stack trace for this exception."""
        return self.exitstacktrace
    def setExitMessage(self, msg):
        """Sets the exit message to be fetched by a subsequent call to
        getExitMessage.  This message may be any object or type except
        None."""
        self.exitmessage = msg
    def getExitMessage(self):
        """For any exit cause, returns the message previously set by
        a call to setExitMessage(), or None if there was no such message
        set."""
        return self.exitmessage
            

######################################################################
# Instance-limited threads
######################################################################

instancelimitedsems = {}
instancelimitedlock = Lock()

def initInstanceLimit(instancename, instancemax):
    """Initialize the instance-limited thread implementation to permit
    up to intancemax threads with the given instancename."""
    instancelimitedlock.acquire()
    if not instancelimitedsems.has_key(instancename):
        instancelimitedsems[instancename] = BoundedSemaphore(instancemax)
    instancelimitedlock.release()

class InstanceLimitedThread(ExitNotifyThread):
    def __init__(self, instancename, *args, **kwargs):
        self.instancename = instancename
                                                   
        apply(ExitNotifyThread.__init__, (self,) + args, kwargs)

    def start(self):
        instancelimitedsems[self.instancename].acquire()
        ExitNotifyThread.start(self)
        
    def run(self):
        try:
            ExitNotifyThread.run(self)
        finally:
            if instancelimitedsems and instancelimitedsems[self.instancename]:
                instancelimitedsems[self.instancename].release()
