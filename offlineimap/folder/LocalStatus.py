# Local status cache virtual folder
# Copyright (C) 2002 - 2008 John Goerzen
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

from Base import BaseFolder
import os, threading

magicline = "OFFLINEIMAP LocalStatus CACHE DATA - DO NOT MODIFY - FORMAT 1"

class LocalStatusFolder(BaseFolder):
    def __init__(self, root, name, repository, accountname, config):
        self.name = name
        self.root = root
        self.sep = '.'
        self.config = config
        self.dofsync = config.getdefaultboolean("general", "fsync", True)
        self.filename = os.path.join(root, name)
        self.filename = repository.getfolderfilename(name)
        self.messagelist = None
        self.repository = repository
        self.savelock = threading.Lock()
        self.doautosave = 1
        self.accountname = accountname
        BaseFolder.__init__(self)

    def getaccountname(self):
        return self.accountname

    def storesmessages(self):
        return 0

    def isnewfolder(self):
        return not os.path.exists(self.filename)

    def getname(self):
        return self.name

    def getroot(self):
        return self.root

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
        if not line and not line.read():
            # The status file is empty - should not have happened,
            # but somehow did.
            file.close()
            return
        assert(line == magicline)
        for line in file.xreadlines():
            line = line.strip()
            try:
                uid, flags = line.split(':')
                uid = long(uid)
            except ValueError, e:
                errstr = "Corrupt line '%s' in cache file '%s'" % (line, self.filename)
                self.ui.warn(errstr)
                raise ValueError(errstr)
            flags = [x for x in flags]
            self.messagelist[uid] = {'uid': uid, 'flags': flags}
        file.close()

    def autosave(self):
        if self.doautosave:
            self.save()

    def save(self):
        self.savelock.acquire()
        try:
            file = open(self.filename + ".tmp", "wt")
            file.write(magicline + "\n")
            for msg in self.messagelist.values():
                flags = msg['flags']
                flags.sort()
                flags = ''.join(flags)
                file.write("%s:%s\n" % (msg['uid'], flags))
            file.flush()
            if self.dofsync:
                os.fsync(file.fileno())
            file.close()
            os.rename(self.filename + ".tmp", self.filename)

            if self.dofsync:
                fd = os.open(os.path.dirname(self.filename), os.O_RDONLY)
                os.fsync(fd)
                os.close(fd)

        finally:
            self.savelock.release()

    def getmessagelist(self):
        return self.messagelist

    def savemessage(self, uid, content, flags, rtime):
        if uid < 0:
            # We cannot assign a uid.
            return uid

        if uid in self.messagelist:     # already have it
            self.savemessageflags(uid, flags)
            return uid

        self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime}
        self.autosave()
        return uid

    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']

    def savemessageflags(self, uid, flags):
        self.messagelist[uid]['flags'] = flags
        self.autosave()

    def deletemessage(self, uid):
        self.deletemessages([uid])

    def deletemessages(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return

        for uid in uidlist:
            del(self.messagelist[uid])
        self.autosave()
