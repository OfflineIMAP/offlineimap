# Maildir folder support
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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Base import BaseFolder
from imapsync import imaputil
import os.path, os, re, time, socket

class MaildirFolder(BaseFolder):
    def __init__(self, root, name):
        self.name = name
        self.root = root
        self.sep = '.'
        self.uidfilename = os.path.join(self.getfullname(), "imapsync.uidvalidity")
        self.messagelist = None

    def getfullname(self):
        return os.path.join(self.getroot(), self.getname())

    def getuidvalidity(self):
        if not os.path.exists(self.uidfilename):
            return None
        file = open(self.uidfilename, "rt")
        retval = long(file.readline().strip())
        file.close()
        return retval

    def saveuidvalidity(self, newval):
        file = open(self.uidfilename, "wt")
        file.write("%d\n", newval)
        file.close()

    def isuidvalidityok(self, remotefolder):
        myval = self.getuidvalidity()
        if myval != None:
            return myval == remotefolder.getuidvalidity()
        else:
            self.saveuidvalidity(remotefolder.getuidvalidity())
            
    def cachemessagelist(self):
        """Cache the message list.  Maildir flags are:
        R (replied)
        S (seen)
        T (trashed)
        D (draft)
        F (flagged)
        and must occur in ASCII order."""
        self.messagelist = {}
        files = []
        nouidcounter = -1               # Messages without UIDs get
                                        # negative UID numbers.
        for dirannex in ['new', 'cur']:
            fulldirname = os.path.join(self.getfullname(), dirannex)
            files.extend([os.path.join(fulldirname, filename) for
                          filename in os.listdir(fulldirname)])
        for file in files:
            messagename = os.path.basename(file)
            uidmatch = re.search(',U=(\d+)', messagename)
            uid = None
            if not uidmatch:
                uid = nouidcounter
                nouidcounter -= 1
            else:
                uid = long(uidmatch.group(1))
            flagmatch = re.search(':.*2,([A-Z]+)', messagename)
            flags = []
            if flagmatch:
                flags = [x for x in flagmatch.group(1)]
            flags.sort()
            self.messagelist[uid] = {'uid': uid,
                                     'flags': flags,
                                     'filename': file}
            
    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        filename = self.getmessagelist()[uid]['filename']
        file = open(filename, 'rt')
        retval = file.read()
        file.close()
        return retval

    def savemessage(self, uid, content):
        if uid < 0:
            # We cannot assign a new uid.
            return uid
        if uid in self.getmessagelist():
            # We already have it.
            return uid
        newdir = os.path.join(self.getfullname(), 'new')
        tmpdir = os.path.join(self.getfullname(), 'tmp')
        messagename = None
        attempts = 0
        while 1:
            if attempts > 15:
                raise IOError, "Couldn't write to file %s" % messagename
            messagename = '%d.%d.%s,U=%d' % \
                          (long(time.time()),
                           os.getpid(),
                           socket.gethostname(),
                           uid)
            if os.path.exists(os.path.join(tmpdir, messagename)):
                time.sleep(2)
                attempts += 1
            else:
                break
        file = open(os.path.join(tmpdir, messagename), "wt")
        file.write(content)
        file.close()
        os.link(os.path.join(tmpdir, messagename),
                os.path.join(newdir, messagename))
        os.unlink(os.path.join(tmpdir, messagename))
        self.messagelist[uid] = {'uid': uid, 'flags': [],
                                 'filename': os.path.join(newdir, messagename)}
        return uid
        
    def getmessageflags(self, uid):
        return self.getmessagelist()[uid]['flags']

    def savemessageflags(self, uid, flags):
        oldfilename = self.getmessagelist()[uid]['filename']
        newpath, newname = os.path.split(oldfilename)
        infostr = ':'
        infomatch = re.search('(:.*)$', newname)
        if infomatch:                   # If the info string is present..
            infostr = infomatch.group(1)
            newname = newname.split(':')[0] # Strip off the info string.
        re.sub('2,[A-Z]*', '', infostr)
        flags.sort()
        infostr += '2,' + ''.join(flags)
        newname += infostr
        
        newfilename = os.path.join(newpath, newname)
        if (newfilename != oldfilename):
            os.rename(oldfilename, newfilename)
            self.getmessagelist()[uid]['flags'] = flags

    def getmessageflags(self, uid):
        return self.getmessagelist()[uid]['flags']

    def deletemessage(self, uid):
        filename = self.getmessagelist()[uid]['filename']
        os.unlink(filename)
        del(self.messagelist[uid])
        
