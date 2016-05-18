# Base folder support
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

import os.path
import re
import time
from sys import exc_info

from offlineimap import threadutil
from offlineimap.ui import getglobalui
from offlineimap.error import OfflineImapError
import offlineimap.accounts


class BaseFolder(object):
    def __init__(self, name, repository):
        """
        :param name: Path & name of folder minus root or reference
        :param repository: Repository() in which the folder is.
        """

        self.ui = getglobalui()
        self.messagelist = {}
        # Save original name for folderfilter operations
        self.ffilter_name = name
        # Top level dir name is always ''
        self.root = None
        self.name = name if not name == self.getsep() else ''
        self.newmail_hook = None
        # Only set the newmail_hook if the IMAP folder is named 'INBOX'
        if self.name == 'INBOX':
            self.newmail_hook = repository.newmail_hook
        self.have_newmail = False
        self.repository = repository
        self.visiblename = repository.nametrans(name)
        # In case the visiblename becomes '.' or '/' (top-level) we use
        # '' as that is the name that e.g. the Maildir scanning will
        # return for the top-level dir.
        if self.visiblename == self.getsep():
            self.visiblename = ''

        self.repoconfname = "Repository " + repository.name

        self.config = repository.getconfig()

        # Do we need to use mail timestamp for filename prefix?
        filename_use_mail_timestamp_global = self.config.getdefaultboolean(
            "general", "filename_use_mail_timestamp", False)
        self._filename_use_mail_timestamp = self.config.getdefaultboolean(
            self.repoconfname,
            "filename_use_mail_timestamp",
            filename_use_mail_timestamp_global)

        self._sync_deletes = self.config.getdefaultboolean(
            self.repoconfname, "sync_deletes", True)

        # Determine if we're running static or dynamic folder filtering
        # and check filtering status
        self._dynamic_folderfilter = self.config.getdefaultboolean(
            self.repoconfname, "dynamic_folderfilter", False)
        self._sync_this = repository.should_sync_folder(self.ffilter_name)
        if self._dynamic_folderfilter:
            self.ui.debug('', "Running dynamic folder filtering on '%s'[%s]"%
                (self.ffilter_name, repository))
        elif not self._sync_this:
            self.ui.debug('', "Filtering out '%s'[%s] due to folderfilter"%
                (self.ffilter_name, repository))

        # Passes for syncmessagesto
        self.syncmessagesto_passes = [
            ('copying messages'       , self.__syncmessagesto_copy),
            ('deleting messages'      , self.__syncmessagesto_delete),
            ('syncing flags'          , self.__syncmessagesto_flags)
        ]

    def getname(self):
        """Returns name"""
        return self.name

    def __str__(self):
        # FIMXE: remove calls of this. We have getname().
        return self.name

    @property
    def accountname(self):
        """Account name as string"""

        return self.repository.accountname

    @property
    def sync_this(self):
        """Should this folder be synced or is it e.g. filtered out?"""

        if not self._dynamic_folderfilter:
            return self._sync_this
        else:
            return self.repository.should_sync_folder(self.ffilter_name)

    def suggeststhreads(self):
        """Returns True if this folder suggests using threads for actions.

        Only IMAP returns True. This method must honor any CLI or configuration
        option."""

        return False

    def waitforthread(self):
        """Implements method that waits for thread to be usable.
        Should be implemented only for folders that suggest threads."""
        raise NotImplementedError

    # XXX: we may need someting like supports_quickstatus() to check
    # XXX: if user specifies 'quick' flag for folder that doesn't
    # XXX: support quick status queries, so one believes that quick
    # XXX: status checks will be done, but it won't really be so.
    def quickchanged(self, statusfolder):
        """ Runs quick check for folder changes and returns changed
        status: True -- changed, False -- not changed.

        :param statusfolder: keeps track of the last known folder state.
        """

        return True

    def getinstancelimitnamespace(self):
        """For threading folders, returns the instancelimitname for
        InstanceLimitedThreads."""

        raise NotImplementedError

    def storesmessages(self):
        """Should be true for any backend that actually saves message bodies.
        (Almost all of them).  False for the LocalStatus backend.  Saves
        us from having to slurp up messages just for localstatus purposes."""

        return 1

    def getvisiblename(self):
        """The nametrans-transposed name of the folder's name."""

        return self.visiblename

    def getexplainedname(self):
        """Name that shows both real and nametrans-mangled values."""

        if self.name == self.visiblename:
            return self.name
        else:
            return "%s [remote name %s]"% (self.visiblename, self.name)

    def getrepository(self):
        """Returns the repository object that this folder is within."""

        return self.repository

    def getroot(self):
        """Returns the root of the folder, in a folder-specific fashion."""

        return self.root

    def getsep(self):
        """Returns the separator for this folder type."""

        return self.sep

    def getfullname(self):
        if self.getroot():
            return self.getroot() + self.getsep() + self.getname()
        else:
            return self.getname()

    def getfolderbasename(self):
        """Return base file name of file to store Status/UID info in."""

        if not self.name:
            basename = '.'
        else: # Avoid directory hierarchies and file names such as '/'.
            basename = self.name.replace('/', '.')
        # Replace with literal 'dot' if final path name is '.' as '.' is
        # an invalid file name.
        basename = re.sub('(^|\/)\.$','\\1dot', basename)
        return basename

    def check_uidvalidity(self):
        """Tests if the cached UIDVALIDITY match the real current one

        If required it saves the UIDVALIDITY value. In this case the
        function is not threadsafe. So don't attempt to call it from
        concurrent threads.

        :returns: Boolean indicating the match. Returns True in case it
            implicitely saved the UIDVALIDITY."""

        if self.get_saveduidvalidity() != None:
            return self.get_saveduidvalidity() == self.get_uidvalidity()
        else:
            self.save_uidvalidity()
            return True

    def _getuidfilename(self):
        """provides UIDVALIDITY cache filename for class internal purposes."""

        return os.path.join(self.repository.getuiddir(),
                            self.getfolderbasename())

    def get_saveduidvalidity(self):
        """Return the previously cached UIDVALIDITY value

        :returns: UIDVALIDITY as (long) number or None, if None had been
            saved yet."""

        if hasattr(self, '_base_saved_uidvalidity'):
            return self._base_saved_uidvalidity
        uidfilename = self._getuidfilename()
        if not os.path.exists(uidfilename):
            self._base_saved_uidvalidity = None
        else:
            file = open(uidfilename, "rt")
            self._base_saved_uidvalidity = int(file.readline().strip())
            file.close()
        return self._base_saved_uidvalidity

    def save_uidvalidity(self):
        """Save the UIDVALIDITY value of the folder to the cache

        This function is not threadsafe, so don't attempt to call it
        from concurrent threads."""

        newval = self.get_uidvalidity()
        uidfilename = self._getuidfilename()

        with open(uidfilename + ".tmp", "wt") as file:
            file.write("%d\n"% newval)
        os.rename(uidfilename + ".tmp", uidfilename)
        self._base_saved_uidvalidity = newval

    def get_uidvalidity(self):
        """Retrieve the current connections UIDVALIDITY value

        This function needs to be implemented by each Backend
        :returns: UIDVALIDITY as a (long) number"""

        raise NotImplementedError

    def cachemessagelist(self):
        """Reads the message list from disk or network and stores it in
        memory for later use.  This list will not be re-read from disk or
        memory unless this function is called again."""

        raise NotImplementedError

    def ismessagelistempty(self):
        """Is the list of messages empty."""

        if len(self.messagelist.keys()) < 1:
            return True
        return False

    def dropmessagelistcache(self):
        """Empty everythings we know about messages."""

        self.messagelist = {}

    def getmessagelist(self):
        """Gets the current message list.

        You must call cachemessagelist() before calling this function!"""

        return self.messagelist

    def msglist_item_initializer(self, uid):
        """Returns value for empty messagelist element with given UID.

        This function must initialize all fields of messagelist item
        and must be called every time when one creates new messagelist
        entry to ensure that all fields that must be present are present."""

        raise NotImplementedError

    def uidexists(self, uid):
        """Returns True if uid exists"""

        return uid in self.getmessagelist()

    def getmessageuidlist(self):
        """Gets a list of UIDs.

        You may have to call cachemessagelist() before calling this function!"""

        return self.getmessagelist().keys()

    def getmessagecount(self):
        """Gets the number of messages."""

        return len(self.getmessagelist())

    def getmessage(self, uid):
        """Returns the content of the specified message."""

        raise NotImplementedError

    def getmaxage(self):
        """ maxage is allowed to be either an integer or a date of the
        form YYYY-mm-dd. This returns a time_struct. """

        maxagestr = self.config.getdefault("Account %s"%
            self.accountname, "maxage", None)
        if maxagestr == None:
            return None
        # is it a number?
        try:
            maxage = int(maxagestr)
            if maxage < 1:
                raise OfflineImapError("invalid maxage value %d"% maxage,
                    OfflineImapError.ERROR.MESSAGE)
            return time.gmtime(time.time() - 60*60*24*maxage)
        except ValueError:
            pass # maybe it was a date
        # is it a date string?
        try:
            date = time.strptime(maxagestr, "%Y-%m-%d")
            if date[0] < 1900:
                raise OfflineImapError("maxage led to year %d. "
                    "Abort syncing."% date[0],
                    OfflineImapError.ERROR.MESSAGE)
            if (time.mktime(date) - time.mktime(time.localtime())) > 0:
                raise OfflineImapError("maxage led to future date %s. "
                    "Abort syncing."% maxagestr,
                    OfflineImapError.ERROR.MESSAGE)
            return date
        except ValueError:
            raise OfflineImapError("invalid maxage value %s"% maxagestr,
                OfflineImapError.ERROR.MESSAGE)

    def getmaxsize(self):
        return self.config.getdefaultint("Account %s"%
            self.accountname, "maxsize", None)

    def getstartdate(self):
        """ Retrieve the value of the configuration option startdate """
        datestr = self.config.getdefault("Repository " + self.repository.name,
            'startdate', None)
        try:
            if not datestr:
                return None
            date = time.strptime(datestr, "%Y-%m-%d")
            if date[0] < 1900:
                raise OfflineImapError("startdate led to year %d. "
                    "Abort syncing."% date[0],
                    OfflineImapError.ERROR.MESSAGE)
            if (time.mktime(date) - time.mktime(time.localtime())) > 0:
                raise OfflineImapError("startdate led to future date %s. "
                    "Abort syncing."% datestr,
                    OfflineImapError.ERROR.MESSAGE)
            return date
        except ValueError:
            raise OfflineImapError("invalid startdate value %s",
                OfflineImapError.ERROR.MESSAGE)

    def get_min_uid_file(self):
        startuiddir = os.path.join(self.config.getmetadatadir(),
            'Repository-' + self.repository.name, 'StartUID')
        if not os.path.exists(startuiddir):
            os.mkdir(startuiddir, 0o700)
        return os.path.join(startuiddir, self.getfolderbasename())

    def retrieve_min_uid(self):
        uidfile = self.get_min_uid_file()
        if not os.path.exists(uidfile):
            return None
        try:
            fd = open(uidfile, 'rt')
            min_uid = int(fd.readline().strip())
            fd.close()
            return min_uid
        except:
            raise IOError("Can't read %s"% uidfile)


    def savemessage(self, uid, content, flags, rtime):
        """Writes a new message, with the specified uid.

        If the uid is < 0: The backend should assign a new uid and
           return it.  In case it cannot assign a new uid, it returns
           the negative uid passed in WITHOUT saving the message.

           If the backend CAN assign a new uid, but cannot find out what
           this UID is (as is the case with some IMAP servers), it
           returns 0 but DOES save the message.

           IMAP backend should be the only one that can assign a new
           uid.

        If the uid is > 0, the backend should set the uid to this, if it can.
           If it cannot set the uid to that, it will save it anyway.
           It will return the uid assigned in any case.

        Note that savemessage() does not check against dryrun settings,
        so you need to ensure that savemessage is never called in a
        dryrun mode."""

        raise NotImplementedError

    def getmessagetime(self, uid):
        """Return the received time for the specified message."""

        raise NotImplementedError

    def getmessagemtime(self, uid):
        """Returns the message modification time of the specified message."""

        raise NotImplementedError

    def getmessageflags(self, uid):
        """Returns the flags for the specified message."""

        raise NotImplementedError

    def getmessagekeywords(self, uid):
        """Returns the keywords for the specified message."""

        raise NotImplementedError

    def savemessageflags(self, uid, flags):
        """Sets the specified message's flags to the given set.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        raise NotImplementedError

    def addmessageflags(self, uid, flags):
        """Adds the specified flags to the message's flag set.  If a given
        flag is already present, it will not be duplicated.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode.

        :param flags: A set() of flags"""

        newflags = self.getmessageflags(uid) | flags
        self.savemessageflags(uid, newflags)

    def addmessagesflags(self, uidlist, flags):
        """Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        for uid in uidlist:
            if self.uidexists(uid):
                self.addmessageflags(uid, flags)

    def deletemessageflags(self, uid, flags):
        """Removes each flag given from the message's flag set.  If a given
        flag is already removed, no action will be taken for that flag.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        newflags = self.getmessageflags(uid) - flags
        self.savemessageflags(uid, newflags)

    def deletemessagesflags(self, uidlist, flags):
        """
        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        for uid in uidlist:
            self.deletemessageflags(uid, flags)

    def getmessagelabels(self, uid):
        """Returns the labels for the specified message."""

        raise NotImplementedError

    def savemessagelabels(self, uid, labels, ignorelabels=set(), mtime=0):
        """Sets the specified message's labels to the given set.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        raise NotImplementedError

    def addmessagelabels(self, uid, labels):
        """Adds the specified labels to the message's labels set.  If a given
        label is already present, it will not be duplicated.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode.

        :param labels: A set() of labels"""

        newlabels = self.getmessagelabels(uid) | labels
        self.savemessagelabels(uid, newlabels)

    def addmessageslabels(self, uidlist, labels):
        """Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        for uid in uidlist:
            self.addmessagelabels(uid, labels)

    def deletemessagelabels(self, uid, labels):
        """Removes each label given from the message's label set.  If a given
        label is already removed, no action will be taken for that label.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        newlabels = self.getmessagelabels(uid) - labels
        self.savemessagelabels(uid, newlabels)

    def deletemessageslabels(self, uidlist, labels):
        """
        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        for uid in uidlist:
            self.deletemessagelabels(uid, labels)

    def addmessageheader(self, content, linebreak, headername, headervalue):
        """Adds new header to the provided message.

        WARNING: This function is a bit tricky, and modifying it in the wrong way,
        may easily lead to data-loss.

        Arguments:
        - content: message content, headers and body as a single string
        - linebreak: string that carries line ending
        - headername: name of the header to add
        - headervalue: value of the header to add

        .. note::

           The following documentation will not get displayed correctly after being
           processed by Sphinx. View the source of this method to read it.

        This has to deal with strange corner cases where the header is
        missing or empty.  Here are illustrations for all the cases,
        showing where the header gets inserted and what the end result
        is.  In each illustration, '+' means the added contents.  Note
        that these examples assume LF for linebreak, not CRLF, so '\n'
        denotes a linebreak and '\n\n' corresponds to the transition
        between header and body.  However if the linebreak parameter
        is set to '\r\n' then you would have to substitute '\r\n' for
        '\n' in the below examples.

          * Case 1: No '\n\n', leading '\n'

            +X-Flying-Pig-Header: i am here\n
            \n
            This is the body\n
            next line\n

          * Case 2: '\n\n' at position 0

            +X-Flying-Pig-Header: i am here
            \n
            \n
            This is the body\n
            next line\n

          * Case 3: No '\n\n', no leading '\n'

            +X-Flying-Pig-Header: i am here\n
            +\n
            This is the body\n
            next line\n

          * Case 4: '\n\n' at non-zero position

            Subject: Something wrong with OI\n
            From: some@person.at
            +\nX-Flying-Pig-Header: i am here
            \n
            \n
            This is the body\n
            next line\n
        """

        self.ui.debug('', 'addmessageheader: called to add %s: %s'%
            (headername, headervalue))

        insertionpoint = content.find(linebreak * 2)
        if insertionpoint == -1:
            self.ui.debug('', 'addmessageheader: headers were missing')
        else:
            self.ui.debug('', 'addmessageheader: headers end at position %d' % insertionpoint)
            mark = '==>EOH<=='
            contextstart = max(0,            insertionpoint - 100)
            contextend   = min(len(content), insertionpoint + 100)
            self.ui.debug('', 'addmessageheader: header/body transition context (marked by %s): %s' %
                          (mark, repr(content[contextstart:insertionpoint]) + \
                          mark + repr(content[insertionpoint:contextend])))

        # Hoping for case #4
        prefix = linebreak
        suffix = ''
        # Case #2
        if insertionpoint == 0:
            prefix = ''
            suffix = ''
        # Either case #1 or #3
        elif insertionpoint == -1:
            prefix = ''
            suffix = linebreak
            insertionpoint = 0
            # Case #3: when body starts immediately, without preceding '\n'
            # (this shouldn't happen with proper mail messages, but
            # we seen many broken ones), we should add '\n' to make
            # new (and the only header, in this case) to be properly
            # separated from the message body.
            if content[0:len(linebreak)] != linebreak:
                suffix = suffix + linebreak

        self.ui.debug('', 'addmessageheader: insertionpoint = %d'% insertionpoint)
        headers = content[0:insertionpoint]
        self.ui.debug('', 'addmessageheader: headers = %s'% repr(headers))
        new_header = prefix + ("%s: %s" % (headername, headervalue)) + suffix
        self.ui.debug('', 'addmessageheader: new_header = ' + repr(new_header))
        return headers + new_header + content[insertionpoint:]


    def __find_eoh(self, content):
        """ Searches for the point where mail headers end.
        Either double '\n', or end of string.

        Arguments:
        - content: contents of the message to search in
        Returns: position of the first non-header byte.
        """

        eoh_cr = content.find('\n\n')
        if eoh_cr == -1:
            eoh_cr = len(content)

        return eoh_cr


    def getmessageheader(self, content, name):
        """Searches for the first occurence of the given header and returns
        its value. Header name is case-insensitive.

        Arguments:
        - contents: message itself
        - name: name of the header to be searched

        Returns: header value or None if no such header was found
        """

        self.ui.debug('', 'getmessageheader: called to get %s'% name)
        eoh = self.__find_eoh(content)
        self.ui.debug('', 'getmessageheader: eoh = %d'% eoh)
        headers = content[0:eoh]
        self.ui.debug('', 'getmessageheader: headers = %s'% repr(headers))

        m = re.search('^%s:(.*)$' % name, headers, flags = re.MULTILINE | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        else:
            return None


    def getmessageheaderlist(self, content, name):
        """Searches for the given header and returns a list of values for
        that header.

        Arguments:
        - contents: message itself
        - name: name of the header to be searched

        Returns: list of header values or emptylist if no such header was found
        """

        self.ui.debug('', 'getmessageheaderlist: called to get %s' % name)
        eoh = self.__find_eoh(content)
        self.ui.debug('', 'getmessageheaderlist: eoh = %d' % eoh)
        headers = content[0:eoh]
        self.ui.debug('', 'getmessageheaderlist: headers = %s' % repr(headers))

        return re.findall('^%s:(.*)$' % name, headers, flags = re.MULTILINE | re.IGNORECASE)


    def deletemessageheaders(self, content, header_list):
        """Deletes headers in the given list from the message content.

        Arguments:
        - content: message itself
        - header_list: list of headers to be deleted or just the header name

        We expect our message to have '\n' as line endings.
        """

        if type(header_list) != type([]):
            header_list = [header_list]
        self.ui.debug('', 'deletemessageheaders: called to delete %s'% (header_list))

        if not len(header_list): return content

        eoh = self.__find_eoh(content)
        self.ui.debug('', 'deletemessageheaders: end of headers = %d'% eoh)
        headers = content[0:eoh]
        rest = content[eoh:]
        self.ui.debug('', 'deletemessageheaders: headers = %s'% repr(headers))
        new_headers = []
        for h in headers.split('\n'):
            keep_it = True
            for trim_h in header_list:
                if len(h) > len(trim_h) and h[0:len(trim_h)+1] == (trim_h + ":"):
                    keep_it = False
                    break
            if keep_it: new_headers.append(h)

        return ('\n'.join(new_headers) + rest)




    def change_message_uid(self, uid, new_uid):
        """Change the message from existing uid to new_uid

        If the backend supports it (IMAP does not).

        :param new_uid: (optional) If given, the old UID will be changed
            to a new UID. This allows backends efficient renaming of
            messages if the UID has changed."""

        raise NotImplementedError

    def deletemessage(self, uid):
        """Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        raise NotImplementedError

    def deletemessages(self, uidlist):
        """Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode."""

        for uid in uidlist:
            self.deletemessage(uid)

    def copymessageto(self, uid, dstfolder, statusfolder, register=1):
        """Copies a message from self to dst if needed, updating the status

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode.

        :param uid: uid of the message to be copied.
        :param dstfolder: A BaseFolder-derived instance
        :param statusfolder: A LocalStatusFolder instance
        :param register: whether we should register a new thread."
        :returns: Nothing on success, or raises an Exception."""

        # Sometimes, it could be the case that if a sync takes awhile,
        # a message might be deleted from the maildir before it can be
        # synced to the status cache.  This is only a problem with
        # self.getmessage().  So, don't call self.getmessage unless
        # really needed.
        if register: # output that we start a new thread
            self.ui.registerthread(self.repository.account)

        try:
            message = None
            flags = self.getmessageflags(uid)
            rtime = self.getmessagetime(uid)

            # If any of the destinations actually stores the message body,
            # load it up.
            if dstfolder.storesmessages():
                message = self.getmessage(uid)
            # Succeeded? -> IMAP actually assigned a UID. If newid
            # remained negative, no server was willing to assign us an
            # UID. If newid is 0, saving succeeded, but we could not
            # retrieve the new UID. Ignore message in this case.
            new_uid = dstfolder.savemessage(uid, message, flags, rtime)
            if new_uid > 0:
                if new_uid != uid:
                    # Got new UID, change the local uid to match the new one.
                    self.change_message_uid(uid, new_uid)
                    statusfolder.deletemessage(uid)
                    # Got new UID, change the local uid.
                # Save uploaded status in the statusfolder
                statusfolder.savemessage(new_uid, message, flags, rtime)
                # Check whether the mail has been seen
                if 'S' not in flags:
                    self.have_newmail = True
            elif new_uid == 0:
                # Message was stored to dstfolder, but we can't find it's UID
                # This means we can't link current message to the one created
                # in IMAP. So we just delete local message and on next run
                # we'll sync it back
                # XXX This could cause infinite loop on syncing between two
                # IMAP servers ...
                self.deletemessage(uid)
            else:
                raise OfflineImapError("Trying to save msg (uid %d) on folder "
                    "%s returned invalid uid %d"% (uid, dstfolder.getvisiblename(),
                    new_uid), OfflineImapError.ERROR.MESSAGE)
        except (KeyboardInterrupt): # bubble up CTRL-C
            raise
        except OfflineImapError as e:
            if e.severity > OfflineImapError.ERROR.MESSAGE:
                raise # bubble severe errors up
            self.ui.error(e, exc_info()[2])
        except Exception as e:
            self.ui.error(e, exc_info()[2],
              msg = "Copying message %s [acc: %s]"% (uid, self.accountname))
            raise    #raise on unknown errors, so we can fix those

    def __syncmessagesto_copy(self, dstfolder, statusfolder):
        """Pass1: Copy locally existing messages not on the other side.

        This will copy messages to dstfolder that exist locally but are
        not in the statusfolder yet. The strategy is:

        1) Look for messages present in self but not in statusfolder.
        2) invoke copymessageto() on those which:
           - If dstfolder doesn't have it yet, add them to dstfolder.
           - Update statusfolder

        This function checks and protects us from action in dryrun mode."""

        # We have no new mail yet
        self.have_newmail = False

        threads = []

        copylist = [uid for uid in self.getmessageuidlist() if not statusfolder.uidexists(uid)]
        num_to_copy = len(copylist)
        if num_to_copy and self.repository.account.dryrun:
            self.ui.info("[DRYRUN] Copy {0} messages from {1}[{2}] to {3}".format(
                num_to_copy, self, self.repository, dstfolder.repository))
            return
        for num, uid in enumerate(copylist):
            # bail out on CTRL-C or SIGTERM
            if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                break
            if uid > 0 and dstfolder.uidexists(uid):
                # dst has message with that UID already, only update status
                flags = self.getmessageflags(uid)
                rtime = self.getmessagetime(uid)
                statusfolder.savemessage(uid, None, flags, rtime)
                continue

            self.ui.copyingmessage(uid, num+1, num_to_copy, self, dstfolder)
            # exceptions are caught in copymessageto()
            if self.suggeststhreads():
                self.waitforthread()
                thread = threadutil.InstanceLimitedThread(
                    self.getinstancelimitnamespace(),
                    target = self.copymessageto,
                    name = "Copy message from %s:%s" % (self.repository, self),
                    args = (uid, dstfolder, statusfolder)
                    )
                thread.start()
                threads.append(thread)
            else:
                self.copymessageto(uid, dstfolder, statusfolder, register=0)
        for thread in threads:
            thread.join()

        # Execute new mail hook if we have new mail.
        if self.have_newmail:
            if self.newmail_hook != None:
                self.newmail_hook()

    def __syncmessagesto_delete(self, dstfolder, statusfolder):
        """Pass 2: Remove locally deleted messages on dst.

        Get all UIDs in statusfolder but not self. These are messages
        that were deleted in 'self'. Delete those from dstfolder and
        statusfolder.

        This function checks and protects us from action in dryrun mode.
        """
        # The list of messages to delete. If sync of deletions is disabled we
        # still remove stale entries from statusfolder (neither in local nor
        # remote).
        deletelist = [uid for uid in statusfolder.getmessageuidlist()
                      if uid >= 0 and
                      not self.uidexists(uid) and
                      (self._sync_deletes or not dstfolder.uidexists(uid))]

        if len(deletelist):
            # Delete in statusfolder first to play safe. In case of abort, we
            # won't lose message, we will just unneccessarily retransmit some.
            # Delete messages from statusfolder that were either deleted by the
            # user, or not being tracked (e.g. because of maxage).
            statusfolder.deletemessages(deletelist)
            # Filter out untracked messages
            deletelist = [uid for uid in deletelist if dstfolder.uidexists(uid)]
            if len(deletelist):
                self.ui.deletingmessages(deletelist, [dstfolder])
                if self.repository.account.dryrun:
                    return #don't delete messages in dry-run mode
                dstfolder.deletemessages(deletelist)

    def combine_flags_and_keywords(self, uid, dstfolder):
        """Combine the message's flags and keywords using the mapping for the
        destination folder."""

        # Take a copy of the message flag set, otherwise
        # __syncmessagesto_flags() will fail because statusflags is actually a
        # reference to selfflags (which it should not, but I don't have time to
        # debug THAT).
        selfflags = set(self.getmessageflags(uid))

        try:
            keywordmap = dstfolder.getrepository().getkeywordmap()
            if keywordmap is None:
                return selfflags

            knownkeywords = set(keywordmap.keys())

            selfkeywords = self.getmessagekeywords(uid)

            if not knownkeywords >= selfkeywords:
                #some of the message's keywords are not in the mapping, so
                #skip them

                skipped_keywords = list(selfkeywords - knownkeywords)
                selfkeywords &= knownkeywords

                self.ui.warn("Unknown keywords skipped: %s\n"
                    "You may want to change your configuration to include "
                    "those\n" % (skipped_keywords))

            keywordletterset = set([keywordmap[keyw] for keyw in selfkeywords])

            #add the mapped keywords to the list of message flags
            selfflags |= keywordletterset
        except NotImplementedError:
            pass

        return selfflags

    def __syncmessagesto_flags(self, dstfolder, statusfolder):
        """Pass 3: Flag synchronization.

        Compare flag mismatches in self with those in statusfolder. If
        msg has a valid UID and exists on dstfolder (has not e.g. been
        deleted there), sync the flag change to both dstfolder and
        statusfolder.

        This function checks and protects us from action in ryrun mode.
        """

        # For each flag, we store a list of uids to which it should be
        # added.  Then, we can call addmessagesflags() to apply them in
        # bulk, rather than one call per message.
        addflaglist = {}
        delflaglist = {}
        for uid in self.getmessageuidlist():
            # Ignore messages with negative UIDs missed by pass 1 and
            # don't do anything if the message has been deleted remotely
            if uid < 0 or not dstfolder.uidexists(uid):
                continue

            if statusfolder.uidexists(uid):
                statusflags = statusfolder.getmessageflags(uid)
            else:
                statusflags = set()

            selfflags = self.combine_flags_and_keywords(uid, dstfolder)

            addflags = selfflags - statusflags
            delflags = statusflags - selfflags

            for flag in addflags:
                if not flag in addflaglist:
                    addflaglist[flag] = []
                addflaglist[flag].append(uid)

            for flag in delflags:
                if not flag in delflaglist:
                    delflaglist[flag] = []
                delflaglist[flag].append(uid)

        for flag, uids in addflaglist.items():
            self.ui.addingflags(uids, flag, dstfolder)
            if self.repository.account.dryrun:
                continue #don't actually add in a dryrun
            dstfolder.addmessagesflags(uids, set(flag))
            statusfolder.addmessagesflags(uids, set(flag))

        for flag,uids in delflaglist.items():
            self.ui.deletingflags(uids, flag, dstfolder)
            if self.repository.account.dryrun:
                continue #don't actually remove in a dryrun
            dstfolder.deletemessagesflags(uids, set(flag))
            statusfolder.deletemessagesflags(uids, set(flag))

    def syncmessagesto(self, dstfolder, statusfolder):
        """Syncs messages in this folder to the destination dstfolder.

        This is the high level entry for syncing messages in one direction.
        Syncsteps are:

        Pass1: Copy locally existing messages
         Copy messages in self, but not statusfolder to dstfolder if not
         already in dstfolder. dstfolder might assign a new UID (e.g. if
         uploading to IMAP). Update statusfolder.

        Pass2: Remove locally deleted messages
         Get all UIDS in statusfolder but not self. These are messages
         that were deleted in 'self'. Delete those from dstfolder and
         statusfolder.

         After this pass, the message lists should be identical wrt the
         uids present (except for potential negative uids that couldn't
         be placed anywhere).

        Pass3: Synchronize flag changes
         Compare flag mismatches in self with those in statusfolder. If
         msg has a valid UID and exists on dstfolder (has not e.g. been
         deleted there), sync the flag change to both dstfolder and
         statusfolder.

        Pass4: Synchronize label changes (Gmail only)
         Compares label mismatches in self with those in statusfolder.
         If msg has a valid UID and exists on dstfolder, syncs the labels
         to both dstfolder and statusfolder.

        :param dstfolder: Folderinstance to sync the msgs to.
        :param statusfolder: LocalStatus instance to sync against.
        """

        for (passdesc, action) in self.syncmessagesto_passes:
            # bail out on CTRL-C or SIGTERM
            if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                break
            try:
                action(dstfolder, statusfolder)
            except (KeyboardInterrupt):
                raise
            except OfflineImapError as e:
                if e.severity > OfflineImapError.ERROR.FOLDER:
                    raise
                self.ui.error(e, exc_info()[2])
            except Exception as e:
                self.ui.error(e, exc_info()[2], "Syncing folder %s [acc: %s]" %\
                                  (self, self.accountname))
                raise # raise unknown Exceptions so we can fix them

    def __eq__(self, other):
        """Comparisons work either on string comparing folder names or
        on the same instance.

        MailDirFolder('foo') == 'foo' --> True
        a = MailDirFolder('foo'); a == b --> True
        MailDirFolder('foo') == 'moo' --> False
        MailDirFolder('foo') == IMAPFolder('foo') --> False
        MailDirFolder('foo') == MaildirFolder('foo') --> False
        """

        if isinstance(other, str):
            return other == self.name
        return id(self) == id(other)

    def __ne__(self, other):
        return not self.__eq__(other)
