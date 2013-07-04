# IMAP server support
# Copyright (C) 2002 - 2011 John Goerzen & contributors
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
from threading import Lock, BoundedSemaphore, Thread, Event, currentThread
import offlineimap.accounts
import hmac
import socket
import base64
import time
import errno
from sys import exc_info
from socket import gaierror
from ssl import SSLError, cert_time_to_seconds

try:
    # do we have a recent pykerberos?
    have_gss = False
    import kerberos
    if 'authGSSClientWrap' in dir(kerberos):
        have_gss = True
except ImportError:
    pass

class IMAPServer:
    """Initializes all variables from an IMAPRepository() instance

    Various functions, such as acquireconnection() return an IMAP4
    object on which we can operate.

    Public instance variables are: self.:
     delim The server's folder delimiter. Only valid after acquireconnection()
     """
    GSS_STATE_STEP = 0
    GSS_STATE_WRAP = 1
    def __init__(self, repos):
        self.ui = getglobalui()
        self.repos = repos
        self.config = repos.getconfig()
        self.tunnel = repos.getpreauthtunnel()
        self.usessl = repos.getssl()
        self.username = None if self.tunnel else repos.getuser()
        self.password = None
        self.passworderror = None
        self.goodpassword = None
        self.hostname = None if self.tunnel else repos.gethost()
        self.port = repos.getport()
        if self.port == None:
            self.port = 993 if self.usessl else 143
        self.sslclientcert = repos.getsslclientcert()
        self.sslclientkey = repos.getsslclientkey()
        self.sslcacertfile = repos.getsslcacertfile()
        self.sslversion = repos.getsslversion()
        if self.sslcacertfile is None:
            self.verifycert = None # disable cert verification
        self.delim = None
        self.root = None
        self.maxconnections = repos.getmaxconnections()
        self.availableconnections = []
        self.assignedconnections = []
        self.lastowner = {}
        self.semaphore = BoundedSemaphore(self.maxconnections)
        self.connectionlock = Lock()
        self.reference = repos.getreference()
        self.idlefolders = repos.getidlefolders()
        self.gss_step = self.GSS_STATE_STEP
        self.gss_vc = None
        self.gssapi = False

    def getpassword(self):
        """Returns the server password or None"""
        if self.goodpassword != None: # use cached good one first
            return self.goodpassword

        if self.password != None and self.passworderror == None:
            return self.password # non-failed preconfigured one

        # get 1) configured password first 2) fall back to asking via UI
        self.password = self.repos.getpassword() or \
                        self.ui.getpass(self.repos.getname(), self.config,
                                        self.passworderror)
        self.passworderror = None
        return self.password

    def getroot(self):
        """Returns this server's folder root.  Can only be called after one
        or more calls to acquireconnection."""
        return self.root


    def releaseconnection(self, connection, drop_conn=False):
        """Releases a connection, returning it to the pool.

        :param drop_conn: If True, the connection will be released and
           not be reused. This can be used to indicate broken connections."""
        if connection is None: return #noop on bad connection
        self.connectionlock.acquire()
        self.assignedconnections.remove(connection)
        # Don't reuse broken connections
        if connection.Terminate or drop_conn:
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
        except kerberos.GSSError as err:
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
        curThread = currentThread()
        imapobj = None

        if len(self.availableconnections): # One is available.
            # Try to find one that previously belonged to this thread
            # as an optimization.  Start from the back since that's where
            # they're popped on.
            imapobj = None
            for i in range(len(self.availableconnections) - 1, -1, -1):
                tryobj = self.availableconnections[i]
                if self.lastowner[tryobj] == curThread.ident:
                    imapobj = tryobj
                    del(self.availableconnections[i])
                    break
            if not imapobj:
                imapobj = self.availableconnections[0]
                del(self.availableconnections[0])
            self.assignedconnections.append(imapobj)
            self.lastowner[imapobj] = curThread.ident
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
                    fingerprint = self.repos.get_ssl_fingerprint()
                    imapobj = imaplibutil.WrappedIMAP4_SSL(self.hostname,
                                                           self.port,
                                                           self.sslclientkey,
                                                           self.sslclientcert,
                                                           self.sslcacertfile,
                                                           self.verifycert,
                                                           self.sslversion,
                                                           timeout=socket.getdefaulttimeout(),
                                                           fingerprint=fingerprint
                                                           )
                else:
                    self.ui.connecting(self.hostname, self.port)
                    imapobj = imaplibutil.WrappedIMAP4(self.hostname, self.port,
                                                       timeout=socket.getdefaulttimeout())

                if not self.tunnel:
                    try:
                        # Try GSSAPI and continue if it fails
                        if 'AUTH=GSSAPI' in imapobj.capabilities and have_gss:
                            self.connectionlock.acquire()
                            self.ui.debug('imap',
                                'Attempting GSSAPI authentication')
                            try:
                                imapobj.authenticate('GSSAPI', self.gssauth)
                            except imapobj.error as val:
                                self.gssapi = False
                                self.ui.debug('imap',
                                    'GSSAPI Authentication failed')
                            else:
                                self.gssapi = True
                                kerberos.authGSSClientClean(self.gss_vc)
                                self.gss_vc = None
                                self.gss_step = self.GSS_STATE_STEP
                                #if we do self.password = None then the next attempt cannot try...
                                #self.password = None
                            self.connectionlock.release()

                        if not self.gssapi:
                            if 'STARTTLS' in imapobj.capabilities and not\
                                    self.usessl:
                                self.ui.debug('imap',
                                              'Using STARTTLS connection')
                                imapobj.starttls()

                            if 'AUTH=CRAM-MD5' in imapobj.capabilities:
                                self.ui.debug('imap',
                                           'Attempting CRAM-MD5 authentication')
                                try:
                                    imapobj.authenticate('CRAM-MD5',
                                                         self.md5handler)
                                except imapobj.error as val:
                                    self.plainauth(imapobj)
                            else:
                                # Use plaintext login, unless
                                # LOGINDISABLED (RFC2595)
                                if 'LOGINDISABLED' in imapobj.capabilities:
                                    raise OfflineImapError("Plaintext login "
                                       "disabled by server. Need to use SSL?",
                                        OfflineImapError.ERROR.REPO)
                                self.plainauth(imapobj)
                        # Would bail by here if there was a failure.
                        success = 1
                        self.goodpassword = self.password
                    except imapobj.error as val:
                        self.passworderror = str(val)
                        raise

            # update capabilities after login, e.g. gmail serves different ones
            typ, dat = imapobj.capability()
            if dat != [None]:
                imapobj.capabilities = tuple(dat[-1].upper().split())

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

            with self.connectionlock:
                self.assignedconnections.append(imapobj)
                self.lastowner[imapobj] = curThread.ident
            return imapobj
        except Exception as e:
            """If we are here then we did not succeed in getting a
            connection - we should clean up and then re-raise the
            error..."""
            self.semaphore.release()

            severity = OfflineImapError.ERROR.REPO
            if type(e) == gaierror:
                #DNS related errors. Abort Repo sync
                #TODO: special error msg for e.errno == 2 "Name or service not known"?
                reason = "Could not resolve name '%s' for repository "\
                         "'%s'. Make sure you have configured the ser"\
                         "ver name correctly and that you are online."%\
                         (self.hostname, self.repos)
                raise OfflineImapError(reason, severity)

            elif isinstance(e, SSLError) and e.errno == 1:
                # SSL unknown protocol error
                # happens e.g. when connecting via SSL to a non-SSL service
                if self.port != 993:
                    reason = "Could not connect via SSL to host '%s' and non-s"\
                        "tandard ssl port %d configured. Make sure you connect"\
                        " to the correct port." % (self.hostname, self.port)
                else:
                    reason = "Unknown SSL protocol connecting to host '%s' for"\
                         "repository '%s'. OpenSSL responded:\n%s"\
                         % (self.hostname, self.repos, e)
                raise OfflineImapError(reason, severity)

            elif isinstance(e, socket.error) and e.args[0] == errno.ECONNREFUSED:
                # "Connection refused", can be a non-existing port, or an unauthorized
                # webproxy (open WLAN?)
                reason = "Connection to host '%s:%d' for repository '%s' was "\
                    "refused. Make sure you have the right host and port "\
                    "configured and that you are actually able to access the "\
                    "network." % (self.hostname, self.port, self.reposname)
                raise OfflineImapError(reason, severity)
            # Could not acquire connection to the remote;
            # socket.error(last_error) raised
            if str(e)[:24] == "can't open socket; error":
                raise OfflineImapError("Could not connect to remote server '%s' "\
                    "for repository '%s'. Remote does not answer."
                    % (self.hostname, self.repos),
                    OfflineImapError.ERROR.REPO)
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
        with self.connectionlock:
            # first, wait till all connections had been released.
            # TODO: won't work IMHO, as releaseconnection() also
            # requires the connectionlock, leading to a potential
            # deadlock! Audit & check!
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

    def keepalive(self, timeout, event):
        """Sends a NOOP to each connection recorded.   It will wait a maximum
        of timeout seconds between doing this, and will continue to do so
        until the Event object as passed is true.  This method is expected
        to be invoked in a separate thread, which should be join()'d after
        the event is set."""
        self.ui.debug('imap', 'keepalive thread started')
        while not event.isSet():
            self.connectionlock.acquire()
            numconnections = len(self.assignedconnections) + \
                             len(self.availableconnections)
            self.connectionlock.release()

            threads = []
            for i in range(numconnections):
                self.ui.debug('imap', 'keepalive: processing connection %d of %d' % (i, numconnections))
                if len(self.idlefolders) > i:
                    # IDLE thread
                    idler = IdleThread(self, self.idlefolders[i])
                else:
                    # NOOP thread
                    idler = IdleThread(self)
                idler.start()
                threads.append(idler)

            self.ui.debug('imap', 'keepalive: waiting for timeout')
            event.wait(timeout)
            self.ui.debug('imap', 'keepalive: after wait')

            for idler in threads:
                # Make sure all the commands have completed.
                idler.stop()
                idler.join()
            self.ui.debug('imap', 'keepalive: all threads joined')
        self.ui.debug('imap', 'keepalive: event is set; exiting')
        return

    def verifycert(self, cert, hostname):
        '''Verify that cert (in socket.getpeercert() format) matches hostname.
        CRLs are not handled.

        Returns error message if any problems are found and None on success.
        '''
        errstr = "CA Cert verifying failed: "
        if not cert:
            return ('%s no certificate received' % errstr)
        dnsname = hostname.lower()
        certnames = []

        # cert expired?
        notafter = cert.get('notAfter')
        if notafter:
            if time.time() >= cert_time_to_seconds(notafter):
                return '%s certificate expired %s' % (errstr, notafter)

        # First read commonName
        for s in cert.get('subject', []):
            key, value = s[0]
            if key == 'commonName':
                certnames.append(value.lower())
        if len(certnames) == 0:
            return ('%s no commonName found in certificate' % errstr)

        # Then read subjectAltName
        for key, value in cert.get('subjectAltName', []):
            if key == 'DNS':
                certnames.append(value.lower())

        # And finally try to match hostname with one of these names
        for certname in certnames:
            if (certname == dnsname or
                '.' in dnsname and certname == '*.' + dnsname.split('.', 1)[1]):
                return None

        return ('%s no matching domain name found in certificate' % errstr)


