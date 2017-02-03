""" IMAP repository support """

# Copyright (C) 2002-2016 John Goerzen & contributors
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

import os
import netrc
import errno
import codecs
from sys import exc_info
from threading import Event

import six

from offlineimap import folder, imaputil, imapserver, OfflineImapError
from offlineimap.repository.Base import BaseRepository
from offlineimap.threadutil import ExitNotifyThread
from offlineimap.utils.distro import get_os_sslcertfile, get_os_sslcertfile_searchpath


class IMAPRepository(BaseRepository):
    def __init__(self, reposname, account):
        self.idlefolders = None
        BaseRepository.__init__(self, reposname, account)
        # self.ui is being set by the BaseRepository
        self._host = None
        # Must be set before calling imapserver.IMAPServer(self)
        self.oauth2_request_url = None
        self.imapserver = imapserver.IMAPServer(self)
        self.folders = None
        self.copy_ignore_eval = None
        # Keep alive.
        self.kaevent = None
        self.kathread = None

        # Only set the newmail_hook in an IMAP repository.
        if self.config.has_option(self.getsection(), 'newmail_hook'):
            self.newmail_hook = self.localeval.eval(
                self.getconf('newmail_hook'))

        if self.getconf('sep', None):
            self.ui.info("The 'sep' setting is being ignored for IMAP "
                         "repository '%s' (it's autodetected)"% self)

    def startkeepalive(self):
        keepalivetime = self.getkeepalive()
        if not keepalivetime:
            return
        self.kaevent = Event()
        self.kathread = ExitNotifyThread(target=self.imapserver.keepalive,
                                         name="Keep alive " + self.getname(),
                                         args=(keepalivetime, self.kaevent))
        self.kathread.setDaemon(1)
        self.kathread.start()

    def stopkeepalive(self):
        if self.kaevent is None:
            return # Keepalive is not active.

        self.kaevent.set()
        self.kathread = None
        self.kaevent = None

    def holdordropconnections(self):
        if not self.getholdconnectionopen():
            self.dropconnections()

    def dropconnections(self):
        self.imapserver.close()

    def get_copy_ignore_UIDs(self, foldername):
        """Return a list of UIDs to not copy for this foldername."""

        if self.copy_ignore_eval is None:
            if self.config.has_option(self.getsection(),
                                     'copy_ignore_eval'):
                self.copy_ignore_eval = self.localeval.eval(
                    self.getconf('copy_ignore_eval'))
            else:
                self.copy_ignore_eval = lambda x: None

        return self.copy_ignore_eval(foldername)

    def getholdconnectionopen(self):
        if self.getidlefolders():
            return True
        return self.getconfboolean("holdconnectionopen", False)

    def getkeepalive(self):
        num = self.getconfint("keepalive", 0)
        if num == 0 and self.getidlefolders():
            return 29*60
        return num

    def getsep(self):
        """Return the folder separator for the IMAP repository

        This requires that self.imapserver has been initialized with an
        acquireconnection() or it will still be `None`"""
        assert self.imapserver.delim != None, "'%s' " \
            "repository called getsep() before the folder separator was " \
            "queried from the server"% self
        return self.imapserver.delim

    def gethost(self):
        """Return the configured hostname to connect to

        :returns: hostname as string or throws Exception"""
        if self._host:  # Use cached value if possible.
            return self._host

        # 1) Check for remotehosteval setting.
        if self.config.has_option(self.getsection(), 'remotehosteval'):
            host = self.getconf('remotehosteval')
            try:
                host = self.localeval.eval(host)
            except Exception as e:
                six.reraise(OfflineImapError,
                            OfflineImapError(
                                "remotehosteval option for repository "
                                "'%s' failed:\n%s"% (self, e),
                                OfflineImapError.ERROR.REPO),
                            exc_info()[2])
            if host:
                self._host = host
                return self._host
        # 2) Check for plain remotehost setting.
        host = self.getconf('remotehost', None)
        if host != None:
            self._host = host
            return self._host

        # No success.
        raise OfflineImapError("No remote host for repository "
            "'%s' specified."% self, OfflineImapError.ERROR.REPO)

    def get_remote_identity(self):
        """Remote identity is used for certain SASL mechanisms
        (currently -- PLAIN) to inform server about the ID
        we want to authorize as instead of our login name."""

        identity = self.getconf('remote_identity', default=None)
        if identity != None:
            identity = identity.encode('UTF-8')
        return identity

    def get_auth_mechanisms(self):
        supported = ["GSSAPI", "XOAUTH2", "CRAM-MD5", "PLAIN", "LOGIN"]
        # Mechanisms are ranged from the strongest to the
        # weakest ones.
        # TODO: we need DIGEST-MD5, it must come before CRAM-MD5
        # due to the chosen-plaintext resistance.
        default = ["GSSAPI", "XOAUTH2", "CRAM-MD5", "PLAIN", "LOGIN"]

        mechs = self.getconflist('auth_mechanisms', r',\s*',
          default)

        for m in mechs:
            if m not in supported:
                raise OfflineImapError("Repository %s: "% self + \
                  "unknown authentication mechanism '%s'"% m,
                  OfflineImapError.ERROR.REPO)

        self.ui.debug('imap', "Using authentication mechanisms %s" % mechs)
        return mechs

    def getuser(self):
        user = None
        localeval = self.localeval

        if self.config.has_option(self.getsection(), 'remoteusereval'):
            user = self.getconf('remoteusereval')
            if user != None:
                return localeval.eval(user).encode('UTF-8')

        if self.config.has_option(self.getsection(), 'remoteuser'):
            # Assume the configuration file to be UTF-8 encoded so we must not
            # encode this string again.
            user = self.getconf('remoteuser')
            if user != None:
                return user

        try:
            netrcentry = netrc.netrc().authenticators(self.gethost())
        except IOError as inst:
            if inst.errno != errno.ENOENT:
                raise
        else:
            if netrcentry:
                return netrcentry[0]

        try:
            netrcentry = netrc.netrc('/etc/netrc').authenticators(self.gethost())
        except IOError as inst:
            if inst.errno not in (errno.ENOENT, errno.EACCES):
                raise
        else:
            if netrcentry:
                return netrcentry[0]

    def getport(self):
        port = None

        if self.config.has_option(self.getsection(), 'remoteporteval'):
            port = self.getconf('remoteporteval')
        if port != None:
            return self.localeval.eval(port)

        return self.getconfint('remoteport', None)

    def getipv6(self):
        return self.getconfboolean('ipv6', None)

    def getssl(self):
        return self.getconfboolean('ssl', True)

    def getsslclientcert(self):
        xforms = [os.path.expanduser, os.path.expandvars, os.path.abspath]
        return self.getconf_xform('sslclientcert', xforms, None)

    def getsslclientkey(self):
        xforms = [os.path.expanduser, os.path.expandvars, os.path.abspath]
        return self.getconf_xform('sslclientkey', xforms, None)

    def getsslcacertfile(self):
        """Determines CA bundle.

        Returns path to the CA bundle.  It is either explicitely specified
        or requested via "OS-DEFAULT" value (and we will search known
        locations for the current OS and distribution).

        If search via "OS-DEFAULT" route yields nothing, we will throw an
        exception to make our callers distinguish between not specified
        value and non-existent default CA bundle.

        It is also an error to specify non-existent file via configuration:
        it will error out later, but, perhaps, with less verbose explanation,
        so we will also throw an exception.  It is consistent with
        the above behaviour, so any explicitely-requested configuration
        that doesn't result in an existing file will give an exception.
        """

        xforms = [os.path.expanduser, os.path.expandvars, os.path.abspath]
        cacertfile = self.getconf_xform('sslcacertfile', xforms, None)
        # Can't use above cacertfile because of abspath.
        if self.getconf('sslcacertfile', None) == "OS-DEFAULT":
            cacertfile = get_os_sslcertfile()
            if cacertfile == None:
                searchpath = get_os_sslcertfile_searchpath()
                if searchpath:
                    reason = "Default CA bundle was requested, "\
                             "but no existing locations available.  "\
                             "Tried %s." % (", ".join(searchpath))
                else:
                    reason = "Default CA bundle was requested, "\
                             "but OfflineIMAP doesn't know any for your "\
                             "current operating system."
                raise OfflineImapError(reason, OfflineImapError.ERROR.REPO)
        if cacertfile is None:
            return None
        if not os.path.isfile(cacertfile):
            reason = "CA certfile for repository '%s' couldn't be found.  "\
                     "No such file: '%s'" % (self.name, cacertfile)
            raise OfflineImapError(reason, OfflineImapError.ERROR.REPO)
        return cacertfile

    def gettlslevel(self):
        return self.getconf('tls_level', 'tls_compat')

    def getsslversion(self):
        return self.getconf('ssl_version', None)

    def getstarttls(self):
        return self.getconfboolean('starttls', True)

    def get_ssl_fingerprint(self):
        """Return array of possible certificate fingerprints.

        Configuration item cert_fingerprint can contain multiple
        comma-separated fingerprints in hex form."""

        value = self.getconf('cert_fingerprint', "")
        return [f.strip().lower() for f in value.split(',') if f]

    def setoauth2_request_url(self, url):
        self.oauth2_request_url = url

    def getoauth2_request_url(self):
        if self.oauth2_request_url is not None: # Use cached value if possible.
            return self.oauth2_request_url

        self.setoauth2_request_url(self.getconf('oauth2_request_url', None))
        return self.oauth2_request_url

    def getoauth2_refresh_token(self):
        refresh_token = self.getconf('oauth2_refresh_token', None)
        if refresh_token is None:
            refresh_token = self.localeval.eval(
                self.getconf('oauth2_refresh_token_eval', "None")
            )
            if refresh_token is not None:
                refresh_token = refresh_token.strip("\n")
        return refresh_token

    def getoauth2_access_token(self):
        access_token = self.getconf('oauth2_access_token', None)
        if access_token is None:
            access_token = self.localeval.eval(
                self.getconf('oauth2_access_token_eval', "None")
            )
            if access_token is not None:
                access_token = access_token.strip("\n")
        return access_token

    def getoauth2_client_id(self):
        client_id = self.getconf('oauth2_client_id', None)
        if client_id is None:
            client_id = self.localeval.eval(
                self.getconf('oauth2_client_id_eval', "None")
            )
            if client_id is not None:
                client_id = client_id.strip("\n")
        return client_id

    def getoauth2_client_secret(self):
        client_secret = self.getconf('oauth2_client_secret', None)
        if client_secret is None:
            client_secret = self.localeval.eval(
                self.getconf('oauth2_client_secret_eval', "None")
            )
            if client_secret is not None:
                client_secret = client_secret.strip("\n")
        return client_secret

    def getpreauthtunnel(self):
        return self.getconf('preauthtunnel', None)

    def gettransporttunnel(self):
        return self.getconf('transporttunnel', None)

    def getreference(self):
        return self.getconf('reference', '')

    def getdecodefoldernames(self):
        return self.getconfboolean('decodefoldernames', False)

    def getidlefolders(self):
        if self.idlefolders is None:
            self.idlefolders = self.localeval.eval(
                self.getconf('idlefolders', '[]')
            )
        return self.idlefolders

    def getmaxconnections(self):
        num1 = len(self.getidlefolders())
        num2 = self.getconfint('maxconnections', 1)
        return max(num1, num2)

    def getexpunge(self):
        return self.getconfboolean('expunge', True)

    def getpassword(self):
        """Return the IMAP password for this repository.

        It tries to get passwords in the following order:

        1. evaluate Repository 'remotepasseval'
        2. read password from Repository 'remotepass'
        3. read password from file specified in Repository 'remotepassfile'
        4. read password from ~/.netrc
        5. read password from /etc/netrc

        On success we return the password.
        If all strategies fail we return None."""

        # 1. Evaluate Repository 'remotepasseval'.
        passwd = self.getconf('remotepasseval', None)
        if passwd is not None:
            return self.localeval.eval(passwd).encode('UTF-8')
        # 2. Read password from Repository 'remotepass'.
        password = self.getconf('remotepass', None)
        if password is not None:
            # Assume the configuration file to be UTF-8 encoded so we must not
            # encode this string again.
            return password
        # 3. Read password from file specified in Repository 'remotepassfile'.
        passfile = self.getconf('remotepassfile', None)
        if passfile is not None:
            fd = codecs.open(os.path.expanduser(passfile), 'r', 'UTF-8')
            password = fd.readline().strip()
            fd.close()
            return password.encode('UTF-8')
        # 4. Read password from ~/.netrc.
        try:
            netrcentry = netrc.netrc().authenticators(self.gethost())
        except IOError as inst:
            if inst.errno != errno.ENOENT:
                raise
        else:
            if netrcentry:
                user = self.getuser()
                if user is None or user == netrcentry[0]:
                    return netrcentry[2]
        # 5. Read password from /etc/netrc.
        try:
            netrcentry = netrc.netrc('/etc/netrc').authenticators(self.gethost())
        except IOError as inst:
            if inst.errno not in (errno.ENOENT, errno.EACCES):
                raise
        else:
            if netrcentry:
                user = self.getuser()
                if user is None or user == netrcentry[0]:
                    return netrcentry[2]
        # No strategy yielded a password!
        return None

    def getfolder(self, foldername):
        """Return instance of OfflineIMAP representative folder."""

        return self.getfoldertype()(self.imapserver, foldername, self)

    def getfoldertype(self):
        return folder.IMAP.IMAPFolder

    def connect(self):
        imapobj = self.imapserver.acquireconnection()
        self.imapserver.releaseconnection(imapobj)

    def forgetfolders(self):
        self.folders = None

    def getfolders(self):
        """Return a list of instances of OfflineIMAP representative folder."""

        if self.folders is not None:
            return self.folders
        retval = []
        imapobj = self.imapserver.acquireconnection()
        # check whether to list all folders, or subscribed only
        listfunction = imapobj.list
        if self.getconfboolean('subscribedonly', False):
            listfunction = imapobj.lsub

        try:
            result, listresult = listfunction(directory=self.imapserver.reference)
            if result != 'OK':
                raise OfflineImapError("Could not list the folders for"
                        " repository %s. Server responded: %s"%
                        (self.name, self, str(listresult)),
                    OfflineImapError.ERROR.FOLDER)
        finally:
            self.imapserver.releaseconnection(imapobj)

        for s in listresult:
            if s == None or \
                   (isinstance(s, str) and s == ''):
                # Bug in imaplib: empty strings in results from
                # literals. TODO: still relevant?
                continue
            try:
                flags, delim, name = imaputil.imapsplit(s)
            except ValueError:
                self.ui.error(
                    "could not correctly parse server response; got: %s"% s)
                raise
            flaglist = [x.lower() for x in imaputil.flagsplit(flags)]
            if '\\noselect' in flaglist:
                continue
            foldername = imaputil.dequote(name)
            retval.append(self.getfoldertype()(self.imapserver, foldername,
                                               self))
        # Add all folderincludes
        if len(self.folderincludes):
            imapobj = self.imapserver.acquireconnection()
            try:
                for foldername in self.folderincludes:
                    try:
                        imapobj.select(foldername, readonly=True)
                    except OfflineImapError as e:
                        # couldn't select this folderinclude, so ignore folder.
                        if e.severity > OfflineImapError.ERROR.FOLDER:
                            raise
                        self.ui.error(e, exc_info()[2],
                                      'Invalid folderinclude:')
                        continue
                    retval.append(self.getfoldertype()(
                        self.imapserver, foldername, self))
            finally:
                self.imapserver.releaseconnection(imapobj)

        if self.foldersort is None:
            # default sorting by case insensitive transposed name
            retval.sort(key=lambda x: str.lower(x.getvisiblename()))
        else:
            # do foldersort in a python3-compatible way
            # http://bytes.com/topic/python/answers/844614-python-3-sorting-comparison-function
            def cmp2key(mycmp):
                """Converts a cmp= function into a key= function
                We need to keep cmp functions for backward compatibility"""
                class K(object):
                    def __init__(self, obj, *args):
                        self.obj = obj
                    def __cmp__(self, other):
                        return mycmp(self.obj.getvisiblename(), other.obj.getvisiblename())
                return K
            retval.sort(key=cmp2key(self.foldersort))

        self.folders = retval
        return self.folders

    def deletefolder(self, foldername):
        """Delete a folder on the IMAP server."""

        imapobj = self.imapserver.acquireconnection()
        try:
            result = imapobj.delete(foldername)
            if result[0] != 'OK':
                raise OfflineImapError("Folder '%s'[%s] could not be deleted. "
                    "Server responded: %s"% (foldername, self, str(result)),
                    OfflineImapError.ERROR.FOLDER)
        finally:
            self.imapserver.releaseconnection(imapobj)

    def makefolder(self, foldername):
        """Create a folder on the IMAP server

        This will not update the list cached in :meth:`getfolders`. You
        will need to invoke :meth:`forgetfolders` to force new caching
        when you are done creating folders yourself.

        :param foldername: Full path of the folder to be created."""

        if foldername is '':
            return

        if self.getreference():
            foldername = self.getreference() + self.getsep() + foldername
        if not foldername: # Create top level folder as folder separator.
            foldername = self.getsep()
        self.ui.makefolder(self, foldername)
        if self.account.dryrun:
            return
        imapobj = self.imapserver.acquireconnection()
        try:
            result = imapobj.create(foldername)
            if result[0] != 'OK':
                raise OfflineImapError("Folder '%s'[%s] could not be created. "
                    "Server responded: %s"% (foldername, self, str(result)),
                    OfflineImapError.ERROR.FOLDER)
        finally:
            self.imapserver.releaseconnection(imapobj)

class MappedIMAPRepository(IMAPRepository):
    def getfoldertype(self):
        return folder.UIDMaps.MappedIMAPFolder
