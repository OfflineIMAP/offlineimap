# Local status cache virtual folder
# Copyright (C) 2002-2015 John Goerzen & contributors
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

from sys import exc_info
import os
import threading

from .Base import BaseFolder

import six


class LocalStatusFolder(BaseFolder):
    """LocalStatus backend implemented as a plain text file."""

    cur_version = 2
    magicline = "OFFLINEIMAP LocalStatus CACHE DATA - DO NOT MODIFY - FORMAT %d"

    def __init__(self, name, repository):
        self.sep = '.' #needs to be set before super.__init__()
        super(LocalStatusFolder, self).__init__(name, repository)
        self.root = repository.root
        self.filename = os.path.join(self.getroot(), self.getfolderbasename())
        self.savelock = threading.Lock()
        # Should we perform fsyncs as often as possible?
        self.doautosave = self.config.getdefaultboolean(
            "general", "fsync", False)

    # Interface from BaseFolder
    def storesmessages(self):
        return 0

    def isnewfolder(self):
        return not os.path.exists(self.filename)

    # Interface from BaseFolder
    def getfullname(self):
        return self.filename

    def deletemessagelist(self):
        if not self.isnewfolder():
            os.unlink(self.filename)

    # Interface from BaseFolder
    def msglist_item_initializer(self, uid):
        return {'uid': uid, 'flags': set(), 'labels': set(), 'time': 0, 'mtime': 0}

    def readstatus_v1(self, fp):
        """Read status folder in format version 1.

        Arguments:
        - fp: I/O object that points to the opened database file.
        """

        for line in fp:
            line = line.strip()
            try:
                uid, flags = line.split(':')
                uid = int(uid)
                flags = set(flags)
            except ValueError as e:
                errstr = "Corrupt line '%s' in cache file '%s'" % \
                    (line, self.filename)
                self.ui.warn(errstr)
                six.reraise(ValueError(errstr), None, exc_info()[2])
            self.messagelist[uid] = self.msglist_item_initializer(uid)
            self.messagelist[uid]['flags'] = flags

    def readstatus(self, fp):
        """Read status file in the current format.

        Arguments:
        - fp: I/O object that points to the opened database file.
        """

        for line in fp:
            line = line.strip()
            try:
                uid, flags, mtime, labels = line.split('|')
                uid = int(uid)
                flags = set(flags)
                mtime = int(mtime)
                labels = set([lb.strip() for lb in labels.split(',') if len(lb.strip()) > 0])
            except ValueError as e:
                errstr = "Corrupt line '%s' in cache file '%s'"% \
                    (line, self.filename)
                self.ui.warn(errstr)
                six.reraise(ValueError(errstr), None, exc_info()[2])
            self.messagelist[uid] = self.msglist_item_initializer(uid)
            self.messagelist[uid]['flags'] = flags
            self.messagelist[uid]['mtime'] = mtime
            self.messagelist[uid]['labels'] = labels


    # Interface from BaseFolder
    def cachemessagelist(self):
        if self.isnewfolder():
            self.dropmessagelistcache()
            return

        # Loop as many times as version, and update format.
        for i in range(1, self.cur_version + 1):
            self.dropmessagelistcache()
            cachefd = open(self.filename, "rt")
            line = cachefd.readline().strip()

            # Format is up to date. break.
            if line == (self.magicline % self.cur_version):
                break

            # Convert from format v1.
            elif line == (self.magicline % 1):
                self.ui._msg('Upgrading LocalStatus cache from version 1'
                    'to version 2 for %s:%s'% (self.repository, self))
                self.readstatus_v1(cachefd)
                cachefd.close()
                self.save()

            # NOTE: Add other format transitions here in the future.
            # elif line == (self.magicline % 2):
            #     self.ui._msg(u'Upgrading LocalStatus cache from version 2'
            #         'to version 3 for %s:%s'% (self.repository, self))
            #     self.readstatus_v2(cache)
            #     cache.close()
            #     cache.save()

            # Something is wrong.
            else:
                errstr = "Unrecognized cache magicline in '%s'" % self.filename
                self.ui.warn(errstr)
                raise ValueError(errstr)

        if not line:
            # The status file is empty - should not have happened,
            # but somehow did.
            errstr = "Cache file '%s' is empty."% self.filename
            self.ui.warn(errstr)
            cachefd.close()
            return

        assert(line == (self.magicline % self.cur_version))
        self.readstatus(cachefd)
        cachefd.close()

    def openfiles(self):
        pass # Closing files is done on a per-transaction basis.

    def closefiles(self):
        pass # Closing files is done on a per-transaction basis.

    def save(self):
        """Save changed data to disk. For this backend it is the same as saveall."""

        self.saveall()

    def saveall(self):
        """Saves the entire messagelist to disk."""

        with self.savelock:
            cachefd = open(self.filename + ".tmp", "wt")
            cachefd.write((self.magicline % self.cur_version) + "\n")
            for msg in self.messagelist.values():
                flags = ''.join(sorted(msg['flags']))
                labels = ', '.join(sorted(msg['labels']))
                cachefd.write("%s|%s|%d|%s\n" % (msg['uid'], flags, msg['mtime'], labels))
            cachefd.flush()
            if self.doautosave:
                os.fsync(cachefd.fileno())
            cachefd.close()
            os.rename(self.filename + ".tmp", self.filename)

            if self.doautosave:
                fd = os.open(os.path.dirname(self.filename), os.O_RDONLY)
                os.fsync(fd)
                os.close(fd)

    # Interface from BaseFolder
    def savemessage(self, uid, content, flags, rtime, mtime=0, labels=set()):
        """Writes a new message, with the specified uid.

        See folder/Base for detail. Note that savemessage() does not
        check against dryrun settings, so you need to ensure that
        savemessage is never called in a dryrun mode."""

        if uid < 0:
            # We cannot assign a uid.
            return uid

        if self.uidexists(uid):     # already have it
            self.savemessageflags(uid, flags)
            return uid

        self.messagelist[uid] = self.msglist_item_initializer(uid)
        self.messagelist[uid]['flags'] = flags
        self.messagelist[uid]['time'] = rtime
        self.messagelist[uid]['mtime'] = mtime
        self.messagelist[uid]['labels'] = labels
        self.save()
        return uid

    # Interface from BaseFolder
    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    # Interface from BaseFolder
    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']

    # Interface from BaseFolder
    def savemessageflags(self, uid, flags):
        self.messagelist[uid]['flags'] = flags
        self.save()

    def savemessagelabels(self, uid, labels, mtime=None):
        self.messagelist[uid]['labels'] = labels
        if mtime: self.messagelist[uid]['mtime'] = mtime
        self.save()

    def savemessageslabelsbulk(self, labels):
        """Saves labels from a dictionary in a single database operation."""

        for uid, lb in labels.items():
            self.messagelist[uid]['labels'] = lb
        self.save()

    def addmessageslabels(self, uids, labels):
        for uid in uids:
            self.messagelist[uid]['labels'] = self.messagelist[uid]['labels'] | labels
        self.save()

    def deletemessageslabels(self, uids, labels):
        for uid in uids:
            self.messagelist[uid]['labels'] = self.messagelist[uid]['labels'] - labels
        self.save()

    def getmessagelabels(self, uid):
        return self.messagelist[uid]['labels']

    def savemessagesmtimebulk(self, mtimes):
        """Saves mtimes from the mtimes dictionary in a single database operation."""

        for uid, mt in mtimes.items():
            self.messagelist[uid]['mtime'] = mt
        self.save()

    def getmessagemtime(self, uid):
        return self.messagelist[uid]['mtime']

    # Interface from BaseFolder
    def deletemessage(self, uid):
        self.deletemessages([uid])

    # Interface from BaseFolder
    def deletemessages(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return

        for uid in uidlist:
            del(self.messagelist[uid])
        self.save()