class IdleThread(object):
    def __init__(self, parent, folder=None):
        """If invoked without 'folder', perform a NOOP and wait for
        self.stop() to be called. If invoked with folder, switch to IDLE
        mode and synchronize once we have a new message"""
        self.parent = parent
        self.folder = folder
        self.stop_sig = Event()
        self.ui = getglobalui()
        if folder is None:
            self.thread = Thread(target=self.noop)
        else:
            self.thread = Thread(target=self.idle)
        self.thread.setDaemon(1)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_sig.set()

    def join(self):
        self.thread.join()

    def noop(self):
        #TODO: AFAIK this is not optimal, we will send a NOOP on one
        #random connection (ie not enough to keep all connections
        #open). In case we do the noop multiple times, we can well use
        #the same connection every time, as we get a random one. This
        #function should IMHO send a noop on ALL available connections
        #to the server.
        imapobj = self.parent.acquireconnection()
        try:
            imapobj.noop()
        except imapobj.abort:
            self.ui.warn('Attempting NOOP on dropped connection %s' % \
                             imapobj.identifier)
            self.parent.releaseconnection(imapobj, True)
            imapobj = None
        finally:
            if imapobj:
                self.parent.releaseconnection(imapobj)
                self.stop_sig.wait() # wait until we are supposed to quit

    def dosync(self):
        remoterepos = self.parent.repos
        account = remoterepos.account
        localrepos = account.localrepos
        remoterepos = account.remoterepos
        statusrepos = account.statusrepos
        remotefolder = remoterepos.getfolder(self.folder)

        hook = account.getconf('presynchook', '')
        account.callhook(hook)
        offlineimap.accounts.syncfolder(account, remotefolder, quick=False)
        hook = account.getconf('postsynchook', '')
        account.callhook(hook)

        ui = getglobalui()
        ui.unregisterthread(currentThread()) #syncfolder registered the thread

    def idle(self):
        """Invoke IDLE mode until timeout or self.stop() is invoked"""
        def callback(args):
            """IDLE callback function invoked by imaplib2

            This is invoked when a) The IMAP server tells us something
            while in IDLE mode, b) we get an Exception (e.g. on dropped
            connections, or c) the standard imaplib IDLE timeout of 29
            minutes kicks in."""
            result, cb_arg, exc_data = args
            if exc_data is None and not self.stop_sig.isSet():
                # No Exception, and we are not supposed to stop:
                self.needsync = True
            self.stop_sig.set() # continue to sync

        while not self.stop_sig.isSet():
            self.needsync = False

            success = False # successfully selected FOLDER?
            while not success:
                imapobj = self.parent.acquireconnection()
                try:
                    imapobj.select(self.folder)
                except OfflineImapError as e:
                    if e.severity == OfflineImapError.ERROR.FOLDER_RETRY:
                        # Connection closed, release connection and retry
                        self.ui.error(e, exc_info()[2])
                        self.parent.releaseconnection(imapobj, True)
                    else:
                        raise e
                else:
                    success = True
            if "IDLE" in imapobj.capabilities:
                imapobj.idle(callback=callback)
            else:
                self.ui.warn("IMAP IDLE not supported on server '%s'."
                    "Sleep until next refresh cycle." % imapobj.identifier)
                imapobj.noop()
            self.stop_sig.wait() # self.stop() or IDLE callback are invoked
            try:
                # End IDLE mode with noop, imapobj can point to a dropped conn.
                imapobj.noop()
            except imapobj.abort:
                self.ui.warn('Attempting NOOP on dropped connection %s' % \
                                 imapobj.identifier)
                self.parent.releaseconnection(imapobj, True)
            else:
                self.parent.releaseconnection(imapobj)

            if self.needsync:
                # here not via self.stop, but because IDLE responded. Do
                # another round and invoke actual syncing.
                self.stop_sig.clear()
                self.dosync()
