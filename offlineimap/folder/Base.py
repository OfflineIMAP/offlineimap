# Base folder support
# Copyright (C) 2002-2011 John Goerzen & contributors
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

from offlineimap import threadutil
from offlineimap.ui import getglobalui
from offlineimap.error import OfflineImapError
import os.path
import re
from sys import exc_info
import traceback
try: # python 2.6 has set() built in
    set
except NameError:
    from sets import Set as set

class BaseFolder(object):
    def __init__(self, name, repository):
        """
        :para name: Path & name of folder minus root or reference
        :para repository: Repository() in which the folder is.
        """
        self.sync_this = True
        """Should this folder be included in syncing?"""
        self.ui = getglobalui()
        self.name = name
        self.repository = repository
        self.visiblename = repository.nametrans(name)
        # In case the visiblename becomes '.' (top-level) we use '' as
        # that is the name that e.g. the Maildir scanning will return
        # for the top-level dir.
        if self.visiblename == '.':
            self.visiblename = ''
        self.config = repository.getconfig()

    def getname(self):
        """Returns name"""
        return self.name

    def __str__(self):
        return self.name

    @property
    def accountname(self):
        """Account name as string"""
        return self.repository.accountname

    def suggeststhreads(self):
        """Returns true if this folder suggests using threads for actions;
        false otherwise.  Probably only IMAP will return true."""
        return 0

    def getcopyinstancelimit(self):
        """For threading folders, returns the instancelimitname for
        InstanceLimitedThreads."""
        raise NotImplementedException

    def storesmessages(self):
        """Should be true for any backend that actually saves message bodies.
        (Almost all of them).  False for the LocalStatus backend.  Saves
        us from having to slurp up messages just for localstatus purposes."""
        return 1

    def getvisiblename(self):
        """The nametrans-transposed name of the folder's name"""
        return self.visiblename

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
        """Return base file name of file to store Status/UID info in"""
        if not self.name:
            basename = '.'
        else: #avoid directory hierarchies and file names such as '/'
            basename = self.name.replace('/', '.')
        # replace with literal 'dot' if final path name is '.' as '.' is
        # an invalid file name.
        basename = re.sub('(^|\/)\.$','\\1dot', basename)
        return basename

    def isuidvalidityok(self):
        """Does the cached UID match the real UID

        If required it caches the UID. In this case the function is not
        threadsafe. So don't attempt to call it from concurrent threads."""

        if self.getsaveduidvalidity() != None:
            return self.getsaveduidvalidity() == self.getuidvalidity()
        else:
            self.saveuidvalidity()
            return 1

    def _getuidfilename(self):
        return os.path.join(self.repository.getuiddir(),
                            self.getfolderbasename())

    def getsaveduidvalidity(self):
        if hasattr(self, '_base_saved_uidvalidity'):
            return self._base_saved_uidvalidity
        uidfilename = self._getuidfilename()
        if not os.path.exists(uidfilename):
            self._base_saved_uidvalidity = None
        else:
            file = open(uidfilename, "rt")
            self._base_saved_uidvalidity = long(file.readline().strip())
            file.close()
        return self._base_saved_uidvalidity

    def saveuidvalidity(self):
        """Save the UID value of the folder to the status

        This function is not threadsafe, so don't attempt to call it
        from concurrent threads."""
        newval = self.getuidvalidity()
        uidfilename = self._getuidfilename()

        file = open(uidfilename + ".tmp", "wt")
        file.write("%d\n" % newval)
        file.close()
        os.rename(uidfilename + ".tmp", uidfilename)
        self._base_saved_uidvalidity = newval

    def getuidvalidity(self):
        raise NotImplementedException

    def cachemessagelist(self):
        """Reads the message list from disk or network and stores it in
        memory for later use.  This list will not be re-read from disk or
        memory unless this function is called again."""
        raise NotImplementedException

    def getmessagelist(self):
        """Gets the current message list.
        You must call cachemessagelist() before calling this function!"""
        raise NotImplementedException

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
        raise NotImplementedException

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
        """
        raise NotImplementedException

    def getmessagetime(self, uid):
        """Return the received time for the specified message."""
        raise NotImplementedException

    def getmessageflags(self, uid):
        """Returns the flags for the specified message."""
        raise NotImplementedException

    def savemessageflags(self, uid, flags):
        """Sets the specified message's flags to the given set."""
        raise NotImplementedException

    def addmessageflags(self, uid, flags):
        """Adds the specified flags to the message's flag set.  If a given
        flag is already present, it will not be duplicated.
        :param flags: A set() of flags"""
        newflags = self.getmessageflags(uid) | flags
        self.savemessageflags(uid, newflags)

    def addmessagesflags(self, uidlist, flags):
        for uid in uidlist:
            self.addmessageflags(uid, flags)

    def deletemessageflags(self, uid, flags):
        """Removes each flag given from the message's flag set.  If a given
        flag is already removed, no action will be taken for that flag."""
        newflags = self.getmessageflags(uid) - flags
        self.savemessageflags(uid, newflags)

    def deletemessagesflags(self, uidlist, flags):
        for uid in uidlist:
            self.deletemessageflags(uid, flags)

    def deletemessage(self, uid):
        raise NotImplementedException

    def deletemessages(self, uidlist):
        for uid in uidlist:
            self.deletemessage(uid)

    def copymessageto(self, uid, dstfolder, statusfolder, register = 1):
        """Copies a message from self to dst if needed, updating the status

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
            self.ui.registerthread(self.accountname)

        try:
            message = None
            flags = self.getmessageflags(uid)
            rtime = self.getmessagetime(uid)

            if uid > 0 and dstfolder.uidexists(uid):
                # dst has message with that UID already, only update status
                statusfolder.savemessage(uid, None, flags, rtime)
                return

            # If any of the destinations actually stores the message body,
            # load it up.
            if dstfolder.storesmessages():
                message = self.getmessage(uid)
            #Succeeded? -> IMAP actually assigned a UID. If newid
            #remained negative, no server was willing to assign us an
            #UID. If newid is 0, saving succeeded, but we could not
            #retrieve the new UID. Ignore message in this case.
            newuid = dstfolder.savemessage(uid, message, flags, rtime)

            if newuid > 0:
                if newuid != uid:
                    # Got new UID, change the local uid.
                    #TODO: Maildir could do this with a rename rather than
                    #load/save/del operation, IMPLEMENT a changeuid()
                    #function or so.
                    self.savemessage(newuid, message, flags, rtime)
                    self.deletemessage(uid)
                    uid = newuid
                # Save uploaded status in the statusfolder
                statusfolder.savemessage(uid, message, flags, rtime)
    
            elif newuid == 0:
                # Message was stored to dstfolder, but we can't find it's UID
                # This means we can't link current message to the one created
                # in IMAP. So we just delete local message and on next run
                # we'll sync it back
                # XXX This could cause infinite loop on syncing between two
                # IMAP servers ...
                self.deletemessage(uid)
            else:
                raise OfflineImapError("Trying to save msg (uid %d) on folder "
                                  "%s returned invalid uid %d" % \
                                      (uid,
                                       dstfolder.getvisiblename(),
                                       newuid),
                                       OfflineImapError.ERROR.MESSAGE)
        except OfflineImapError, e:
            if e.severity > OfflineImapError.ERROR.MESSAGE:
                raise # buble severe errors up
            self.ui.error(e, exc_info()[2])
        except Exception, e:
            self.ui.error(e, "Copying message %s [acc: %s]:\n %s" %\
                              (uid, self.accountname,
                               traceback.format_exc()))
            raise    #raise on unknown errors, so we can fix those


    def syncmessagesto_copy(self, dstfolder, statusfolder):
        """Pass1: Copy locally existing messages not on the other side

        This will copy messages to dstfolder that exist locally but are
        not in the statusfolder yet. The strategy is:

        1) Look for messages present in self but not in statusfolder.
        2) invoke copymessageto() on those which:
           - If dstfolder doesn't have it yet, add them to dstfolder.
           - Update statusfolder
        """
        threads = []

        copylist = filter(lambda uid: not \
                              statusfolder.uidexists(uid),
                            self.getmessageuidlist())
        num_to_copy = len(copylist)
        for num, uid in enumerate(copylist):
            self.ui.copyingmessage(uid, num+1, num_to_copy, self, dstfolder)
            # exceptions are caught in copymessageto()
            if self.suggeststhreads():
                self.waitforthread()
                thread = threadutil.InstanceLimitedThread(\
                    self.getcopyinstancelimit(),
                    target = self.copymessageto,
                    name = "Copy message from %s:%s" % (self.repository, self),
                    args = (uid, dstfolder, statusfolder))
                thread.start()
                threads.append(thread)
            else:
                self.copymessageto(uid, dstfolder, statusfolder,
                                   register = 0)
        for thread in threads:
            thread.join()

    def syncmessagesto_delete(self, dstfolder, statusfolder):
        """Pass 2: Remove locally deleted messages on dst

        Get all UIDS in statusfolder but not self. These are messages
        that were deleted in 'self'. Delete those from dstfolder and
        statusfolder."""
        deletelist = filter(lambda uid: uid>=0 \
                                and not self.uidexists(uid),
                            statusfolder.getmessageuidlist())
        if len(deletelist):
            self.ui.deletingmessages(deletelist, [dstfolder])
            # delete in statusfolder first to play safe. In case of abort, we
            # won't lose message, we will just retransmit some unneccessary.
            for folder in [statusfolder, dstfolder]:
                folder.deletemessages(deletelist)

    def syncmessagesto_flags(self, dstfolder, statusfolder):
        """Pass 3: Flag synchronization

        Compare flag mismatches in self with those in statusfolder. If
        msg has a valid UID and exists on dstfolder (has not e.g. been
        deleted there), sync the flag change to both dstfolder and
        statusfolder.
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

            selfflags = self.getmessageflags(uid)
            statusflags = statusfolder.getmessageflags(uid)
            #if we could not get message flags from LocalStatus, assume empty.
            if statusflags is None:
                statusflags = set()

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
            dstfolder.addmessagesflags(uids, set(flag))
            statusfolder.addmessagesflags(uids, set(flag))

        for flag,uids in delflaglist.items():
            self.ui.deletingflags(uids, flag, dstfolder)
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

        :param dstfolder: Folderinstance to sync the msgs to.
        :param statusfolder: LocalStatus instance to sync against.
        """
        passes = [('copying messages'       , self.syncmessagesto_copy),
                  ('deleting messages'      , self.syncmessagesto_delete),
                  ('syncing flags'          , self.syncmessagesto_flags)]

        for (passdesc, action) in passes:
            try:
                action(dstfolder, statusfolder)
            except (KeyboardInterrupt):
                raise
            except OfflineImapError, e:
                if e.severity > OfflineImapError.ERROR.FOLDER:
                    raise
                self.ui.error(e, exc_info()[2])
            except Exception, e:
                self.ui.error(e, exc_info()[2], "Syncing folder %s [acc: %s]" %\
                                  (self, self.accountname))
                raise # raise unknown Exceptions so we can fix them
