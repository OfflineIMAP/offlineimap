# IMAP folder support
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
from offlineimap import imaputil, imaplib
import rfc822
from StringIO import StringIO

class IMAPFolder(BaseFolder):
    def __init__(self, imapserver, name, visiblename):
        self.name = imaputil.dequote(name)
        self.root = imapserver.root
        self.sep = imapserver.delim
        self.imapserver = imapserver
        self.messagelist = None
        self.visiblename = visiblename

    def suggeststhreads(self):
        return 1

    def waitforthread(self):
        self.imapserver.connectionwait()

    def getvisiblename(self):
        return self.visiblename

    def getuidvalidity(self):
        imapobj = self.imapserver.acquireconnection()
        try:
            x = imapobj.status(self.getfullname(), '(UIDVALIDITY)')[1][0]
        finally:
            self.imapserver.releaseconnection(imapobj)
        uidstring = imaputil.imapsplit(x)[1]
        return long(imaputil.flagsplit(uidstring)[1])
    
    def cachemessagelist(self):
        imapobj = self.imapserver.acquireconnection()
        try:
            imapobj.select(self.getfullname())
            self.messagelist = {}
            response = self.imapobj.status(self.getfullname(), '(MESSAGES)')[1][0]
            result = imaputil.imapsplit(response)[1]
            maxmsgid = long(imaputil.flags2hash(result)['MESSAGES'])
            if (maxmsgid < 1):
                # No messages?  return.
                return

            # Now, get the flags and UIDs for these.
            response = imapobj.fetch('1:%d' % maxmsgid, '(FLAGS UID)')[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        for messagestr in response:
            # Discard the message number.
            messagestr = imaputil.imapsplit(messagestr)[1]
            options = imaputil.flags2hash(messagestr)
            uid = long(options['UID'])
            flags = imaputil.flagsimap2maildir(options['FLAGS'])
            self.messagelist[uid] = {'uid': uid, 'flags': flags}

    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        imapobj = self.imapserver.acquireconnection()
        try:
            imapobj.select(self.getfullname())
            return imapobj.uid('fetch', '%d' % uid, '(BODY.PEEK[])')[1][0][1].replace("\r\n", "\n")
        finally:
            self.imapserver.releaseconnection(imapobj)
    
    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']
    
    def savemessage(self, uid, content, flags):
        imapobj = self.imapserver.acquireconnection()
        try:
            # This backend always assigns a new uid, so the uid arg is ignored.
            # In order to get the new uid, we need to save off the message ID.

            message = rfc822.Message(StringIO(content))
            mid = imapobj._quote(message.getheader('Message-Id'))
            date = imaplib.Time2Internaldate(rfc822.parsedate(message.getheader('Date')))

            if content.find("\r\n") == -1:  # Convert line endings if not already
                content = content.replace("\n", "\r\n")

            assert(imapobj.append(self.getfullname(),
                                       imaputil.flagsmaildir2imap(flags),
                                       date, content)[0] == 'OK')
            # Checkpoint.  Let it write out the messages, etc.
            assert(imapobj.check()[0] == 'OK')
            # Now find the UID it got.
            matchinguids = imapobj.uid('search', None,
                                       '(HEADER Message-Id %s)' % mid)[1][0]
            matchinguids = matchinguids.split(' ')
            matchinguids.sort()
            uid = long(matchinguids[-1])
            self.messagelist[uid] = {'uid': uid, 'flags': flags}
            return uid
        finally:
            self.imapserver.releaseconnection(imapobj)

    def savemessageflags(self, uid, flags):
        imapobj = self.imapserver.acquireconnection(imapobj)
        try:
            imapobj.select(self.getfullname())
            result = imapobj.uid('store', '%d' % uid, 'FLAGS',
                                 imaputil.flagsmaildir2imap(flags))[1][0]
        finally:
            self.imapserver.releaseconnection(imapobj)
        flags = imaputil.flags2hash(imaputil.imapsplit(result)[1])['FLAGS']
        self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)

    def addmessagesflags(self, uidlist, flags):
        imapobj = self.imapserver.acquireconnection(imapobj)
        try:
            imapobj.select(self.getfullname())
            r = imapobj.uid('store',
                            ','.join([str(uid) for uid in uidlist]),
                            '+FLAGS',
                            imaputil.flagsmaildir2imap(flags))[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        resultcount = 0
        for result in r:
            resultcount += 1
            flags = imaputil.flags2hash(imaputil.imapsplit(result)[1])['FLAGS']
            uid = long(imaputil.flags2hash(imaputil.imapsplit(result)[1])['UID'])
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)
        assert resultcount == len(uidlist), "Got incorrect number of results back"

    def deletemessage(self, uid):
        self.deletemessages([uid])

    def deletemessages(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return        

        self.addmessagesflags(uidlist, ['T'])
        imapobj = self.imapserver.acquireconnection()
        try:
            imapobj.select(self.getfullname())
            assert(imapobj.expunge()[0] == 'OK')
        finally:
            self.imapserver.releaseconnection(imapobj)
        for uid in uidlist:
            del(self.messagelist[uid])
        
        
