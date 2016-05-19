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

from threading import Lock, BoundedSemaphore, Thread, Event, currentThread
import hmac
import socket
import base64

import json
import urllib

import socket
import time
import errno
from sys import exc_info
from socket import gaierror
from ssl import SSLError, cert_time_to_seconds

from offlineimap import imaplibutil, imaputil, threadutil, OfflineImapError
import offlineimap.accounts
from offlineimap.ui import getglobalui

import six


try:
    # do we have a recent pykerberos?
    have_gss = False
    import kerberos
    if 'authGSSClientWrap' in dir(kerberos):
        have_gss = True
except ImportError:
    pass

class IMAPServer(object):
    """Initializes all variables from an IMAPRepository() instance

    Various functions, such as acquireconnection() return an IMAP4
    object on which we can operate.

    Public instance variables are: self.:
     delim The server's folder delimiter. Only valid after acquireconnection()
    """

    GSS_STATE_STEP = 0
    GSS_STATE_WRAP = 1

    def __init__(self, repos):
        """:repos: a IMAPRepository instance."""

        self.ui = getglobalui()
        self.repos = repos
        self.config = repos.getconfig()

        self.preauth_tunnel = repos.getpreauthtunnel()
        self.transport_tunnel = repos.gettransporttunnel()
        if self.preauth_tunnel and self.transport_tunnel:
            raise OfflineImapError('%s: '% repos +
                'you must enable precisely one '
                'type of tunnel (preauth or transport), '
                'not both', OfflineImapError.ERROR.REPO)
        self.tunnel = \
            self.preauth_tunnel if self.preauth_tunnel \
            else self.transport_tunnel

        self.username = \
            None if self.preauth_tunnel else repos.getuser()
        self.user_identity = repos.get_remote_identity()
        self.authmechs = repos.get_auth_mechanisms()
        self.password = None
        self.passworderror = None
        self.goodpassword = None

        self.usessl = repos.getssl()
        self.useipv6 = repos.getipv6()
        if self.useipv6 == True:
            self.af = socket.AF_INET6
        elif self.useipv6 == False:
            self.af = socket.AF_INET
        else:
            self.af = socket.AF_UNSPEC
        self.hostname = \
            None if self.preauth_tunnel else repos.gethost()
        self.port = repos.getport()
        if self.port == None:
            self.port = 993 if self.usessl else 143
        self.sslclientcert = repos.getsslclientcert()
        self.sslclientkey = repos.getsslclientkey()
        self.sslcacertfile = repos.getsslcacertfile()
        if self.sslcacertfile is None:
            self.__verifycert = None # disable cert verification
        self.fingerprint = repos.get_ssl_fingerprint()
        self.sslversion = repos.getsslversion()
        self.tlslevel = repos.gettlslevel()

        self.oauth2_refresh_token = repos.getoauth2_refresh_token()
        self.oauth2_access_token = repos.getoauth2_access_token()
        self.oauth2_client_id = repos.getoauth2_client_id()
        self.oauth2_client_secret = repos.getoauth2_client_secret()
        self.oauth2_request_url = repos.getoauth2_request_url()

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

        # In order to support proxy connection, we have to override the
        # default socket instance with our own socksified socket instance.
        # We add this option to bypass the GFW in China.
        _account_section = 'Account ' + self.repos.account.name
        if not self.config.has_option(_account_section, 'proxy'):
            self.proxied_socket = socket.socket
        else:
            proxy = self.config.get(_account_section, 'proxy')
            # Powered by PySocks.
            try:
                import socks
                proxy_type, host, port = proxy.split(":")
                port = int(port)
                socks.setdefaultproxy(getattr(socks, proxy_type), host, port)
                self.proxied_socket = socks.socksocket
            except ImportError:
                self.ui.warn("PySocks not installed, ignoring proxy option.")
                self.proxied_socket = socket.socket
            except (AttributeError, ValueError) as e:
                self.ui.warn("Bad proxy option %s for account %s: %s "
                    "Ignoring proxy option."%
                    (proxy, self.repos.account.name, e))
                self.proxied_socket = socket.socket


    def __getpassword(self):
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

    # XXX: is this function used anywhere?
    def getroot(self):
        """Returns this server's folder root. Can only be called after one
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

    def __md5handler(self, response):
        challenge = response.strip()
        self.ui.debug('imap', '__md5handler: got challenge %s'% challenge)

        passwd = self.__getpassword()
        retval = self.username + ' ' + hmac.new(passwd, challenge).hexdigest()
        self.ui.debug('imap', '__md5handler: returning %s'% retval)
        return retval

    def __loginauth(self, imapobj):
        """ Basic authentication via LOGIN command."""

        self.ui.debug('imap', 'Attempting IMAP LOGIN authentication')
        imapobj.login(self.username, self.__getpassword())


    def __plainhandler(self, response):
        """Implements SASL PLAIN authentication, RFC 4616,
          http://tools.ietf.org/html/rfc4616"""

        authc = self.username
        passwd = self.__getpassword()
        authz = ''
        if self.user_identity != None:
            authz = self.user_identity
        NULL = u'\x00'
        retval = NULL.join((authz, authc, passwd)).encode('utf-8')
        logsafe_retval = NULL.join((authz, authc, "(passwd hidden for log)")).encode('utf-8')
        self.ui.debug('imap', '__plainhandler: returning %s' % logsafe_retval)
        return retval


    def __xoauth2handler(self, response):
        if self.oauth2_refresh_token is None \
                and self.oauth2_access_token is None:
            return None

        if self.oauth2_access_token is None:
            if self.oauth2_request_url is None:
                raise OfflineImapError("No remote oauth2_request_url for "
                    "repository '%s' specified."%
                    self, OfflineImapError.ERROR.REPO)

            # Generate new access token.
            params = {}
            params['client_id'] = self.oauth2_client_id
            params['client_secret'] = self.oauth2_client_secret
            params['refresh_token'] = self.oauth2_refresh_token
            params['grant_type'] = 'refresh_token'

            self.ui.debug('imap', 'xoauth2handler: url "%s"'%
                self.oauth2_request_url)
            self.ui.debug('imap', 'xoauth2handler: params "%s"'% params)

            original_socket = socket.socket
            socket.socket = self.proxied_socket
            try:
                response = urllib.urlopen(
                    self.oauth2_request_url, urllib.urlencode(params)).read()
            finally:
                socket.socket = original_socket

            resp = json.loads(response)
            self.ui.debug('imap', 'xoauth2handler: response "%s"'% resp)
            self.oauth2_access_token = resp['access_token']

        self.ui.debug('imap', 'xoauth2handler: access_token "%s"'%
            self.oauth2_access_token)
        auth_string = 'user=%s\1auth=Bearer %s\1\1'% (
            self.username, self.oauth2_access_token)
        #auth_string = base64.b64encode(auth_string)
        self.ui.debug('imap', 'xoauth2handler: returning "%s"'% auth_string)
        return auth_string

    def __gssauth(self, response):
        data = base64.b64encode(response)
        try:
            if self.gss_step == self.GSS_STATE_STEP:
                if not self.gss_vc:
                    rc, self.gss_vc = kerberos.authGSSClientInit(
                        'imap@' + self.hostname)
                    response = kerberos.authGSSClientResponse(self.gss_vc)
                rc = kerberos.authGSSClientStep(self.gss_vc, data)
                if rc != kerberos.AUTH_GSS_CONTINUE:
                    self.gss_step = self.GSS_STATE_WRAP
            elif self.gss_step == self.GSS_STATE_WRAP:
                rc = kerberos.authGSSClientUnwrap(self.gss_vc, data)
                response = kerberos.authGSSClientResponse(self.gss_vc)
                rc = kerberos.authGSSClientWrap(
                    self.gss_vc, response, self.username)
            response = kerberos.authGSSClientResponse(self.gss_vc)
        except kerberos.GSSError as err:
            # Kerberos errored out on us, respond with None to cancel the
            # authentication
            self.ui.debug('imap', '%s: %s'% (err[0][0], err[1][0]))
            return None

        if not response:
            response = ''
        return base64.b64decode(response)


    def __start_tls(self, imapobj):
        if 'STARTTLS' in imapobj.capabilities and not self.usessl:
            self.ui.debug('imap', 'Using STARTTLS connection')
            try:
                imapobj.starttls()
            except imapobj.error as e:
                raise OfflineImapError("Failed to start "
                    "TLS connection: %s"% str(e),
                    OfflineImapError.ERROR.REPO, None, exc_info()[2])


    ## All __authn_* procedures are helpers that do authentication.
    ## They are class methods that take one parameter, IMAP object.
    ##
    ## Each function should return True if authentication was
    ## successful and False if authentication wasn't even tried
    ## for some reason (but not when IMAP has no such authentication
    ## capability, calling code checks that).
    ##
    ## Functions can also raise exceptions; two types are special
    ## and will be handled by the calling code:
    ##
    ## - imapobj.error means that there was some error that
    ##   comes from imaplib2;
    ##
    ## - OfflineImapError means that function detected some
    ##   problem by itself.

    def __authn_gssapi(self, imapobj):
        if not have_gss:
            return False

        self.connectionlock.acquire()
        try:
            imapobj.authenticate('GSSAPI', self.__gssauth)
            return True
        except imapobj.error as e:
            self.gssapi = False
            raise
        else:
            self.gssapi = True
            kerberos.authGSSClientClean(self.gss_vc)
            self.gss_vc = None
            self.gss_step = self.GSS_STATE_STEP
        finally:
            self.connectionlock.release()

    def __authn_cram_md5(self, imapobj):
        imapobj.authenticate('CRAM-MD5', self.__md5handler)
        return True

    def __authn_plain(self, imapobj):
        imapobj.authenticate('PLAIN', self.__plainhandler)
        return True

    def __authn_xoauth2(self, imapobj):
        imapobj.authenticate('XOAUTH2', self.__xoauth2handler)
        return True

    def __authn_login(self, imapobj):
        # Use LOGIN command, unless LOGINDISABLED is advertized
        # (per RFC 2595)
        if 'LOGINDISABLED' in imapobj.capabilities:
            raise OfflineImapError("IMAP LOGIN is "
                "disabled by server.  Need to use SSL?",
                OfflineImapError.ERROR.REPO)
        else:
            self.__loginauth(imapobj)
            return True


    def __authn_helper(self, imapobj):
        """Authentication machinery for self.acquireconnection().

        Raises OfflineImapError() of type ERROR.REPO when
        there are either fatal problems or no authentications
        succeeded.

        If any authentication method succeeds, routine should exit:
        warnings for failed methods are to be produced in the
        respective except blocks."""

        # Authentication routines, hash keyed by method name
        # with value that is a tuple with
        # - authentication function,
        # - tryTLS flag,
        # - check IMAP capability flag.
        auth_methods = {
          "GSSAPI": (self.__authn_gssapi, False, True),
          "CRAM-MD5": (self.__authn_cram_md5, True, True),
          "XOAUTH2": (self.__authn_xoauth2, True, True),
          "PLAIN": (self.__authn_plain, True, True),
          "LOGIN": (self.__authn_login, True, False),
        }
        # Stack stores pairs of (method name, exception)
        exc_stack = []
        tried_to_authn = False
        tried_tls = False
        mechs = self.authmechs

        # GSSAPI must be tried first: we will probably go TLS after it
        # and GSSAPI mustn't be tunneled over TLS.
        if "GSSAPI" in mechs:
            mechs.remove("GSSAPI")
            mechs.insert(0, "GSSAPI")

        for m in mechs:
            if m not in auth_methods:
                raise Exception("Bad authentication method %s, "
                  "please, file OfflineIMAP bug" % m)

            func, tryTLS, check_cap = auth_methods[m]

            # TLS must be initiated before checking capabilities:
            # they could have been changed after STARTTLS.
            if tryTLS and not tried_tls:
                tried_tls = True
                self.__start_tls(imapobj)

            if check_cap:
                cap = "AUTH=" + m
                if cap not in imapobj.capabilities:
                    continue

            tried_to_authn = True
            self.ui.debug('imap', u'Attempting '
              '%s authentication'% m)
            try:
                if func(imapobj):
                    return
            except (imapobj.error, OfflineImapError) as e:
                self.ui.warn('%s authentication failed: %s'% (m, e))
                exc_stack.append((m, e))

        if len(exc_stack):
            msg = "\n\t".join(map(
              lambda x: ": ".join((x[0], str(x[1]))),
              exc_stack
            ))
            raise OfflineImapError("All authentication types "
              "failed:\n\t%s"% msg, OfflineImapError.ERROR.REPO)

        if not tried_to_authn:
            methods = ", ".join(map(
              lambda x: x[5:], [x for x in imapobj.capabilities if x[0:5] == "AUTH="]
            ))
            raise OfflineImapError(u"Repository %s: no supported "
              "authentication mechanisms found; configured %s, "
              "server advertises %s"% (self.repos,
              ", ".join(self.authmechs), methods),
              OfflineImapError.ERROR.REPO)


    # XXX: move above, closer to releaseconnection()
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

        # Must be careful here that if we fail we should bail out gracefully
        # and release locks / threads so that the next attempt can try...
        success = False
        try:
            while success is not True:
                # Generate a new connection.
                if self.tunnel:
                    self.ui.connecting('tunnel', self.tunnel)
                    imapobj = imaplibutil.IMAP4_Tunnel(
                        self.tunnel,
                        timeout=socket.getdefaulttimeout(),
                        use_socket=self.proxied_socket,
                        )
                    success = True
                elif self.usessl:
                    self.ui.connecting(self.hostname, self.port)
                    imapobj = imaplibutil.WrappedIMAP4_SSL(
                        self.hostname,
                        self.port,
                        self.sslclientkey,
                        self.sslclientcert,
                        self.sslcacertfile,
                        self.__verifycert,
                        self.sslversion,
                        timeout=socket.getdefaulttimeout(),
                        fingerprint=self.fingerprint,
                        use_socket=self.proxied_socket,
                        tls_level=self.tlslevel,
                        af=self.af,
                        )
                else:
                    self.ui.connecting(self.hostname, self.port)
                    imapobj = imaplibutil.WrappedIMAP4(
                        self.hostname, self.port,
                        timeout=socket.getdefaulttimeout(),
                        use_socket=self.proxied_socket,
                        af=self.af,
                        )

                if not self.preauth_tunnel:
                    try:
                        self.__authn_helper(imapobj)
                        self.goodpassword = self.password
                        success = True
                    except OfflineImapError as e:
                        self.passworderror = str(e)
                        raise

            # Enable compression
            if self.repos.getconfboolean('usecompression', 0):
                imapobj.enable_compression()

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
                    err = "Server '%s' returned no folders in '%s'"% \
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
                six.reraise(OfflineImapError(reason, severity), None, exc_info()[2])

            elif isinstance(e, SSLError) and e.errno == errno.EPERM:
                # SSL unknown protocol error
                # happens e.g. when connecting via SSL to a non-SSL service
                if self.port != 993:
                    reason = "Could not connect via SSL to host '%s' and non-s"\
                        "tandard ssl port %d configured. Make sure you connect"\
                        " to the correct port."% (self.hostname, self.port)
                else:
                    reason = "Unknown SSL protocol connecting to host '%s' for "\
                         "repository '%s'. OpenSSL responded:\n%s"\
                         % (self.hostname, self.repos, e)
                six.reraise(OfflineImapError(reason, severity), None, exc_info()[2])

            elif isinstance(e, socket.error) and e.args[0] == errno.ECONNREFUSED:
                # "Connection refused", can be a non-existing port, or an unauthorized
                # webproxy (open WLAN?)
                reason = "Connection to host '%s:%d' for repository '%s' was "\
                    "refused. Make sure you have the right host and port "\
                    "configured and that you are actually able to access the "\
                    "network."% (self.hostname, self.port, self.repos)
                six.reraise(OfflineImapError(reason, severity), None, exc_info()[2])
            # Could not acquire connection to the remote;
            # socket.error(last_error) raised
            if str(e)[:24] == "can't open socket; error":
                six.reraise(OfflineImapError("Could not connect to remote server '%s' "\
                    "for repository '%s'. Remote does not answer."
                    % (self.hostname, self.repos),
                    OfflineImapError.ERROR.REPO), None, exc_info()[2])
            else:
                # re-raise all other errors
                raise

    def connectionwait(self):
        """Waits until there is a connection available.

        Note that between the time that a connection becomes available and the
        time it is requested, another thread may have grabbed it.  This function
        is mainly present as a way to avoid spawning thousands of threads to
        copy messages, then have them all wait for 3 available connections.
        It's OK if we have maxconnections + 1 or 2 threads, which is what this
        will help us do."""

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
        """Sends a NOOP to each connection recorded.

        It will wait a maximum of timeout seconds between doing this, and will
        continue to do so until the Event object as passed is true.  This method
        is expected to be invoked in a separate thread, which should be join()'d
        after the event is set."""

        self.ui.debug('imap', 'keepalive thread started')
        while not event.isSet():
            self.connectionlock.acquire()
            numconnections = len(self.assignedconnections) + \
                             len(self.availableconnections)
            self.connectionlock.release()

            threads = []
            for i in range(numconnections):
                self.ui.debug('imap', 'keepalive: processing connection %d of %d'% (i, numconnections))
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

    def __verifycert(self, cert, hostname):
        """Verify that cert (in socket.getpeercert() format) matches hostname.

        CRLs are not handled.
        Returns error message if any problems are found and None on success."""

        errstr = "CA Cert verifying failed: "
        if not cert:
            return ('%s no certificate received'% errstr)
        dnsname = hostname.lower()
        certnames = []

        # cert expired?
        notafter = cert.get('notAfter')
        if notafter:
            if time.time() >= cert_time_to_seconds(notafter):
                return '%s certificate expired %s'% (errstr, notafter)

        # First read commonName
        for s in cert.get('subject', []):
            key, value = s[0]
            if key == 'commonName':
                certnames.append(value.lower())
        if len(certnames) == 0:
            return ('%s no commonName found in certificate'% errstr)

        # Then read subjectAltName
        for key, value in cert.get('subjectAltName', []):
            if key == 'DNS':
                certnames.append(value.lower())

        # And finally try to match hostname with one of these names
        for certname in certnames:
            if (certname == dnsname or
                '.' in dnsname and certname == '*.' + dnsname.split('.', 1)[1]):
                return None

        return ('%s no matching domain name found in certificate'% errstr)


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
            self.thread = Thread(target=self.__idle)
        self.thread.setDaemon(1)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_sig.set()

    def join(self):
        self.thread.join()

    def noop(self):
        # TODO: AFAIK this is not optimal, we will send a NOOP on one
        # random connection (ie not enough to keep all connections
        # open). In case we do the noop multiple times, we can well use
        # the same connection every time, as we get a random one. This
        # function should IMHO send a noop on ALL available connections
        # to the server.
        imapobj = self.parent.acquireconnection()
        try:
            imapobj.noop()
        except imapobj.abort:
            self.ui.warn('Attempting NOOP on dropped connection %s'%
                imapobj.identifier)
            self.parent.releaseconnection(imapobj, True)
            imapobj = None
        finally:
            if imapobj:
                self.parent.releaseconnection(imapobj)
                self.stop_sig.wait() # wait until we are supposed to quit

    def __dosync(self):
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

    def __idle(self):
        """Invoke IDLE mode until timeout or self.stop() is invoked."""

        def callback(args):
            """IDLE callback function invoked by imaplib2.

            This is invoked when a) The IMAP server tells us something
            while in IDLE mode, b) we get an Exception (e.g. on dropped
            connections, or c) the standard imaplib IDLE timeout of 29
            minutes kicks in."""
            result, cb_arg, exc_data = args
            if exc_data is None and not self.stop_sig.isSet():
                # No Exception, and we are not supposed to stop:
                self.needsync = True
            self.stop_sig.set() # Continue to sync.

        while not self.stop_sig.isSet():
            self.needsync = False

            success = False # Successfully selected FOLDER?
            while not success:
                imapobj = self.parent.acquireconnection()
                try:
                    imapobj.select(self.folder)
                except OfflineImapError as e:
                    if e.severity == OfflineImapError.ERROR.FOLDER_RETRY:
                        # Connection closed, release connection and retry.
                        self.ui.error(e, exc_info()[2])
                        self.parent.releaseconnection(imapobj, True)
                    elif e.severity == OfflineImapError.ERROR.FOLDER:
                        # Just continue the process on such error for now.
                        self.ui.error(e, exc_info()[2])
                    else:
                        # Stops future attempts to sync this account.
                        raise
                else:
                    success = True
            if "IDLE" in imapobj.capabilities:
                imapobj.idle(callback=callback)
            else:
                self.ui.warn("IMAP IDLE not supported on server '%s'."
                    "Sleep until next refresh cycle."% imapobj.identifier)
                imapobj.noop()
            self.stop_sig.wait() # self.stop() or IDLE callback are invoked.
            try:
                # End IDLE mode with noop, imapobj can point to a dropped conn.
                imapobj.noop()
            except imapobj.abort:
                self.ui.warn('Attempting NOOP on dropped connection %s'%
                    imapobj.identifier)
                self.parent.releaseconnection(imapobj, True)
            else:
                self.parent.releaseconnection(imapobj)

            if self.needsync:
                # Here not via self.stop, but because IDLE responded. Do
                # another round and invoke actual syncing.
                self.stop_sig.clear()
                self.__dosync()
