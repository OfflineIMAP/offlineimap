# Curses-based interfaces
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

from Blinkenlights import BlinkenBase
from UIBase import UIBase
from threading import *
import thread, time, sys, os, signal, time
from offlineimap import version, threadutil
from offlineimap.threadutil import MultiLock

import curses, curses.panel, curses.textpad, curses.wrapper

acctkeys = '1234567890abcdefghijklmnoprstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-=;/.,'

class CursesUtil:
    def __init__(self):
        self.pairlock = Lock()
        self.iolock = MultiLock()
        self.start()

    def initpairs(self):
        self.pairlock.acquire()
        try:
            self.pairs = {self._getpairindex(curses.COLOR_WHITE,
                                             curses.COLOR_BLACK): 0}
            self.nextpair = 1
        finally:
            self.pairlock.release()

    def lock(self):
        self.iolock.acquire()

    def unlock(self):
        self.iolock.release()
        
    def locked(self, target, *args, **kwargs):
        """Perform an operation with full locking."""
        self.lock()
        try:
            apply(target, args, kwargs)
        finally:
            self.unlock()

    def refresh(self):
        def lockedstuff():
            curses.panel.update_panels()
            curses.doupdate()
        self.locked(lockedstuff)

    def isactive(self):
        return hasattr(self, 'stdscr')

    def _getpairindex(self, fg, bg):
        return '%d/%d' % (fg,bg)

    def getpair(self, fg, bg):
        if not self.has_color:
            return 0
        pindex = self._getpairindex(fg, bg)
        self.pairlock.acquire()
        try:
            if self.pairs.has_key(pindex):
                return curses.color_pair(self.pairs[pindex])
            else:
                self.pairs[pindex] = self.nextpair
                curses.init_pair(self.nextpair, fg, bg)
                self.nextpair += 1
                return curses.color_pair(self.nextpair - 1)
        finally:
            self.pairlock.release()
    
    def start(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        try:
            curses.start_color()
            self.has_color = curses.has_colors()
        except:
            self.has_color = 0

        self.oldcursor = None
        try:
            self.oldcursor = curses.curs_set(0)
        except:
            pass
        
        self.stdscr.clear()
        self.stdscr.refresh()
        (self.height, self.width) = self.stdscr.getmaxyx()
        self.initpairs()

    def stop(self):
        if not hasattr(self, 'stdscr'):
            return
        #self.stdscr.addstr(self.height - 1, 0, "\n",
        #                   self.getpair(curses.COLOR_WHITE,
        #                                curses.COLOR_BLACK))
        if self.oldcursor != None:
            curses.curs_set(self.oldcursor)
        self.stdscr.refresh()
        self.stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        del self.stdscr

    def reset(self):
        # dirty walkaround for bug http://bugs.python.org/issue7567 in python 2.6 to 2.6.5 (fixed since #83743)
        if (sys.version_info[0:3] >= (2,6) and  sys.version_info[0:3] <= (2,6,5)): return
        self.stop()
        self.start()

class CursesAccountFrame:
    def __init__(s, master, accountname, ui):
        s.c = master
        s.children = []
        s.accountname = accountname
        s.ui = ui

    def drawleadstr(s, secs = None):
        if secs == None:
            acctstr = '%s: [active] %13.13s: ' % (s.key, s.accountname)
        else:
            acctstr = '%s: [%3d:%02d] %13.13s: ' % (s.key,
                                                    secs / 60, secs % 60,
                                                    s.accountname)
        s.c.locked(s.window.addstr, 0, 0, acctstr)
        s.location = len(acctstr)

    def setwindow(s, window, key):
        s.window = window
        s.key = key
        s.drawleadstr()
        for child in s.children:
            child.update(window, 0, s.location)
            s.location += 1

    def getnewthreadframe(s):
        tf = CursesThreadFrame(s.c, s.ui, s.window, 0, s.location)
        s.location += 1
        s.children.append(tf)
        return tf

    def startsleep(s, sleepsecs):
        s.sleeping_abort = 0

    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs:
            s.c.lock()
            try:
                s.drawleadstr(remainingsecs)
                s.window.refresh()
            finally:
                s.c.unlock()
            time.sleep(sleepsecs)
        else:
            s.c.lock()
            try:
                s.drawleadstr()
                s.window.refresh()
            finally:
                s.c.unlock()
        return s.sleeping_abort

    def syncnow(s):
        s.sleeping_abort = 1

class CursesThreadFrame:
    def __init__(s, master, ui, window, y, x):
        """master should be a CursesUtil object."""
        s.c = master
        s.ui = ui
        s.window = window
        s.x = x
        s.y = y
        s.colors = []
        bg = curses.COLOR_BLACK
        s.colormap = {'black': s.c.getpair(curses.COLOR_BLACK, bg),
                         'gray': s.c.getpair(curses.COLOR_WHITE, bg),
                         'white': curses.A_BOLD | s.c.getpair(curses.COLOR_WHITE, bg),
                         'blue': s.c.getpair(curses.COLOR_BLUE, bg),
                         'red': s.c.getpair(curses.COLOR_RED, bg),
                         'purple': s.c.getpair(curses.COLOR_MAGENTA, bg),
                         'cyan': s.c.getpair(curses.COLOR_CYAN, bg),
                         'green': s.c.getpair(curses.COLOR_GREEN, bg),
                         'orange': s.c.getpair(curses.COLOR_YELLOW, bg),
                         'yellow': curses.A_BOLD | s.c.getpair(curses.COLOR_YELLOW, bg),
                         'pink': curses.A_BOLD | s.c.getpair(curses.COLOR_RED, bg)}
        #s.setcolor('gray')
        s.setcolor('black')

    def setcolor(self, color):
        self.color = self.colormap[color]
        self.colorname = color
        self.display()

    def display(self):
        def lockedstuff():
            if self.getcolor() == 'black':
                self.window.addstr(self.y, self.x, ' ', self.color)
            else:
                self.window.addstr(self.y, self.x, self.ui.config.getdefault("ui.Curses.Blinkenlights", "statuschar", '.'), self.color)
            self.c.stdscr.move(self.c.height - 1, self.c.width - 1)
            self.window.refresh()
        self.c.locked(lockedstuff)

    def getcolor(self):
        return self.colorname

    def getcolorpair(self):
        return self.color

    def update(self, window, y, x):
        self.window = window
        self.y = y
        self.x = x
        self.display()

    def setthread(self, newthread):
        self.setcolor('black')
        #if newthread:
        #    self.setcolor('gray')
        #else:
        #    self.setcolor('black')

class InputHandler:
    def __init__(s, util):
        s.c = util
        s.bgchar = None
        s.inputlock = Lock()
        s.lockheld = 0
        s.statuslock = Lock()
        s.startup = Event()
        s.startthread()

    def startthread(s):
        s.thread = threadutil.ExitNotifyThread(target = s.bgreaderloop,
                                               name = "InputHandler loop")
        s.thread.setDaemon(1)
        s.thread.start()

    def bgreaderloop(s):
        while 1:
            s.statuslock.acquire()
            if s.lockheld or s.bgchar == None:
                s.statuslock.release()
                s.startup.wait()
            else:
                s.statuslock.release()
                ch = s.c.stdscr.getch()
                s.statuslock.acquire()
                try:
                    if s.lockheld or s.bgchar == None:
                        curses.ungetch(ch)
                    else:
                        s.bgchar(ch)
                finally:
                    s.statuslock.release()

    def set_bgchar(s, callback):
        """Sets a "background" character handler.  If a key is pressed
        while not doing anything else, it will be passed to this handler.

        callback is a function taking a single arg -- the char pressed.

        If callback is None, clears the request."""
        s.statuslock.acquire()
        oldhandler = s.bgchar
        newhandler = callback
        s.bgchar = callback

        if oldhandler and not newhandler:
            pass
        if newhandler and not oldhandler:
            s.startup.set()
            
        s.statuslock.release()

    def input_acquire(s):
        """Call this method when you want exclusive input control.
        Make sure to call input_release afterwards!
        """

        s.inputlock.acquire()
        s.statuslock.acquire()
        s.lockheld = 1
        s.statuslock.release()

    def input_release(s):
        """Call this method when you are done getting input."""
        s.statuslock.acquire()
        s.lockheld = 0
        s.statuslock.release()
        s.inputlock.release()
        s.startup.set()
        
class Blinkenlights(BlinkenBase, UIBase):
    def init_banner(s):
        s.af = {}
        s.aflock = Lock()
        s.c = CursesUtil()
        s.text = []
        BlinkenBase.init_banner(s)
        s.setupwindows()
        s.inputhandler = InputHandler(s.c)
        s.gettf().setcolor('red')
        s._msg(version.banner)
        s.inputhandler.set_bgchar(s.keypress)
        signal.signal(signal.SIGWINCH, s.resizehandler)
        s.resizelock = Lock()
        s.resizecount = 0

    def resizehandler(s, signum, frame):
        s.resizeterm()

    def resizeterm(s, dosleep = 1):
        if not s.resizelock.acquire(0):
            s.resizecount += 1
            return
        signal.signal(signal.SIGWINCH, signal.SIG_IGN)
        s.aflock.acquire()
        s.c.lock()
        s.resizecount += 1
        while s.resizecount:
            s.c.reset()
            s.setupwindows()
            s.resizecount -= 1
        s.c.unlock()
        s.aflock.release()
        s.resizelock.release()
        signal.signal(signal.SIGWINCH, s.resizehandler)
        if dosleep:
            time.sleep(1)
            s.resizeterm(0)

    def isusable(s):
        # Not a terminal?  Can't use curses.
        if not sys.stdout.isatty() and sys.stdin.isatty():
            return 0

        # No TERM specified?  Can't use curses.
        try:
            if not len(os.environ['TERM']):
                return 0
        except: return 0

        # ncurses doesn't want to start?  Can't use curses.
        # This test is nasty because initscr() actually EXITS on error.
        # grr.

        pid = os.fork()
        if pid:
            # parent
            return not os.WEXITSTATUS(os.waitpid(pid, 0)[1])
        else:
            # child
            curses.initscr()
            curses.endwin()
            # If we didn't die by here, indicate success.
            sys.exit(0)

    def keypress(s, key):
        if key < 1 or key > 255:
            return
        
        if chr(key) == 'q':
            # Request to quit.
            s.terminate()
        
        try:
            index = acctkeys.index(chr(key))
        except ValueError:
            # Key not a valid one: exit.
            return

        if index >= len(s.hotkeys):
            # Not in our list of valid hotkeys.
            return

        # Trying to end sleep somewhere.

        s.getaccountframe(s.hotkeys[index]).syncnow()

    def getpass(s, accountname, config, errmsg = None):
        s.inputhandler.input_acquire()

        # See comment on _msg for info on why both locks are obtained.
        
        s.tflock.acquire()
        s.c.lock()
        try:
            s.gettf().setcolor('white')
            s._addline(" *** Input Required", s.gettf().getcolorpair())
            s._addline(" *** Please enter password for account %s: " % accountname,
                   s.gettf().getcolorpair())
            s.logwindow.refresh()
            password = s.logwindow.getstr()
        finally:
            s.tflock.release()
            s.c.unlock()
            s.inputhandler.input_release()
        return password

    def setupwindows(s):
        s.c.lock()
        try:
            s.bannerwindow = curses.newwin(1, s.c.width, 0, 0)
            s.setupwindow_drawbanner()
            s.logheight = s.c.height - 1 - len(s.af.keys())
            s.logwindow = curses.newwin(s.logheight, s.c.width, 1, 0)
            s.logwindow.idlok(1)
            s.logwindow.scrollok(1)
            s.logwindow.move(s.logheight - 1, 0)
            s.setupwindow_drawlog()
            accounts = s.af.keys()
            accounts.sort()
            accounts.reverse()

            pos = s.c.height - 1
            index = 0
            s.hotkeys = []
            for account in accounts:
                accountwindow = curses.newwin(1, s.c.width, pos, 0)
                s.af[account].setwindow(accountwindow, acctkeys[index])
                s.hotkeys.append(account)
                index += 1
                pos -= 1

            curses.doupdate()
        finally:
            s.c.unlock()

    def setupwindow_drawbanner(s):
        if s.c.has_color:
            color = s.c.getpair(curses.COLOR_WHITE, curses.COLOR_BLUE) | \
                    curses.A_BOLD
        else:
            color = curses.A_REVERSE
        s.bannerwindow.bkgd(' ', color) # Fill background with that color
        s.bannerwindow.addstr("%s %s" % (version.productname,
                                         version.versionstr))
        s.bannerwindow.addstr(0, s.bannerwindow.getmaxyx()[1] - len(version.copyright) - 1,
                              version.copyright)
        
        s.bannerwindow.noutrefresh()

    def setupwindow_drawlog(s):
        if s.c.has_color:
            color = s.c.getpair(curses.COLOR_WHITE, curses.COLOR_BLACK)
        else:
            color = curses.A_NORMAL
        s.logwindow.bkgd(' ', color)
        for line, color in s.text:
            s.logwindow.addstr("\n" + line, color)
        s.logwindow.noutrefresh()

    def getaccountframe(s, accountname = None):
        if accountname == None:
            accountname = s.getthreadaccount()
        s.aflock.acquire()
        try:
            if accountname in s.af:
                return s.af[accountname]

            # New one.
            s.af[accountname] = CursesAccountFrame(s.c, accountname, s)
            s.c.lock()
            try:
                s.c.reset()
                s.setupwindows()
            finally:
                s.c.unlock()
        finally:
            s.aflock.release()
        return s.af[accountname]


    def _display(s, msg, color = None):
        if "\n" in msg:
            for thisline in msg.split("\n"):
                s._msg(thisline)
            return

        # We must acquire both locks.  Otherwise, deadlock can result.
        # This can happen if one thread calls _msg (locking curses, then
        # tf) and another tries to set the color (locking tf, then curses)
        #
        # By locking both up-front here, in this order, we prevent deadlock.
        
        s.tflock.acquire()
        s.c.lock()
        try:
            if not s.c.isactive():
                # For dumping out exceptions and stuff.
                print msg
                return
            if color:
                s.gettf().setcolor(color)
            elif s.gettf().getcolor() == 'black':
                s.gettf().setcolor('gray')
            s._addline(msg, s.gettf().getcolorpair())
            s.logwindow.refresh()
        finally:
            s.c.unlock()
            s.tflock.release()

    def _addline(s, msg, color):
        s.c.lock()
        try:
            s.logwindow.addstr("\n" + msg, color)
            s.text.append((msg, color))
            while len(s.text) > s.logheight:
                s.text = s.text[1:]
        finally:
            s.c.unlock()

    def terminate(s, exitstatus = 0, errortitle = None, errormsg = None):
        s.c.stop()
        UIBase.terminate(s, exitstatus = exitstatus, errortitle = errortitle, errormsg = errormsg)

    def threadException(s, thread):
        s.c.stop()
        UIBase.threadException(s, thread)

    def mainException(s):
        s.c.stop()
        UIBase.mainException(s)

    def sleep(s, sleepsecs, siglistener):
        s.gettf().setcolor('red')
        s._msg("Next sync in %d:%02d" % (sleepsecs / 60, sleepsecs % 60))
        return BlinkenBase.sleep(s, sleepsecs, siglistener)
            
if __name__ == '__main__':
    x = Blinkenlights(None)
    x.init_banner()
    import time
    time.sleep(5)
    x.c.stop()
    fgs = {'black': curses.COLOR_BLACK, 'red': curses.COLOR_RED,
           'green': curses.COLOR_GREEN, 'yellow': curses.COLOR_YELLOW,
           'blue': curses.COLOR_BLUE, 'magenta': curses.COLOR_MAGENTA,
           'cyan': curses.COLOR_CYAN, 'white': curses.COLOR_WHITE}
    
    x = CursesUtil()
    win1 = curses.newwin(x.height, x.width / 4 - 1, 0, 0)
    win1.addstr("Black/normal\n")
    for name, fg in fgs.items():
        win1.addstr("%s\n" % name, x.getpair(fg, curses.COLOR_BLACK))
    win2 = curses.newwin(x.height, x.width / 4 - 1, 0, win1.getmaxyx()[1])
    win2.addstr("Blue/normal\n")
    for name, fg in fgs.items():
        win2.addstr("%s\n" % name, x.getpair(fg, curses.COLOR_BLUE))
    win3 = curses.newwin(x.height, x.width / 4 - 1, 0, win1.getmaxyx()[1] +
                         win2.getmaxyx()[1])
    win3.addstr("Black/bright\n")
    for name, fg in fgs.items():
        win3.addstr("%s\n" % name, x.getpair(fg, curses.COLOR_BLACK) | \
                    curses.A_BOLD)
    win4 = curses.newwin(x.height, x.width / 4 - 1, 0, win1.getmaxyx()[1] * 3)
    win4.addstr("Blue/bright\n")
    for name, fg in fgs.items():
        win4.addstr("%s\n" % name, x.getpair(fg, curses.COLOR_BLUE) | \
                    curses.A_BOLD)
        
        
    win1.refresh()
    win2.refresh()
    win3.refresh()
    win4.refresh()
    x.stdscr.refresh()
    import time
    time.sleep(5)
    x.stop()
    print x.has_color
    print x.height
    print x.width

