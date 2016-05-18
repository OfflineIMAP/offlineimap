# Copyright (C) 2002-2012 John Goerzen & contributors
# Thread support module
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

from threading import Lock, Thread, BoundedSemaphore, currentThread
try:
    from Queue import Queue, Empty
except ImportError: # python3
    from queue import Queue, Empty
import traceback
import os.path
from offlineimap.ui import getglobalui


STOP_MONITOR = 'STOP_MONITOR'

######################################################################
# General utilities
######################################################################

def semaphorereset(semaphore, originalstate):
    """Block until `semaphore` gets back to its original state, ie all acquired
    resources have been released."""

    for i in range(originalstate):
        semaphore.acquire()
    # Now release these.
    for i in range(originalstate):
        semaphore.release()

class accountThreads(object):
    """Store the list of all threads in the software so it can be used to find out
    what's running and what's not."""

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

    def wait(self):
        while 1:
            thread = self.pop()
            if not thread:
                return
            thread.join()


######################################################################
# Exit-notify threads
######################################################################

exitedThreads = Queue()

def monitor():
    """An infinite "monitoring" loop watching for finished ExitNotifyThread's.

    This one is supposed to run in the main thread.
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

    global exitedThreads
    ui = getglobalui()

    while True:
        # Loop forever and call 'callback' for each thread that exited
        try:
            # We need a timeout in the get() call, so that ctrl-c can throw a
            # SIGINT (http://bugs.python.org/issue1360). A timeout with empty
            # Queue will raise `Empty`.
            #
            # ExitNotifyThread add themselves to the exitedThreads queue once
            # they are done (normally or with exception).
            thread = exitedThreads.get(True, 60)
            # Request to abort when callback returns True.

            if thread.exit_exception is not None:
                if isinstance(thread.exit_exception, SystemExit):
                    # Bring a SystemExit into the main thread.
                    # Do not send it back to UI layer right now.
                    # Maybe later send it to ui.terminate?
                    raise SystemExit
                ui.threadException(thread) # Expected to terminate the program.
                # Should never hit this line.
                raise AssertionError("thread has 'exit_exception' set to"
                    " '%s' [%s] but this value is unexpected"
                    " and the ui did not stop the program."%
                    (repr(thread.exit_exception), type(thread.exit_exception)))

            # Only the monitor thread has this exit message set.
            elif thread.exit_message == STOP_MONITOR:
                break # Exit the loop here.
            else:
                ui.threadExited(thread)
        except Empty:
            pass

class ExitNotifyThread(Thread):
    """This class is designed to alert a "monitor" to the fact that a
    thread has exited and to provide for the ability for it to find out
    why.  All instances are made daemon threads (setDaemon(True), so we
    bail out when the mainloop dies.

    The thread can set instance variables self.exit_message for a human
    readable reason of the thread exit.

    There is one instance of this class at runtime. The main thread waits for
    the monitor to end."""

    profiledir = None
    """Class variable that is set to the profile directory if required."""

    def __init__(self, *args, **kwargs):
        super(ExitNotifyThread, self).__init__(*args, **kwargs)
        # These are all child threads that are supposed to go away when
        # the main thread is killed.
        self.setDaemon(True)
        self.exit_message = None
        self._exit_exc = None
        self._exit_stacktrace = None

    def run(self):
        """Allow profiling of a run and store exceptions."""

        global exitedThreads
        try:
            if not ExitNotifyThread.profiledir: # normal case
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
                prof.dump_stats(os.path.join(ExitNotifyThread.profiledir,
                                "%s_%s.prof"% (self.ident, self.getName())))
        except Exception as e:
            # Thread exited with Exception, store it
            tb = traceback.format_exc()
            self.set_exit_exception(e, tb)

        exitedThreads.put(self, True)

    def set_exit_exception(self, exc, st=None):
        """Sets Exception and stacktrace of a thread, so that other
        threads can query its exit status"""

        self._exit_exc = exc
        self._exit_stacktrace = st

    @property
    def exit_exception(self):
        """Returns the cause of the exit, one of:
        Exception() -- the thread aborted with this exception
        None -- normal termination."""

        return self._exit_exc

    @property
    def exit_stacktrace(self):
        """Returns a string representing the stack trace if set"""

        return self._exit_stacktrace

    @classmethod
    def set_profiledir(cls, directory):
        """If set, will output profile information to 'directory'"""

        cls.profiledir = directory


######################################################################
# Instance-limited threads
######################################################################

limitedNamespaces = {}

def initInstanceLimit(limitNamespace, instancemax):
    """Initialize the instance-limited thread implementation.

    Run up to intancemax threads for the given limitNamespace. This allows to
    honor maxsyncaccounts and maxconnections."""

    global limitedNamespaces

    if not limitNamespace in limitedNamespaces:
        limitedNamespaces[limitNamespace] = BoundedSemaphore(instancemax)


class InstanceLimitedThread(ExitNotifyThread):
    def __init__(self, limitNamespace, *args, **kwargs):
        self.limitNamespace = limitNamespace
        super(InstanceLimitedThread, self).__init__(*args, **kwargs)

    def start(self):
        global limitedNamespaces

        limitedNamespaces[self.limitNamespace].acquire()
        ExitNotifyThread.start(self)

    def run(self):
        global limitedNamespaces

        try:
            ExitNotifyThread.run(self)
        finally:
            if limitedNamespaces and limitedNamespaces[self.limitNamespace]:
                limitedNamespaces[self.limitNamespace].release()
