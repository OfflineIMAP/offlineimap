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

from imapsync import repository
import re

class UIBase:
    ################################################## UTILS
    def _msg(s, msg):
        """Generic tool called when no other works."""
        raise NotImplementedException

    def warn(s, msg):
        s._msg("WARNING: " + msg)

    def getnicename(s, object):
        prelimname = str(object.__class__).split('.')[-1]
        # Strip off extra stuff.
        return re.sub('(Folder|Repository)', '', prelimname)

    ################################################## INPUT

    def getpass(s, accountname, host, port, user):
        raise NotImplementedException

    def folderlist(s, list):
        return ', '.join(["%s[%s]" % (s.getnicename(x), x.getname()) for x in list])

    ################################################## MESSAGES

    def init_banner(s):
        "Display the copyright banner."
        s._msg("""imapsync
        Copyright (C) 2002 John Goerzen.  All rights reserved.
        This software comes with NO WARRANTY: see the file COPYING for details.""")

    def acct(s, accountname):
        s._msg("***** Processing account %s" % accountname)

    def syncfolders(s, srcrepos, destrepos):
        s._msg("Copying folder structure from %s to %s" % \
               (s.getnicename(srcrepos), s.getnicename(destrepos)))

    ############################## Folder syncing
    def syncingfolder(s, srcrepos, srcfolder, destrepos, destfolder):
        """Called when a folder sync operation is started."""
        s._msg("Syncing %s: %s -> %s" % (srcfolder.getname(),
                                         s.getnicename(srcrepos),
                                         s.getnicename(destrepos)))

    def validityproblem(s, folder):
        s.warn("UID validity problem for folder %s; skipping it" % \
               folder.getname())

    def loadmessagelist(s, repos, folder):
        s._msg("Loading message list for %s[%s]" % (s.getnicename(repos),
                                                    folder.getname()))

    def messagelistloaded(s, repos, folder, count):
        s._msg("Message list for %s[%s] loaded: %d messages" % \
               (s.getnicename(repos), folder.getname(), count))

    ############################## Message syncing

    def syncingmessages(s, sr, sf, dr, df):
        s._msg("Syncing messages %s[%s] -> %s[%s]" % (s.getnicename(sr),
                                                      sf.getname(),
                                                      s.getnicename(dr),
                                                      df.getname()))

    def copyingmessage(s, uid, src, destlist):
        ds = s.folderlist(destlist)
        s._msg("Copy message %d %s[%s] -> %s" % (uid, s.getnicename(src),
                                                 src.getname(), ds))

    def deletingmessage(s, uid, destlist):
        ds = s.folderlist(destlist)
        s._msg("Deleting message %d in %s" % (uid, ds))

    def addingflags(s, uid, flags, destlist):
        ds = s.folderlist(destlist)
        s._msg("Adding flags %s to message %d on %s" % \
               (flags.join(", "), uid, ds))

    def deletingflags(s, uid, flags, destlist):
        ds = s.folderlist(destlist)
        s._msg("Deleting flags %s to message %d on %s" % \
               (flags.join(", "), uid, ds))


    
