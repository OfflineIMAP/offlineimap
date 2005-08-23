# Local status cache virtual folder
# Copyright (C) 2002 - 2003 John Goerzen
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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Base import BaseFolder
import os, threading

magicline = "OFFLINEIMAP LocalStatus CACHE DATA - DO NOT MODIFY - FORMAT 1"

class LocalStatusFolder(BaseFolder):
    def __init__(self, root, name, repository, accountname):
        self.name = name
        self.root = root
        self.sep = '.'
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
        assert(line == magicline)
        for line in file.xreadlines():
            line = line.strip()
            uid, flags = line.split(':')
            uid = long(uid)
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
            file.close()
            os.rename(self.filename + ".tmp", self.filename)
        finally:
            self.savelock.release()

    def getmessagelist(self):
        return self.messagelist

    def savemessage(self, uid, content, flags):
        if uid < 0:
            # We cannot assign a uid.
            return uid

        if uid in self.messagelist:     # already have it
            self.savemessageflags(uid, flags)
            return uid

        self.messagelist[uid] = {'uid': uid, 'flags': flags}
        self.autosave()
        return uid

    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def savemessageflags(self, uid, flags):
        self.messagelist[uid]['flags'] = flags
        self.autosave()

    def deletemessage(self, uid):
        if not uid in self.messagelist:
            return
        del(self.messagelist[uid])
        self.autosave()