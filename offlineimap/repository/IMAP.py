# IMAP repository support
# Copyright (C) 2002-2011 John Goerzen & contributors
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

from offlineimap.repository.Base import BaseRepository
from offlineimap import folder, imaputil, imapserver, OfflineImapError
from offlineimap.folder.UIDMaps import MappedIMAPFolder
from offlineimap.threadutil import ExitNotifyThread
from threading import Event
import types
import os
from sys import exc_info
import netrc
import errno

class IMAPRepository(BaseRepository):
    def __init__(self, reposname, account):
        """Initialize an IMAPRepository object."""
        BaseRepository.__init__(self, reposname, account)
        # self.ui is being set by the BaseRepository
        self._host = None
        self.imapserver = imapserver.IMAPServer(self)
        self.folders = None

    def startkeepalive(self):
        keepalivetime = self.getkeepalive()
        if not keepalivetime: return
        self.kaevent = Event()
        self.kathread = ExitNotifyThread(target = self.imapserver.keepalive,
                                         name = "Keep alive " + self.getname(),
                                         args = (keepalivetime, self.kaevent))
        self.kathread.setDaemon(1)
        self.kathread.start()

    def stopkeepalive(self):
        if not hasattr(self, 'kaevent'):
            # Keepalive is not active.
            return

        self.kaevent.set()
        del self.kathread
        del self.kaevent

    def holdordropconnections(self):
        if not self.getholdconnectionopen():
            self.dropconnections()

    def dropconnections(self):
        self.imapserver.close()

    def getholdconnectionopen(self):
        if self.getidlefolders():
            return 1
        return self.getconfboolean("holdconnectionopen", 0)

    def getkeepalive(self):
        num = self.getconfint("keepalive", 0)
        if num == 0 and self.getidlefolders():
            return 29*60
        else:
            return num

    def getsep(self):
        return self.imapserver.delim

    def gethost(self):
        """Return the configured hostname to connect to

        :returns: hostname as string or throws Exception"""
        if self._host:  # use cached value if possible
            return self._host

        # 1) check for remotehosteval setting
        if self.config.has_option(self.getsection(), 'remotehosteval'):
            host = self.getconf('remotehosteval')
            try:
                host = self.localeval.eval(host)
            except Exception, e:
                raise OfflineImapError("remotehosteval option for repository "\
                                       "'%s' failed:\n%s" % (self, e),
                                       OfflineImapError.ERROR.REPO)
            if host:
                self._host = host
                return self._host
        # 2) check for plain remotehost setting
        host = self.getconf('remotehost', None)
        if host != None:
            self._host = host
            return self._host

        # no success
        raise OfflineImapError("No remote host for repository "\
                                   "'%s' specified." % self,
                               OfflineImapError.ERROR.REPO)

    def getuser(self):
        user = None
        localeval = self.localeval

        if self.config.has_option(self.getsection(), 'remoteusereval'):
            user = self.getconf('remoteusereval')
        if user != None:
            return localeval.eval(user)

        user = self.getconf('remoteuser')
        if user != None:
            return user

        try:
            netrcentry = netrc.netrc().authenticators(self.gethost())
        except IOError, inst:
            if inst.errno != errno.ENOENT:
                raise
        else:
            if netrcentry:
                return netrcentry[0]

        try:
            netrcentry = netrc.netrc('/etc/netrc').authenticators(self.gethost())
        except IOError, inst:
            if inst.errno != errno.ENOENT:
                raise
        else:
            if netrcentry:
                return netrcentry[0]


    def getport(self):
        return self.getconfint('remoteport', None)

    def getssl(self):
        return self.getconfboolean('ssl', 0)

    def getsslclientcert(self):
        return self.getconf('sslclientcert', None)

    def getsslclientkey(self):
        return self.getconf('sslclientkey', None)

    def getsslcacertfile(self):
        """Return the absolute path of the CA certfile to use, if any"""
        cacertfile = self.getconf('sslcacertfile', None)
        if cacertfile is None:
            return None
        cacertfile = os.path.expanduser(cacertfile)
        cacertfile = os.path.abspath(cacertfile)
        if not os.path.isfile(cacertfile):
            raise SyntaxWarning("CA certfile for repository '%s' could "
                                "not be found. No such file: '%s'" \
                                % (self.name, cacertfile))
        return cacertfile

    def get_ssl_fingerprint(self):
        return self.getconf('cert_fingerprint', None)

    def getpreauthtunnel(self):
        return self.getconf('preauthtunnel', None)

    def getreference(self):
        return self.getconf('reference', '')

    def getidlefolders(self):
        localeval = self.localeval
        return localeval.eval(self.getconf('idlefolders', '[]'))

    def getmaxconnections(self):
        num1 = len(self.getidlefolders())
        num2 = self.getconfint('maxconnections', 1)
        return max(num1, num2)

    def getexpunge(self):
        return self.getconfboolean('expunge', 1)

    def getpassword(self):
        """Return the IMAP password for this repository.

        It tries to get passwords in the following order:

        1. evaluate Repository 'remotepasseval'
        2. read password from Repository 'remotepass'
        3. read password from file specified in Repository 'remotepassfile'
        4. read password from ~/.netrc
        5. read password from /etc/netrc

        On success we return the password.
        If all strategies fail we return None.
        """
        # 1. evaluate Repository 'remotepasseval'
        passwd = self.getconf('remotepasseval', None)
        if passwd != None:
            return self.localeval.eval(passwd)
        # 2. read password from Repository 'remotepass'
        password = self.getconf('remotepass', None)
        if password != None:
            return password
        # 3. read password from file specified in Repository 'remotepassfile'
        passfile = self.getconf('remotepassfile', None)
        if passfile != None:
            fd = open(os.path.expanduser(passfile))
            password = fd.readline().strip()
            fd.close()
            return password
        # 4. read password from ~/.netrc
        try:
            netrcentry = netrc.netrc().authenticators(self.gethost())
        except IOError, inst:
            if inst.errno != errno.ENOENT:
                raise
        else:
            if netrcentry:
                user = self.getconf('remoteuser')
                if user == None or user == netrcentry[0]:
                    return netrcentry[2]
        # 5. read password from /etc/netrc
        try:
            netrcentry = netrc.netrc('/etc/netrc').authenticators(self.gethost())
        except IOError, inst:
            if inst.errno != errno.ENOENT:
                raise
        else:
            if netrcentry:
                user = self.getconf('remoteuser')
                if user == None or user == netrcentry[0]:
                    return netrcentry[2]
        # no strategy yielded a password!
        return None


    def getfolder(self, foldername):
        return self.getfoldertype()(self.imapserver, foldername, self)

    def getfoldertype(self):
        return folder.IMAP.IMAPFolder

    def connect(self):
        imapobj = self.imapserver.acquireconnection()
        self.imapserver.releaseconnection(imapobj)

    def forgetfolders(self):
        self.folders = None

    def getfolders(self):
        if self.folders != None:
            return self.folders
        retval = []
        imapobj = self.imapserver.acquireconnection()
        # check whether to list all folders, or subscribed only
        listfunction = imapobj.list
        if self.getconfboolean('subscribedonly', False):
            listfunction = imapobj.lsub
        try:
            listresult = listfunction(directory = self.imapserver.reference)[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        for string in listresult:
            if string == None or \
                   (type(string) == types.StringType and string == ''):
                # Bug in imaplib: empty strings in results from
                # literals.
                continue
            flags, delim, name = imaputil.imapsplit(string)
            flaglist = [x.lower() for x in imaputil.flagsplit(flags)]
            if '\\noselect' in flaglist:
                continue
            foldername = imaputil.dequote(name)
            retval.append(self.getfoldertype()(self.imapserver, foldername,
                                               self))
            # filter out the folder?
            if not self.folderfilter(foldername):
                self.ui.debug('imap', "Filtering out '%s'[%s] due to folderfilt"
                              "er" % (foldername, self))
                retval[-1].sync_this = False
        # Add all folderincludes
        if len(self.folderincludes):
            imapobj = self.imapserver.acquireconnection()
            try:
                for foldername in self.folderincludes:
                    try:
                        imapobj.select(foldername, readonly = True)
                    except OfflineImapError, e:
                        # couldn't select this folderinclude, so ignore folder.
                        if e.severity > OfflineImapError.ERROR.FOLDER:
                            raise
                        self.ui.error(e, exc_info()[2],
                                      'Invalid folderinclude:')
                        continue
                    retval.append(self.getfoldertype()(self.imapserver,
                                                       foldername,
                                                       self))
            finally:
                self.imapserver.releaseconnection(imapobj)
                
        retval.sort(lambda x, y: self.foldersort(x.getvisiblename(), y.getvisiblename()))
        self.folders = retval
        return self.folders

    def makefolder(self, foldername):
        """Create a folder on the IMAP server

        This will not update the list cached in :meth:`getfolders`. You
        will need to invoke :meth:`forgetfolders` to force new caching
        when you are done creating folders yourself.

        :param foldername: Full path of the folder to be created."""
        if self.getreference():
            foldername = self.getreference() + self.getsep() + foldername

        imapobj = self.imapserver.acquireconnection()
        try:
            self.ui._msg("Creating new IMAP folder '%s' on server %s" %\
                              (foldername, self))
            result = imapobj.create(foldername)
            if result[0] != 'OK':
                raise OfflineImapError("Folder '%s'[%s] could not be created. "
                                       "Server responded: %s" % \
                                           (foldername, self, str(result)),
                                       OfflineImapError.ERROR.FOLDER)
        finally:
            self.imapserver.releaseconnection(imapobj)
            
class MappedIMAPRepository(IMAPRepository):
    def getfoldertype(self):
        return MappedIMAPFolder
