# UI base class
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

import re
import time
import sys
import traceback
import threading
from StringIO import StringIO
from Queue import Empty
import offlineimap

debugtypes = {'imap': 'IMAP protocol debugging',
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
        s.logfile = None
    
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

    def registerthread(s, account):
        """Provides a hint to UIs about which account this particular
        thread is processing."""
        if s.threadaccounts.has_key(threading.currentThread()):
            raise ValueError, "Thread %s already registered (old %s, new %s)" %\
                  (threading.currentThread().getName(),
                   s.getthreadaccount(s), account)
        s.threadaccounts[threading.currentThread()] = account

    def unregisterthread(s, thr):
        """Recognizes a thread has exited."""
        if s.threadaccounts.has_key(thr):
            del s.threadaccounts[thr]

    def getthreadaccount(s, thr = None):
        if not thr:
            thr = threading.currentThread()
        if s.threadaccounts.has_key(thr):
            return s.threadaccounts[thr]
        return '*Control'

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
        prelimname = str(object.__class__).split('.')[-1]
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
        if s.verbose < 0:
            return
        if hostname == None:
            hostname = ''
        if port != None:
            port = ":%s" % str(port)
        displaystr = ' to %s%s.' % (hostname, port)
        if hostname == '' and port == None:
            displaystr = '.'
        s._msg("Establishing connection" + displaystr)

    def acct(s, accountname):
        if s.verbose >= 0:
            s._msg("***** Processing account %s" % accountname)

    def acctdone(s, accountname):
        if s.verbose >= 0:
            s._msg("***** Finished processing account " + accountname)

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

    def copyingmessage(s, uid, src, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Copy message %d %s[%s] -> %s" % (uid, s.getnicename(src),
                                                     src.getname(), ds))

    def deletingmessage(s, uid, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Deleting message %d in %s" % (uid, ds))

    def deletingmessages(s, uidlist, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Deleting %d messages (%s) in %s" % \
                   (len(uidlist),
                    ", ".join([str(u) for u in uidlist]),
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

    def getMainExceptionString(s):
        sbuf = StringIO()
        traceback.print_exc(file = sbuf)
        return "Main program terminated with exception:\n" + \
               sbuf.getvalue() + "\n" + \
               s.getThreadDebugLog(threading.currentThread())

    def mainException(s):
        s._msg(s.getMainExceptionString())

    def terminate(s, exitstatus = 0, errortitle = None, errormsg = None):
        """Called to terminate the application."""
        if errormsg <> None:
            if errortitle <> None:
                sys.stderr.write('ERROR: %s\n\n%s\n'%(errortitle, errormsg))
            else:
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

    def sleep(s, sleepsecs, siglistener):
        """This function does not actually output anything, but handles
        the overall sleep, dealing with updates as necessary.  It will,
        however, call sleeping() which DOES output something.

        Returns 0 if timeout expired, 1 if there is a request to cancel
        the timer, and 2 if there is a request to abort the program."""

        abortsleep = 0
        while sleepsecs > 0 and not abortsleep:
            try:
                abortsleep = siglistener.get_nowait()
                # retrieved signal while sleeping: 1 means immediately resynch, 2 means immediately die
            except Empty:
                # no signal
                abortsleep = s.sleeping(10, sleepsecs)
            sleepsecs -= 10
        s.sleeping(0, 0)               # Done sleeping.
        return abortsleep

    def sleeping(s, sleepsecs, remainingsecs):
        """Sleep for sleepsecs, display remainingsecs to go.

        Does nothing if sleepsecs <= 0.
        Display a message on the screen every 10 seconds.

        This implementation in UIBase does not support this, but some
        implementations return 0 for successful sleep and 1 for an
        'abort', ie a request to sync immediately.
        """
        if sleepsecs > 0:
            if remainingsecs % 10 == 0:
                s._msg("Next refresh in %d seconds" % remainingsecs)
            time.sleep(sleepsecs)
        return 0
