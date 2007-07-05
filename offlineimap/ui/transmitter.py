# User interface transmitter
#
# Used by per-account OfflineIMAP threads
#
# Transmits messages using Machine
#
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


import offlineimap.version
import re, time, sys, traceback, threading, thread
from StringIO import StringIO

debugtypes = {'imap': 'IMAP protocol debugging',
              'maildir': 'Maildir repository debugging',
              'thread': 'Threading debugging'}

globalui = None
def setglobalui(newui):
    global globalui
    globalui = newui
def getglobalui():
    global globalui
    return globalui

class UITransmitter:
    """This class is designed to transmit UI messages to the OfflineIMAP
    ui process.  It receives raw data and formats it nicely."""
    def __init__(s, config, verbose = 0):
        s.verbose = verbose
        s.config = config
        s.debuglist = []
        s.debugmessages = {}
        s.debugmsglen = 50
        s.threadaccounts = {}
        s.logfile = None
        s.m = Machine.MachineUI(config, verbose)

    def warn(s, msg, minor = 0):
        s.m.warn(msg, minor)

    def registerthread(s, accountname):
        s.m.registerthread(threading.currentThread().getName(), accountname)

    def unregisterthread(s, threadobj):
        s.m.unregisterthread(threadobj.getName())

    def debugging(s, debugtype):
        s.m.debugging(s, debugtype)

    def debug(s, debugtype, msg):
        thisthread = threading.currentThread()
        if s.debugmessages.has_key(thisthread):
            s.debugmessages[thisthread].append("%s: %s" % (debugtype, msg))
        else:
            s.debugmessages[thisthread] = ["%s: %s" % (debugtype, msg)]

        while len(s.debugmessages[thisthread]) > s.debugmsglen:
            s.debugmessages[thisthread] = s.debugmessages[thisthread][1:]

        s.print_debug(debugtype, msg)

    def print_debug(s, debugtype, msg):
        s.m.print_debug(s, debugtype, msg)

    def debugging(s, debugtype):
        s.m.debugging(s, debugtype)

    def invaliddebug(s, debugtype):
        s.warn("Invalid debug type: %s" % debugtype)

    def getnicename(s, object):
        prelimname = str(object.__class__).split('.')[-1]
        # Strip off extra stuff.
        return re.sub('(Folder|Repository)', '', prelimname)

    ################################################## INPUT
    def getpass(s, accountname, errmsg = None):
        s.m.getpass(accountname, errmsg)

    ################################################## WARNINGS
    def msgtoreadonly(s, destfolder, uid):
        s.m.msgtoreadonly(s, s.getnicename(destfolder), 
                destfolder.getname(), uid)

