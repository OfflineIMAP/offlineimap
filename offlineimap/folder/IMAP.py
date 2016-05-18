# IMAP folder support
# Copyright (C) 2002-2012 John Goerzen & contributors
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

import random
import binascii
import re
import os
import time
from sys import exc_info

from .Base import BaseFolder
from offlineimap import imaputil, imaplibutil, emailutil, OfflineImapError
from offlineimap import globals
from offlineimap.imaplib2 import MonthNames

import six


# Globals
CRLF = '\r\n'
MSGCOPY_NAMESPACE = 'MSGCOPY_'


# NB: message returned from getmessage() will have '\n' all over the place,
# NB: there will be no CRLFs.  Just before the sending stage of savemessage()
# NB: '\n' will be transformed back to CRLF.  So, for the most parts of the
# NB: code the stored content will be clean of CRLF and one can rely that
# NB: line endings will be pure '\n'.


class IMAPFolder(BaseFolder):
    def __init__(self, imapserver, name, repository):
        # FIXME: decide if unquoted name is from the responsability of the
        # caller or not, but not both.
        name = imaputil.dequote(name)
        self.sep = imapserver.delim
        super(IMAPFolder, self).__init__(name, repository)
        self.expunge = repository.getexpunge()
        self.root = None # imapserver.root
        self.imapserver = imapserver
        self.randomgenerator = random.Random()
        #self.ui is set in BaseFolder
        self.imap_query = ['BODY.PEEK[]']

        fh_conf = self.repository.account.getconf('filterheaders', '')
        self.filterheaders = [h for h in re.split(r'\s*,\s*', fh_conf) if h]


    def __selectro(self, imapobj, force=False):
        """Select this folder when we do not need write access.

        Prefer SELECT to EXAMINE if we can, since some servers
        (Courier) do not stabilize UID validity until the folder is
        selected.
        .. todo: Still valid? Needs verification
        :param: Enforce new SELECT even if we are on that folder already.
        :returns: raises :exc:`OfflineImapError` severity FOLDER on error"""
        try:
            imapobj.select(self.getfullname(), force = force)
        except imapobj.readonly:
            imapobj.select(self.getfullname(), readonly = True, force = force)

    # Interface from BaseFolder
    def suggeststhreads(self):
        return not globals.options.singlethreading

    # Interface from BaseFolder
    def waitforthread(self):
        self.imapserver.connectionwait()

    def getmaxage(self):
        if self.config.getdefault("Account %s"%
                self.accountname, "maxage", None):
            six.reraise(OfflineImapError("maxage is not supported on IMAP-IMAP sync",
                OfflineImapError.ERROR.REPO), None, exc_info()[2])

    # Interface from BaseFolder
    def getinstancelimitnamespace(self):
        return MSGCOPY_NAMESPACE + self.repository.getname()

    # Interface from BaseFolder
    def get_uidvalidity(self):
        """Retrieve the current connections UIDVALIDITY value

        UIDVALIDITY value will be cached on the first call.
        :returns: The UIDVALIDITY as (long) number."""

        if hasattr(self, '_uidvalidity'):
            # use cached value if existing
            return self._uidvalidity
        imapobj = self.imapserver.acquireconnection()
        try:
            # SELECT (if not already done) and get current UIDVALIDITY
            self.__selectro(imapobj)
            typ, uidval = imapobj.response('UIDVALIDITY')
            assert uidval != [None] and uidval != None, \
                "response('UIDVALIDITY') returned [None]!"
            self._uidvalidity = int(uidval[-1])
            return self._uidvalidity
        finally:
            self.imapserver.releaseconnection(imapobj)

    # Interface from BaseFolder
    def quickchanged(self, statusfolder):
        # An IMAP folder has definitely changed if the number of
        # messages or the UID of the last message have changed.  Otherwise
        # only flag changes could have occurred.
        retry = True # Should we attempt another round or exit?
        while retry:
            retry = False
            imapobj = self.imapserver.acquireconnection()
            try:
                # Select folder and get number of messages
                restype, imapdata = imapobj.select(self.getfullname(), True,
                                                   True)
                self.imapserver.releaseconnection(imapobj)
            except OfflineImapError as e:
                # retry on dropped connections, raise otherwise
                self.imapserver.releaseconnection(imapobj, True)
                if e.severity == OfflineImapError.ERROR.FOLDER_RETRY:
                    retry = True
                else: raise
            except:
                # cleanup and raise on all other errors
                self.imapserver.releaseconnection(imapobj, True)
                raise
        # 1. Some mail servers do not return an EXISTS response
        # if the folder is empty.  2. ZIMBRA servers can return
        # multiple EXISTS replies in the form 500, 1000, 1500,
        # 1623 so check for potentially multiple replies.
        if imapdata == [None]:
            return True
        maxmsgid = 0
        for msgid in imapdata:
            maxmsgid = max(int(msgid), maxmsgid)
        # Different number of messages than last time?
        if maxmsgid != statusfolder.getmessagecount():
            return True
        return False

    def _msgs_to_fetch(self, imapobj, min_date=None, min_uid=None):
        """Determines sequence numbers of messages to be fetched.

        Message sequence numbers (MSNs) are more easily compacted
        into ranges which makes transactions slightly faster.

        Arguments:
        - imapobj: instance of IMAPlib
        - min_date (optional): a time_struct; only fetch messages newer than this
        - min_uid (optional): only fetch messages with UID >= min_uid

        This function should be called with at MOST one of min_date OR
        min_uid set but not BOTH.

        Returns: range(s) for messages or None if no messages
        are to be fetched."""

        def search(search_conditions):
            """Actually request the server with the specified conditions.

            Returns: range(s) for messages or None if no messages
            are to be fetched."""
            res_type, res_data = imapobj.search(None, search_conditions)
            if res_type != 'OK':
                raise OfflineImapError("SEARCH in folder [%s]%s failed. "
                    "Search string was '%s'. Server responded '[%s] %s'"% (
                    self.getrepository(), self, search_cond, res_type, res_data),
                    OfflineImapError.ERROR.FOLDER)
            # Davmail returns list instead of list of one element string.
            # On first run the first element is empty.
            if ' ' in res_data[0] or res_data[0] == '':
                res_data = res_data[0].split()
            return res_data

        res_type, imapdata = imapobj.select(self.getfullname(), True, True)
        if imapdata == [None] or imapdata[0] == '0':
            # Empty folder, no need to populate message list.
            return None

        conditions = []
        # 1. min_uid condition.
        if min_uid != None:
            conditions.append("UID %d:*"% min_uid)
        # 2. date condition.
        elif min_date != None:
            # Find out what the oldest message is that we should look at.
            conditions.append("SINCE %02d-%s-%d"% (
                min_date[2], MonthNames[min_date[1]], min_date[0]))
        # 3. maxsize condition.
        maxsize = self.getmaxsize()
        if maxsize != None:
            conditions.append("SMALLER %d"% maxsize)

        if len(conditions) >= 1:
            # Build SEARCH command.
            search_cond = "(%s)"% ' '.join(conditions)
            search_result = search(search_cond)
            return imaputil.uid_sequence(search_result)

        # By default consider all messages in this folder.
        return '1:*'

    # Interface from BaseFolder
    def msglist_item_initializer(self, uid):
        return {'uid': uid, 'flags': set(), 'time': 0}


    # Interface from BaseFolder
    def cachemessagelist(self, min_date=None, min_uid=None):
        self.ui.loadmessagelist(self.repository, self)
        self.dropmessagelistcache()

        imapobj = self.imapserver.acquireconnection()
        try:
            msgsToFetch = self._msgs_to_fetch(
                imapobj, min_date=min_date, min_uid=min_uid)
            if not msgsToFetch:
                return # No messages to sync

            # Get the flags and UIDs for these. single-quotes prevent
            # imaplib2 from quoting the sequence.
            res_type, response = imapobj.fetch("'%s'"%
                msgsToFetch, '(FLAGS UID INTERNALDATE)')
            if res_type != 'OK':
                raise OfflineImapError("FETCHING UIDs in folder [%s]%s failed. "
                    "Server responded '[%s] %s'"% (self.getrepository(), self,
                    res_type, response), OfflineImapError.ERROR.FOLDER)
        finally:
            self.imapserver.releaseconnection(imapobj)

        for messagestr in response:
            # looks like: '1 (FLAGS (\\Seen Old) UID 4807)' or None if no msg
            # Discard initial message number.
            if messagestr == None:
                continue
            messagestr = messagestr.split(' ', 1)[1]
            options = imaputil.flags2hash(messagestr)
            if not 'UID' in options:
                self.ui.warn('No UID in message with options %s'% \
                                          str(options),
                                          minor = 1)
            else:
                uid = int(options['UID'])
                self.messagelist[uid] = self.msglist_item_initializer(uid)
                flags = imaputil.flagsimap2maildir(options['FLAGS'])
                keywords = imaputil.flagsimap2keywords(options['FLAGS'])
                rtime = imaplibutil.Internaldate2epoch(messagestr)
                self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime,
                    'keywords': keywords}
        self.ui.messagelistloaded(self.repository, self, self.getmessagecount())

    # Interface from BaseFolder
    def getvisiblename(self):
        vname = super(IMAPFolder, self).getvisiblename()
        if self.repository.getdecodefoldernames():
            return imaputil.decode_mailbox_name(vname)
        return vname

    # Interface from BaseFolder
    def getmessage(self, uid):
        """Retrieve message with UID from the IMAP server (incl body).

        After this function all CRLFs will be transformed to '\n'.

        :returns: the message body or throws and OfflineImapError
                  (probably severity MESSAGE) if e.g. no message with
                  this UID could be found.
        """

        data = self._fetch_from_imap(str(uid), 2)

        # data looks now e.g. [('320 (UID 17061 BODY[]
        # {2565}','msgbody....')]  we only asked for one message,
        # and that msg is in data[0]. msbody is in [0][1]
        data = data[0][1].replace(CRLF, "\n")

        if len(data)>200:
            dbg_output = "%s...%s"% (str(data)[:150], str(data)[-50:])
        else:
            dbg_output = data

        self.ui.debug('imap', "Returned object from fetching %d: '%s'"%
                      (uid, dbg_output))

        return data

    # Interface from BaseFolder
    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']

    # Interface from BaseFolder
    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    # Interface from BaseFolder
    def getmessagekeywords(self, uid):
        return self.messagelist[uid]['keywords']

    def __generate_randomheader(self, content):
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


    def __savemessage_searchforheader(self, imapobj, headername, headervalue):
        self.ui.debug('imap', '__savemessage_searchforheader called for %s: %s'% \
            (headername, headervalue))
        # Now find the UID it got.
        headervalue = imapobj._quote(headervalue)
        try:
            matchinguids = imapobj.uid('search', 'HEADER',
                headername, headervalue)[1][0]
        except imapobj.error as err:
            # IMAP server doesn't implement search or had a problem.
            self.ui.debug('imap', "__savemessage_searchforheader: got IMAP error '%s' while attempting to UID SEARCH for message with header %s"% (err, headername))
            return 0
        self.ui.debug('imap', '__savemessage_searchforheader got initial matchinguids: ' + repr(matchinguids))

        if matchinguids == '':
            self.ui.debug('imap', "__savemessage_searchforheader: UID SEARCH for message with header %s yielded no results"% headername)
            return 0

        matchinguids = matchinguids.split(' ')
        self.ui.debug('imap', '__savemessage_searchforheader: matchinguids now ' + \
                 repr(matchinguids))
        if len(matchinguids) != 1 or matchinguids[0] == None:
            raise ValueError("While attempting to find UID for message with "
                             "header %s, got wrong-sized matchinguids of %s"%\
                                 (headername, str(matchinguids)))
        return int(matchinguids[0])

    def __savemessage_fetchheaders(self, imapobj, headername, headervalue):
        """ We fetch all new mail headers and search for the right
        X-OfflineImap line by hand. The response from the server has form:
        (
          'OK',
          [
            (
              '185 (RFC822.HEADER {1789}',
              '... mail headers ...'
            ),
            ' UID 2444)',
            (
              '186 (RFC822.HEADER {1789}',
              '... 2nd mail headers ...'
            ),
            ' UID 2445)'
          ]
        )
        We need to locate the UID just after mail headers containing our
        X-OfflineIMAP line.

        Returns UID when found, 0 when not found."""

        self.ui.debug('imap', '__savemessage_fetchheaders called for %s: %s'% \
                 (headername, headervalue))

        # run "fetch X:* rfc822.header"
        # since we stored the mail we are looking for just recently, it would
        # not be optimal to fetch all messages. So we'll find highest message
        # UID in our local messagelist and search from there (exactly from
        # UID+1). That works because UIDs are guaranteed to be unique and
        # ascending.

        if self.getmessagelist():
            start = 1 + max(self.getmessagelist().keys())
        else:
            # Folder was empty - start from 1
            start = 1

        # Imaplib quotes all parameters of a string type. That must not happen
        # with the range X:*. So we use bytearray to stop imaplib from getting
        # in our way

        result = imapobj.uid('FETCH', bytearray('%d:*'% start), 'rfc822.header')
        if result[0] != 'OK':
            raise OfflineImapError('Error fetching mail headers: %s'%
                '. '.join(result[1]), OfflineImapError.ERROR.MESSAGE)

        result = result[1]

        found = 0
        for item in result:
            if found == 0 and type(item) == type( () ):
                # Walk just tuples
                if re.search("(?:^|\\r|\\n)%s:\s*%s(?:\\r|\\n)"% (headername, headervalue),
                        item[1], flags=re.IGNORECASE):
                    found = 1
            elif found == 1:
                if type(item) == type (""):
                    uid = re.search("UID\s+(\d+)", item, flags=re.IGNORECASE)
                    if uid:
                        return int(uid.group(1))
                    else:
                        self.ui.warn("Can't parse FETCH response, can't find UID: %s", result.__repr__())
                else:
                    self.ui.warn("Can't parse FETCH response, we awaited string: %s", result.__repr__())

        return 0

    def __getmessageinternaldate(self, content, rtime=None):
        """Parses mail and returns an INTERNALDATE string

        It will use information in the following order, falling back as an
        attempt fails:
          - rtime parameter
          - Date header of email

        We return None, if we couldn't find a valid date. In this case
        the IMAP server will use the server local time when appening
        (per RFC).

        Note, that imaplib's Time2Internaldate is inherently broken as
        it returns localized date strings which are invalid for IMAP
        servers. However, that function is called for *every* append()
        internally. So we need to either pass in `None` or the correct
        string (in which case Time2Internaldate() will do nothing) to
        append(). The output of this function is designed to work as
        input to the imapobj.append() function.

        TODO: We should probably be returning a bytearray rather than a
        string here, because the IMAP server will expect plain
        ASCII. However, imaplib.Time2INternaldate currently returns a
        string so we go with the same for now.

        :param rtime: epoch timestamp to be used rather than analyzing
                  the email.
        :returns: string in the form of "DD-Mmm-YYYY HH:MM:SS +HHMM"
                  (including double quotes) or `None` in case of failure
                  (which is fine as value for append)."""

        if rtime is None:
            rtime = emailutil.get_message_date(content)
            if rtime == None:
                return None
        datetuple = time.localtime(rtime)

        try:
            # Check for invalid dates
            if datetuple[0] < 1981:
                raise ValueError

            # Check for invalid dates
            datetuple_check = time.localtime(time.mktime(datetuple))
            if datetuple[:2] != datetuple_check[:2]:
                raise ValueError

        except (ValueError, OverflowError):
            # Argh, sometimes it's a valid format but year is 0102
            # or something.  Argh.  It seems that Time2Internaldate
            # will rause a ValueError if the year is 0102 but not 1902,
            # but some IMAP servers nonetheless choke on 1902.
            self.ui.debug('imap', "Message with invalid date %s. "
                "Server will use local time."% datetuple)
            return None

        # Produce a string representation of datetuple that works as
        # INTERNALDATE.
        num2mon = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
                   7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

        # tm_isdst coming from email.parsedate is not usable, we still use it
        # here, mhh.
        if datetuple.tm_isdst == 1:
            zone = -time.altzone
        else:
            zone = -time.timezone
        offset_h, offset_m = divmod(zone//60, 60)

        internaldate = '"%02d-%s-%04d %02d:%02d:%02d %+03d%02d"'% \
            (datetuple.tm_mday, num2mon[datetuple.tm_mon], datetuple.tm_year, \
             datetuple.tm_hour, datetuple.tm_min, datetuple.tm_sec, offset_h, offset_m)

        return internaldate

    # Interface from BaseFolder
    def savemessage(self, uid, content, flags, rtime):
        """Save the message on the Server

        This backend always assigns a new uid, so the uid arg is ignored.

        This function will update the self.messagelist dict to contain
        the new message after sucessfully saving it.

        See folder/Base for details. Note that savemessage() does not
        check against dryrun settings, so you need to ensure that
        savemessage is never called in a dryrun mode.

        :param rtime: A timestamp to be used as the mail date
        :returns: the UID of the new message as assigned by the server. If the
                  message is saved, but it's UID can not be found, it will
                  return 0. If the message can't be written (folder is
                  read-only for example) it will return -1."""

        self.ui.savemessage('imap', uid, flags, self)

        # already have it, just save modified flags
        if uid > 0 and self.uidexists(uid):
            self.savemessageflags(uid, flags)
            return uid

        content = self.deletemessageheaders(content, self.filterheaders)

        # Use proper CRLF all over the message
        content = re.sub("(?<!\r)\n", CRLF, content)

        # get the date of the message, so we can pass it to the server.
        date = self.__getmessageinternaldate(content, rtime)

        # Message-ID is handy for debugging messages
        msg_id = self.getmessageheader(content, "message-id")
        if not msg_id:
            msg_id = '[unknown message-id]'

        retry_left = 2 # succeeded in APPENDING?
        imapobj = self.imapserver.acquireconnection()
        # NB: in the finally clause for this try we will release
        # NB: the acquired imapobj, so don't do that twice unless
        # NB: you will put another connection to imapobj.  If you
        # NB: really do need to release connection manually, set
        # NB: imapobj to None.
        try:
            while retry_left:
                # XXX: we can mangle message only once, out of the loop
                # UIDPLUS extension provides us with an APPENDUID response.
                use_uidplus = 'UIDPLUS' in imapobj.capabilities

                if not use_uidplus:
                    # insert a random unique header that we can fetch later
                    (headername, headervalue) = self.__generate_randomheader(
                        content)
                    self.ui.debug('imap', 'savemessage: header is: %s: %s'%
                        (headername, headervalue))
                    content = self.addmessageheader(content, CRLF, headername, headervalue)

                if len(content)>200:
                    dbg_output = "%s...%s"% (content[:150], content[-50:])
                else:
                    dbg_output = content
                self.ui.debug('imap', "savemessage: date: %s, content: '%s'"%
                    (date, dbg_output))

                try:
                    # Select folder for append and make the box READ-WRITE
                    imapobj.select(self.getfullname())
                except imapobj.readonly:
                    # readonly exception. Return original uid to notify that
                    # we did not save the message. (see savemessage in Base.py)
                    self.ui.msgtoreadonly(self, uid, content, flags)
                    return uid

                #Do the APPEND
                try:
                    (typ, dat) = imapobj.append(self.getfullname(),
                        imaputil.flagsmaildir2imap(flags), date, content)
                    # This should only catch 'NO' responses since append()
                    # will raise an exception for 'BAD' responses:
                    if typ != 'OK':
                        # For example, Groupwise IMAP server can return something like:
                        #
                        #   NO APPEND The 1500 MB storage limit has been exceeded.
                        #
                        # In this case, we should immediately abort the repository sync
                        # and continue with the next account.
                        msg = \
                            "Saving msg (%s) in folder '%s', repository '%s' failed (abort). " \
                            "Server responded: %s %s\n"% \
                            (msg_id, self, self.getrepository(), typ, dat)
                        raise OfflineImapError(msg, OfflineImapError.ERROR.REPO)
                    retry_left = 0 # Mark as success
                except imapobj.abort as e:
                    # connection has been reset, release connection and retry.
                    retry_left -= 1
                    self.imapserver.releaseconnection(imapobj, True)
                    imapobj = self.imapserver.acquireconnection()
                    if not retry_left:
                        six.reraise(OfflineImapError("Saving msg (%s) in folder '%s', "
                              "repository '%s' failed (abort). Server responded: %s\n"
                              "Message content was: %s"%
                              (msg_id, self, self.getrepository(), str(e), dbg_output),
                                               OfflineImapError.ERROR.MESSAGE), None, exc_info()[2])
                    # XXX: is this still needed?
                    self.ui.error(e, exc_info()[2])
                except imapobj.error as e: # APPEND failed
                    # If the server responds with 'BAD', append()
                    # raise()s directly.  So we catch that too.
                    # drop conn, it might be bad.
                    self.imapserver.releaseconnection(imapobj, True)
                    imapobj = None
                    six.reraise(OfflineImapError("Saving msg (%s) folder '%s', repo '%s'"
                        "failed (error). Server responded: %s\nMessage content was: "
                        "%s" % (msg_id, self, self.getrepository(), str(e), dbg_output),
                            OfflineImapError.ERROR.MESSAGE), None, exc_info()[2])
            # Checkpoint. Let it write out stuff, etc. Eg searches for
            # just uploaded messages won't work if we don't do this.
            (typ,dat) = imapobj.check()
            assert(typ == 'OK')

            # get the new UID, do we use UIDPLUS?
            if use_uidplus:
                # get new UID from the APPENDUID response, it could look
                # like OK [APPENDUID 38505 3955] APPEND completed with
                # 38505 bein folder UIDvalidity and 3955 the new UID.
                # note: we would want to use .response() here but that
                # often seems to return [None], even though we have
                # data. TODO
                resp = imapobj._get_untagged_response('APPENDUID')
                if resp == [None] or resp is None:
                    self.ui.warn("Server supports UIDPLUS but got no APPENDUID "
                        "appending a message.")
                    return 0
                uid = int(resp[-1].split(' ')[1])
                if uid == 0:
                    self.ui.warn("savemessage: Server supports UIDPLUS, but"
                        " we got no usable uid back. APPENDUID reponse was "
                        "'%s'"% str(resp))
            else:
                # we don't support UIDPLUS
                uid = self.__savemessage_searchforheader(imapobj, headername,
                    headervalue)
                # See docs for savemessage in Base.py for explanation
                # of this and other return values
                if uid == 0:
                    self.ui.debug('imap', 'savemessage: attempt to get new UID '
                        'UID failed. Search headers manually.')
                    uid = self.__savemessage_fetchheaders(imapobj, headername,
                        headervalue)
                    self.ui.warn('imap', "savemessage: Searching mails for new "
                        "Message-ID failed. Could not determine new UID.")
        finally:
            if imapobj: self.imapserver.releaseconnection(imapobj)

        if uid: # avoid UID FETCH 0 crash happening later on
            self.messagelist[uid] = self.msglist_item_initializer(uid)
            self.messagelist[uid]['flags'] = flags

        self.ui.debug('imap', 'savemessage: returning new UID %d'% uid)
        return uid


    def _fetch_from_imap(self, uids, retry_num=1):
        """Fetches data from IMAP server.

        Arguments:
        - imapobj: IMAPlib object
        - uids: message UIDS
        - retry_num: number of retries to make

        Returns: data obtained by this query."""

        imapobj = self.imapserver.acquireconnection()
        try:
            query = "(%s)"% (" ".join(self.imap_query))
            fails_left = retry_num  ## retry on dropped connection
            while fails_left:
                try:
                    imapobj.select(self.getfullname(), readonly = True)
                    res_type, data = imapobj.uid('fetch', uids, query)
                    break
                except imapobj.abort as e:
                    fails_left -= 1
                    # self.ui.error() will show the original traceback
                    if fails_left <= 0:
                        message = ("%s, while fetching msg %r in folder %r."
                            " Max retry reached (%d)"%
                            (e, uids, self.name, retry_num))
                        severity = OfflineImapError.ERROR.MESSAGE
                        raise OfflineImapError(message,
                            OfflineImapError.ERROR.MESSAGE)
                    # Release dropped connection, and get a new one
                    self.imapserver.releaseconnection(imapobj, True)
                    imapobj = self.imapserver.acquireconnection()
                    self.ui.error("%s. While fetching msg %r in folder %r."
                        " Retrying (%d/%d)"%
                        (e, uids, self.name, retry_num - fails_left, retry_num))
        finally:
             # The imapobj here might be different than the one created before
             # the ``try`` clause. So please avoid transforming this to a nice
             # ``with`` without taking this into account.
            self.imapserver.releaseconnection(imapobj)

        if data == [None] or res_type != 'OK':
            #IMAP server says bad request or UID does not exist
            severity = OfflineImapError.ERROR.MESSAGE
            reason = "IMAP server '%s' failed to fetch messages UID '%s'."\
                "Server responded: %s %s"% (self.getrepository(), uids,
                                             res_type, data)
            if data == [None]:
                #IMAP server did not find a message with this UID
                reason = "IMAP server '%s' does not have a message "\
                    "with UID '%s'" % (self.getrepository(), uids)
            raise OfflineImapError(reason, severity)

        return data


    def _store_to_imap(self, imapobj, uid, field, data):
        """Stores data to IMAP server

        Arguments:
        - imapobj: instance of IMAPlib to use
        - uid: message UID
        - field: field name to be stored/updated
        - data: field contents
        """
        imapobj.select(self.getfullname())
        res_type, retdata = imapobj.uid('store', uid, field, data)
        if res_type != 'OK':
            severity = OfflineImapError.ERROR.MESSAGE
            reason = "IMAP server '%s' failed to store %s for message UID '%d'."\
                     "Server responded: %s %s"% (
                    self.getrepository(), field, uid, res_type, retdata)
            raise OfflineImapError(reason, severity)
        return retdata[0]

    # Interface from BaseFolder
    def savemessageflags(self, uid, flags):
        """Change a message's flags to `flags`.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        imapobj = self.imapserver.acquireconnection()
        try:
            result = self._store_to_imap(imapobj, str(uid), 'FLAGS',
                imaputil.flagsmaildir2imap(flags))
        except imapobj.readonly:
            self.ui.flagstoreadonly(self, [uid], flags)
            return
        finally:
            self.imapserver.releaseconnection(imapobj)

        if not result:
            self.messagelist[uid]['flags'] = flags
        else:
            flags = imaputil.flags2hash(imaputil.imapsplit(result)[1])['FLAGS']
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)

    # Interface from BaseFolder
    def addmessageflags(self, uid, flags):
        self.addmessagesflags([uid], flags)

    def __addmessagesflags_noconvert(self, uidlist, flags):
        self.__processmessagesflags('+', uidlist, flags)

    # Interface from BaseFolder
    def addmessagesflags(self, uidlist, flags):
        """This is here for the sake of UIDMaps.py -- deletemessages must
        add flags and get a converted UID, and if we don't have noconvert,
        then UIDMaps will try to convert it twice."""

        self.__addmessagesflags_noconvert(uidlist, flags)

    # Interface from BaseFolder
    def deletemessageflags(self, uid, flags):
        self.deletemessagesflags([uid], flags)

    # Interface from BaseFolder
    def deletemessagesflags(self, uidlist, flags):
        self.__processmessagesflags('-', uidlist, flags)

    def __processmessagesflags_real(self, operation, uidlist, flags):
        imapobj = self.imapserver.acquireconnection()
        try:
            try:
                imapobj.select(self.getfullname())
            except imapobj.readonly:
                self.ui.flagstoreadonly(self, uidlist, flags)
                return
            r = imapobj.uid('store',
                imaputil.uid_sequence(uidlist), operation + 'FLAGS',
                    imaputil.flagsmaildir2imap(flags))
            assert r[0] == 'OK', 'Error with store: ' + '. '.join(r[1])
            r = r[1]
        finally:
            self.imapserver.releaseconnection(imapobj)
        # Some IMAP servers do not always return a result.  Therefore,
        # only update the ones that it talks about, and manually fix
        # the others.
        needupdate = list(uidlist)
        for result in r:
            if result == None:
                # Compensate for servers that don't return anything from
                # STORE.
                continue
            attributehash = imaputil.flags2hash(imaputil.imapsplit(result)[1])
            if not ('UID' in attributehash and 'FLAGS' in attributehash):
                # Compensate for servers that don't return a UID attribute.
                continue
            flagstr = attributehash['FLAGS']
            uid = int(attributehash['UID'])
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flagstr)
            try:
                needupdate.remove(uid)
            except ValueError:          # Let it slide if it's not in the list
                pass
        for uid in needupdate:
            if operation == '+':
                self.messagelist[uid]['flags'] |= flags
            elif operation == '-':
                self.messagelist[uid]['flags'] -= flags


    def __processmessagesflags(self, operation, uidlist, flags):
        # Hack for those IMAP servers with a limited line length
        batch_size = 100
        for i in range(0, len(uidlist), batch_size):
            self.__processmessagesflags_real(operation,
              uidlist[i:i + batch_size], flags)
        return


    # Interface from BaseFolder
    def change_message_uid(self, uid, new_uid):
        """Change the message from existing uid to new_uid

        If the backend supports it. IMAP does not and will throw errors."""

        raise OfflineImapError('IMAP backend cannot change a messages UID from '
            '%d to %d'% (uid, new_uid), OfflineImapError.ERROR.MESSAGE)

    # Interface from BaseFolder
    def deletemessage(self, uid):
        self.__deletemessages_noconvert([uid])

    # Interface from BaseFolder
    def deletemessages(self, uidlist):
        self.__deletemessages_noconvert(uidlist)

    def __deletemessages_noconvert(self, uidlist):
        if not len(uidlist):
            return

        self.__addmessagesflags_noconvert(uidlist, set('T'))
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
