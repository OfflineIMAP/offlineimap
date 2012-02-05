# Copyright (C) 2007-2011 John Goerzen & contributors
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
from urllib import urlencode
import sys
import time
import logging
from threading import currentThread
from offlineimap.ui.UIBase import UIBase
import offlineimap

protocol = '7.0.0'

class MachineLogFormatter(logging.Formatter):
    """urlencodes any outputted line, to avoid multi-line output"""
    def format(self, record):
        # urlencode the "mesg" attribute and append to regular line...
        line = super(MachineLogFormatter, self).format(record)
        return line + urlencode([('', record.mesg)])[1:]

class MachineUI(UIBase):
    def __init__(self, config, loglevel = logging.INFO):
        super(MachineUI, self).__init__(config, loglevel)
        self._log_con_handler.createLock()
        """lock needed to block on password input"""
        # Set up the formatter that urlencodes the strings...
        self._log_con_handler.setFormatter(MachineLogFormatter())

    def _printData(self, command, msg):
        self.logger.info("%s:%s:%s" % (
                'msg', command, currentThread().getName()), extra={'mesg': msg})

    def _msg(s, msg):
        s._printData('_display', msg)

    def warn(self, msg, minor = 0):
        # TODO, remove and cleanup the unused minor stuff
        self.logger.warning("%s:%s:%s:%s" % (
                'warn', '', currentThread().getName(), msg))

    def registerthread(self, account):
        super(MachineUI, self).registerthread(account)
        self._printData('registerthread', account)

    def unregisterthread(s, thread):
        UIBase.unregisterthread(s, thread)
        s._printData('unregisterthread', thread.getName())

    def debugging(s, debugtype):
        s._printData('debugging', debugtype)

    def acct(s, accountname):
        s._printData('acct', accountname)

    def acctdone(s, accountname):
        s._printData('acctdone', accountname)

    def validityproblem(s, folder):
        s._printData('validityproblem', "%s\n%s\n%s\n%s" % \
                (folder.getname(), folder.getrepository().getname(),
                 folder.get_saveduidvalidity(), folder.get_uidvalidity()))

    def connecting(s, hostname, port):
        s._printData('connecting', "%s\n%s" % (hostname, str(port)))

    def syncfolders(s, srcrepos, destrepos):
        s._printData('syncfolders', "%s\n%s" % (s.getnicename(srcrepos), 
                                                s.getnicename(destrepos)))

    def syncingfolder(s, srcrepos, srcfolder, destrepos, destfolder):
        s._printData('syncingfolder', "%s\n%s\n%s\n%s\n" % \
                (s.getnicename(srcrepos), srcfolder.getname(),
                 s.getnicename(destrepos), destfolder.getname()))

    def loadmessagelist(s, repos, folder):
        s._printData('loadmessagelist', "%s\n%s" % (s.getnicename(repos),
                                                    folder.getvisiblename()))

    def messagelistloaded(s, repos, folder, count):
        s._printData('messagelistloaded', "%s\n%s\n%d" % \
                (s.getnicename(repos), folder.getname(), count))

    def syncingmessages(s, sr, sf, dr, df):
        s._printData('syncingmessages', "%s\n%s\n%s\n%s\n" % \
                (s.getnicename(sr), sf.getname(), s.getnicename(dr),
                 df.getname()))

    def copyingmessage(self, uid, num, num_to_copy, srcfolder, destfolder):
        self._printData('copyingmessage', "%d\n%s\n%s\n%s[%s]" % \
                (uid, self.getnicename(srcfolder), srcfolder.getname(),
                 self.getnicename(destfolder), destfolder))

    def folderlist(s, list):
        return ("\f".join(["%s\t%s" % (s.getnicename(x), x.getname()) for x in list]))

    def uidlist(s, list):
        return ("\f".join([str(u) for u in list]))

    def deletingmessages(s, uidlist, destlist):
        ds = s.folderlist(destlist)
        s._printData('deletingmessages', "%s\n%s" % (s.uidlist(uidlist), ds))

    def addingflags(s, uidlist, flags, dest):
        s._printData("addingflags", "%s\n%s\n%s" % (s.uidlist(uidlist),
                                                    "\f".join(flags),
                                                    dest))

    def deletingflags(s, uidlist, flags, dest):
        s._printData('deletingflags', "%s\n%s\n%s" % (s.uidlist(uidlist),
                                                      "\f".join(flags),
                                                      dest))

    def threadException(s, thread):
        print s.getThreadExceptionString(thread)
        s._printData('threadException', "%s\n%s" % \
                     (thread.getName(), s.getThreadExceptionString(thread)))
        s.delThreadDebugLog(thread)
        s.terminate(100)

    def terminate(s, exitstatus = 0, errortitle = '', errormsg = ''):
        s._printData('terminate', "%d\n%s\n%s" % (exitstatus, errortitle, errormsg))
        sys.exit(exitstatus)

    def mainException(s):
        s._printData('mainException', s.getMainExceptionString())

    def threadExited(s, thread):
        s._printData('threadExited', thread.getName())
        UIBase.threadExited(s, thread)

    def sleeping(s, sleepsecs, remainingsecs):
        s._printData('sleeping', "%d\n%d" % (sleepsecs, remainingsecs))
        if sleepsecs > 0:
            time.sleep(sleepsecs)
        return 0


    def getpass(self, accountname, config, errmsg = None):
        if errmsg:
            self._printData('getpasserror', "%s\n%s" % (accountname, errmsg),
                         False)

        self._log_con_handler.acquire() # lock the console output
        try:
            self._printData('getpass', accountname, False)
            return (sys.stdin.readline()[:-1])
        finally:
            self._log_con_handler.release()

    def init_banner(self):
        self._printData('protocol', protocol)
        self._printData('initbanner', offlineimap.banner)

    def callhook(self, msg):
        self._printData('callhook', msg)
