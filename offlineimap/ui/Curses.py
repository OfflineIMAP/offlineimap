# Curses-based interfaces
# Copyright (C) 2003-2015 John Goerzen & contributors
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

from threading import RLock, currentThread, Lock, Event
from collections import deque
import time
import sys
import os
import curses
import logging

from offlineimap.ui.UIBase import UIBase
from offlineimap.threadutil import ExitNotifyThread
import offlineimap


class CursesUtil:
    def __init__(self, *args, **kwargs):
        # iolock protects access to the
        self.iolock = RLock()
        self.tframe_lock = RLock()
        # tframe_lock protects the self.threadframes manipulation to
        # only happen from 1 thread.
        self.colormap = {}
        """dict, translating color string to curses color pair number"""

    def curses_colorpair(self, col_name):
        """Return the curses color pair, that corresponds to the color."""

        return curses.color_pair(self.colormap[col_name])

    def init_colorpairs(self):
        """Initialize the curses color pairs available."""

        # set special colors 'gray' and 'banner'
        self.colormap['white'] = 0 #hardcoded by curses
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        self.colormap['banner'] = 1 # color 'banner' for bannerwin

        bcol = curses.COLOR_BLACK
        colors = ( # name, color, bold?
                ('black', curses.COLOR_BLACK, False),
                ('blue', curses.COLOR_BLUE,False),
                ('red', curses.COLOR_RED, False),
                ('purple', curses.COLOR_MAGENTA, False),
                ('cyan', curses.COLOR_CYAN, False),
                ('green', curses.COLOR_GREEN, False),
                ('orange', curses.COLOR_YELLOW, False))
        #set the rest of all colors starting at pair 2
        i = 1
        for name, fcol, bold  in colors:
            i += 1
            self.colormap[name] = i
            curses.init_pair(i, fcol, bcol)

    def lock(self, block=True):
        """Locks the Curses ui thread.

        Can be invoked multiple times from the owning thread. Invoking
        from a non-owning thread blocks and waits until it has been
        unlocked by the owning thread."""

        return self.iolock.acquire(block)

    def unlock(self):
        """Unlocks the Curses ui thread.

        Decrease the lock counter by one and unlock the ui thread if the
        counter reaches 0.  Only call this method when the calling
        thread owns the lock. A RuntimeError is raised if this method is
        called when the lock is unlocked."""

        self.iolock.release()

    def exec_locked(self, target, *args, **kwargs):
        """Perform an operation with full locking."""

        self.lock()
        try:
            target(*args, **kwargs)
        finally:
            self.unlock()

    def refresh(self):
        def lockedstuff():
            curses.panel.update_panels()
            curses.doupdate()
        self.exec_locked(lockedstuff)

    def isactive(self):
        return hasattr(self, 'stdscr')


