# Copyright (C) 2007-2015 John Goerzen & contributors
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
try:
    from urllib import urlencode
except ImportError: # python3
    from urllib.parse import urlencode
import sys
import time
import logging
from threading import currentThread
from offlineimap.ui.UIBase import UIBase
import offlineimap

protocol = '7.0.0'

class MachineLogFormatter(logging.Formatter):
    """urlencodes any outputted line, to avoid multi-line output"""
    def format(s, record):
        # Mapping of log levels to historic tag names
        severity_map = {
         'info': 'msg',
         'warning': 'warn',
        }
        line = super(MachineLogFormatter, s).format(record)
        severity = record.levelname.lower()
        if severity in severity_map:
            severity = severity_map[severity]
        if hasattr(record, "machineui"):
            command = record.machineui["command"]
            whoami = record.machineui["id"]
        else:
            command = ""
            whoami = currentThread().getName()

        prefix = "%s:%s"% (command, urlencode([('', whoami)])[1:])
        return "%s:%s:%s"% (severity, prefix, urlencode([('', line)])[1:])


class MachineUI(UIBase):
    def __init__(s, config, loglevel=logging.INFO):
        super(MachineUI, s).__init__(config, loglevel)
        s._log_con_handler.createLock()
        """lock needed to block on password input"""
        # Set up the formatter that urlencodes the strings...
        s._log_con_handler.setFormatter(MachineLogFormatter())

    # Arguments:
    # - handler: must be method from s.logger that reflects
    #   the severity of the passed message
    # - command: command that produced this message
    # - msg: the message itself
    def _printData(s, handler, command, msg):
        handler(msg,
                extra = {
                  'machineui': {
                   'command': command,
                   'id': currentThread().getName(),
                  }
                })

    def _msg(s, msg):
        s._printData(s.logger.info, '_display', msg)

    def warn(s, msg, minor=0):
        # TODO, remove and cleanup the unused minor stuff
        s._printData(s.logger.warning, '', msg)

    def registerthread(s, account):
        super(MachineUI, s).registerthread(account)
        s._printData(s.logger.info, 'registerthread', account)

    def unregisterthread(s, thread):
        UIBase.unregisterthread(s, thread)
        s._printData(s.logger.info, 'unregisterthread', thread.getName())

    def debugging(s, debugtype):
        s._printData(s.logger.debug, 'debugging', debugtype)

    def acct(s, accountname):
        s._printData(s.logger.info, 'acct', accountname)

    def acctdone(s, accountname):
        s._printData(s.logger.info, 'acctdone', accountname)

    def validityproblem(s, folder):
        s._printData(s.logger.warning, 'validityproblem', "%s\n%s\n%s\n%s"%
                (folder.getname(), folder.getrepository().getname(),
                 folder.get_saveduidvalidity(), folder.get_uidvalidity()))

    def connecting(s, hostname, port):
        s._printData(s.logger.info, 'connecting', "%s\n%s"% (hostname, str(port)))

    def syncfolders(s, srcrepos, destrepos):
        s._printData(s.logger.info, 'syncfolders', "%s\n%s"% (s.getnicename(srcrepos),
                                                s.getnicename(destrepos)))

    def syncingfolder(s, srcrepos, srcfolder, destrepos, destfolder):
        s._printData(s.logger.info, 'syncingfolder', "%s\n%s\n%s\n%s\n"%
                (s.getnicename(srcrepos), srcfolder.getname(),
                 s.getnicename(destrepos), destfolder.getname()))

    def loadmessagelist(s, repos, folder):
        s._printData(s.logger.info, 'loadmessagelist', "%s\n%s"% (s.getnicename(repos),
                                                    folder.getvisiblename()))

    def messagelistloaded(s, repos, folder, count):
        s._printData(s.logger.info, 'messagelistloaded', "%s\n%s\n%d"%
                (s.getnicename(repos), folder.getname(), count))

    def syncingmessages(s, sr, sf, dr, df):
        s._printData(s.logger.info, 'syncingmessages', "%s\n%s\n%s\n%s\n"%
                (s.getnicename(sr), sf.getname(), s.getnicename(dr),
                 df.getname()))

    def copyingmessage(s, uid, num, num_to_copy, srcfolder, destfolder):
        s._printData(s.logger.info, 'copyingmessage', "%d\n%s\n%s\n%s[%s]"%
                (uid, s.getnicename(srcfolder), srcfolder.getname(),
                 s.getnicename(destfolder), destfolder))

    def folderlist(s, list):
        return ("\f".join(["%s\t%s"% (s.getnicename(x), x.getname()) for x in list]))

    def uidlist(s, list):
        return ("\f".join([str(u) for u in list]))

    def deletingmessages(s, uidlist, destlist):
        ds = s.folderlist(destlist)
        s._printData(s.logger.info, 'deletingmessages', "%s\n%s"% (s.uidlist(uidlist), ds))

    def addingflags(s, uidlist, flags, dest):
        s._printData(s.logger.info, "addingflags", "%s\n%s\n%s"% (s.uidlist(uidlist),
                                                    "\f".join(flags),
                                                    dest))

    def deletingflags(s, uidlist, flags, dest):
        s._printData(s.logger.info, 'deletingflags', "%s\n%s\n%s"% (s.uidlist(uidlist),
                                                      "\f".join(flags),
                                                      dest))

    def threadException(s, thread):
        s._printData(s.logger.warning, 'threadException', "%s\n%s"%
                     (thread.getName(), s.getThreadExceptionString(thread)))
        s.delThreadDebugLog(thread)
        s.terminate(100)

    def terminate(s, exitstatus=0, errortitle='', errormsg=''):
        s._printData(s.logger.info, 'terminate', "%d\n%s\n%s"% (exitstatus, errortitle, errormsg))
        sys.exit(exitstatus)

    def mainException(s):
        s._printData(s.logger.warning, 'mainException', s.getMainExceptionString())

    def threadExited(s, thread):
        s._printData(s.logger.info, 'threadExited', thread.getName())
        UIBase.threadExited(s, thread)

    def sleeping(s, sleepsecs, remainingsecs):
        s._printData(s.logger.info, 'sleeping', "%d\n%d"% (sleepsecs, remainingsecs))
        if sleepsecs > 0:
            time.sleep(sleepsecs)
        return 0


    def getpass(s, accountname, config, errmsg=None):
        if errmsg:
            s._printData(s.logger.warning,
              'getpasserror', "%s\n%s"% (accountname, errmsg),
              False)

        s._log_con_handler.acquire() # lock the console output
        try:
            s._printData(s.logger.info, 'getpass', accountname)
            return (sys.stdin.readline()[:-1])
        finally:
            s._log_con_handler.release()

    def init_banner(s):
        s._printData(s.logger.info, 'protocol', protocol)
        s._printData(s.logger.info, 'initbanner', offlineimap.banner)

    def callhook(s, msg):
        s._printData(s.logger.info, 'callhook', msg)
