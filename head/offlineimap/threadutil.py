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
    for thread in threadlist:
        thread.join()

instancelimitedsems = {}
instancelimitedlock = Lock()

def initInstanceLimit(instancename, instancemax):
    instancelimitedlock.acquire()
    if not instancelimitedsems.has_key(instancename):
        instancelimitedsems[instancename] = BoundedSemaphore(instancemax)
    instancelimitedlock.release()

class InstanceLimitedThread(Thread):
    def __init__(self, instancename, *args, **kwargs):
        self.instancename = instancename
                                                   
        apply(Thread.__init__, (self,) + args, kwargs)

    def start(self):
        instancelimitedsems[self.instancename].acquire()
        Thread.start(self)
        
    def run(self):
        try:
            Thread.run(self)
        finally:
            instancelimitedsems[self.instancename].release()
        
    