class CursesAccountFrame:
    """Notable instance variables:

    - account: corresponding Account()
    - children
    - ui
    - key
    - window: curses window associated with an account
    """

    def __init__(self, ui, account):
        """
        :param account: An Account() or None (for eg SyncrunnerThread)"""

        self.children = []
        self.account = account if account else '*Control'
        self.ui = ui
        self.window = None
        # Curses window associated with this acc.
        self.acc_num = None
        # Account number (& hotkey) associated with this acc.
        self.location = 0
        # length of the account prefix string

    def drawleadstr(self, secs = 0):
        """Draw the account status string.

        secs tells us how long we are going to sleep."""

        sleepstr = '%3d:%02d'% (secs // 60, secs % 60) if secs else 'active'
        accstr = '%s: [%s] %12.12s: '% (self.acc_num, sleepstr, self.account)

        self.ui.exec_locked(self.window.addstr, 0, 0, accstr)
        self.location = len(accstr)

    def setwindow(self, curses_win, acc_num):
        """Register an curses win and a hotkey as Account window.

        :param curses_win: the curses window associated with an account
        :param acc_num: int denoting the hotkey associated with this account."""

        self.window = curses_win
        self.acc_num = acc_num
        self.drawleadstr()
        # Update the child ThreadFrames
        for child in self.children:
            child.update(curses_win, self.location, 0)
            self.location += 1

    def get_new_tframe(self):
        """Create a new ThreadFrame and append it to self.children.

        :returns: The new ThreadFrame"""

        tf = CursesThreadFrame(self.ui, self.window, self.location, 0)
        self.location += 1
        self.children.append(tf)
        return tf

    def sleeping(self, sleepsecs, remainingsecs):
        """Show how long we are going to sleep and sleep.

        :returns: Boolean, whether we want to abort the sleep"""

        self.drawleadstr(remainingsecs)
        self.ui.exec_locked(self.window.refresh)
        time.sleep(sleepsecs)
        return self.account.get_abort_event()

    def syncnow(self):
        """Request that we stop sleeping asap and continue to sync."""

        # if this belongs to an Account (and not *Control), set the
        # skipsleep pref
        if isinstance(self.account, offlineimap.accounts.Account):
            self.ui.info("Requested synchronization for acc: %s"% self.account)
            self.account.config.set('Account %s'% self.account.name,
                'skipsleep', '1')

class CursesThreadFrame:
    """curses_color: current color pair for logging."""

    def __init__(self, ui, acc_win, x, y):
        """
        :param ui: is a Blinkenlights() instance
        :param acc_win: curses Account window"""

        self.ui = ui
        self.window = acc_win
        self.x = x
        self.y = y
        self.curses_color = curses.color_pair(0) #default color

    def setcolor(self, color, modifier=0):
        """Draw the thread symbol '@' in the specified color

        :param modifier: Curses modified, such as curses.A_BOLD
        """

        self.curses_color = modifier | self.ui.curses_colorpair(color)
        self.colorname = color
        self.display()

    def display(self):
        def locked_display():
            self.window.addch(self.y, self.x, '@', self.curses_color)
            self.window.refresh()
        # lock the curses IO while fudging stuff
        self.ui.exec_locked(locked_display)

    def update(self, acc_win, x, y):
        """Update the xy position of the '.' (and possibly the aframe)."""

        self.window = acc_win
        self.y = y
        self.x = x
        self.display()

    def std_color(self):
        self.setcolor('black')


class InputHandler(ExitNotifyThread):
    """Listens for input via the curses interfaces"""

    #TODO, we need to use the ugly exitnotifythread (rather than simply
    #threading.Thread here, so exiting this thread via the callback
    #handler, kills off all parents too. Otherwise, they would simply
    #continue.
    def __init__(self, ui):
        super(InputHandler, self).__init__()
        self.char_handler = None
        self.ui = ui
        self.enabled = Event()
        # We will only parse input if we are enabled.
        self.inputlock = RLock()
        # denotes whether we should be handling the next char.
        self.start() #automatically start the thread

    def get_next_char(self):
        """Return the key pressed or -1.

        Wait until `enabled` and loop internally every stdscr.timeout()
        msecs, releasing the inputlock.
        :returns: char or None if disabled while in here"""

        self.enabled.wait()
        while self.enabled.is_set():
            with self.inputlock:
                char = self.ui.stdscr.getch()
            if char != -1: yield char

    def run(self):
        while True:
            char_gen = self.get_next_char()
            for char in char_gen:
                self.char_handler(char)
                #curses.ungetch(char)

    def set_char_hdlr(self, callback):
        """Sets a character callback handler.

        If a key is pressed it will be passed to this handler. Keys
        include the curses.KEY_RESIZE key.

        callback is a function taking a single arg -- the char pressed.
        If callback is None, input will be ignored."""

        with self.inputlock:
            self.char_handler = callback
            # start or stop the parsing of things
            if callback is None:
                self.enabled.clear()
            else:
                self.enabled.set()

    def input_acquire(self):
        """Call this method when you want exclusive input control.

        Make sure to call input_release afterwards! While this lockis
        held, input can go to e.g. the getpass input."""

        self.enabled.clear()
        self.inputlock.acquire()

    def input_release(self):
        """Call this method when you are done getting input."""

        self.inputlock.release()
        self.enabled.set()


class CursesLogHandler(logging.StreamHandler):
    """self.ui has been set to the UI class before anything is invoked"""

    def emit(self, record):
        log_str = logging.StreamHandler.format(self, record)
        color = self.ui.gettf().curses_color
        # We must acquire both locks.  Otherwise, deadlock can result.
        # This can happen if one thread calls _msg (locking curses, then
        # tf) and another tries to set the color (locking tf, then curses)
        #
        # By locking both up-front here, in this order, we prevent deadlock.
        self.ui.tframe_lock.acquire()
        self.ui.lock()
        try:
            y,x = self.ui.logwin.getyx()
            if y or x: self.ui.logwin.addch(10) # no \n before 1st item
            self.ui.logwin.addstr(log_str, color)
        finally:
            self.ui.unlock()
            self.ui.tframe_lock.release()
        self.ui.logwin.noutrefresh()
        self.ui.stdscr.refresh()

class Blinkenlights(UIBase, CursesUtil):
    """Curses-cased fancy UI.

    Notable instance variables self. ....:

       - stdscr: THe curses std screen
       - bannerwin: The top line banner window
       - width|height: The total curses screen dimensions
       - logheight: Available height for the logging part
       - log_con_handler: The CursesLogHandler()
       - threadframes:
       - accframes[account]: 'Accountframe'"""

    def __init__(self, *args, **kwargs):
        super(Blinkenlights, self).__init__(*args, **kwargs)
        CursesUtil.__init__(self)

    ################################################## UTILS
    def setup_consolehandler(self):
        """Backend specific console handler.

        Sets up things and adds them to self.logger.
        :returns: The logging.Handler() for console output"""

        # create console handler with a higher log level
        ch = CursesLogHandler()
        #ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        self.formatter = logging.Formatter("%(message)s")
        ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(ch)
        # the handler is not usable yet. We still need all the
        # intialization stuff currently done in init_banner. Move here?
        return ch

    def isusable(s):
        """Returns true if the backend is usable ie Curses works."""

        # Not a terminal?  Can't use curses.
        if not sys.stdout.isatty() and sys.stdin.isatty():
            return False
        # No TERM specified?  Can't use curses.
        if not os.environ.get('TERM', None):
            return False
        # Test if ncurses actually starts up fine. Only do so for
        # python>=2.6.6 as calling initscr() twice messing things up.
        # see http://bugs.python.org/issue7567 in python 2.6 to 2.6.5
        if sys.version_info[0:3] < (2,6) or sys.version_info[0:3] >= (2,6,6):
            try:
                curses.initscr()
                curses.endwin()
            except:
                return False
        return True

    def init_banner(self):
        self.availablethreadframes = {}
        self.threadframes = {}
        self.accframes = {}
        self.aflock = Lock()

        self.stdscr = curses.initscr()
        # turn off automatic echoing of keys to the screen
        curses.noecho()
        # react to keys instantly, without Enter key
        curses.cbreak()
        # return special key values, eg curses.KEY_LEFT
        self.stdscr.keypad(1)
        # wait 1s for input, so we don't block the InputHandler infinitely
        self.stdscr.timeout(1000)
        curses.start_color()
        # turn off cursor and save original state
        self.oldcursor = None
        try:
            self.oldcursor = curses.curs_set(0)
        except:
            pass

        self.stdscr.clear()
        self.stdscr.refresh()
        self.init_colorpairs()
        # set log handlers ui to ourself
        self._log_con_handler.ui = self
        self.setupwindows()
        # Settup keyboard handler
        self.inputhandler = InputHandler(self)
        self.inputhandler.set_char_hdlr(self.on_keypressed)

        self.gettf().setcolor('red')
        self.info(offlineimap.banner)

    def acct(self, *args):
        """Output that we start syncing an account (and start counting)."""

        self.gettf().setcolor('purple')
        super(Blinkenlights, self).acct(*args)

    def connecting(self, *args):
        self.gettf().setcolor('white')
        super(Blinkenlights, self).connecting(*args)

    def syncfolders(self, *args):
        self.gettf().setcolor('blue')
        super(Blinkenlights, self).syncfolders(*args)

    def syncingfolder(self, *args):
        self.gettf().setcolor('cyan')
        super(Blinkenlights, self).syncingfolder(*args)

    def skippingfolder(self, *args):
        self.gettf().setcolor('cyan')
        super(Blinkenlights, self).skippingfolder(*args)

    def loadmessagelist(self, *args):
        self.gettf().setcolor('green')
        super(Blinkenlights, self).loadmessagelist(*args)

    def syncingmessages(self, *args):
        self.gettf().setcolor('blue')
        super(Blinkenlights, self).syncingmessages(*args)

    def copyingmessage(self, *args):
        self.gettf().setcolor('orange')
        super(Blinkenlights, self).copyingmessage(*args)

    def deletingmessages(self, *args):
        self.gettf().setcolor('red')
        super(Blinkenlights, self).deletingmessages(*args)

    def addingflags(self, *args):
        self.gettf().setcolor('blue')
        super(Blinkenlights, self).addingflags(*args)

    def deletingflags(self, *args):
        self.gettf().setcolor('blue')
        super(Blinkenlights, self).deletingflags(*args)

    def callhook(self, *args):
        self.gettf().setcolor('white')
        super(Blinkenlights, self).callhook(*args)

    ############ Generic logging functions #############################
    def warn(self, msg, minor=0):
        self.gettf().setcolor('red', curses.A_BOLD)
        super(Blinkenlights, self).warn(msg)

    def threadExited(self, thread):
        acc = self.getthreadaccount(thread)
        with self.tframe_lock:
            if thread in self.threadframes[acc]:
                tf = self.threadframes[acc][thread]
                tf.setcolor('black')
                self.availablethreadframes[acc].append(tf)
                del self.threadframes[acc][thread]
        super(Blinkenlights, self).threadExited(thread)

    def gettf(self):
        """Return the ThreadFrame() of the current thread."""

        cur_thread = currentThread()
        acc = self.getthreadaccount() #Account() or None

        with self.tframe_lock:
            # Ideally we already have self.threadframes[accountname][thread]
            try:
                if cur_thread in self.threadframes[acc]:
                    return self.threadframes[acc][cur_thread]
            except KeyError:
                # Ensure threadframes already has an account dict
                self.threadframes[acc] = {}
                self.availablethreadframes[acc] = deque()

            # If available, return a ThreadFrame()
            if len(self.availablethreadframes[acc]):
                tf = self.availablethreadframes[acc].popleft()
                tf.std_color()
            else:
                tf = self.getaccountframe(acc).get_new_tframe()
            self.threadframes[acc][cur_thread] = tf
        return tf

    def on_keypressed(self, key):
        # received special KEY_RESIZE, resize terminal
        if key == curses.KEY_RESIZE:
            self.resizeterm()

        if key < 1 or key > 255:
            return
        if chr(key) == 'q':
            # Request to quit completely.
            self.warn("Requested shutdown via 'q'")
            offlineimap.accounts.Account.set_abort_event(self.config, 3)
        try:
            index = int(chr(key))
        except ValueError:
            return # Key not a valid number: exit.
        if index >= len(self.hotkeys):
            # Not in our list of valid hotkeys.
            return
        # Trying to end sleep somewhere.
        self.getaccountframe(self.hotkeys[index]).syncnow()

    def sleep(self, sleepsecs, account):
        self.gettf().setcolor('red')
        self.info("Next sync in %d:%02d"% (sleepsecs / 60, sleepsecs % 60))
        return super(Blinkenlights, self).sleep(sleepsecs, account)

    def sleeping(self, sleepsecs, remainingsecs):
        if not sleepsecs:
            # reset color to default if we are done sleeping.
            self.gettf().setcolor('white')
        accframe = self.getaccountframe(self.getthreadaccount())
        return accframe.sleeping(sleepsecs, remainingsecs)

    def resizeterm(self):
        """Resize the current windows."""

        self.exec_locked(self.setupwindows, True)

    def mainException(self):
        UIBase.mainException(self)

    def getpass(self, accountname, config, errmsg=None):
        # disable the hotkeys inputhandler
        self.inputhandler.input_acquire()

        # See comment on _msg for info on why both locks are obtained.
        self.lock()
        try:
            #s.gettf().setcolor('white')
            self.warn(" *** Input Required")
            self.warn(" *** Please enter password for account %s: " % \
                          accountname)
            self.logwin.refresh()
            password = self.logwin.getstr()
        finally:
            self.unlock()
            self.inputhandler.input_release()
        return password

    def setupwindows(self, resize=False):
        """Setup and draw bannerwin and logwin.

        If `resize`, don't create new windows, just adapt size. This
        function should be invoked with CursesUtils.locked()."""

        self.height, self.width = self.stdscr.getmaxyx()
        self.logheight = self.height - len(self.accframes) - 1
        if resize:
            curses.resizeterm(self.height, self.width)
            self.bannerwin.resize(1, self.width)
            self.logwin.resize(self.logheight, self.width)
        else:
            self.bannerwin = curses.newwin(1, self.width, 0, 0)
            self.logwin = curses.newwin(self.logheight, self.width, 1, 0)

        self.draw_bannerwin()
        self.logwin.idlok(True)    # needed for scrollok below
        self.logwin.scrollok(True) # scroll window when too many lines added
        self.draw_logwin()
        self.accounts = reversed(sorted(self.accframes.keys()))
        pos = self.height - 1
        index = 0
        self.hotkeys = []
        for account in self.accounts:
            acc_win = curses.newwin(1, self.width, pos, 0)
            self.accframes[account].setwindow(acc_win, index)
            self.hotkeys.append(account)
            index += 1
            pos -= 1
        curses.doupdate()

    def draw_bannerwin(self):
        """Draw the top-line banner line."""

        if curses.has_colors():
            color = curses.A_BOLD | self.curses_colorpair('banner')
        else:
            color = curses.A_REVERSE
        self.bannerwin.clear() # Delete old content (eg before resizes)
        self.bannerwin.bkgd(' ', color) # Fill background with that color
        string = "%s %s"% (offlineimap.__productname__,
            offlineimap.__version__)
        self.bannerwin.addstr(0, 0, string, color)
        self.bannerwin.addstr(0, self.width -len(offlineimap.__copyright__) -1,
                              offlineimap.__copyright__, color)
        self.bannerwin.noutrefresh()

    def draw_logwin(self):
        """(Re)draw the current logwindow."""

        if curses.has_colors():
            color = curses.color_pair(0) #default colors
        else:
            color = curses.A_NORMAL
        self.logwin.move(0, 0)
        self.logwin.erase()
        self.logwin.bkgd(' ', color)

    def getaccountframe(self, acc_name):
        """Return an AccountFrame() corresponding to acc_name.

        Note that the *control thread uses acc_name `None`."""

        with self.aflock:
            # 1) Return existing or 2) create a new CursesAccountFrame.
            if acc_name in self.accframes: return self.accframes[acc_name]
            self.accframes[acc_name] = CursesAccountFrame(self, acc_name)
            # update the window layout
            self.setupwindows(resize= True)
        return self.accframes[acc_name]

    def terminate(self, *args, **kwargs):
        curses.nocbreak();
        self.stdscr.keypad(0);
        curses.echo()
        curses.endwin()
        # need to remove the Curses console handler now and replace with
        # basic one, so exceptions and stuff are properly displayed
        self.logger.removeHandler(self._log_con_handler)
        UIBase.setup_consolehandler(self)
        # reset the warning method, we do not have curses anymore
        self.warn = super(Blinkenlights, self).warn
        # finally call parent terminate which prints out exceptions etc
        super(Blinkenlights, self).terminate(*args, **kwargs)

    def threadException(self, thread):
        #self._log_con_handler.stop()
        UIBase.threadException(self, thread)

