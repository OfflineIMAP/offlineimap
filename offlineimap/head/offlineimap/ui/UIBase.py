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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from offlineimap import repository
import offlineimap.version
import re, time, sys, traceback
from StringIO import StringIO

class UIBase:
    def __init__(s, verbose = 0):
        s.verbose = verbose
    
    ################################################## UTILS
    def _msg(s, msg):
        """Generic tool called when no other works."""
        raise NotImplementedError

    def warn(s, msg):
        s._msg("WARNING: " + msg)

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

    def getpass(s, accountname, config):
        raise NotImplementedError

    def folderlist(s, list):
        return ', '.join(["%s[%s]" % (s.getnicename(x), x.getname()) for x in list])

    ################################################## MESSAGES

    def init_banner(s):
        """Called when the UI starts.  Must be called before any other UI
        call except isusable().  Displays the copyright banner.  This is
        where the UI should do its setup -- TK, for instance, would
        create the application window here."""
        if s.verbose >= 0:
            s._msg(offlineimap.version.banner)

    def acct(s, accountname):
        if s.verbose >= 0:
            s._msg("***** Processing account %s" % accountname)

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

    def validityproblem(s, folder):
        s.warn("UID validity problem for folder %s; skipping it" % \
               folder.getname())

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

    def addingflags(s, uid, flags, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Adding flags %s to message %d on %s" % \
                   (", ".join(flags), uid, ds))

    def deletingflags(s, uid, flags, destlist):
        if s.verbose >= 0:
            ds = s.folderlist(destlist)
            s._msg("Deleting flags %s to message %d on %s" % \
                   (", ".join(flags), uid, ds))

    ################################################## Threads

    def threadException(s, thread):
        """Called when a thread has terminated with an exception.
        The argument is the ExitNotifyThread that has so terminated."""
        s._msg("Thread '%s' terminated with exception:\n%s" % \
               (thread.getName(), thread.getExitStackTrace()))
        s.terminate(100)

    def mainException(s):
        sbuf = StringIO()
        traceback.print_exc(file = sbuf)
        s._msg("Main program terminated with exception:\n" +
               sbuf.getvalue())

    def terminate(s, exitstatus = 0):
        """Called to terminate the application."""
        sys.exit(exitstatus)

    def threadExited(s, thread):
        """Called when a thread has exited normally.  Many UIs will
        just ignore this."""
        pass

    ################################################## Other

    def sleep(s, sleepsecs):
        """This function does not actually output anything, but handles
        the overall sleep, dealing with updates as necessary.  It will,
        however, call sleeping() which DOES output something.

        Returns 0 if timeout expired, 1 if there is a request to cancel
        the timer, and 2 if there is a request to abort the program."""

        abortsleep = 0
        while sleepsecs > 0 and not abortsleep:
            abortsleep = s.sleeping(1, sleepsecs)
            sleepsecs -= 1
        s.sleeping(0, 0)               # Done sleeping.
        return abortsleep

    def sleeping(s, sleepsecs, remainingsecs):
        """Sleep for sleepsecs, remainingsecs to go.
        If sleepsecs is 0, indicates we're done sleeping.

        Return 0 for normal sleep, or 1 to indicate a request
        to sync immediately."""
        s._msg("Next refresh in %d seconds" % remainingsecs)
        if sleepsecs > 0:
            time.sleep(sleepsecs)
        return 0
