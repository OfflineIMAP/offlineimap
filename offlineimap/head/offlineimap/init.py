# OfflineIMAP initialization code
# Copyright (C) 2002, 2003 John Goerzen
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

from offlineimap import imaplib, imapserver, repository, folder, mbnames, threadutil, version, syncmaster, accounts
from offlineimap.localeval import LocalEval
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
from offlineimap.ui import UIBase
import re, os, os.path, offlineimap, sys, fcntl
from offlineimap.CustomConfig import CustomConfigParser
from threading import *
import threading
from getopt import getopt

lockfd = None

def lock(config, ui):
    global lockfd
    lockfd = open(config.getmetadatadir() + "/lock", "w")
    try:
        fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        ui.locked()
        ui.terminate(1)

def startup(versionno):
    assert versionno == version.versionstr, "Revision of main program (%d) does not match that of library (%d).  Please double-check your PYTHONPATH and installation locations." % (revno, version.revno)
    options = {}
    if '--help' in sys.argv[1:]:
        sys.stdout.write(version.cmdhelp + "\n")
        sys.exit(0)

    for optlist in getopt(sys.argv[1:], 'P:1oa:c:d:u:h')[0]:
        options[optlist[0]] = optlist[1]

    if '-h' in options:
        sys.stdout.write(version.cmdhelp)
        sys.stdout.write("\n")
        sys.exit(0)
    configfilename = os.path.expanduser("~/.offlineimaprc")
    if '-c' in options:
        configfilename = options['-c']
    if '-P' in options:
        if not '-1' in options:
            sys.stderr.write("FATAL: profile mode REQUIRES -1\n")
            sys.exit(100)
        profiledir = options['-P']
        os.mkdir(profiledir)
        threadutil.setprofiledir(profiledir)
        sys.stderr.write("WARNING: profile mode engaged;\nPotentially large data will be created in " + profiledir + "\n")

    config = CustomConfigParser()
    if not os.path.exists(configfilename):
        sys.stderr.write(" *** Config file %s does not exist; aborting!\n" % configfilename)
        sys.exit(1)

    config.read(configfilename)

    ui = offlineimap.ui.detector.findUI(config, options.get('-u'))
    ui.init_banner()
    UIBase.setglobalui(ui)

    if '-d' in options:
        for debugtype in options['-d'].split(','):
            ui.add_debug(debugtype.strip())
            if debugtype == 'imap':
                imaplib.Debug = 5
            if debugtype == 'thread':
                threading._VERBOSE = 1

    if '-l' in options:
        ui.setlogfd(open(options['-l'], 'wt'))

    if '-o' in options:
        # FIXME: maybe need a better
        for section in accounts.getaccountlist(config):
            config.remove_option('Account ' + section, "autorefresh")

    lock(config, ui)

    activeaccounts = config.get("general", "accounts")
    if '-a' in options:
        activeaccounts = options['-a']
    activeaccounts = activeaccounts.replace(" ", "")
    activeaccounts = activeaccounts.split(",")
    allaccounts = accounts.AccountHashGenerator(config)

    syncaccounts = {}
    for account in activeaccounts:
        syncaccounts[account] = allaccounts[account]

    server = None
    remoterepos = None
    localrepos = None

    if '-1' in options:
        threadutil.initInstanceLimit("ACCOUNTLIMIT", 1)
    else:
        threadutil.initInstanceLimit("ACCOUNTLIMIT",
                                     config.getdefaultint("general", "maxsyncaccounts", 1))

    for reposname in config.getsectionlist('Repository'):
        for instancename in ["FOLDER_" + reposname,
                             "MSGCOPY_" + reposname]:
            if '-1' in options:
                threadutil.initInstanceLimit(instancename, 1)
            else:
                threadutil.initInstanceLimit(instancename,
                                             config.getdefaultint('Repository ' + reposname, "maxconnections", 1))

    threadutil.initexitnotify()
    t = ExitNotifyThread(target=syncmaster.syncitall,
                         name='Sync Runner',
                         kwargs = {'accounts': syncaccounts,
                                   'config': config})
    t.setDaemon(1)
    t.start()
    try:
        threadutil.exitnotifymonitorloop(threadutil.threadexited)
    except SystemExit:
        raise
    except:
        ui.mainException()                  # Also expected to terminate.

        
