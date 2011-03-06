# Base folder support
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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from offlineimap import threadutil
from offlineimap.ui import getglobalui
import os.path
import re
import sys
import traceback

class BaseFolder:
    def __init__(self):
        self.ui = getglobalui()
        
    def getname(self):
        """Returns name"""
        return self.name

    def suggeststhreads(self):
        """Returns true if this folder suggests using threads for actions;
        false otherwise.  Probably only IMAP will return true."""
        return 0

    def waitforthread(self):
        """For threading folders, waits until there is a resource available
        before firing off a thread.  For all others, returns immediately."""
        pass

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
        return self.name

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
        foldername = self.getname()
        foldername = foldername.replace(self.repository.getsep(), '.')
        foldername = re.sub('/\.$', '/dot', foldername)
        foldername = re.sub('^\.$', 'dot', foldername)
        return foldername

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

    def getmessage(self, uid):
        """Returns the content of the specified message."""
        raise NotImplementedException

    def savemessage(self, uid, content, flags, rtime):
        """Writes a new message, with the specified uid.
        If the uid is < 0, the backend should assign a new uid and return it.

        If the backend cannot assign a new uid, it returns the uid passed in
        WITHOUT saving the message.

        If the backend CAN assign a new uid, but cannot find out what this UID
        is (as is the case with many IMAP servers), it returns 0 but DOES save
        the message.
        
        IMAP backend should be the only one that can assign a new uid.

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
        flag is already present, it will not be duplicated."""
        newflags = self.getmessageflags(uid)
        for flag in flags:
            if not flag in newflags:
                newflags.append(flag)
        newflags.sort()
        self.savemessageflags(uid, newflags)

    def addmessagesflags(self, uidlist, flags):
        for uid in uidlist:
            self.addmessageflags(uid, flags)

    def deletemessageflags(self, uid, flags):
        """Removes each flag given from the message's flag set.  If a given
        flag is already removed, no action will be taken for that flag."""
        newflags = self.getmessageflags(uid)
        for flag in flags:
            if flag in newflags:
                newflags.remove(flag)
        newflags.sort()
        self.savemessageflags(uid, newflags)

    def deletemessagesflags(self, uidlist, flags):
        for uid in uidlist:
            self.deletemessageflags(uid, flags)

    def deletemessage(self, uid):
        raise NotImplementedException

    def deletemessages(self, uidlist):
        for uid in uidlist:
            self.deletemessage(uid)

    def syncmessagesto_neguid_msg(self, uid, dstfolder, statusfolder,
                                  register = 1):
        """Copy a single message from self to dests.

        This is called by meth:`syncmessagesto_neguid`, possibly in a
        new thread. It does not return anything.

        :param dstfolder: A BaseFolder-derived instance
        :param statusfolder: A LocalStatusFolder instance
        :param register: If True, output that a new thread was created
                         (and register it with the ui)."""
        successobject = None
        successuid = None

        if register:
            self.ui.registerthread(self.getaccountname())
        self.ui.copyingmessage(uid, self, [dstfolder])

        message = self.getmessage(uid)
        flags = self.getmessageflags(uid)
        rtime = self.getmessagetime(uid)

        #Save messages to dstfolder and see if a valid UID was returned
        successuid = dstfolder.savemessage(uid, message, flags, rtime)

        #Succeeded? -> IMAP actually assigned a UID
        #If successuid remained negative, no server was willing to assign us
        #an UID. Ignore message.
        if successuid >= 0:
            # Copy the message to the statusfolder
            statusfolder.savemessage(successuid, message, flags, rtime)
            # Copy to its new name son the local server and delete
            # the one without a UID.
            self.savemessage(successuid, message, flags, rtime)
            #TODO: above means, we read in the message and write it out
            #to the very same dir with a different UID. Investigate if we
            #cannot simply rename it.
            
            # delete the negative uid message. We have it with a good UID now.
            self.deletemessage(uid)
        

    def syncmessagesto_neguid(self, dstfolder, statusfolder):
        """Pass 1 of folder synchronization.

        Look for messages in self with a negative uid.  These are
        messages in Maildirs that were not added by us.  Try to add them
        to the dstfolder. If that succeeds, get the new UID, add
        it to the statusfolder, add it to local for real, and delete the
        old fake (negative) one.

        :param dstfolder: A BaseFolder-derived instance
        :param statusfolder: A LocalStatusFolder instance"""

        uidlist = [uid for uid in self.getmessagelist().keys() if uid < 0]
        threads = []

        for uid in uidlist:
            if dstfolder.suggeststhreads():
                dstfolder.waitforthread()
                thread = threadutil.InstanceLimitedThread(\
                    dstfolder.getcopyinstancelimit(),
                    target = self.syncmessagesto_neguid_msg,
                    name = "New msg sync from %s" % self.getvisiblename(),
                    args = (uid, dstfolder, statusfolder))
                thread.setDaemon(1)
                thread.start()
                threads.append(thread)
            else:
                self.syncmessagesto_neguid_msg(uid, dstfolder, statusfolder,
                                               register = 0)
        #wait for all uploads to finish
        for thread in threads:
            thread.join()

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
        try:
            if register:
                self.ui.registerthread(self.getaccountname())

            message = None
            flags = self.getmessageflags(uid)
            rtime = self.getmessagetime(uid)
            
            if uid in dstfolder.getmessagelist():
                # dst has message with that UID already, only update status
                statusfolder.savemessage(uid, None, flags, rtime)
                return

            # really need to copy to dst...
            self.ui.copyingmessage(uid, self, [dstfolder])

            # If any of the destinations actually stores the message body,
            # load it up.            
            if dstfolder.storesmessages():
                message = self.getmessage(uid)

            newuid = dstfolder.savemessage(uid, message, flags, rtime)
            if newuid > 0 and newuid != uid:
                # Change the local uid.
                self.savemessage(newuid, message, flags, rtime)
                self.deletemessage(uid)
                uid = newuid
            statusfolder.savemessage(uid, message, flags, rtime)
        except (KeyboardInterrupt):
            raise
        except:
            self.ui.warn("ERROR attempting to copy message " + str(uid) \
                 + " for account " + self.getaccountname() + ":" \
                 + traceback.format_exc())
            raise

    def syncmessagesto_copy(self, dstfolder, statusfolder):
        """Pass2: Copy locally existing messages

        This will copy messages with a valid UID but are not on the
        other side yet. The strategy is:

        1) Look for messages present in self but not in statusfolder.
        2) invoke copymessageto() on those which:
           - If dstfolder doesn't have it yet, add them to dstfolder.
           - Update statusfolder
        """
        threads = []

        copylist = filter(lambda uid: uid>=0 and not \
                              uid in statusfolder.getmessagelist(),
                            self.getmessagelist().keys())
        for uid in copylist:
            if self.suggeststhreads():
                self.waitforthread()
                thread = threadutil.InstanceLimitedThread(\
                    self.getcopyinstancelimit(),
                    target = self.copymessageto,
                    name = "Copy message %d from %s" % (uid,
                                                        self.getvisiblename()),
                    args = (uid, dstfolder, statusfolder))
                thread.setDaemon(1)
                thread.start()
                threads.append(thread)
            else:
                self.copymessageto(uid, dstfolder, statusfolder, register = 0)

        for thread in threads:
            thread.join()

    def syncmessagesto_delete(self, dstfolder, statusfolder):
        """Pass 3: Remove locally deleted messages on dst

        Get all UIDS in statusfolder but not self. These are messages
        that were deleted in 'self'. Delete those from dstfolder and
        statusfolder."""
        deletelist = filter(lambda uid: uid>=0 \
                                and not uid in self.getmessagelist(),
                            statusfolder.getmessagelist().keys())
        if len(deletelist):
            self.ui.deletingmessages(deletelist, [dstfolder])
            # delete in statusfolder first to play safe. In case of abort, we
            # won't lose message, we will just retransmit some unneccessary.
            for folder in [statusfolder, dstfolder]:
                folder.deletemessages(deletelist)

    def syncmessagesto_flags(self, dstfolder, statusfolder):
        """Pass 4: Flag synchronization

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
        for uid in self.getmessagelist().keys():
            # Ignore messages with negative UIDs missed by pass 1
            # also don't do anything if the message has been deleted remotely
            if uid < 0 or not uid in dstfolder.getmessagelist():
                continue

            selfflags = self.getmessageflags(uid)
            statusflags = statusfolder.getmessageflags(uid)
            #if we could not get message flags from LocalStatus, assume empty.
            if statusflags is None:
                statusflags = []
            addflags = [x for x in selfflags if x not in statusflags]

            for flag in addflags:
                if not flag in addflaglist:
                    addflaglist[flag] = []
                addflaglist[flag].append(uid)

            delflags = [x for x in statusflags if x not in selfflags]
            for flag in delflags:
                if not flag in delflaglist:
                    delflaglist[flag] = []
                delflaglist[flag].append(uid)

        for flag in addflaglist.keys():
            self.ui.addingflags(addflaglist[flag], flag, [dstfolder])
            dstfolder.addmessagesflags(addflaglist[flag], [flag])
            statusfolder.addmessagesflags(addflaglist[flag], [flag])

        for flag in delflaglist.keys():
            self.ui.deletingflags(delflaglist[flag], flag, [dstfolder])
            dstfolder.deletemessagesflags(delflaglist[flag], [flag])
            statusfolder.deletemessagesflags(delflaglist[flag], [flag])
                
    def syncmessagesto(self, dstfolder, statusfolder):
        """Syncs messages in this folder to the destination dstfolder.

        This is the high level entry for syncing messages in one direction.
        Syncsteps are:

        Pass1: Transfer new local messages
         Upload msg with negative/no UIDs to dstfolder. dstfolder
         might assign that message a new UID. Update statusfolder.

        Pass2: Copy locally existing messages
         Copy messages in self, but not statusfolder to dstfolder if not
         already in dstfolder. Update statusfolder.

        Pass3: Remove locally deleted messages
         Get all UIDS in statusfolder but not self. These are messages
         that were deleted in 'self'. Delete those from dstfolder and
         statusfolder.

         After this pass, the message lists should be identical wrt the
         uids present (except for potential negative uids that couldn't
         be placed anywhere).

        Pass4: Synchronize flag changes 
         Compare flag mismatches in self with those in statusfolder. If
         msg has a valid UID and exists on dstfolder (has not e.g. been
         deleted there), sync the flag change to both dstfolder and
         statusfolder.


        :param dstfolder: Folderinstance to sync the msgs to.
        :param statusfolder: LocalStatus instance to sync against.
        """
        passes = [('uploading negative UIDs', self.syncmessagesto_neguid),
                  ('copying messages'       , self.syncmessagesto_copy),
                  ('deleting messages'      , self.syncmessagesto_delete),
                  ('syncing flags'          , self.syncmessagesto_flags)]

        for (passdesc, action) in passes:
            try:
                action(dstfolder, statusfolder)
            except (KeyboardInterrupt):
                raise
            except:
                self.ui.warn("ERROR attempting to sync flags " \
                             + "for account " + self.getaccountname() \
                             + ":" + traceback.format_exc())

                raise
