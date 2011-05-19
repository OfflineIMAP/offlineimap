# IMAP server support
# Copyright (C) 2002 - 2007 John Goerzen
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

from offlineimap import imaplibutil, imaputil, threadutil, OfflineImapError
from offlineimap.ui import getglobalui
from threading import Lock, BoundedSemaphore
from thread import get_ident	# python < 2.6 support
import time
import hmac
import socket
import base64

from socket import gaierror

try:
    # do we have a recent pykerberos?
    have_gss = False
    import kerberos
    if 'authGSSClientWrap' in dir(kerberos):
        have_gss = True
except ImportError:
    pass

class IMAPServer:
    GSS_STATE_STEP = 0
    GSS_STATE_WRAP = 1
    def __init__(self, config, reposname,
                 username = None, password = None, hostname = None,
                 port = None, ssl = 1, maxconnections = 1, tunnel = None,
                 reference = '""', sslclientcert = None, sslclientkey = None,
                 sslcacertfile = None, idlefolders = []):
        self.ui = getglobalui()
        self.reposname = reposname
        self.config = config
        self.username = username
        self.password = password
        self.passworderror = None
        self.goodpassword = None
        self.hostname = hostname
        self.tunnel = tunnel
        self.port = port
        self.usessl = ssl
        self.sslclientcert = sslclientcert
        self.sslclientkey = sslclientkey
        self.sslcacertfile = sslcacertfile
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
        self.idlefolders = idlefolders
        self.gss_step = self.GSS_STATE_STEP
        self.gss_vc = None
        self.gssapi = False

    def getpassword(self):
        if self.goodpassword != None:
            return self.goodpassword

        if self.password != None and self.passworderror == None:
            return self.password

        self.password = self.ui.getpass(self.reposname,
                                                     self.config,
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
        """Releases a connection, returning it to the pool."""
        self.connectionlock.acquire()
        self.assignedconnections.remove(connection)
        # Don't reuse broken connections
        if connection.Terminate:
            connection.logout()
        else:
            self.availableconnections.append(connection)
        self.connectionlock.release()
        self.semaphore.release()

    def md5handler(self, response):
        challenge = response.strip()
        self.ui.debug('imap', 'md5handler: got challenge %s' % challenge)

        passwd = self.getpassword()
        retval = self.username + ' ' + hmac.new(passwd, challenge).hexdigest()
        self.ui.debug('imap', 'md5handler: returning %s' % retval)
        return retval

    def plainauth(self, imapobj):
        self.ui.debug('imap', 'Attempting plain authentication')
        imapobj.login(self.username, self.getpassword())

    def gssauth(self, response):
        data = base64.b64encode(response)
        try:
            if self.gss_step == self.GSS_STATE_STEP:
                if not self.gss_vc:
                    rc, self.gss_vc = kerberos.authGSSClientInit('imap@' + 
                                                                 self.hostname)
                    response = kerberos.authGSSClientResponse(self.gss_vc)
                rc = kerberos.authGSSClientStep(self.gss_vc, data)
                if rc != kerberos.AUTH_GSS_CONTINUE:
                   self.gss_step = self.GSS_STATE_WRAP
            elif self.gss_step == self.GSS_STATE_WRAP:
                rc = kerberos.authGSSClientUnwrap(self.gss_vc, data)
                response = kerberos.authGSSClientResponse(self.gss_vc)
                rc = kerberos.authGSSClientWrap(self.gss_vc, response,
                                                self.username)
            response = kerberos.authGSSClientResponse(self.gss_vc)
        except kerberos.GSSError, err:
            # Kerberos errored out on us, respond with None to cancel the
            # authentication
            self.ui.debug('imap', '%s: %s' % (err[0][0], err[1][0]))
            return None

        if not response:
            response = ''
        return base64.b64decode(response)

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
            imapobj = None
            for i in range(len(self.availableconnections) - 1, -1, -1):
                tryobj = self.availableconnections[i]
                if self.lastowner[tryobj] == get_ident():
                    imapobj = tryobj
                    del(self.availableconnections[i])
                    break
            if not imapobj:
                imapobj = self.availableconnections[0]
                del(self.availableconnections[0])
            self.assignedconnections.append(imapobj)
            self.lastowner[imapobj] = get_ident()
            self.connectionlock.release()
            return imapobj
        
        self.connectionlock.release()   # Release until need to modify data

        """ Must be careful here that if we fail we should bail out gracefully
        and release locks / threads so that the next attempt can try...
        """
        success = 0
        try:
            while not success:
                # Generate a new connection.
                if self.tunnel:
                    self.ui.connecting('tunnel', self.tunnel)
                    imapobj = imaplibutil.IMAP4_Tunnel(self.tunnel,
                                                       timeout=socket.getdefaulttimeout())
                    success = 1
                elif self.usessl:
                    self.ui.connecting(self.hostname, self.port)
                    imapobj = imaplibutil.WrappedIMAP4_SSL(self.hostname, self.port,
                                                           self.sslclientkey, self.sslclientcert,
                                                           timeout=socket.getdefaulttimeout(),
                                                           cacertfile = self.sslcacertfile)
                else:
                    self.ui.connecting(self.hostname, self.port)
                    imapobj = imaplibutil.WrappedIMAP4(self.hostname, self.port,
                                                       timeout=socket.getdefaulttimeout())

                imapobj.mustquote = imaplibutil.mustquote

                if not self.tunnel:
                    try:
                        # Try GSSAPI and continue if it fails
                        if 'AUTH=GSSAPI' in imapobj.capabilities and have_gss:
                            self.ui.debug('imap',
                                'Attempting GSSAPI authentication')
                            try:
                                imapobj.authenticate('GSSAPI', self.gssauth)
                            except imapobj.error, val:
                                self.gssapi = False
                                self.ui.debug('imap',
                                    'GSSAPI Authentication failed')
                            else:
                                self.gssapi = True
                                #if we do self.password = None then the next attempt cannot try...
                                #self.password = None

                        if not self.gssapi:
                            if 'AUTH=CRAM-MD5' in imapobj.capabilities:
                                self.ui.debug('imap',
                                                       'Attempting CRAM-MD5 authentication')
                                try:
                                    imapobj.authenticate('CRAM-MD5', self.md5handler)
                                except imapobj.error, val:
                                    self.plainauth(imapobj)
                            else:
                                self.plainauth(imapobj)
                        # Would bail by here if there was a failure.
                        success = 1
                        self.goodpassword = self.password
                    except imapobj.error, val:
                        self.passworderror = str(val)
                        raise
                        #self.password = None

            if self.delim == None:
                listres = imapobj.list(self.reference, '""')[1]
                if listres == [None] or listres == None:
                    # Some buggy IMAP servers do not respond well to LIST "" ""
                    # Work around them.
                    listres = imapobj.list(self.reference, '"*"')[1]
                if listres == [None] or listres == None:
                    # No Folders were returned. This occurs, e.g. if the
                    # 'reference' prefix does not exist on the mail
                    # server. Raise exception.
                    err = "Server '%s' returned no folders in '%s'" % \
                        (self.repos.getname(), self.reference)
                    self.ui.warn(err)
                    raise Exception(err)
                self.delim, self.root = \
                            imaputil.imapsplit(listres[0])[1:]
                self.delim = imaputil.dequote(self.delim)
                self.root = imaputil.dequote(self.root)

            self.connectionlock.acquire()
            self.assignedconnections.append(imapobj)
            self.lastowner[imapobj] = get_ident()
            self.connectionlock.release()
            return imapobj
        except Exception, e:
            """If we are here then we did not succeed in getting a
            connection - we should clean up and then re-raise the
            error..."""
            self.semaphore.release()

            #Make sure that this can be retried the next time...
            self.passworderror = None
            if(self.connectionlock.locked()):
                self.connectionlock.release()

            if type(e) == gaierror:
                #DNS related errors. Abort Repo sync
                severity = OfflineImapError.ERROR.REPO
                #TODO: special error msg for e.errno == 2 "Name or service not known"?
                reason = "Could not resolve name '%s' for repository "\
                         "'%s'. Make sure you have configured the ser"\
                         "ver name correctly and that you are online."\
                         % (self.hostname, self.reposname)
                raise OfflineImapError(reason, severity)
            else:
                # re-raise all other errors
                raise
    
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
        threadutil.semaphorereset(self.semaphore, self.maxconnections)
        for imapobj in self.assignedconnections + self.availableconnections:
            imapobj.logout()
        self.assignedconnections = []
        self.availableconnections = []
        self.lastowner = {}
        # reset kerberos state
        self.gss_step = self.GSS_STATE_STEP
        self.gss_vc = None
        self.gssapi = False
        self.connectionlock.release()

    def keepalive(self, timeout, event):
        """Sends a NOOP to each connection recorded.   It will wait a maximum
        of timeout seconds between doing this, and will continue to do so
        until the Event object as passed is true.  This method is expected
        to be invoked in a separate thread, which should be join()'d after
        the event is set."""
        self.ui.debug('imap', 'keepalive thread started')
        while 1:
            self.ui.debug('imap', 'keepalive: top of loop')
            time.sleep(timeout)
            self.ui.debug('imap', 'keepalive: after wait')
            if event.isSet():
                self.ui.debug('imap', 'keepalive: event is set; exiting')
                return
            self.ui.debug('imap', 'keepalive: acquiring connectionlock')
            self.connectionlock.acquire()
            numconnections = len(self.assignedconnections) + \
                             len(self.availableconnections)
            self.connectionlock.release()
            self.ui.debug('imap', 'keepalive: connectionlock released')
            threads = []
            imapobjs = []
        
            for i in range(numconnections):
                self.ui.debug('imap', 'keepalive: processing connection %d of %d' % (i, numconnections))
                imapobj = self.acquireconnection()
                self.ui.debug('imap', 'keepalive: connection %d acquired' % i)
                imapobjs.append(imapobj)
                thr = threadutil.ExitNotifyThread(target = imapobj.noop)
                thr.setDaemon(1)
                thr.start()
                threads.append(thr)
                self.ui.debug('imap', 'keepalive: thread started')

            self.ui.debug('imap', 'keepalive: joining threads')

            for thr in threads:
                # Make sure all the commands have completed.
                thr.join()

            self.ui.debug('imap', 'keepalive: releasing connections')

            for imapobj in imapobjs:
                self.releaseconnection(imapobj)

            self.ui.debug('imap', 'keepalive: bottom of loop')

class ConfigedIMAPServer(IMAPServer):
    """This class is designed for easier initialization given a ConfigParser
    object and an account name.  The passwordhash is used if
    passwords for certain accounts are known.  If the password for this
    account is listed, it will be obtained from there."""
    def __init__(self, repository, passwordhash = {}):
        """Initialize the object.  If the account is not a tunnel,
        the password is required."""
        self.repos = repository
        self.config = self.repos.getconfig()
        usetunnel = self.repos.getpreauthtunnel()
        if not usetunnel:
            host = self.repos.gethost()
            user = self.repos.getuser()
            port = self.repos.getport()
            ssl = self.repos.getssl()
            sslclientcert = self.repos.getsslclientcert()
            sslclientkey = self.repos.getsslclientkey()
            sslcacertfile = self.repos.getsslcacertfile()
        reference = self.repos.getreference()
        idlefolders = self.repos.getidlefolders()
        server = None
        password = None
        
        if repository.getname() in passwordhash:
            password = passwordhash[repository.getname()]

        # Connect to the remote server.
        if usetunnel:
            IMAPServer.__init__(self, self.config, self.repos.getname(),
                                tunnel = usetunnel,
                                reference = reference,
                                idlefolders = idlefolders,
                                maxconnections = self.repos.getmaxconnections())
        else:
            if not password:
                password = self.repos.getpassword()
            IMAPServer.__init__(self, self.config, self.repos.getname(),
                                user, password, host, port, ssl,
                                self.repos.getmaxconnections(),
                                reference = reference,
                                idlefolders = idlefolders,
                                sslclientcert = sslclientcert,
                                sslclientkey = sslclientkey,
                                sslcacertfile = sslcacertfile)
