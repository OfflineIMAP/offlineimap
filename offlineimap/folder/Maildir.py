# Maildir folder support
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

import socket
import time
import re
import os
from Base import BaseFolder
from threading import Lock

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

try: # python 2.6 has set() built in
    set
except NameError:
    from sets import Set as set

from offlineimap import OfflineImapError

# Find the UID in a message filename
re_uidmatch = re.compile(',U=(\d+)')
# Find a numeric timestamp in a string (filename prefix)
re_timestampmatch = re.compile('(\d+)');

timeseq = 0
lasttime = long(0)
timelock = Lock()

def gettimeseq():
    global lasttime, timeseq, timelock
    timelock.acquire()
    try:
        thistime = long(time.time())
        if thistime == lasttime:
            timeseq += 1
            return (thistime, timeseq)
        else:
            lasttime = thistime
            timeseq = 0
            return (thistime, timeseq)
    finally:
        timelock.release()

class MaildirFolder(BaseFolder):
    def __init__(self, root, name, sep, repository):
        self.sep = sep # needs to be set before super().__init__
        super(MaildirFolder, self).__init__(name, repository)
        self.dofsync = self.config.getdefaultboolean("general", "fsync", True)
        self.root = root
        self.messagelist = None
        # check if we should use a different infosep to support Win file systems
        self.wincompatible = self.config.getdefaultboolean(
            "Account "+self.accountname, "maildir-windows-compatible", False)
        self.infosep = '!' if self.wincompatible else ':'
        """infosep is the separator between maildir name and flag appendix"""
        self.re_flagmatch = re.compile('%s2,(\w*)' % self.infosep)
        #self.ui is set in BaseFolder.init()
        # Everything up to the first comma or colon (or ! if Windows):
        self.re_prefixmatch = re.compile('([^'+ self.infosep + ',]*)')
        #folder's md, so we can match with recorded file md5 for validity
        self._foldermd5 = md5(self.getvisiblename()).hexdigest()
        # Cache the full folder path, as we use getfullname() very often
        self._fullname = os.path.join(self.getroot(), self.getname())

    def getfullname(self):
        """Return the absolute file path to the Maildir folder (sans cur|new)"""
        return self._fullname

    def get_uidvalidity(self):
        """Retrieve the current connections UIDVALIDITY value

        Maildirs have no notion of uidvalidity, so we just return a magic
        token."""
        return 42

    #Checks to see if the given message is within the maximum age according
    #to the maildir name which should begin with a timestamp
    def _iswithinmaxage(self, messagename, maxage):
        #In order to have the same behaviour as SINCE in an IMAP search
        #we must convert this to the oldest time and then strip off hrs/mins
        #from that day
        oldest_time_utc = time.time() - (60*60*24*maxage)
        oldest_time_struct = time.gmtime(oldest_time_utc)
        oldest_time_today_seconds = ((oldest_time_struct[3] * 3600) \
            + (oldest_time_struct[4] * 60) \
            + oldest_time_struct[5])
        oldest_time_utc -= oldest_time_today_seconds

        timestampmatch = re_timestampmatch.search(messagename)
        timestampstr = timestampmatch.group()
        timestamplong = long(timestampstr)
        if(timestamplong < oldest_time_utc):
            return False
        else:
            return True

    def _parse_filename(self, filename):
        """Returns a messages file name components

        Receives the file name (without path) of a msg.  Usual format is
        '<%d_%d.%d.%s>,U=<%d>,FMD5=<%s>:2,<FLAGS>' (pointy brackets
        denoting the various components).

        If FMD5 does not correspond with the current folder MD5, we will
        return None for the UID & FMD5 (as it is not valid in this
        folder).  If UID or FMD5 can not be detected, we return `None`
        for the respective element.  If flags are empty or cannot be
        detected, we return an empty flags list.

        :returns: (prefix, UID, FMD5, flags). UID is a numeric "long"
            type. flags is a set() of Maildir flags"""
        prefix, uid, fmd5, flags = None, None, None, set()
        prefixmatch = self.re_prefixmatch.match(filename)
        if prefixmatch:
            prefix = prefixmatch.group(1)
        folderstr = ',FMD5=%s' % self._foldermd5
        foldermatch = folderstr in filename
        # If there was no folder MD5 specified, or if it mismatches,
        # assume it is a foreign (new) message and ret: uid, fmd5 = None, None
        if foldermatch:
            uidmatch = re_uidmatch.search(filename)
            if uidmatch:
                uid = long(uidmatch.group(1))
        flagmatch = self.re_flagmatch.search(filename)
        if flagmatch:
            # Filter out all lowercase (custom maildir) flags. We don't
            # handle them yet.
            flags = set((c for c in flagmatch.group(1) if not c.islower()))
        return prefix, uid, fmd5, flags

    def _scanfolder(self):
        """Cache the message list from a Maildir.

        Maildir flags are: R (replied) S (seen) T (trashed) D (draft) F
        (flagged).
        :returns: dict that can be used as self.messagelist"""
        maxage = self.config.getdefaultint("Account " + self.accountname,
                                           "maxage", None)
        maxsize = self.config.getdefaultint("Account " + self.accountname,
                                            "maxsize", None)
        retval = {}
        files = []
        nouidcounter = -1          # Messages without UIDs get negative UIDs.
        for dirannex in ['new', 'cur']:
            fulldirname = os.path.join(self.getfullname(), dirannex)
            files.extend((dirannex, filename) for
                         filename in os.listdir(fulldirname))

        for dirannex, filename in files:
            # We store just dirannex and filename, ie 'cur/123...'
            filepath = os.path.join(dirannex, filename)
            # check maxage/maxsize if this message should be considered
            if maxage and not self._iswithinmaxage(filename, maxage):
                continue
            if maxsize and (os.path.getsize(os.path.join(
                        self.getfullname(), filepath)) > maxsize):
                continue

            (prefix, uid, fmd5, flags) = self._parse_filename(filename)
            if uid is None: # assign negative uid to upload it.
                uid = nouidcounter
                nouidcounter -= 1
            else:                       # It comes from our folder.
                uidmatch = re_uidmatch.search(filename)
                uid = None
                if not uidmatch:
                    uid = nouidcounter
                    nouidcounter -= 1
                else:
                    uid = long(uidmatch.group(1))
            # 'filename' is 'dirannex/filename', e.g. cur/123,U=1,FMD5=1:2,S
            retval[uid] = {'flags': flags, 'filename': filepath}
        return retval

    def quickchanged(self, statusfolder):
        """Returns True if the Maildir has changed"""
        self.cachemessagelist()
        # Folder has different uids than statusfolder => TRUE
        if sorted(self.getmessageuidlist()) != \
                sorted(statusfolder.getmessageuidlist()):
            return True
        # Also check for flag changes, it's quick on a Maildir 
        for (uid, message) in self.getmessagelist().iteritems():
            if message['flags'] != statusfolder.getmessageflags(uid):
                return True
        return False  #Nope, nothing changed

    def cachemessagelist(self):
        if self.messagelist is None:
            self.messagelist = self._scanfolder()

    def getmessagelist(self):
        return self.messagelist

    def getmessage(self, uid):
        """Return the content of the message"""
        filename = self.messagelist[uid]['filename']
        filepath = os.path.join(self.getfullname(), filename)
        file = open(filepath, 'rt')
        retval = file.read()
        file.close()
        #TODO: WHY are we replacing \r\n with \n here? And why do we
        #      read it as text?
        return retval.replace("\r\n", "\n")

    def getmessagetime(self, uid):
        filename = self.messagelist[uid]['filename']
        filepath = os.path.join(self.getfullname(), filename)
        return os.path.getmtime(filepath)

    def new_message_filename(self, uid, flags=set()):
        """Creates a new unique Maildir filename

        :param uid: The UID`None`, or a set of maildir flags
        :param flags: A set of maildir flags
        :returns: String containing unique message filename"""
        timeval, timeseq = gettimeseq()
        return '%d_%d.%d.%s,U=%d,FMD5=%s%s2,%s' % \
            (timeval, timeseq, os.getpid(), socket.gethostname(),
             uid, self._foldermd5, self.infosep, ''.join(sorted(flags)))
        
    def savemessage(self, uid, content, flags, rtime):
        # This function only ever saves to tmp/,
        # but it calls savemessageflags() to actually save to cur/ or new/.
        self.ui.debug('maildir', 'savemessage: called to write with flags %s '
                      'and content %s' % (repr(flags), repr(content)))
        if uid < 0:
            # We cannot assign a new uid.
            return uid
        if uid in self.messagelist:
            # We already have it, just update flags.
            self.savemessageflags(uid, flags)
            return uid

        # Otherwise, save the message in tmp/ and then call savemessageflags()
        # to give it a permanent home.
        tmpdir = os.path.join(self.getfullname(), 'tmp')
        messagename = self.new_message_filename(uid, flags)
        # open file and write it out
        try:
            fd = os.open(os.path.join(tmpdir, messagename),
                           os.O_EXCL|os.O_CREAT|os.O_WRONLY, 0666)
        except OSError as e:
            if e.errno == 17: 
                #FILE EXISTS ALREADY
                severity = OfflineImapError.ERROR.MESSAGE
                raise OfflineImapError("Unique filename %s already existing." %\
                                           messagename, severity)
            else:
                raise

        file = os.fdopen(fd, 'wt')
        file.write(content)
        # Make sure the data hits the disk
        file.flush()
        if self.dofsync:
            os.fsync(fd)
        file.close()

        if rtime != None:
            os.utime(os.path.join(tmpdir, messagename), (rtime, rtime))

        self.messagelist[uid] = {'flags': flags,
                                 'filename': os.path.join('tmp', messagename)}
        # savemessageflags moves msg to 'cur' or 'new' as appropriate
        self.savemessageflags(uid, flags)
        self.ui.debug('maildir', 'savemessage: returning uid %d' % uid)
        return uid

    def getmessageflags(self, uid):
        return self.messagelist[uid]['flags']

    def savemessageflags(self, uid, flags):
        """Sets the specified message's flags to the given set.

        This function moves the message to the cur or new subdir,
        depending on the 'S'een flag."""

        oldfilename = self.messagelist[uid]['filename']
        dir_prefix, filename = os.path.split(oldfilename)
        # If a message has been seen, it goes into 'cur'
        dir_prefix = 'cur' if 'S' in flags else 'new'

        if flags != self.messagelist[uid]['flags']:
            # Flags have actually changed, construct new filename Strip
            # off existing infostring (possibly discarding small letter
            # flags that dovecot uses TODO)
            infomatch = self.re_flagmatch.search(filename)
            if infomatch:
                filename = filename[:-len(infomatch.group())] #strip off
            infostr = '%s2,%s' % (self.infosep, ''.join(sorted(flags)))
            filename += infostr

        newfilename = os.path.join(dir_prefix, filename)
        if (newfilename != oldfilename):
            try:
                os.rename(os.path.join(self.getfullname(), oldfilename),
                          os.path.join(self.getfullname(), newfilename))
            except OSError as e:
                raise OfflineImapError("Can't rename file '%s' to '%s': %s" % (
                                       oldfilename, newfilename, e[1]),
                                       OfflineImapError.ERROR.FOLDER)

            self.messagelist[uid]['flags'] = flags
            self.messagelist[uid]['filename'] = newfilename

    def change_message_uid(self, uid, new_uid):
        """Change the message from existing uid to new_uid

        This will not update the statusfolder UID, you need to do that yourself.
        :param new_uid: (optional) If given, the old UID will be changed
            to a new UID. The Maildir backend can implement this as an efficient
            rename."""
        if not uid in self.messagelist:
            raise OfflineImapError("Cannot change unknown Maildir UID %s" % uid)
        if uid == new_uid: return

        oldfilename = self.messagelist[uid]['filename']
        dir_prefix, filename = os.path.split(oldfilename)
        flags = self.getmessageflags(uid)
        filename = self.new_message_filename(new_uid, flags)
        os.rename(os.path.join(self.getfullname(), oldfilename),
                  os.path.join(self.getfullname(), dir_prefix, filename))
        self.messagelist[new_uid] = self.messagelist[uid]
        del self.messagelist[uid]
        
    def deletemessage(self, uid):
        """Unlinks a message file from the Maildir.

        :param uid: UID of a mail message
        :type uid: String
        :return: Nothing, or an Exception if UID but no corresponding file
                 found.
        """
        if not self.uidexists(uid):
            return

        filename = self.messagelist[uid]['filename']
        filepath = os.path.join(self.getfullname(), filename)
        try:
            os.unlink(filepath)
        except OSError:
            # Can't find the file -- maybe already deleted?
            newmsglist = self._scanfolder()
            if uid in newmsglist:       # Nope, try new filename.
                filename = newmsglist[uid]['filename']
                filepath = os.path.join(self.getfullname(), filename)
                os.unlink(filepath)
            # Yep -- return.
        del(self.messagelist[uid])
        
