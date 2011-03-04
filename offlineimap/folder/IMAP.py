# IMAP folder support
# Copyright (C) 2002-2007 John Goerzen
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

import imaplib
import rfc822
import random
import binascii
import re
import time
from StringIO import StringIO
from copy import copy
from Base import BaseFolder
from offlineimap import imaputil, imaplibutil

class IMAPFolder(BaseFolder):
    def __init__(self, imapserver, name, visiblename, accountname, repository):
        self.config = imapserver.config
        self.expunge = repository.getexpunge()
        self.name = imaputil.dequote(name)
        self.root = None # imapserver.root
        self.sep = imapserver.delim
        self.imapserver = imapserver
        self.messagelist = None
        self.visiblename = visiblename
        self.accountname = accountname
        self.repository = repository
        self.randomgenerator = random.Random()
        BaseFolder.__init__(self)
        #self.ui is set in BaseFolder

    def selectro(self, imapobj):
        """Select this folder when we do not need write access.
        Prefer SELECT to EXAMINE if we can, since some servers
        (Courier) do not stabilize UID validity until the folder is
        selected."""
        try:
            imapobj.select(self.getfullname())
        except imapobj.readonly:
            imapobj.select(self.getfullname(), readonly = 1)

    def getaccountname(self):
        return self.accountname

    def suggeststhreads(self):
        return 1

    def waitforthread(self):
        self.imapserver.connectionwait()

    def getcopyinstancelimit(self):
        return 'MSGCOPY_' + self.repository.getname()

    def getvisiblename(self):
        return self.visiblename

    def getuidvalidity(self):
        imapobj = self.imapserver.acquireconnection()
        try:
            # Primes untagged_responses
            self.selectro(imapobj)
            return long(imapobj.untagged_responses['UIDVALIDITY'][0])
        finally:
            self.imapserver.releaseconnection(imapobj)
    
    def quickchanged(self, statusfolder):
        # An IMAP folder has definitely changed if the number of
        # messages or the UID of the last message have changed.  Otherwise
        # only flag changes could have occurred.
        imapobj = self.imapserver.acquireconnection()
        try:
            # Primes untagged_responses
            imapobj.select(self.getfullname(), readonly = 1, force = 1)
            try:
                # 1. Some mail servers do not return an EXISTS response
                # if the folder is empty.  2. ZIMBRA servers can return
                # multiple EXISTS replies in the form 500, 1000, 1500,
                # 1623 so check for potentially multiple replies.
                maxmsgid = 0
                for msgid in imapobj.untagged_responses['EXISTS']:
                    maxmsgid = max(long(msgid), maxmsgid)
            except KeyError:
                return True

            # Different number of messages than last time?
            if maxmsgid != len(statusfolder.getmessagelist()):
                return True

            if maxmsgid < 1:
                # No messages; return
                return False

            # Now, get the UID for the last message.
            response = imapobj.fetch('%d' % maxmsgid, '(UID)')[1]
        finally:
            self.imapserver.releaseconnection(imapobj)

        # Discard the message number.
        messagestr = response[0].split(' ', 1)[1]
        options = imaputil.flags2hash(messagestr)
        if not options.has_key('UID'):
            return True
        uid = long(options['UID'])
        saveduids = statusfolder.getmessagelist().keys()
        saveduids.sort()
        if uid != saveduids[-1]:
            return True

        return False

    # TODO: Make this so that it can define a date that would be the oldest messages etc.
    def cachemessagelist(self):
        imapobj = self.imapserver.acquireconnection()
        self.messagelist = {}

        try:
            # Primes untagged_responses
            imapobj.select(self.getfullname(), readonly = 1, force = 1)

            maxage = self.config.getdefaultint("Account " + self.accountname, "maxage", -1)
            maxsize = self.config.getdefaultint("Account " + self.accountname, "maxsize", -1)

            if (maxage != -1) | (maxsize != -1):
                try:
                    search_condition = "(";

                    if(maxage != -1):
                        #find out what the oldest message is that we should look at
                        oldest_time_struct = time.gmtime(time.time() - (60*60*24*maxage))

                        #format this manually - otherwise locales could cause problems
                        monthnames_standard = ["Jan", "Feb", "Mar", "Apr", "May", \
                            "June", "July", "Aug", "Sep", "Oct", "Nov", "Dec"]

                        our_monthname = monthnames_standard[oldest_time_struct[1]-1]
                        daystr = "%(day)02d" % {'day' : oldest_time_struct[2]}
                        date_search_str = "SINCE " + daystr + "-" + our_monthname \
                            + "-" + str(oldest_time_struct[0])

                        search_condition += date_search_str

                    if(maxsize != -1):
                        if(maxage != 1): #There are two conditions - add a space
                            search_condition += " "

                        search_condition += "SMALLER " + self.config.getdefault("Account " + self.accountname, "maxsize", -1)

                    search_condition += ")"
                    searchresult = imapobj.search(None, search_condition)

                    #result would come back seperated by space - to change into a fetch
                    #statement we need to change space to comma
                    messagesToFetch = searchresult[1][0].replace(" ", ",")
                except KeyError:
                    return
                if len(messagesToFetch) < 1:
                    # No messages; return
                    return
            else:
                try:
                    # 1. Some mail servers do not return an EXISTS response
                    # if the folder is empty.  2. ZIMBRA servers can return
                    # multiple EXISTS replies in the form 500, 1000, 1500,
                    # 1623 so check for potentially multiple replies.
                    maxmsgid = 0
                    for msgid in imapobj.untagged_responses['EXISTS']:
                        maxmsgid = max(long(msgid), maxmsgid)
                    messagesToFetch = '1:%d' % maxmsgid;
                except KeyError:
                    return
                if maxmsgid < 1:
                    #no messages; return
                    return
            # Now, get the flags and UIDs for these.
            # We could conceivably get rid of maxmsgid and just say
            # '1:*' here.
            response = imapobj.fetch(messagesToFetch, '(FLAGS UID)')[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        for messagestr in response:
            # Discard the message number.
            messagestr = messagestr.split(' ', 1)[1]
            options = imaputil.flags2hash(messagestr)
            if not options.has_key('UID'):
                self.ui.warn('No UID in message with options %s' %\
                                          str(options),
                                          minor = 1)
            else:
                uid = long(options['UID'])
                flags = imaputil.flagsimap2maildir(options['FLAGS'])
                rtime = imaplibutil.Internaldate2epoch(messagestr)
                self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime}

    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        imapobj = self.imapserver.acquireconnection()
        try:
            imapobj.select(self.getfullname(), readonly = 1)
            initialresult = imapobj.uid('fetch', '%d' % uid, '(BODY.PEEK[])')
            self.ui.debug('imap', 'Returned object from fetching %d: %s' % \
                     (uid, str(initialresult)))
            return initialresult[1][0][1].replace("\r\n", "\n")
                
        finally:
            self.imapserver.releaseconnection(imapobj)

    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']
    
    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def generate_randomheader(self, content):
        """Returns a unique X-OfflineIMAP header

         Generate an 'X-OfflineIMAP' mail header which contains a random
         unique value (which is based on the mail content, and a random
         number). This header allows us to fetch a mail after APPENDing
         it to an IMAP server and thus find out the UID that the server
         assigned it.

        :returns: (headername, headervalue) tuple, consisting of strings
                  headername == 'X-OfflineIMAP' and headervalue will be a
                  random string
        """
        headername = 'X-OfflineIMAP'
        # We need a random component too. If we ever upload the same
        # mail twice (e.g. in different folders), we would still need to
        # get the UID for the correct one. As we won't have too many
        # mails with identical content, the randomness requirements are
        # not extremly critial though.

        # compute unsigned crc32 of 'content' as unique hash
        # NB: crc32 returns unsigned only starting with python 3.0
        headervalue  = str( binascii.crc32(content) & 0xffffffff ) + '-'
        headervalue += str(self.randomgenerator.randint(0,9999999999))
        return (headername, headervalue)

    def savemessage_addheader(self, content, headername, headervalue):
        self.ui.debug('imap',
                 'savemessage_addheader: called to add %s: %s' % (headername,
                                                                  headervalue))
        insertionpoint = content.find("\r\n")
        self.ui.debug('imap', 'savemessage_addheader: insertionpoint = %d' % insertionpoint)
        leader = content[0:insertionpoint]
        self.ui.debug('imap', 'savemessage_addheader: leader = %s' % repr(leader))
        if insertionpoint == 0 or insertionpoint == -1:
            newline = ''
            insertionpoint = 0
        else:
            newline = "\r\n"
        newline += "%s: %s" % (headername, headervalue)
        self.ui.debug('imap', 'savemessage_addheader: newline = ' + repr(newline))
        trailer = content[insertionpoint:]
        self.ui.debug('imap', 'savemessage_addheader: trailer = ' + repr(trailer))
        return leader + newline + trailer

    def savemessage_searchforheader(self, imapobj, headername, headervalue):
        if imapobj.untagged_responses.has_key('APPENDUID'):
            return long(imapobj.untagged_responses['APPENDUID'][-1].split(' ')[1])

        self.ui.debug('imap', 'savemessage_searchforheader called for %s: %s' % \
                 (headername, headervalue))
        # Now find the UID it got.
        headervalue = imapobj._quote(headervalue)
        try:
            matchinguids = imapobj.uid('search', 'HEADER', headername, headervalue)[1][0]
        except imapobj.error, err:
            # IMAP server doesn't implement search or had a problem.
            self.ui.debug('imap', "savemessage_searchforheader: got IMAP error '%s' while attempting to UID SEARCH for message with header %s" % (err, headername))
            return 0
        self.ui.debug('imap', 'savemessage_searchforheader got initial matchinguids: ' + repr(matchinguids))

        if matchinguids == '':
            self.ui.debug('imap', "savemessage_searchforheader: UID SEARCH for message with header %s yielded no results" % headername)
            return 0

        matchinguids = matchinguids.split(' ')
        self.ui.debug('imap', 'savemessage_searchforheader: matchinguids now ' + \
                 repr(matchinguids))
        if len(matchinguids) != 1 or matchinguids[0] == None:
            raise ValueError, "While attempting to find UID for message with header %s, got wrong-sized matchinguids of %s" % (headername, str(matchinguids))
        matchinguids.sort()
        return long(matchinguids[0])

    def savemessage(self, uid, content, flags, rtime):
        imapobj = self.imapserver.acquireconnection()
        self.ui.debug('imap', 'savemessage: called')
        try:
            try:
                imapobj.select(self.getfullname()) # Needed for search
            except imapobj.readonly:
                self.ui.msgtoreadonly(self, uid, content, flags)
                # Return indicating message taken, but no UID assigned.
                # Fudge it.
                return 0
            
            # This backend always assigns a new uid, so the uid arg is ignored.
            # In order to get the new uid, we need to save off the message ID.

            message = rfc822.Message(StringIO(content))
            datetuple_msg = rfc822.parsedate(message.getheader('Date'))
            # Will be None if missing or not in a valid format.

            # If time isn't known
            if rtime == None and datetuple_msg == None:
                datetuple = time.localtime()
            elif rtime == None:
                datetuple = datetuple_msg
            else:
                datetuple = time.localtime(rtime)

            try:
                if datetuple[0] < 1981:
                    raise ValueError

                # Check for invalid date
                datetuple_check = time.localtime(time.mktime(datetuple))
                if datetuple[:2] != datetuple_check[:2]:
                    raise ValueError

                # This could raise a value error if it's not a valid format.
                date = imaplib.Time2Internaldate(datetuple) 
            except (ValueError, OverflowError):
                # Argh, sometimes it's a valid format but year is 0102
                # or something.  Argh.  It seems that Time2Internaldate
                # will rause a ValueError if the year is 0102 but not 1902,
                # but some IMAP servers nonetheless choke on 1902.
                date = imaplib.Time2Internaldate(time.localtime())

            self.ui.debug('imap', 'savemessage: using date ' + str(date))
            content = re.sub("(?<!\r)\n", "\r\n", content)
            self.ui.debug('imap', 'savemessage: initial content is: ' + repr(content))

            (headername, headervalue) = self.generate_randomheader(content)
            ui.debug('imap', 'savemessage: new headers are: %s: %s' % \
                     (headername, headervalue))
            content = self.savemessage_addheader(content, headername,
                                                 headervalue)
            self.ui.debug('imap', 'savemessage: new content is: ' + repr(content))
            self.ui.debug('imap', 'savemessage: new content length is ' + \
                     str(len(content)))

            assert(imapobj.append(self.getfullname(),
                                       imaputil.flagsmaildir2imap(flags),
                                       date, content)[0] == 'OK')

            # Checkpoint.  Let it write out the messages, etc.
            assert(imapobj.check()[0] == 'OK')

            # Keep trying until we get the UID.
            self.ui.debug('imap', 'savemessage: first attempt to get new UID')
            uid = self.savemessage_searchforheader(imapobj, headername,
                                                   headervalue)
            # See docs for savemessage in Base.py for explanation of this and other return values
            if uid <= 0:
                self.ui.debug('imap', 'savemessage: first attempt to get new UID failed.  Going to run a NOOP and try again.')
                assert(imapobj.noop()[0] == 'OK')
                uid = self.savemessage_searchforheader(imapobj, headername,
                                                       headervalue)
        finally:
            self.imapserver.releaseconnection(imapobj)

        if uid: # avoid UID FETCH 0 crash happening later on
            self.messagelist[uid] = {'uid': uid, 'flags': flags}

        self.ui.debug('imap', 'savemessage: returning %d' % uid)
        return uid

    def savemessageflags(self, uid, flags):
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.flagstoreadonly(self, [uid], flags)
                return
            result = imapobj.uid('store', '%d' % uid, 'FLAGS',
                                 imaputil.flagsmaildir2imap(flags))
            assert result[0] == 'OK', 'Error with store: ' + '. '.join(r[1])
        finally:
            self.imapserver.releaseconnection(imapobj)
        result = result[1][0]
        if not result:
            self.messagelist[uid]['flags'] = flags
        else:
            flags = imaputil.flags2hash(imaputil.imapsplit(result)[1])['FLAGS']
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)

    def addmessageflags(self, uid, flags):
        self.addmessagesflags([uid], flags)

    def addmessagesflags_noconvert(self, uidlist, flags):
        self.processmessagesflags('+', uidlist, flags)

    def addmessagesflags(self, uidlist, flags):
        """This is here for the sake of UIDMaps.py -- deletemessages must
        add flags and get a converted UID, and if we don't have noconvert,
        then UIDMaps will try to convert it twice."""
        self.addmessagesflags_noconvert(uidlist, flags)

    def deletemessageflags(self, uid, flags):
        self.deletemessagesflags([uid], flags)

    def deletemessagesflags(self, uidlist, flags):
        self.processmessagesflags('-', uidlist, flags)

    def processmessagesflags(self, operation, uidlist, flags):
        if len(uidlist) > 101:
            # Hack for those IMAP ervers with a limited line length
            self.processmessagesflags(operation, uidlist[:100], flags)
            self.processmessagesflags(operation, uidlist[100:], flags)
            return
        
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.flagstoreadonly(self, uidlist, flags)
                return
            r = imapobj.uid('store',
                            imaputil.listjoin(uidlist),
                            operation + 'FLAGS',
                            imaputil.flagsmaildir2imap(flags))
            assert r[0] == 'OK', 'Error with store: ' + '. '.join(r[1])
            r = r[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        # Some IMAP servers do not always return a result.  Therefore,
        # only update the ones that it talks about, and manually fix
        # the others.
        needupdate = copy(uidlist)
        for result in r:
            if result == None:
                # Compensate for servers that don't return anything from
                # STORE.
                continue
            attributehash = imaputil.flags2hash(imaputil.imapsplit(result)[1])
            if not ('UID' in attributehash and 'FLAGS' in attributehash):
                # Compensate for servers that don't return a UID attribute.
                continue
            lflags = attributehash['FLAGS']
            uid = long(attributehash['UID'])
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(lflags)
            try:
                needupdate.remove(uid)
            except ValueError:          # Let it slide if it's not in the list
                pass
        for uid in needupdate:
            if operation == '+':
                for flag in flags:
                    if not flag in self.messagelist[uid]['flags']:
                        self.messagelist[uid]['flags'].append(flag)
                    self.messagelist[uid]['flags'].sort()
            elif operation == '-':
                for flag in flags:
                    if flag in self.messagelist[uid]['flags']:
                        self.messagelist[uid]['flags'].remove(flag)

    def deletemessage(self, uid):
        self.deletemessages_noconvert([uid])

    def deletemessages(self, uidlist):
        self.deletemessages_noconvert(uidlist)

    def deletemessages_noconvert(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return        

        self.addmessagesflags_noconvert(uidlist, ['T'])
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.deletereadonly(self, uidlist)
                return
            if self.expunge:
                assert(imapobj.expunge()[0] == 'OK')
        finally:
            self.imapserver.releaseconnection(imapobj)
        for uid in uidlist:
            del self.messagelist[uid]
        
        
