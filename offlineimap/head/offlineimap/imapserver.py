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

from offlineimap import imaplib, imaputil, threadutil
from offlineimap.ui import UIBase
from threading import *
import thread, hmac


class UsefulIMAPMixIn:
    def getstate(self):
        return self.state
    def getselectedfolder(self):
        if self.getstate() == 'SELECTED':
            return self.selectedfolder
        return None

    def select(self, mailbox='INBOX', readonly=None):
        if self.getselectedfolder() == mailbox:
            self.is_readonly = readonly
            # No change; return.
            return
        result = self.__class__.__bases__[1].select(self, mailbox, readonly)
        if result[0] != 'OK':
            raise ValueError, "Error from select: %s" % str(result)
        if self.getstate() == 'SELECTED':
            self.selectedfolder = mailbox
        else:
            self.selectedfolder = None

class UsefulIMAP4(UsefulIMAPMixIn, imaplib.IMAP4): pass
class UsefulIMAP4_SSL(UsefulIMAPMixIn, imaplib.IMAP4_SSL): pass
class UsefulIMAP4_Tunnel(UsefulIMAPMixIn, imaplib.IMAP4_Tunnel): pass

class IMAPServer:
    def __init__(self, config, accountname,
                 username = None, password = None, hostname = None,
                 port = None, ssl = 1, maxconnections = 1, tunnel = None,
                 reference = '""'):
        self.account = accountname
        self.config = config
        self.username = username
        self.password = password
        self.passworderror = None
        self.hostname = hostname
        self.tunnel = tunnel
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
        self.lastowner = {}
        self.semaphore = BoundedSemaphore(self.maxconnections)
        self.connectionlock = Lock()
        self.reference = reference

    def getpassword(self):
        if self.password != None and self.passworderror == None:
            return self.password

        self.password = UIBase.getglobalui().getpass(self.account, self.config,
                                                     self.passworderror)
        self.passworderror = None

        return self.password

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

    def md5handler(self, response):
        challenge = response.strip()
        msg = self.getpassword()
        while len(msg) < 64:
            msg += "\0"

        reply = hmac.new(challenge, msg)
        retval = self.username + ' ' + \
                     reply.hexdigest()
        return retval

    def acquireconnection(self):
        """Fetches a connection from the pool, making sure to create a new one
        if needed, to obey the maximum connection limits, etc.
        Opens a connection to the server and returns an appropriate
        object."""

        self.semaphore.acquire()
        self.connectionlock.acquire()
        imapobj = None

        if len(self.availableconnections): # One is available.
            # Try to find one that previously belonged to this thread
            # as an optimization.  Start from the back since that's where
            # they're popped on.
            threadid = thread.get_ident()
            imapobj = None
            for i in range(len(self.availableconnections) - 1, -1, -1):
                tryobj = self.availableconnections[i]
                if self.lastowner[tryobj] == threadid:
                    imapobj = tryobj
                    del(self.availableconnections[i])
                    break
            if not imapobj:
                imapobj = self.availableconnections[0]
                del(self.availableconnections[0])
            self.assignedconnections.append(imapobj)
            self.lastowner[imapobj] = thread.get_ident()
            self.connectionlock.release()
            return imapobj
        
        self.connectionlock.release()   # Release until need to modify data

        UIBase.getglobalui().connecting(self.hostname, self.port)

        success = 0
        while not success:
            # Generate a new connection.
            if self.tunnel:
                imapobj = UsefulIMAP4_Tunnel(self.tunnel)
            elif self.usessl:
                imapobj = UsefulIMAP4_SSL(self.hostname, self.port)
            else:
                imapobj = UsefulIMAP4(self.hostname, self.port)

            if not self.tunnel:
                try:
                    if 'AUTH=CRAM-MD5' in imapobj.capabilities:
                        UIBase.getglobalui().debug('imap',
                                                   'Attempting CRAM-MD5 authentication')
                        imapobj.authenticate('CRAM-MD5', self.md5handler)
                    else:
                        UIBase.getglobalui().debug('imap',
                                                   'Attempting plain authentication')
                        imapobj.login(self.username, self.getpassword())
                    # Would bail by here if there was a failure.
                    success = 1
                except imapobj.error, val:
                    self.passworderror = str(val)
                    self.password = None

        if self.delim == None:
            listres = imapobj.list(self.reference, '""')[1]
            if listres == [None] or listres == None:
                # Some buggy IMAP servers do not respond well to LIST "" ""
                # Work around them.
                listres = imapobj.list(self.reference, '"*"')[1]
            self.delim, self.root = \
                        imaputil.imapsplit(listres[0])[1:]
            self.delim = imaputil.dequote(self.delim)
            self.root = imaputil.dequote(self.root)

        self.connectionlock.acquire()
        self.assignedconnections.append(imapobj)
        self.lastowner[imapobj] = thread.get_ident()
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
        threadutil.semaphorewait(self.semaphore)

    def close(self):
        # Make sure I own all the semaphores.  Let the threads finish
        # their stuff.  This is a blocking method.
        self.connectionlock.acquire()
        threadutil.semaphorereset(self.semaphore, self.maxconnections)
        for imapobj in self.assignedconnections + self.availableconnections:
            imapobj.logout()
        self.assignedconnections = []
        self.availableconnections = []
        self.lastowner = {}
        self.connectionlock.release()

    def keepalive(self, timeout, event):
        """Sends a NOOP to each connection recorded.   It will wait a maximum
        of timeout seconds between doing this, and will continue to do so
        until the Event object as passed is true.  This method is expected
        to be invoked in a separate thread, which should be join()'d after
        the event is set."""
        while 1:
            event.wait(timeout)
            if event.isSet():
                return
            self.connectionlock.acquire()
            numconnections = len(self.assignedconnections) + \
                             len(self.availableconnections)
            self.connectionlock.release()
            threads = []
            imapobjs = []
        
            for i in range(numconnections):
                imapobj = self.acquireconnection()
                imapobjs.append(imapobj)
                thr = threadutil.ExitNotifyThread(target = imapobj.noop)
                thr.setDaemon(1)
                thr.start()
                threads.append(thr)

            for thr in threads:
                # Make sure all the commands have completed.
                thr.join()

            for imapobj in imapobjs:
                self.releaseconnection(imapobj)

