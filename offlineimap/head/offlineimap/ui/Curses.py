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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Blinkenlights import BlinkenBase
from UIBase import UIBase
from threading import *
from offlineimap import version, threadutil

import curses, curses.panel, curses.textpad, curses.wrapper

class CursesUtil:
    def __init__(self):
        self.pairs = {self._getpairindex(curses.COLOR_WHITE,
                                         curses.COLOR_BLACK): 0}
        self.start()
        self.nextpair = 1
        self.pairlock = Lock()

    def isactive(self):
        return hasattr(self, 'stdscr')

    def _getpairindex(self, fg, bg):
        return '%d/%d' % (fg,bg)

    def getpair(self, fg, bg):
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

        self.stdscr.clear()
        self.stdscr.refresh()
        (self.height, self.width) = self.stdscr.getmaxyx()

    def stop(self):
        if not hasattr(self, 'stdscr'):
            return
        #self.stdscr.addstr(self.height - 1, 0, "\n",
        #                   self.getpair(curses.COLOR_WHITE,
        #                                curses.COLOR_BLACK))
        self.stdscr.refresh()
        self.stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        del self.stdscr

    def reset(self):
        self.stop()
        self.start()

class CursesAccountFrame:
    def __init__(s, master):
        s.c = master
        s.children = []

    def setwindow(s, window):
        s.window = window
        location = 0
        for child in s.children:
            child.update(window, 0, location)
            location += 1

    def getnewthreadframe(s):
        tf = CursesThreadFrame(s.c, s.window, 0, len(s.children))
        s.children.append(tf)
        return tf

class CursesThreadFrame:
    def __init__(s, master, window, y, x):
        """master should be a CursesUtil object."""
        s.c = master
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
        s.setcolor('gray')

    def setcolor(self, color):
        self.color = self.colormap[color]
        self.window.addstr(self.y, self.x, '.', self.color)
        self.window.refresh()

    def getcolor(self):
        return self.color

    def setthread(self, newthread):
        if newthread:
            self.setcolor('gray')
        else:
            self.setcolor('black')

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
        s.iolock = Lock()
        s.af = {}
        s.aflock = Lock()
        s.c = CursesUtil()
        s.text = []
        BlinkenBase.init_banner(s)
        s.setupwindows(dolock = 0)
        s.inputhandler = InputHandler(s.c)
        
        s._msg(version.banner)
        s._msg(str(dir(s.c.stdscr)))
        s.inputhandler.set_bgchar(s.keypress)

    def keypress(s, key):
        s._msg("Key pressed: " + str(key))

    def getpass(s, accountname, config, errmsg = None):
        s.inputhandler.input_acquire()
        s.iolock.acquire()
        try:
            s.gettf().setcolor('white')
            s._addline_unlocked(" *** Input Required", s.gettf().getcolor())
            s._addline_unlocked(" *** Please enter password for account %s: " % accountname,
                   s.gettf().getcolor())
            s.logwindow.refresh()
            password = s.logwindow.getstr()
        finally:
            s.iolock.release()
            s.inputhandler.input_release()
        return password

    def setupwindows(s, dolock = 1):
        if dolock:
            s.iolock.acquire()
        try:
            s.bannerwindow = curses.newwin(1, s.c.width, 0, 0)
            s.setupwindow_drawbanner()
            s.logheight = s.c.height - 1 - len(s.af.keys())
            s.logwindow = curses.newwin(s.logheight, s.c.width, 1, 0)
            s.logwindow.idlok(1)
            s.logwindow.scrollok(1)
            s.setupwindow_drawlog()

            accounts = s.af.keys()
            accounts.sort()
            accounts.reverse()

            pos = s.c.height - 1
            for account in accounts:
                accountwindow = curses.newwin(1, s.c.width, pos, 0)
                s.af[account].setwindow(accountwindow)
                pos -= 1

            curses.doupdate()

        finally:
            if dolock:
                s.iolock.release()

    def setupwindow_drawbanner(s):
        s.bannerwindow.bkgd(' ', curses.A_BOLD | \
                            s.c.getpair(curses.COLOR_WHITE,
                                        curses.COLOR_BLUE))
        s.bannerwindow.addstr("%s %s" % (version.productname,
                                         version.versionstr))
        s.bannerwindow.addstr(0, s.bannerwindow.getmaxyx()[1] - len(version.copyright) - 1,
                              version.copyright)
        
        s.bannerwindow.noutrefresh()

    def setupwindow_drawlog(s):
        s.logwindow.bkgd(' ', s.c.getpair(curses.COLOR_WHITE, curses.COLOR_BLACK))
        for line, color in s.text:
            s.logwindow.addstr(line + "\n", color)
            s.logwindow.noutrefresh()

    def getaccountframe(s):
        accountname = s.getthreadaccount()
        s.aflock.acquire()
        try:
            if accountname in s.af:
                return s.af[accountname]

            # New one.
            s.af[accountname] = CursesAccountFrame(s.c)
            #s.iolock.acquire()
            s.c.reset()
            s.setupwindows(dolock = 0)
            #s.iolock.release()
        finally:
            s.aflock.release()
        return s.af[accountname]


    def _msg(s, msg, color = None):
        if "\n" in msg:
            for thisline in msg.split("\n"):
                s._msg(thisline)
            return
        s.iolock.acquire()
        try:
            if not s.c.isactive():
                # For dumping out exceptions and stuff.
                print msg
                return
            if color:
                s.gettf().setcolor(color)
            s._addline_unlocked(msg, s.gettf().getcolor())
            s.logwindow.refresh()
        finally:
            s.iolock.release()

    def _addline_unlocked(s, msg, color):
        s.logwindow.addstr(msg + "\n", color)
        s.text.append((msg, color))
        while len(s.text) > s.logheight:
            s.text = s.text[1:]
        

    def terminate(s, exitstatus = 0):
        s.c.stop()
        UIBase.terminate(s, exitstatus)

    def threadException(s, thread):
        s.c.stop()
        UIBase.threadException(s, thread)

    def mainException(s):
        s.c.stop()
        UIBase.mainException(s)
            
if __name__ == '__main__':
    x = Blinkenlights(None)
    x.init_banner()
    import time
    time.sleep(10)
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
    time.sleep(40)
    x.stop()
    print x.has_color
    print x.height
    print x.width

