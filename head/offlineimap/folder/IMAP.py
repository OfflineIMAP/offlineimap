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
from imapsync import imaputil, imaplib
import rfc822
from StringIO import StringIO

class IMAPFolder(BaseFolder):
    def __init__(self, imapserver, name):
        self.name = imaputil.dequote(name)
        self.root = imapserver.root
        self.sep = imapserver.delim
        self.imapserver = imapserver
        self.imapobj = self.imapserver.makeconnection()
        self.messagelist = None

    def getuidvalidity(self):
        x = self.imapobj.status(self.getfullname(), ('UIDVALIDITY'))[1][0]
        uidstring = imaputil.imapsplit(x)[1]
        return long(imaputil.flagsplit(uidstring)[1])
    
    def cachemessagelist(self):
        assert(self.imapobj.select(self.getfullname())[0] == 'OK')
        self.messagelist = {}
        response = self.imapobj.status(self.getfullname(), ('MESSAGES'))[1][0]
        result = imaputil.imapsplit(response)[1]
        maxmsgid = long(imaputil.flags2hash(result)['MESSAGES'])
        if (maxmsgid < 1):
            # No messages?  return.
            return

        # Now, get the flags and UIDs for these.
        response = self.imapobj.fetch('1:%d' % maxmsgid, '(FLAGS UID)')[1]
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
        print "***************** GETMESSAGE %d" % uid
        assert(self.imapobj.select(self.getfullname())[0] == 'OK')
        return self.imapobj.uid('fetch', '%d' % uid, '(RFC822)')[1][0][1].replace("\r\n", "\n")
    
    def getmessageflags(self, uid):
        return self.getmessagelist()[uid]['flags']
    
    def savemessage(self, uid, content, flags):
        # This backend always assigns a new uid, so the uid arg is ignored.

        # In order to get the new uid, we need to save off the message ID.

        message = rfc822.Message(StringIO(content))
        mid = self.imapobj._quote(message.getheader('Message-Id'))
        date = imaplib.Time2Internaldate(rfc822.parsedate(message.getheader('Date')))

        if content.find("\r\n") == -1:  # Convert line endings if not already
            content = content.replace("\n", "\r\n")

        assert(self.imapobj.append(self.getfullname(),
                                   imaputil.flagsmaildir2imap(flags),
                                   date, content)[0] == 'OK')
        
        # Now find the UID it got.
        matchinguids = self.imapobj.uid('search', None,
                                        '(HEADER Message-Id %s)' % mid)[1][0]
        matchinguids = matchinguids.split(' ')
        matchinguids.sort()
        uid = long(matchinguids[-1])
        self.messagelist[uid] = {'uid': uid, 'flags': flags}
        return uid

    def savemessageflags(self, uid, flags):
        assert(self.imapobj.select(self.getfullname())[0] == 'OK')
        result = self.imapobj.uid('store', '%d' % uid, 'FLAGS',
                                  imaputil.flagsmaildir2imap(flags))[1][0]
        flags = imaputil.flags2hash(imaputil.imapsplit(result)[1])['FLAGS']
        self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)

    def deletemessage(self, uid):
        if not uid in self.messagelist:
            return
        self.addmessageflags(uid, ['T'])
        assert(self.imapobj.select(self.getfullname())[0] == 'OK')
        assert(self.imapobj.expunge()[0] == 'OK')
        del(self.messagelist[uid])
        
        
