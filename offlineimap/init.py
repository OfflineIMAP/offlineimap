# OfflineIMAP initialization code
# Copyright (C) 2002-2007 John Goerzen
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

import imaplib
from offlineimap import imapserver, threadutil, version, syncmaster, accounts
from offlineimap.localeval import LocalEval
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
import offlineimap.ui
from offlineimap.CustomConfig import CustomConfigParser
from offlineimap.ui.detector import DEFAULT_UI_LIST
from optparse import OptionParser
import re, os, sys
from threading import *
import threading, socket
import signal
import logging

try:
    import fcntl
    hasfcntl = 1
except:
    hasfcntl = 0

lockfd = None

class OfflineImap:
    """The main class that encapsulates the high level use of OfflineImap.

    To invoke OfflineImap you would call it with:
    oi = OfflineImap()
    oi.run()
    """
    def lock(self, config, ui):
        global lockfd, hasfcntl
        if not hasfcntl:
            return
        lockfd = open(config.getmetadatadir() + "/lock", "w")
        try:
            fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            ui.locked()
            ui.terminate(1)
    
    def run(self):
        """Parse the commandline and invoke everything"""

        parser = OptionParser()
        parser.add_option("-1",
                  action="store_true", dest="singlethreading",
                  default=False,
                  help="Disable all multithreading operations and use "
              "solely a single-thread sync. This effectively sets the "
              "maxsyncaccounts and all maxconnections configuration file "
              "variables to 1.")

        parser.add_option("-P", dest="profiledir", metavar="DIR",
                  help="Sets OfflineIMAP into profile mode. The program "
              "will create DIR (it must not already exist). "
              "As it runs, Python profiling information about each "
              "thread is logged into profiledir. Please note: "
              "This option is present for debugging and optimization "
              "only, and should NOT be used unless you have a "
              "specific reason to do so. It will significantly "
              "decrease program performance, may reduce reliability, "
              "and can generate huge amounts of data. This option "
              "implies the -1 option.")

        parser.add_option("-a", dest="accounts", metavar="ACCOUNTS",
                  help="""Overrides the accounts section in the config file.
              Lets you specify a particular account or set of
              accounts to sync without having to edit the config
              file. You might use this to exclude certain accounts,
              or to sync some accounts that you normally prefer not to.""")

        parser.add_option("-c", dest="configfile", metavar="FILE",
                  default="~/.offlineimaprc",
                  help="Specifies a configuration file to use in lieu of "
                       "the default, ~/.offlineimaprc.")

        parser.add_option("-d", dest="debugtype", metavar="type1,[type2...]",
                  help=
              "Enables debugging for OfflineIMAP. This is useful "
              "if you are trying to track down a malfunction or "
              "figure out what is going on under the hood. It is recommended "
              "to use this with -1 in order to make the "
              "results more sensible. This option requires one or more "
              "debugtypes, separated by commas. "
              "These define what exactly will be debugged, "
              "and so far include two options: imap, "
              "maildir or ALL. The imap option will enable IMAP protocol "
              "stream and parsing debugging. Note that the output "
              "may contain passwords, so take care to remove that "
              "from the debugging output before sending it to anyone else. "
              "The maildir option will enable debugging "
              "for certain Maildir operations.")

        parser.add_option("-l", dest="logfile", metavar="FILE",
                  help="Log to FILE")

        parser.add_option("-f", dest="folders", metavar="folder1,[folder2...]",
                  help=
              "Only sync the specified folders. The folder names "
              "are the *untranslated* foldernames. This "
              "command-line option overrides any 'folderfilter' "
              "and 'folderincludes' options in the configuration " 
              "file.")

        parser.add_option("-k", dest="configoverride",
                  action="append",
                  metavar="[section:]option=value",
                  help=
              """Override configuration file option. If"section" is
              omitted, it defaults to "general". Any underscores
              in the section name are replaced with spaces:
              for instance, to override option "autorefresh" in
              the "[Account Personal]" section in the config file
              one would use "-k Account_Personal:autorefresh=30".""")

        parser.add_option("-o",
                  action="store_true", dest="runonce",
                  default=False,
                  help="Run only once, ignoring any autorefresh setting "
                       "in the configuration file.")

        parser.add_option("-q",
                  action="store_true", dest="quick",
                  default=False,
                  help="Run only quick synchronizations. Ignore any "
              "flag updates on IMAP servers (if a flag on the remote IMAP "
              "changes, and we have the message locally, it will be left "
              "untouched in a quick run.")

        parser.add_option("-u", dest="interface",
                  help="Specifies an alternative user interface to "
              "use. This overrides the default specified in the "
              "configuration file. The UI specified with -u will "
              "be forced to be used, even if checks determine that it is "
              "not usable. Possible interface choices are: %s " %
              ", ".join(DEFAULT_UI_LIST))

        (options, args) = parser.parse_args()

        #read in configuration file
        configfilename = os.path.expanduser(options.configfile)
    
        config = CustomConfigParser()
        if not os.path.exists(configfilename):
            logging.error(" *** Config file '%s' does not exist; aborting!" %
                          configfilename)
            sys.exit(1)
        config.read(configfilename)

        #profile mode chosen?
        if options.profiledir:
            if not options.singlethreading:
                logging.warn("Profile mode: Forcing to singlethreaded.")
                options.singlethreaded = True
            profiledir = options.profiledir
            os.mkdir(profiledir)
            threadutil.setprofiledir(profiledir)
            logging.warn("Profile mode: Potentially large data will be "
                         "created in '%s'" % profiledir)

        #override a config value
        if options.configoverride:
            for option in options.configoverride:
                (key, value) = option.split('=', 1)
                if ':' in key:
                    (secname, key) = key.split(':', 1)
                    section = secname.replace("_", " ")
                else:
                    section = "general"
                config.set(section, key, value)

        #init the ui, and set up additional log files
        ui = offlineimap.ui.detector.findUI(config, options.interface)
        offlineimap.ui.UIBase.setglobalui(ui)
    
        if options.logfile:
            ui.setlogfd(open(options.logfile, 'wt'))
    
        #welcome blurb
        ui.init_banner()

        if options.debugtype:
            if options.debugtype.lower() == 'all':
                options.debugtype = 'imap,maildir,thread'
            for type in options.debugtype.split(','):
                type = type.strip()
                ui.add_debug(type)
                if type.lower() == 'imap':
                    imaplib.Debug = 5
                if type.lower() == 'thread':
                    threading._VERBOSE = 1

        if options.runonce:
            # FIXME: maybe need a better
            for section in accounts.getaccountlist(config):
                config.remove_option('Account ' + section, "autorefresh")

        if options.quick:
            for section in accounts.getaccountlist(config):
                config.set('Account ' + section, "quick", '-1')

        if options.folders:
            foldernames = options.folders.replace(" ", "").split(",")
            folderfilter = "lambda f: f in %s" % foldernames
            folderincludes = "[]"
            for accountname in accounts.getaccountlist(config):
                account_section = 'Account ' + accountname
                remote_repo_section = 'Repository ' + \
                                      config.get(account_section, 'remoterepository')
                local_repo_section = 'Repository ' + \
                                     config.get(account_section, 'localrepository')
                for section in [remote_repo_section, local_repo_section]:
                    config.set(section, "folderfilter", folderfilter)
                    config.set(section, "folderincludes", folderincludes)

        self.lock(config, ui)

    
        def sigterm_handler(self, signum, frame):
            # die immediately
            ui = BaseUI.getglobalui()
            ui.terminate(errormsg="terminating...")

        signal.signal(signal.SIGTERM,sigterm_handler)
    
        try:
            pidfd = open(config.getmetadatadir() + "/pid", "w")
            pidfd.write(str(os.getpid()) + "\n")
            pidfd.close()
        except:
            pass
    
        try:
            if options.logfile:
                sys.stderr = ui.logfile
    
            socktimeout = config.getdefaultint("general", "socktimeout", 0)
            if socktimeout > 0:
                socket.setdefaulttimeout(socktimeout)
    
            activeaccounts = config.get("general", "accounts")
            if options.accounts:
                activeaccounts = options.accounts
            activeaccounts = activeaccounts.replace(" ", "")
            activeaccounts = activeaccounts.split(",")
            allaccounts = accounts.AccountHashGenerator(config)
    
            syncaccounts = []
            for account in activeaccounts:
                if account not in allaccounts:
                    if len(allaccounts) == 0:
                        errormsg = 'The account "%s" does not exist because no accounts are defined!'%account
                    else:
                        errormsg = 'The account "%s" does not exist.  Valid accounts are:'%account
                        for name in allaccounts.keys():
                            errormsg += '\n%s'%name
                    ui.terminate(1, errortitle = 'Unknown Account "%s"'%account, errormsg = errormsg)
                if account not in syncaccounts:
                    syncaccounts.append(account)
    
            server = None
            remoterepos = None
            localrepos = None
    
            if options.singlethreading:
                threadutil.initInstanceLimit("ACCOUNTLIMIT", 1)
            else:
                threadutil.initInstanceLimit("ACCOUNTLIMIT",
                                             config.getdefaultint("general", "maxsyncaccounts", 1))
    
            for reposname in config.getsectionlist('Repository'):
                for instancename in ["FOLDER_" + reposname,
                                     "MSGCOPY_" + reposname]:
                    if options.singlethreading:
                        threadutil.initInstanceLimit(instancename, 1)
                    else:
                        threadutil.initInstanceLimit(instancename,
                                                     config.getdefaultint('Repository ' + reposname, "maxconnections", 1))
            siglisteners = []
            def sig_handler(signum, frame):
                if signum == signal.SIGUSR1:
                    # tell each account to do a full sync asap
                    signum = (1,)
                elif signum == signal.SIGHUP:
                    # tell each account to die asap
                    signum = (2,)
                elif signum == signal.SIGUSR2:
                    # tell each account to do a full sync asap, then die
                    signum = (1, 2)
                # one listener per account thread (up to maxsyncaccounts)
                for listener in siglisteners:
                    for sig in signum:
                        listener.put_nowait(sig)
            signal.signal(signal.SIGHUP,sig_handler)
            signal.signal(signal.SIGUSR1,sig_handler)
            signal.signal(signal.SIGUSR2,sig_handler)
    
            threadutil.initexitnotify()
            t = ExitNotifyThread(target=syncmaster.syncitall,
                                 name='Sync Runner',
                                 kwargs = {'accounts': syncaccounts,
                                           'config': config,
                                           'siglisteners': siglisteners})
            t.setDaemon(1)
            t.start()
        except:
            ui.mainException()
    
        try:
            threadutil.exitnotifymonitorloop(threadutil.threadexited)
        except SystemExit:
            raise
        except:
            ui.mainException()  # Also expected to terminate.

        
