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
from offlineimap import imaputil
import os.path, os, re, time, socket, md5

foldermatchre = re.compile(',FMD5=([0-9a-f]{32})')
uidmatchre = re.compile(',U=(\d+)')
flagmatchre = re.compile(':.*2,([A-Z]+)')

timeseq = 0
lasttime = long(0)

def gettimeseq():
    global lasttime, timeseq
    thistime = long(time.time())
    if thistime == lasttime:
        timeseq += 1
        return timeseq
    else:
        lasttime = long(time.time())
        timeseq = 0
        return timeseq

class MaildirFolder(BaseFolder):
    def __init__(self, root, name):
        self.name = name
        self.root = root
        self.sep = '.'
        self.uidfilename = os.path.join(self.getfullname(), "offlineimap.uidvalidity")
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
        file.write("%d\n" % newval)
        file.close()

    def isuidvalidityok(self, remotefolder):
        myval = self.getuidvalidity()
        if myval != None:
            return myval == remotefolder.getuidvalidity()
        else:
            self.saveuidvalidity(remotefolder.getuidvalidity())
            return 1
            
    def _scanfolder(self):
        """Cache the message list.  Maildir flags are:
        R (replied)
        S (seen)
        T (trashed)
        D (draft)
        F (flagged)
        and must occur in ASCII order."""
        retval = {}
        files = []
        nouidcounter = -1               # Messages without UIDs get
                                        # negative UID numbers.
        for dirannex in ['new', 'cur']:
            fulldirname = os.path.join(self.getfullname(), dirannex)
            files.extend([os.path.join(fulldirname, filename) for
                          filename in os.listdir(fulldirname)])
        for file in files:
            messagename = os.path.basename(file)
            foldermatch = foldermatchre.search(messagename)
            if (not foldermatch) or \
               md5.new(self.getvisiblename()).hexdigest() \
               != foldermatch.group(1):
                # If there is no folder MD5 specified, or if it mismatches,
                # assume it is a foreign (new) message and generate a
                # negative uid for it
                uid = nouidcounter
                nouidcounter -= 1
            else:                       # It comes from our folder.
                uidmatch = uidmatchre.search(messagename)
                uid = None
                if not uidmatch:
                    uid = nouidcounter
                    nouidcounter -= 1
                else:
                    uid = long(uidmatch.group(1))
            flagmatch = flagmatchre.search(messagename)
            flags = []
            if flagmatch:
                flags = [x for x in flagmatch.group(1)]
            flags.sort()
            if 'T' in flags:
                # Message is marked for deletion; just delete it now.
                # Otherwise, the T flag will be propogated to the IMAP
                # server, and then expunged there, and then deleted here.
                # Might as well just delete it now, to help make things
                # more robust.
                os.unlink(file)
            else:
                retval[uid] = {'uid': uid,
                               'flags': flags,
                               'filename': file}
        return retval

    def cachemessagelist(self):
        self.messagelist = self._scanfolder()
            
    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        filename = self.messagelist[uid]['filename']
        file = open(filename, 'rt')
        retval = file.read()
        file.close()
        return retval.replace("\r\n", "\n")

    def savemessage(self, uid, content, flags):
        if uid < 0:
            # We cannot assign a new uid.
            return uid
        if uid in self.messagelist:
            # We already have it.
            self.savemessageflags(uid, flags)
            return uid
        if 'S' in flags:
            # If a message has been seen, it goes into the cur
            # directory.  CR debian#152482, [complete.org #4]
            newdir = os.path.join(self.getfullname(), 'cur')
        else:
            newdir = os.path.join(self.getfullname(), 'new')
        tmpdir = os.path.join(self.getfullname(), 'tmp')
        messagename = None
        attempts = 0
        while 1:
            if attempts > 15:
                raise IOError, "Couldn't write to file %s" % messagename
            messagename = '%d_%d.%d.%s,U=%d,FMD5=%s' % \
                          (long(time.time()),
                           gettimeseq(),
                           os.getpid(),
                           socket.gethostname(),
                           uid,
                           md5.new(self.getvisiblename()).hexdigest())
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
        self.savemessageflags(uid, flags)
        return uid
        
    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def savemessageflags(self, uid, flags):
        oldfilename = self.messagelist[uid]['filename']
        newpath, newname = os.path.split(oldfilename)
        infostr = ':'
        infomatch = re.search('(:.*)$', newname)
        if infomatch:                   # If the info string is present..
            infostr = infomatch.group(1)
            newname = newname.split(':')[0] # Strip off the info string.
        infostr = re.sub('2,[A-Z]*', '', infostr)
        flags.sort()
        infostr += '2,' + ''.join(flags)
        newname += infostr
        
        newfilename = os.path.join(newpath, newname)
        if (newfilename != oldfilename):
            os.rename(oldfilename, newfilename)
            self.messagelist[uid]['flags'] = flags
            self.messagelist[uid]['filename'] = newfilename

    def deletemessage(self, uid):
        if not uid in self.messagelist:
            return
        filename = self.messagelist[uid]['filename']
        try:
            os.unlink(filename)
        except IOError:
            # Can't find the file -- maybe already deleted?
            newmsglist = self._scanfolder()
            if uid in newmsglist:       # Nope, try new filename.
                os.unlink(newmsglist[uid]['filename'])
            # Yep -- return.
        del(self.messagelist[uid])
        
