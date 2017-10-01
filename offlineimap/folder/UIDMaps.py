# Base folder support
# Copyright (C) 2002-2016 John Goerzen & contributors.
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

import os.path
import shutil
from os import fsync, unlink
from sys import exc_info
from threading import Lock
import six

from offlineimap import OfflineImapError
from .IMAP import IMAPFolder


class MappedIMAPFolder(IMAPFolder):
    """IMAP class to map between Folder() instances where both side assign a uid

    This Folder is used on the local side, while the remote side should
    be an IMAPFolder.

    Instance variables (self.):
      dryrun: boolean.
      r2l: dict mapping message uids: self.r2l[remoteuid]=localuid
      l2r: dict mapping message uids: self.r2l[localuid]=remoteuid
      #TODO: what is the difference, how are they used?
      diskr2l: dict mapping message uids: self.r2l[remoteuid]=localuid
      diskl2r: dict mapping message uids: self.r2l[localuid]=remoteuid"""

    def __init__(self, imapserver, name, repository, decode=True):
        IMAPFolder.__init__(self, imapserver, name, repository, decode=False)
        self.dryrun = self.config.getdefaultboolean("general", "dry-run", True)
        self.maplock = Lock()
        self.diskr2l, self.diskl2r = self._loadmaps()
        self.r2l, self.l2r = None, None
        # Representing the local IMAP Folder using local UIDs.
        # XXX: This should be removed since we inherit from IMAPFolder.
        # See commit 3ce514e92ba7 to know more.
        self._mb = IMAPFolder(imapserver, name, repository, decode=False)

    def _getmapfilename(self):
        return os.path.join(self.repository.getmapdir(),
                            self.getfolderbasename())

    def _loadmaps(self):
        mapfilename = self._getmapfilename()
        mapfilenametmp = "%s.tmp"% mapfilename
        mapfilenamelock = "%s.lock"% mapfilename
        with self.maplock and open(mapfilenamelock, 'w') as mapfilelock:
            try:
                fnctl.lockf(mapfilelock, fnctl.LOCK_EX) # Blocks until acquired.
            except NameError:
                pass # Windows...
            if os.path.exists(mapfilenametmp):
                self.ui.warn("a previous run might have leave the UIDMaps file"
                    " in incorrect state; some sync operations might be done"
                    " again and some emails might become duplicated.")
                unlink(mapfilenametmp)
            if not os.path.exists(mapfilename):
                return ({}, {})
            file = open(mapfilename, 'rt')
            r2l = {}
            l2r = {}
            while True:
                line = file.readline()
                if not len(line):
                    break
                try:
                    line = line.strip()
                except ValueError:
                    six.reraise(Exception,
                            Exception(
                                "Corrupt line '%s' in UID mapping file '%s'"%
                                (line, mapfilename)),
                            exc_info()[2])
                (str1, str2) = line.split(':')
                loc = int(str1)
                rem = int(str2)
                r2l[rem] = loc
                l2r[loc] = rem
            return (r2l, l2r)

    def _savemaps(self):
        if self.dryrun is True:
            return

        mapfilename = self._getmapfilename()
        # Do not use the map file directly to prevent from leaving it truncated.
        mapfilenametmp = "%s.tmp"% mapfilename
        mapfilenamelock = "%s.lock"% mapfilename
        with self.maplock and open(mapfilenamelock, 'w') as mapfilelock:
            # The "account" lock already prevents from multiple access by
            # different processes. However, we still need to protect for
            # multiple access from different threads.
            try:
                fnctl.lockf(mapfilelock, fnctl.LOCK_EX) # Blocks until acquired.
            except NameError:
                pass # Windows...
            with open(mapfilenametmp, 'wt') as mapfilefd:
                for (key, value) in self.diskl2r.items():
                    mapfilefd.write("%d:%d\n"% (key, value))
                if self.dofsync():
                    fsync(mapfilefd)
            # The lock is released when the file descriptor ends.
            shutil.move(mapfilenametmp, mapfilename)

    def _uidlist(self, mapping, items):
        try:
            return [mapping[x] for x in items]
        except KeyError as e:
            six.reraise(OfflineImapError,
                        OfflineImapError(
                            "Could not find UID for msg '{0}' (f:'{1}'."
                            " This is usually a bad thing and should be "
                            "reported on the mailing list.".format(
                                e.args[0], self),
                            OfflineImapError.ERROR.MESSAGE),
                        exc_info()[2])

    # Interface from BaseFolder
    def cachemessagelist(self, min_date=None, min_uid=None):
        self._mb.cachemessagelist(min_date=min_date, min_uid=min_uid)
        reallist = self._mb.getmessagelist()
        self.messagelist = self._mb.messagelist

        with self.maplock:
            # OK.  Now we've got a nice list.  First, delete things from the
            # summary that have been deleted from the folder.
            for luid in self.diskl2r.keys():
                if not luid in reallist:
                    ruid = self.diskl2r[luid]
                    #XXX: the following KeyError are sightly unexpected. This
                    # would require more digging to understand how it's
                    # possible.
                    errorMessage = ("unexpected error: key {} was not found "
                        "in memory, see "
                        "https://github.com/OfflineIMAP/offlineimap/issues/445"
                        " to know more."
                    )
                    try:
                        del self.diskr2l[ruid]
                    except KeyError as e:
                        self.ui.warn(errorMessage.format(ruid))
                    try:
                        del self.diskl2r[luid]
                    except KeyError as e:
                        self.ui.warn(errorMessage.format(ruid))

            # Now, assign negative UIDs to local items.
            self._savemaps()
            nextneg = -1

            self.r2l = self.diskr2l.copy()
            self.l2r = self.diskl2r.copy()

            for luid in reallist.keys():
                if not luid in self.l2r:
                    ruid = nextneg
                    nextneg -= 1
                    self.l2r[luid] = ruid
                    self.r2l[ruid] = luid

    def dropmessagelistcache(self):
        self._mb.dropmessagelistcache()

    # Interface from BaseFolder
    def uidexists(self, ruid):
        """Checks if the (remote) UID exists in this Folder"""

        # This implementation overrides the one in BaseFolder, as it is
        # much more efficient for the mapped case.
        return ruid in self.r2l

    # Interface from BaseFolder
    def getmessageuidlist(self):
        """Gets a list of (remote) UIDs.

        You may have to call cachemessagelist() before calling this function!"""

        # This implementation overrides the one in BaseFolder, as it is
        # much more efficient for the mapped case.
        return self.r2l.keys()

    # Interface from BaseFolder
    def getmessagecount(self):
        """Gets the number of messages in this folder.

        You may have to call cachemessagelist() before calling this function!"""

        # This implementation overrides the one in BaseFolder, as it is
        # much more efficient for the mapped case.
        return len(self.r2l)

    # Interface from BaseFolder
    def getmessagelist(self):
        """Gets the current message list.

        This function's implementation is quite expensive for the mapped UID
        case.  You must call cachemessagelist() before calling this function!"""

        retval = {}
        localhash = self._mb.getmessagelist()
        with self.maplock:
            for key, value in list(localhash.items()):
                try:
                    key = self.l2r[key]
                except KeyError:
                    # Sometimes, the IMAP backend may put in a new message,
                    # then this function acquires the lock before the system
                    # has the chance to note it in the mapping.  In that case,
                    # just ignore it.
                    continue
                value = value.copy()
                value['uid'] = self.l2r[value['uid']]
                retval[key] = value
            return retval

    # Interface from BaseFolder
    def getmessage(self, uid):
        """Returns the content of the specified message."""
        return self._mb.getmessage(self.r2l[uid])

    # Interface from BaseFolder
    def savemessage(self, uid, content, flags, rtime):
        """Writes a new message, with the specified uid.

        The UIDMaps class will not return a newly assigned uid, as it
        internally maps different uids between IMAP servers. So a
        successful savemessage() invocation will return the same uid it
        has been invoked with. As it maps between 2 IMAP servers which
        means the source message must already have an uid, it requires a
        positive uid to be passed in. Passing in a message with a
        negative uid will do nothing and return the negative uid.

        If the uid is > 0, the backend should set the uid to this, if it can.
        If it cannot set the uid to that, it will save it anyway.
        It will return the uid assigned in any case.

        See folder/Base for details. Note that savemessage() does not
        check against dryrun settings, so you need to ensure that
        savemessage is never called in a dryrun mode.
        """

        self.ui.savemessage('imap', uid, flags, self)
        # Mapped UID instances require the source to already have a
        # positive UID, so simply return here.
        if uid < 0:
            return uid

        # If msg uid already exists, just modify the flags.
        if uid in self.r2l:
            self.savemessageflags(uid, flags)
            return uid

        newluid = self._mb.savemessage(-1, content, flags, rtime)
        if newluid < 1:
            raise OfflineImapError("server of repository '%s' did not return "
                "a valid UID (got '%s') for UID '%s' from '%s'"% (
                    self._mb.getname(), newluid, uid, self.getname()
                ),
                OfflineImapError.ERROR.MESSAGE
            )
        with self.maplock:
            self.diskl2r[newluid] = uid
            self.diskr2l[uid] = newluid
            self.l2r[newluid] = uid
            self.r2l[uid] = newluid
            self._savemaps()
        return uid

    # Interface from BaseFolder
    def getmessageflags(self, uid):
        return self._mb.getmessageflags(self.r2l[uid])

    # Interface from BaseFolder
    def getmessagetime(self, uid):
        return None

    # Interface from BaseFolder
    def savemessageflags(self, uid, flags):
        """Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        self._mb.savemessageflags(self.r2l[uid], flags)

    # Interface from BaseFolder
    def addmessageflags(self, uid, flags):
        self._mb.addmessageflags(self.r2l[uid], flags)

    # Interface from BaseFolder
    def addmessagesflags(self, uidlist, flags):
        self._mb.addmessagesflags(self._uidlist(self.r2l, uidlist),
                                  flags)

    # Interface from BaseFolder
    def change_message_uid(self, ruid, new_ruid):
        """Change the message from existing ruid to new_ruid

        :param new_uid: The old remote UID will be changed to a new
            UID. The UIDMaps case handles this efficiently by simply
            changing the mappings file."""

        if ruid not in self.r2l:
            raise OfflineImapError("Cannot change unknown Maildir UID %s"%
                ruid, OfflineImapError.ERROR.MESSAGE)
        if ruid == new_ruid: return  # sanity check shortcut
        with self.maplock:
            luid = self.r2l[ruid]
            self.l2r[luid] = new_ruid
            del self.r2l[ruid]
            self.r2l[new_ruid] = luid
            # TODO: diskl2r|r2l are a pain to sync and should be done away with
            # diskl2r only contains positive UIDs, so wrap in ifs.
            if luid > 0: self.diskl2r[luid] = new_ruid
            if ruid > 0: del self.diskr2l[ruid]
            if new_ruid > 0: self.diskr2l[new_ruid] = luid
            self._savemaps()

    def _mapped_delete(self, uidlist):
        with self.maplock:
            needssave = 0
            for ruid in uidlist:
                luid = self.r2l[ruid]
                del self.r2l[ruid]
                del self.l2r[luid]
                if ruid > 0:
                    del self.diskr2l[ruid]
                    del self.diskl2r[luid]
                    needssave = 1
            if needssave:
                self._savemaps()

    # Interface from BaseFolder
    def deletemessageflags(self, uid, flags):
        self._mb.deletemessageflags(self.r2l[uid], flags)

    # Interface from BaseFolder
    def deletemessagesflags(self, uidlist, flags):
        self._mb.deletemessagesflags(self._uidlist(self.r2l, uidlist),
            flags)

    # Interface from BaseFolder
    def deletemessage(self, uid):
        self._mb.deletemessage(self.r2l[uid])
        self._mapped_delete([uid])

    # Interface from BaseFolder
    def deletemessages(self, uidlist):
        self._mb.deletemessages(self._uidlist(self.r2l, uidlist))
        self._mapped_delete(uidlist)
