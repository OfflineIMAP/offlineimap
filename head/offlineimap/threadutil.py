# Copyright (C) 2002 John Goerzen
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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from threading import *
from StringIO import StringIO
import sys, traceback, thread

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

######################################################################
# Exit-notify threads
######################################################################

exitcondition = Condition(Lock())
exitthread = None
inited = 0

def initexitnotify():
    """Initialize the exit notify system.  This MUST be called from the
    SAME THREAD that will call monitorloop BEFORE it calls monitorloop.
    This SHOULD be called before the main thread starts any other
    ExitNotifyThreads, or else it may miss the ability to catch the exit
    status from them!"""
    exitcondition.acquire()

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
    global exitcondition, exitthread
    while 1:                            # Loop forever.
        while exitthread == None:
            exitcondition.wait(1)
        callback(exitthread)
        exitthread = None
    

class ExitNotifyThread(Thread):
    """This class is designed to alert a "monitor" to the fact that a thread has
    exited and to provide for the ability for it to find out why."""
    def run(self):
        global exitcondition, exitthread
        self.threadid = thread.get_ident()
        try:
            Thread.run(self)
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
        exitcondition.acquire()
        exitthread = self
        exitcondition.notify()
        exitcondition.release()

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
        
    
