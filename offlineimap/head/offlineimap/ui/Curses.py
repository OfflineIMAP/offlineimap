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

import curses, curses.panel, curses.textpad, curses.wrapper

class CursesUtil:
    def __init__(self):
        self.pairs = {self._getpairindex(curses.COLOR_WHITE,
                                         curses.COLOR_BLACK): 0}
        self.start()
        self.nextpair = 1
        self.pairlock = Lock()

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
        self.stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        del self.stdscr

    #def resize(self):
        
if __name__ == '__main__':
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

#class Blinkenlights(BlinkenBase, UIBase):
#    def init_banner(s):
        
