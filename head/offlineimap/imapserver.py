# IMAP server support
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

from offlineimap import imaplib, imaputil
from threading import *

class UsefulIMAPMixIn:
    def getstate(self):
        return self.state
    def getselectedfolder(self):
        if self.getstate() == 'SELECTED':
            return self.selectedfolder
        return None

    def select(self, mailbox='INBOX', readonly=None):
        if self.getselectedfolder() == mailbox and not readonly:
            # No change; return.
            return
        result = self.__class__.__bases__[1].select(self, mailbox, readonly)
        if result[0] != 'OK':
            raise ValueError, "Error from select: %s" % str(result)
        if self.getstate() == 'SELECTED' and not readonly:
            self.selectedfolder = mailbox
        else:
            self.selectedfolder = None

class UsefulIMAP4(UsefulIMAPMixIn, imaplib.IMAP4): pass
class UsefulIMAP4_SSL(UsefulIMAPMixIn, imaplib.IMAP4_SSL): pass

class IMAPServer:
    def __init__(self, username, password, hostname, port = None, ssl = 1,
                 maxconnections = 1):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.usessl = ssl
        self.delim = None
        self.root = None
        if port == None:
            if ssl:
                self.port = 993
            else:
                self.port = 143
        self.maxconnections = maxconnections
        self.availableconnections = []
        self.assignedconnections = []
        self.semaphore = BoundedSemaphore(self.maxconnections)
        self.connectionlock = Lock()
        

    def getdelim(self):
        """Returns this server's folder delimiter.  Can only be called
        after one or more calls to acquireconnection."""
        return self.delim

    def getroot(self):
        """Returns this server's folder root.  Can only be called after one
        or more calls to acquireconnection."""
        return self.root


    def releaseconnection(self, connection):
        self.connectionlock.acquire()
        self.assignedconnections.remove(connection)
        self.availableconnections.append(connection)
        self.connectionlock.release()
        self.semaphore.release()
            

    def acquireconnection(self):
        """Fetches a connection from the pool, making sure to create a new one
        if needed, to obey the maximum connection limits, etc.
        Opens a connection to the server and returns an appropriate
        object."""

        self.semaphore.acquire()
        self.connectionlock.acquire()
        imapobj = None

        if len(self.availableconnections): # One is available.
            imapobj = self.availableconnections[0]
            self.assignedconnections.append(imapobj)
            del(self.availableconnections[0])
            self.connectionlock.release()
            return imapobj
        
        self.connectionlock.release()   # Release until need to modify data

        # Generate a new connection.
        if self.usessl:
            imapobj = UsefulIMAP4_SSL(self.hostname, self.port)
        else:
            imapobj = UsefulIMAP4(self.hostname, self.port)
            
        imapobj.login(self.username, self.password)

        if self.delim == None:
            self.delim, self.root = \
                        imaputil.imapsplit(imapobj.list('""', '""')[1][0])[1:]
            self.delim = imaputil.dequote(self.delim)
            self.root = imaputil.dequote(self.root)

        self.connectionlock.acquire()
        self.assignedconnections.append(imapobj)
        self.connectionlock.release()
        return imapobj
    
    def connectionwait(self):
        """Waits until there is a connection available.  Note that between
        the time that a connection becomes available and the time it is
        requested, another thread may have grabbed it.  This function is
        mainly present as a way to avoid spawning thousands of threads
        to copy messages, then have them all wait for 3 available connections.
        It's OK if we have maxconnections + 1 or 2 threads, which is what
        this will help us do."""
        self.semaphore.acquire()
        self.semaphore.release()

    def close(self):
        # Make sure I own all the semaphores.  Let the threads finish
        # their stuff.  This is a blocking method.
        self.connectionlock.acquire()
        for i in range(self.maxconnections):
            self.semaphore.acquire()
        for imapobj in self.assignedconnections + self.availableconnections:
            imapobj.logout()
        self.assignedconnections = []
        self.availableconnections = []
        for i in range(self.maxconnections):
            self.semaphore.release()
        self.connectionlock.release()
        

