# Local status cache virtual folder
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

from .Base import BaseFolder
import os
import threading

magicline = "OFFLINEIMAP LocalStatus CACHE DATA - DO NOT MODIFY - FORMAT 1"


class LocalStatusFolder(BaseFolder):
    def __init__(self, name, repository):
        self.sep = '.' #needs to be set before super.__init__()
        super(LocalStatusFolder, self).__init__(name, repository)
        self.filename = os.path.join(self.getroot(), self.getfolderbasename())
        self.messagelist = {}
        self.savelock = threading.Lock()
        self.doautosave = self.config.getdefaultboolean("general", "fsync",
                                                        False)
        """Should we perform fsyncs as often as possible?"""

    def storesmessages(self):
        return 0

    def isnewfolder(self):
        return not os.path.exists(self.filename)

    def getname(self):
        return self.name

    def getroot(self):
        return self.repository.root

    def getsep(self):
        return self.sep

    def getfullname(self):
        return self.filename

    def deletemessagelist(self):
        if not self.isnewfolder():
            os.unlink(self.filename)

    def cachemessagelist(self):
        if self.isnewfolder():
            self.messagelist = {}
            return
        file = open(self.filename, "rt")
        self.messagelist = {}
        line = file.readline().strip()
        if not line:
            # The status file is empty - should not have happened,
            # but somehow did.
            errstr = "Cache file '%s' is empty. Closing..." % self.filename
            self.ui.warn(errstr)
            file.close()
            return
        assert(line == magicline)
        for line in file.xreadlines():
            line = line.strip()
            try:
                uid, flags = line.split(':')
                uid = long(uid)
                flags = set(flags)
            except ValueError as e:
                errstr = "Corrupt line '%s' in cache file '%s'" % \
                    (line, self.filename)
                self.ui.warn(errstr)
                raise ValueError(errstr)
            self.messagelist[uid] = {'uid': uid, 'flags': flags}
        file.close()

    def save(self):
        self.savelock.acquire()
        try:
            file = open(self.filename + ".tmp", "wt")
            file.write(magicline + "\n")
            for msg in self.messagelist.values():
                flags = msg['flags']
                flags = ''.join(sorted(flags))
                file.write("%s:%s\n" % (msg['uid'], flags))
            file.flush()
            if self.doautosave:
                os.fsync(file.fileno())
            file.close()
            os.rename(self.filename + ".tmp", self.filename)

            if self.doautosave:
                fd = os.open(os.path.dirname(self.filename), os.O_RDONLY)
                os.fsync(fd)
                os.close(fd)

        finally:
            self.savelock.release()

    def getmessagelist(self):
        return self.messagelist

    def savemessage(self, uid, content, flags, rtime):
        """Writes a new message, with the specified uid.

        See folder/Base for detail. Note that savemessage() does not
        check against dryrun settings, so you need to ensure that
        savemessage is never called in a dryrun mode."""
        if uid < 0:
            # We cannot assign a uid.
            return uid

        if uid in self.messagelist:     # already have it
            self.savemessageflags(uid, flags)
            return uid

        self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime}
        self.save()
        return uid

    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']

    def savemessageflags(self, uid, flags):
        self.messagelist[uid]['flags'] = flags
        self.save()

    def deletemessage(self, uid):
        self.deletemessages([uid])

    def deletemessages(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return

        for uid in uidlist:
            del(self.messagelist[uid])
        self.save()
