# UI base class
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

import re
import time
import sys
import traceback
import threading
from Queue import Queue
import offlineimap

debugtypes = {'':'Other offlineimap related sync messages',
              'imap': 'IMAP protocol debugging',
              'maildir': 'Maildir repository debugging',
              'thread': 'Threading debugging'}

globalui = None
def setglobalui(newui):
    """Set the global ui object to be used for logging"""
    global globalui
    globalui = newui
def getglobalui():
    """Return the current ui object"""
    global globalui
    return globalui

class UIBase:
    def __init__(s, config, verbose = 0):
        s.verbose = verbose
        s.config = config
        s.debuglist = []
        s.debugmessages = {}
        s.debugmsglen = 50
        s.threadaccounts = {}
        """dict linking active threads (k) to account names (v)"""
        s.acct_startimes = {}
        """linking active accounts with the time.time() when sync started"""
        s.logfile = None
        s.exc_queue = Queue()
        """saves all occuring exceptions, so we can output them at the end"""

    ################################################## UTILS
    def _msg(s, msg):
        """Generic tool called when no other works."""
        s._log(msg)
        s._display(msg)

    def _log(s, msg):
        """Log it to disk.  Returns true if it wrote something; false
        otherwise."""
        if s.logfile:
            s.logfile.write("%s: %s\n" % (threading.currentThread().getName(),
                                          msg))
            return 1
        return 0

    def setlogfd(s, logfd):
        s.logfile = logfd
        logfd.write("This is %s %s\n" % \
                    (offlineimap.__productname__,
                     offlineimap.__version__))
        logfd.write("Python: %s\n" % sys.version)
        logfd.write("Platform: %s\n" % sys.platform)
        logfd.write("Args: %s\n" % sys.argv)

    def _display(s, msg):
        """Display a message."""
        raise NotImplementedError

    def warn(s, msg, minor = 0):
        if minor:
            s._msg("warning: " + msg)
        else:
            s._msg("WARNING: " + msg)

    def error(self, exc, exc_traceback=None, msg=None):
        """Log a message at severity level ERROR

        Log Exception 'exc' to error log, possibly prepended by a preceding
        error "msg", detailing at what point the error occurred.

        In debug mode, we also output the full traceback that occurred
        if one has been passed in via sys.info()[2].

        Also save the Exception to a stack that can be output at the end
        of the sync run when offlineiamp exits. It is recommended to
        always pass in exceptions if possible, so we can give the user
        the best debugging info.

        One example of such a call might be:

           ui.error(exc, sys.exc_info()[2], msg="While syncing Folder %s in "
                                                "repo %s")
        """
        if msg:
            self._msg("ERROR: %s\n  %s" % (msg, exc))
        else:
            self._msg("ERROR: %s" % (exc))

        if not self.debuglist:
            # only output tracebacks in debug mode
            exc_traceback = None
        # push exc on the queue for later output
        self.exc_queue.put((msg, exc, exc_traceback))
        if exc_traceback:
            self._msg(traceback.format_tb(exc_traceback))

    def registerthread(self, account):
        """Register current thread as being associated with an account name"""
        cur_thread = threading.currentThread()
        if cur_thread in self.threadaccounts:
            # was already associated with an old account, update info
            self.debug('thread', "Register thread '%s' (previously '%s', now "
                    "'%s')" % (cur_thread.getName(),
                               self.getthreadaccount(cur_thread), account))
        else:
            self.debug('thread', "Register new thread '%s' (account '%s')" %\
                        (cur_thread.getName(), account))
        self.threadaccounts[cur_thread] = account

    def unregisterthread(self, thr):
        """Unregister a thread as being associated with an account name"""
        if self.threadaccounts.has_key(thr):
            del self.threadaccounts[thr]
        self.debug('thread', "Unregister thread '%s'" % thr.getName())

    def getthreadaccount(self, thr = None):
        """Get name of account for a thread (current if None)"""
        if not thr:
            thr = threading.currentThread()
        if thr in self.threadaccounts:
            return self.threadaccounts[thr]
        return '*Control' # unregistered thread is '*Control'

    def debug(s, debugtype, msg):
        thisthread = threading.currentThread()
        if s.debugmessages.has_key(thisthread):
            s.debugmessages[thisthread].append("%s: %s" % (debugtype, msg))
        else:
            s.debugmessages[thisthread] = ["%s: %s" % (debugtype, msg)]

        while len(s.debugmessages[thisthread]) > s.debugmsglen:
            s.debugmessages[thisthread] = s.debugmessages[thisthread][1:]

        if debugtype in s.debuglist:
            if not s._log("DEBUG[%s]: %s" % (debugtype, msg)):
                s._display("DEBUG[%s]: %s" % (debugtype, msg))

    def add_debug(s, debugtype):
        global debugtypes
        if debugtype in debugtypes:
            if not debugtype in s.debuglist:
                s.debuglist.append(debugtype)
                s.debugging(debugtype)
        else:
            s.invaliddebug(debugtype)

    def debugging(s, debugtype):
        global debugtypes
        s._msg("Now debugging for %s: %s" % (debugtype, debugtypes[debugtype]))

    def invaliddebug(s, debugtype):
        s.warn("Invalid debug type: %s" % debugtype)

    def locked(s):
        raise Exception, "Another OfflineIMAP is running with the same metadatadir; exiting."

    def getnicename(s, object):
        """Return the type of a repository or Folder as string

        (IMAP, Gmail, Maildir, etc...)"""
        prelimname = object.__class__.__name__.split('.')[-1]
        # Strip off extra stuff.
        return re.sub('(Folder|Repository)', '', prelimname)

    def isusable(s):
        """Returns true if this UI object is usable in the current
        environment.  For instance, an X GUI would return true if it's
        being run in X with a valid DISPLAY setting, and false otherwise."""
        return 1

    ################################################## INPUT

    def getpass(s, accountname, config, errmsg = None):
        raise NotImplementedError

    def folderlist(s, list):
        return ', '.join(["%s[%s]" % (s.getnicename(x), x.getname()) for x in list])

    ################################################## WARNINGS
    def msgtoreadonly(s, destfolder, uid, content, flags):
        if not (s.config.has_option('general', 'ignore-readonly') and s.config.getboolean("general", "ignore-readonly")):
            s.warn("Attempted to synchronize message %d to folder %s[%s], but that folder is read-only.  The message will not be copied to that folder." % \
                   (uid, s.getnicename(destfolder), destfolder.getname()))

    def flagstoreadonly(s, destfolder, uidlist, flags):
        if not (s.config.has_option('general', 'ignore-readonly') and s.config.getboolean("general", "ignore-readonly")):
            s.warn("Attempted to modify flags for messages %s in folder %s[%s], but that folder is read-only.  No flags have been modified for that message." % \
                   (str(uidlist), s.getnicename(destfolder), destfolder.getname()))

    def deletereadonly(s, destfolder, uidlist):
        if not (s.config.has_option('general', 'ignore-readonly') and s.config.getboolean("general", "ignore-readonly")):
            s.warn("Attempted to delete messages %s in folder %s[%s], but that folder is read-only.  No messages have been deleted in that folder." % \
                   (str(uidlist), s.getnicename(destfolder), destfolder.getname()))

    ################################################## MESSAGES

    def init_banner(s):
        """Called when the UI starts.  Must be called before any other UI
        call except isusable().  Displays the copyright banner.  This is
        where the UI should do its setup -- TK, for instance, would
        create the application window here."""
        if s.verbose >= 0:
            s._msg(offlineimap.banner)

    def connecting(s, hostname, port):
        """Log 'Establishing connection to'"""
        if s.verbose < 0: return
        displaystr = ''
        hostname = hostname if hostname else ''
        port = "%d" % port if port else ''
        if hostname:
            displaystr = ' to %s:%s' % (hostname, port)
        s._msg("Establishing connection%s" % displaystr)

    def acct(self, account):
        """Output that we start syncing an account (and start counting)"""
        self.acct_startimes[account] = time.time()
        if self.verbose >= 0:
            self._msg("*** Processing account %s" % account)

    def acctdone(self, account):
        """Output that we finished syncing an account (in which time)"""
        sec = time.time() - self.acct_startimes[account]
        del self.acct_startimes[account]
        self._msg("*** Finished account '%s' in %d:%02d" %
               (account, sec // 60, sec % 60))

    def syncfolders(s, srcrepos, destrepos):
        if s.verbose >= 0:
            s._msg("Copying folder structure from %s to %s" % \
                   (s.getnicename(srcrepos), s.getnicename(destrepos)))

    ############################## Folder syncing
    def syncingfolder(s, srcrepos, srcfolder, destrepos, destfolder):
        """Called when a folder sync operation is started."""
        if s.verbose >= 0:
            s._msg("Syncing %s: %s -> %s" % (srcfolder.getname(),
                                             s.getnicename(srcrepos),
                                             s.getnicename(destrepos)))

    def skippingfolder(s, folder):
        """Called when a folder sync operation is started."""
        if s.verbose >= 0:
            s._msg("Skipping %s (not changed)" % folder.getname())

    def validityproblem(s, folder):
        s.warn("UID validity problem for folder %s (repo %s) (saved %d; got %d); skipping it" % \
               (folder.getname(), folder.getrepository().getname(),
                folder.getsaveduidvalidity(), folder.getuidvalidity()))

    def loadmessagelist(s, repos, folder):
        if s.verbose > 0:
            s._msg("Loading message list for %s[%s]" % (s.getnicename(repos),
                                                        folder.getname()))

    def messagelistloaded(s, repos, folder, count):
        if s.verbose > 0:
            s._msg("Message list for %s[%s] loaded: %d messages" % \
                   (s.getnicename(repos), folder.getname(), count))

    ############################## Message syncing

    def syncingmessages(s, sr, sf, dr, df):
        if s.verbose > 0:
            s._msg("Syncing messages %s[%s] -> %s[%s]" % (s.getnicename(sr),
                                                          sf.getname(),
                                                          s.getnicename(dr),
                                                          df.getname()))

    def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
        """Output a log line stating which message we copy"""
        if self.verbose < 0: return
        self._msg("Copy message %s (%d of %d) %s:%s -> %s" % (uid, num,
                  num_to_copy, src.repository, src, destfolder.repository))

    def deletingmessage(s, uid, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Deleting message %d in %s" % (uid, ds))

    def deletingmessages(s, uidlist, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Deleting %d messages (%s) in %s" % \
                   (len(uidlist),
                    offlineimap.imaputil.uid_sequence(uidlist),
                    ds))

    def addingflags(s, uidlist, flags, dest):
        if s.verbose >= 0:
            s._msg("Adding flag %s to %d messages on %s" % \
                   (", ".join(flags), len(uidlist), dest))

    def deletingflags(s, uidlist, flags, dest):
        if s.verbose >= 0:
            s._msg("Deleting flag %s from %d messages on %s" % \
                   (", ".join(flags), len(uidlist), dest))

    ################################################## Threads

    def getThreadDebugLog(s, thread):
        if s.debugmessages.has_key(thread):
            message = "\nLast %d debug messages logged for %s prior to exception:\n"\
                       % (len(s.debugmessages[thread]), thread.getName())
            message += "\n".join(s.debugmessages[thread])
        else:
            message = "\nNo debug messages were logged for %s." % \
                      thread.getName()
        return message

    def delThreadDebugLog(s, thread):
        if s.debugmessages.has_key(thread):
            del s.debugmessages[thread]

    def getThreadExceptionString(s, thread):
        message = "Thread '%s' terminated with exception:\n%s" % \
                  (thread.getName(), thread.getExitStackTrace())
        message += "\n" + s.getThreadDebugLog(thread)
        return message

    def threadException(s, thread):
        """Called when a thread has terminated with an exception.
        The argument is the ExitNotifyThread that has so terminated."""
        s._msg(s.getThreadExceptionString(thread))
        s.delThreadDebugLog(thread)
        s.terminate(100)

    def terminate(self, exitstatus = 0, errortitle = None, errormsg = None):
        """Called to terminate the application."""
        #print any exceptions that have occurred over the run
        if not self.exc_queue.empty():
           self._msg("\nERROR: Exceptions occurred during the run!")
        while not self.exc_queue.empty():
            msg, exc, exc_traceback = self.exc_queue.get()
            if msg:
                self._msg("ERROR: %s\n  %s" % (msg, exc))
            else:
                self._msg("ERROR: %s" % (exc))
            if exc_traceback:
                self._msg("\nTraceback:\n%s" %"".join(
                        traceback.format_tb(exc_traceback)))

        if errormsg and errortitle:
            sys.stderr.write('ERROR: %s\n\n%s\n'%(errortitle, errormsg))
        elif errormsg:
                sys.stderr.write('%s\n' % errormsg)
        sys.exit(exitstatus)

    def threadExited(s, thread):
        """Called when a thread has exited normally.  Many UIs will
        just ignore this."""
        s.delThreadDebugLog(thread)
        s.unregisterthread(thread)

    ################################################## Hooks

    def callhook(s, msg):
        if s.verbose >= 0:
            s._msg(msg)

    ################################################## Other

    def sleep(s, sleepsecs, account):
        """This function does not actually output anything, but handles
        the overall sleep, dealing with updates as necessary.  It will,
        however, call sleeping() which DOES output something.

        :returns: 0/False if timeout expired, 1/2/True if there is a
                  request to cancel the timer.
        """
        abortsleep = False
        while sleepsecs > 0 and not abortsleep:
            if account.get_abort_event():
               abortsleep = True
            else:
                abortsleep = s.sleeping(10, sleepsecs)
                sleepsecs -= 10            
        s.sleeping(0, 0)  # Done sleeping.
        return abortsleep

    def sleeping(s, sleepsecs, remainingsecs):
        """Sleep for sleepsecs, display remainingsecs to go.

        Does nothing if sleepsecs <= 0.
        Display a message on the screen if we pass a full minute.

        This implementation in UIBase does not support this, but some
        implementations return 0 for successful sleep and 1 for an
        'abort', ie a request to sync immediately.
        """
        if sleepsecs > 0:
            if remainingsecs//60 != (remainingsecs-sleepsecs)//60:
                s._msg("Next refresh in %.1f minutes" % (remainingsecs/60.0))
            time.sleep(sleepsecs)
        return 0
