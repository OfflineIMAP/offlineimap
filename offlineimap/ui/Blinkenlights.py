# Blinkenlights base classes
# Copyright (C) 2003 John Goerzen
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

from threading import RLock, currentThread
from offlineimap.ui.UIBase import UIBase
from thread import get_ident	# python < 2.6 support

class BlinkenBase:
    """This is a mix-in class that should be mixed in with either UIBase
    or another appropriate base class.  The Tk interface, for instance,
    will probably mix it in with VerboseUI."""

    def acct(s, accountname):
        s.gettf().setcolor('purple')
        s.__class__.__bases__[-1].acct(s, accountname)

    def connecting(s, hostname, port):
        s.gettf().setcolor('gray')
        s.__class__.__bases__[-1].connecting(s, hostname, port)

    def syncfolders(s, srcrepos, destrepos):
        s.gettf().setcolor('blue')
        s.__class__.__bases__[-1].syncfolders(s, srcrepos, destrepos)

    def syncingfolder(s, srcrepos, srcfolder, destrepos, destfolder):
        s.gettf().setcolor('cyan')
        s.__class__.__bases__[-1].syncingfolder(s, srcrepos, srcfolder, destrepos, destfolder)

    def skippingfolder(s, folder):
        s.gettf().setcolor('cyan')
        s.__class__.__bases__[-1].skippingfolder(s, folder)

    def loadmessagelist(s, repos, folder):
        s.gettf().setcolor('green')
        s._msg("Scanning folder [%s/%s]" % (s.getnicename(repos),
                                            folder.getvisiblename()))

    def syncingmessages(s, sr, sf, dr, df):
        s.gettf().setcolor('blue')
        s.__class__.__bases__[-1].syncingmessages(s, sr, sf, dr, df)

    def copyingmessage(s, uid, src, destlist):
        s.gettf().setcolor('orange')
        s.__class__.__bases__[-1].copyingmessage(s, uid, src, destlist)

    def deletingmessages(s, uidlist, destlist):
        s.gettf().setcolor('red')
        s.__class__.__bases__[-1].deletingmessages(s, uidlist, destlist)

    def deletingmessage(s, uid, destlist):
        s.gettf().setcolor('red')
        s.__class__.__bases__[-1].deletingmessage(s, uid, destlist)

    def addingflags(s, uidlist, flags, dest):
        s.gettf().setcolor('yellow')
        s.__class__.__bases__[-1].addingflags(s, uidlist, flags, dest)

    def deletingflags(s, uidlist, flags, dest):
        s.gettf().setcolor('pink')
        s.__class__.__bases__[-1].deletingflags(s, uidlist, flags, dest)

    def warn(s, msg, minor = 0):
        if minor:
            s.gettf().setcolor('pink')
        else:
            s.gettf().setcolor('red')
        s.__class__.__bases__[-1].warn(s, msg, minor)

    def init_banner(s):
        s.availablethreadframes = {}
        s.threadframes = {}
        #tflock protects the s.threadframes manipulation to only happen from 1 thread
        s.tflock = RLock()

    def threadExited(s, thread):
        threadid = thread.threadid
        accountname = s.getthreadaccount(thread)
        s.tflock.acquire()
        try:
            if threadid in s.threadframes[accountname]:
                tf = s.threadframes[accountname][threadid]
                del s.threadframes[accountname][threadid]
                s.availablethreadframes[accountname].append(tf)
                tf.setthread(None)
        finally:
            s.tflock.release()

        UIBase.threadExited(s, thread)

    def gettf(s):
        threadid = get_ident()
        accountname = s.getthreadaccount()

        s.tflock.acquire()

        try:
            if not accountname in s.threadframes:
                s.threadframes[accountname] = {}
                
            if threadid in s.threadframes[accountname]:
                return s.threadframes[accountname][threadid]

            if not accountname in s.availablethreadframes:
                s.availablethreadframes[accountname] = []

            if len(s.availablethreadframes[accountname]):
                tf = s.availablethreadframes[accountname].pop(0)
                tf.setthread(currentThread())
            else:
                tf = s.getaccountframe().getnewthreadframe()
            s.threadframes[accountname][threadid] = tf
            return tf
        finally:
            s.tflock.release()

    def callhook(s, msg):
        s.gettf().setcolor('white')
        s.__class__.__bases__[-1].callhook(s, msg)
            
    def sleep(s, sleepsecs, account):
        s.gettf().setcolor('red')
        s.getaccountframe().startsleep(sleepsecs)
        return UIBase.sleep(s, sleepsecs, account)

    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs and s.gettf().getcolor() == 'black':
            s.gettf().setcolor('red')
        else:
            s.gettf().setcolor('black')
        return s.getaccountframe().sleeping(sleepsecs, remainingsecs)

    
