# IMAP repository support
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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from offlineimap.repository.Base import BaseRepository
from offlineimap import folder, imaputil, imapserver
from offlineimap.folder.UIDMaps import MappedIMAPFolder
from offlineimap.threadutil import ExitNotifyThread
from threading import Event
import re
import types
import os
import netrc
import errno

class IMAPRepository(BaseRepository):
    def __init__(self, reposname, account):
        """Initialize an IMAPRepository object."""
        BaseRepository.__init__(self, reposname, account)
        # self.ui is being set by the BaseRepository
        self.imapserver = imapserver.ConfigedIMAPServer(self)
        self.folders = None
        self.nametrans = lambda foldername: foldername
        self.folderfilter = lambda foldername: 1
        self.folderincludes = []
        self.foldersort = cmp
        localeval = self.localeval
        if self.config.has_option(self.getsection(), 'nametrans'):
            self.nametrans = localeval.eval(self.getconf('nametrans'),
                                            {'re': re})
        if self.config.has_option(self.getsection(), 'folderfilter'):
            self.folderfilter = localeval.eval(self.getconf('folderfilter'),
                                               {'re': re})
        if self.config.has_option(self.getsection(), 'folderincludes'):
            self.folderincludes = localeval.eval(self.getconf('folderincludes'),
                                                 {'re': re})
        if self.config.has_option(self.getsection(), 'foldersort'):
            self.foldersort = localeval.eval(self.getconf('foldersort'),
                                             {'re': re})

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
        host = None
        localeval = self.localeval

        if self.config.has_option(self.getsection(), 'remotehosteval'):
            host = self.getconf('remotehosteval')
        if host != None:
            return localeval.eval(host)

        host = self.getconf('remotehost')
        if host != None:
            return host

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

    def getpreauthtunnel(self):
        return self.getconf('preauthtunnel', None)

    def getreference(self):
        return self.getconf('reference', '""')

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
        return self.getfoldertype()(self.imapserver, foldername,
                                    self.nametrans(foldername),
                                    self.accountname, self)

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
        if self.config.has_option(self.getsection(), 'subscribedonly'):
          if self.getconf('subscribedonly') == "yes":
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
            if not self.folderfilter(foldername):
                self.ui.debug('imap',"Filtering out '%s' due to folderfilter" %\
                                  foldername)
                continue
            retval.append(self.getfoldertype()(self.imapserver, foldername,
                                               self.nametrans(foldername),
                                               self.accountname, self))
        if len(self.folderincludes):
            imapobj = self.imapserver.acquireconnection()
            try:
                for foldername in self.folderincludes:
                    try:
                        imapobj.select(foldername, readonly = 1)
                    except ValueError:
                        continue
                    retval.append(self.getfoldertype()(self.imapserver,
                                                       foldername,
                                                       self.nametrans(foldername),
                                                       self.accountname, self))
            finally:
                self.imapserver.releaseconnection(imapobj)
                
        retval.sort(lambda x, y: self.foldersort(x.getvisiblename(), y.getvisiblename()))
        self.folders = retval
        return retval

    def makefolder(self, foldername):
        #if self.getreference() != '""':
        #    newname = self.getreference() + self.getsep() + foldername
        #else:
        #    newname = foldername
        newname = foldername
        imapobj = self.imapserver.acquireconnection()
        try:
            result = imapobj.create(newname)
            if result[0] != 'OK':
                raise RuntimeError, "Repository %s could not create folder %s: %s" % (self.getname(), foldername, str(result))
        finally:
            self.imapserver.releaseconnection(imapobj)
            
class MappedIMAPRepository(IMAPRepository):
    def getfoldertype(self):
        return MappedIMAPFolder
