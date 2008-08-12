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

from threading import *
from StringIO import StringIO
from Queue import Queue, Empty
import sys, traceback, thread, time
from offlineimap.ui import UIBase       # for getglobalui()

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
        
def semaphorewait(semaphore):
    semaphore.acquire()
    semaphore.release()
    
def threadsreset(threadlist):
    for thr in threadlist:
        thr.join()

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
inited = 0

def initexitnotify():
    """Initialize the exit notify system.  This MUST be called from the
    SAME THREAD that will call monitorloop BEFORE it calls monitorloop.
    This SHOULD be called before the main thread starts any other
    ExitNotifyThreads, or else it may miss the ability to catch the exit
    status from them!"""
    pass

def exitnotifymonitorloop(callback):
    """Enter an infinite "monitoring" loop.  The argument, callback,
    defines the function to call when an ExitNotifyThread has terminated.
    That function is called with a single argument -- the ExitNotifyThread
    that has terminated.  The monitor will not continue to monitor for
    other threads until the function returns, so if it intends to perform
    long calculations, it should start a new thread itself -- but NOT
    an ExitNotifyThread, or else an infinite loop may result.  Furthermore,
    the monitor will hold the lock all the while the other thread is waiting.
    """
    global exitthreads
    while 1:                            # Loop forever.
        try:
            thrd = exitthreads.get(False)
            callback(thrd)
        except Empty:
            time.sleep(1)

def threadexited(thread):
    """Called when a thread exits."""
    ui = UIBase.getglobalui()
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

class ExitNotifyThread(Thread):
    """This class is designed to alert a "monitor" to the fact that a thread has
    exited and to provide for the ability for it to find out why."""
    def run(self):
        global exitthreads, profiledir
        self.threadid = thread.get_ident()
        try:
            if not profiledir:          # normal case
                Thread.run(self)
            else:
                import profile
                prof = profile.Profile()
                try:
                    prof = prof.runctx("Thread.run(self)", globals(), locals())
                except SystemExit:
                    pass
                prof.dump_stats( \
                            profiledir + "/" + str(self.threadid) + "_" + \
                            self.getName() + ".prof")
        except:
            self.setExitCause('EXCEPTION')
            self.setExitException(sys.exc_info()[1])
            sbuf = StringIO()
            traceback.print_exc(file = sbuf)
            self.setExitStackTrace(sbuf.getvalue())
        else:
            self.setExitCause('NORMAL')
        if not hasattr(self, 'exitmessage'):
            self.setExitMessage(None)

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
            instancelimitedsems[self.instancename].release()
        
    
######################################################################
# Multi-lock -- capable of handling a single thread requesting a lock
# multiple times
######################################################################

class MultiLock:
    def __init__(self):
        self.lock = Lock()
        self.statuslock = Lock()
        self.locksheld = {}

    def acquire(self):
        """Obtain a lock.  Provides nice support for a single
        thread trying to lock it several times -- as may be the case
        if one I/O-using object calls others, while wanting to make it all
        an atomic operation.  Keeps a "lock request count" for the current
        thread, and acquires the lock when it goes above zero, releases when
        it goes below one.

        This call is always blocking."""
        
        # First, check to see if this thread already has a lock.
        # If so, increment the lock count and just return.
        self.statuslock.acquire()
        try:
            threadid = thread.get_ident()

            if threadid in self.locksheld:
                self.locksheld[threadid] += 1
                return
            else:
                # This is safe because it is a per-thread structure
                self.locksheld[threadid] = 1
        finally:
            self.statuslock.release()
        self.lock.acquire()

    def release(self):
        self.statuslock.acquire()
        try:
            threadid = thread.get_ident()
            if self.locksheld[threadid] > 1:
                self.locksheld[threadid] -= 1
                return
            else:
                del self.locksheld[threadid]
                self.lock.release()
        finally:
            self.statuslock.release()

        