class ConfigedIMAPServer(IMAPServer):
    """This class is designed for easier initialization given a ConfigParser
    object and an account name.  The passwordhash is used if
    passwords for certain accounts are known.  If the password for this
    account is listed, it will be obtained from there."""
    def __init__(self, config, accountname, passwordhash = {}):
        """Initialize the object.  If the account is not a tunnel,
        the password is required."""
        host = config.get(accountname, "remotehost")
        user = config.get(accountname, "remoteuser")
        port = None
        if config.has_option(accountname, "remoteport"):
            port = config.getint(accountname, "remoteport")
        ssl = config.getboolean(accountname, "ssl")
        usetunnel = config.has_option(accountname, "preauthtunnel")
        reference = '""'
        if config.has_option(accountname, "reference"):
            reference = config.get(accountname, "reference")
        server = None
        password = None
        if accountname in passwordhash:
            password = passwordhash[accountname]

        # Connect to the remote server.
        if usetunnel:
            IMAPServer.__init__(self, config, accountname,
                                tunnel = config.get(accountname, "preauthtunnel"),
                                reference = reference,
                                maxconnections = config.getint(accountname, "maxconnections"))
        else:
            if not password:
                if config.has_option(accountname, 'remotepass'):
                    password = config.get(accountname, 'remotepass')
                elif config.has_option(accountname, 'remotepassfile'):
                    passfile = open(os.path.expanduser(config.get(accountname, "remotepassfile")))
                    password = passfile.readline().strip()
                    passfile.close()
            IMAPServer.__init__(self, config, accountname,
                                user, password, host, port, ssl,
                                config.getint(accountname, "maxconnections"),
                                reference = reference)
