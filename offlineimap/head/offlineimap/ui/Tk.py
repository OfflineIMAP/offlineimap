# Tk UI
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

from __future__ import nested_scopes

from Tkinter import *
import tkFont
from threading import *
import thread, traceback, time, threading
from StringIO import StringIO
from ScrolledText import ScrolledText
from offlineimap import threadutil, version
from Queue import Queue
from UIBase import UIBase
from offlineimap.ui.Blinkenlights import BlinkenBase

class PasswordDialog:
    def __init__(self, accountname, config, master=None, errmsg = None):
        self.top = Toplevel(master)
        self.top.title(version.productname + " Password Entry")
        text = ''
        if errmsg:
            text = '%s: %s\n' % (accountname, errmsg)
        text += "%s: Enter password for %s on %s: " % \
                (accountname, config.get(accountname, "remoteuser"),
                 config.get(accountname, "remotehost"))
        self.label = Label(self.top, text = text)
        self.label.pack()

        self.entry = Entry(self.top, show='*')
        self.entry.bind("<Return>", self.ok)
        self.entry.pack()
        self.entry.focus_force()

        self.button = Button(self.top, text = "OK", command=self.ok)
        self.button.pack()

        self.entry.focus_force()
        self.top.wait_window(self.label)

    def ok(self, args = None):
        self.password = self.entry.get()
        self.top.destroy()

    def getpassword(self):
        return self.password

class TextOKDialog:
    def __init__(self, title, message, blocking = 1, master = None):
        if not master:
            self.top = Tk()
        else:
            self.top = Toplevel(master)
        self.top.title(title)
        self.text = ScrolledText(self.top, font = "Courier 10")
        self.text.pack()
        self.text.insert(END, message)
        self.text['state'] = DISABLED
        self.button = Button(self.top, text = "OK", command=self.ok)
        self.button.pack()

        if blocking:
            self.top.wait_window(self.button)

    def ok(self):
        self.top.destroy()
        
                                 

class ThreadFrame(Frame):
    def __init__(self, master=None):
        self.threadextraframe = None
        self.thread = currentThread()
        self.threadid = thread.get_ident()
        Frame.__init__(self, master, relief = RIDGE, borderwidth = 2)
        self.pack(fill = 'x')
        self.threadlabel = Label(self, foreground = '#FF0000',
                                 text ="Thread %d (%s)" % (self.threadid,
                                                     self.thread.getName()))
        self.threadlabel.pack()
        self.setthread(currentThread())

        self.account = "Unknown"
        self.mailbox = "Unknown"
        self.loclabel = Label(self,
                              text = "Account/mailbox information unknown")
        #self.loclabel.pack()

        self.updateloclabel()

        self.message = Label(self, text="Messages will appear here.\n",
                             foreground = '#0000FF')
        self.message.pack(fill = 'x')

    def setthread(self, newthread):
        if newthread:
            self.threadlabel['text'] = newthread.getName()
        else:
            self.threadlabel['text'] = "No thread"
        self.destroythreadextraframe()

    def destroythreadextraframe(self):
        if self.threadextraframe:
            self.threadextraframe.destroy()
            self.threadextraframe = None

    def getthreadextraframe(self):
        if self.threadextraframe:
            return self.threadextraframe
        self.threadextraframe = Frame(self)
        self.threadextraframe.pack(fill = 'x')
        return self.threadextraframe

    def setaccount(self, account):
        self.account = account
        self.mailbox = "Unknown"
        self.updateloclabel()

    def setmailbox(self, mailbox):
        self.mailbox = mailbox
        self.updateloclabel()

    def updateloclabel(self):
        self.loclabel['text'] = "Processing %s: %s" % (self.account,
                                                       self.mailbox)
    
    def appendmessage(self, newtext):
        self.message['text'] += "\n" + newtext

    def setmessage(self, newtext):
        self.message['text'] = newtext
        

class VerboseUI(UIBase):
    def isusable(s):
        try:
            Tk().destroy()
            return 1
        except TclError:
            return 0

    def _createTopWindow(self, doidlevac = 1):
        self.notdeleted = 1
        self.created = threading.Event()

        self.af = {}
        self.aflock = Lock()

        t = threadutil.ExitNotifyThread(target = self._runmainloop,
                                        name = "Tk Mainloop")
        t.setDaemon(1)
        t.start()

        self.created.wait()
        del self.created

        if doidlevac:
            t = threadutil.ExitNotifyThread(target = self.idlevacuum,
                                            name = "Tk idle vacuum")
            t.setDaemon(1)
            t.start()

    def _runmainloop(s):
        s.top = Tk()
        s.top.title(version.productname + " " + version.versionstr)
        s.top.after_idle(s.created.set)
        s.top.mainloop()
        s.notdeleted = 0

    def getaccountframe(s):
        accountname = s.getthreadaccount()
        s.aflock.acquire()
        try:
            if accountname in s.af:
                return s.af[accountname]

            s.af[accountname] = LEDAccountFrame(s.top, accountname,
                                                s.fontfamily, s.fontsize)
        finally:
            s.aflock.release()
        return s.af[accountname]
    
    def getpass(s, accountname, config, errmsg = None):
        pd = PasswordDialog(accountname, config, errmsg = errmsg)
        return pd.getpassword()

    def gettf(s, newtype=ThreadFrame, master = None):
        if master == None:
            master = s.top
        threadid = thread.get_ident()
        s.tflock.acquire()
        try:
            if threadid in s.threadframes:
                return s.threadframes[threadid]
            if len(s.availablethreadframes):
                tf = s.availablethreadframes.pop(0)
                tf.setthread(currentThread())
            else:
                tf = newtype(master)
            s.threadframes[threadid] = tf
            return tf
        finally:
            s.tflock.release()

    def _msg(s, msg):
        s.gettf().setmessage(msg)

    def threadExited(s, thread):
        threadid = thread.threadid
        s.tflock.acquire()
        if threadid in s.threadframes:
            tf = s.threadframes[threadid]
            tf.setthread(None)
            tf.setaccount("Unknown")
            tf.setmessage("Idle")
            s.availablethreadframes.append(tf)
            del s.threadframes[threadid]
        s.tflock.release()
        UIBase.threadExited(s, thread)

    def idlevacuum(s):
        while s.notdeleted:
            time.sleep(10)
            s.tflock.acquire()
            while len(s.availablethreadframes):
                tf = s.availablethreadframes.pop()
                tf.destroy()
            s.tflock.release()
            
    def threadException(s, thread):
        exceptionstr = s.getThreadExceptionString(thread)
        print exceptionstr
    
        s.top.destroy()
        s.top = None
        TextOKDialog("Thread Exception", exceptionstr)
        s.delThreadDebugLog(thread)
        s.terminate(100)

    def mainException(s):
        exceptionstr = s.getMainExceptionString()
        print exceptionstr

        s.top.destroy()
        s.top = None
        TextOKDialog("Main Program Exception", exceptionstr)

    def warn(s, msg, minor):
        if minor:
            # Just let the default handler catch it
            UIBase.warn(s, msg, minor)
        else:
            TextOKDialog("OfflineIMAP Warning", msg)

    def showlicense(s):
        TextOKDialog(version.productname + " License",
                     version.bigcopyright + "\n" +
                     version.homepage + "\n\n" + version.license,
                     blocking = 0, master = s.top)


    def init_banner(s):
        s._createTopWindow()
        s._msg(version.productname + " " + version.versionstr + ", " +\
               version.copyright)
        tf = s.gettf().getthreadextraframe()

        b = Button(tf, text = "About", command = s.showlicense)
        b.pack(side = LEFT)
        
        b = Button(tf, text = "Exit", command = s.terminate)
        b.pack(side = RIGHT)
        s.sleeping_abort = {}

    def deletingmessages(s, uidlist, destlist):
        ds = s.folderlist(destlist)
        s._msg("Deleting %d messages in %s" % (len(uidlist), ds))

    def _sleep_cancel(s, args = None):
        s.sleeping_abort[thread.get_ident()] = 1

    def sleep(s, sleepsecs):
        threadid = thread.get_ident()
        s.sleeping_abort[threadid] = 0
        tf = s.gettf().getthreadextraframe()

        def sleep_cancel():
            s.sleeping_abort[threadid] = 1

        sleepbut = Button(tf, text = 'Sync immediately',
                          command = sleep_cancel)
        sleepbut.pack()
        UIBase.sleep(s, sleepsecs)
        
    def sleeping(s, sleepsecs, remainingsecs):
        retval = s.sleeping_abort[thread.get_ident()]
        if remainingsecs:
            s._msg("Next sync in %d:%02d" % (remainingsecs / 60,
                                             remainingsecs % 60))
        else:
            s._msg("Wait done; synchronizing now.")
            s.gettf().destroythreadextraframe()
            del s.sleeping_abort[thread.get_ident()]
        time.sleep(sleepsecs)
        return retval

TkUI = VerboseUI

################################################## Blinkenlights

class LEDAccountFrame:
    def __init__(self, top, accountname, fontfamily, fontsize):
        self.top = top
        self.accountname = accountname
        self.fontfamily = fontfamily
        self.fontsize = fontsize
        self.frame = Frame(self.top, background = 'black')
        self.frame.pack(side = BOTTOM, expand = 1, fill = X)
        self._createcanvas(self.frame)

        self.label = Label(self.frame, text = accountname,
                           background = "black", foreground = "blue",
                           font = (self.fontfamily, self.fontsize))
        self.label.grid(sticky = E, row = 0, column = 1)

    def getnewthreadframe(s):
        return LEDThreadFrame(s.canvas)

    def _createcanvas(self, parent):
        c = LEDFrame(parent)
        self.canvas = c
        c.grid(sticky = E, row = 0, column = 0)
        parent.grid_columnconfigure(1, weight = 1)
        #c.pack(side = LEFT, expand = 0, fill = X)

    def startsleep(s, sleepsecs):
        s.sleeping_abort = 0
        s.button = Button(s.frame, text = "Sync now", command = s.syncnow,
                          background = "black", activebackground = "black",
                          activeforeground = "white",
                          foreground = "blue", highlightthickness = 0,
                          padx = 0, pady = 0,
                          font = (s.fontfamily, s.fontsize), borderwidth = 0,
                          relief = 'solid')
        s.button.grid(sticky = E, row = 0, column = 2)

    def syncnow(s):
        s.sleeping_abort = 1

    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs:
            s.button.config(text = 'Sync now (%d:%02d remain)' % \
                            (remainingsecs / 60, remainingsecs % 60))
            time.sleep(sleepsecs)
        else:
            s.button.destroy()
            del s.button
        return s.sleeping_abort

class LEDFrame(Frame):
    """This holds the different lights."""
    def getnewobj(self):
        retval = Canvas(self, background = 'black', height = 20, bd = 0,
                        highlightthickness = 0, width = 10)
        retval.pack(side = LEFT, padx = 0, pady = 0, ipadx = 0, ipady = 0)
        return retval

class LEDThreadFrame:
    """There is one of these for each little light."""
    def __init__(self, master):
        self.canvas = master.getnewobj()
        self.color = ''
        self.ovalid = self.canvas.create_oval(5, 5, 10,
                                              10, fill = 'gray',
                                              outline = '#303030')

    def setcolor(self, newcolor):
        if newcolor != self.color:
            self.canvas.itemconfigure(self.ovalid, fill = newcolor)
            self.color = newcolor

    def getcolor(self):
        return self.color

    def setthread(self, newthread):
        if newthread:
            self.setcolor('gray')
        else:
            self.setcolor('black')


class Blinkenlights(BlinkenBase, VerboseUI):
    def __init__(s, config, verbose = 0):
        VerboseUI.__init__(s, config, verbose)
        s.fontfamily = 'Helvetica'
        s.fontsize = 8
        if config.has_option('ui.Tk.Blinkenlights', 'fontfamily'):
            s.fontfamily = config.get('ui.Tk.Blinkenlights', 'fontfamily')
        if config.has_option('ui.Tk.Blinkenlights', 'fontsize'):
            s.fontsize = config.getint('ui.Tk.Blinkenlights', 'fontsize')

    def _createTopWindow(self):
        VerboseUI._createTopWindow(self, 0)
        #self.top.resizable(width = 0, height = 0)
        self.top.configure(background = 'black', bd = 0)

        widthmetric = tkFont.Font(family = self.fontfamily, size = self.fontsize).measure("0")
        self.loglines = 5
        if self.config.has_option("ui.Tk.Blinkenlights", "loglines"):
            self.loglines = self.config.getint("ui.Tk.Blinkenlights",
                                               "loglines")
        self.bufferlines = 500
        if self.config.has_option("ui.Tk.Blinkenlights", "bufferlines"):
            self.bufferlines = self.config.getint("ui.Tk.Blinkenlights",
                                                  "bufferlines")
        self.text = ScrolledText(self.top, bg = 'black', #scrollbar = 'y',
                                 font = (self.fontfamily, self.fontsize),
                                 bd = 0, highlightthickness = 0, setgrid = 0,
                                 state = DISABLED, height = self.loglines,
                                 wrap = NONE, width = 60)
        self.text.vbar.configure(background = '#000050',
                                 activebackground = 'blue',
                                 highlightbackground = 'black',
                                 troughcolor = "black", bd = 0,
                                 elementborderwidth = 2)
                                 
        self.textenabled = 0
        self.tags = []
        self.textlock = Lock()

    def init_banner(s):
        BlinkenBase.init_banner(s)
        s._createTopWindow()
        menubar = Menu(s.top, activebackground = "black",
                       activeforeground = "white",
                       activeborderwidth = 0,
                       background = "black", foreground = "blue",
                       font = (s.fontfamily, s.fontsize), bd = 0)
        menubar.add_command(label = "About", command = s.showlicense)
        menubar.add_command(label = "Show Log", command = s._togglelog)
        menubar.add_command(label = "Exit", command = s.terminate)
        s.top.config(menu = menubar)
        s.menubar = menubar
        s.text.see(END)
        if s.config.has_option("ui.Tk.Blinkenlights", "showlog") and \
           s.config.getboolean("ui.Tk.Blinkenlights", "showlog"):
            s._togglelog()
        s.gettf().setcolor('red')
        s.top.resizable(width = 0, height = 0)
        s._msg(version.banner)

    def _togglelog(s):
        if s.textenabled:
            s.oldtextheight = s.text.winfo_height()
            s.text.pack_forget()
            s.textenabled = 0
            s.menubar.entryconfig('Hide Log', label = 'Show Log')
            s.top.update()
            s.top.geometry("")
            s.top.update()
            s.top.resizable(width = 0, height = 0)
            s.top.update()
        
        else: 
            s.text.pack(side = TOP, expand = 1, fill = BOTH)
            s.textenabled = 1
            s.top.update()
            s.top.geometry("")
            s.menubar.entryconfig('Show Log', label = 'Hide Log')
            s._rescroll()
            s.top.resizable(width = 1, height = 1)

    def sleep(s, sleepsecs):
        s.gettf().setcolor('red')
        s._msg("Next sync in %d:%02d" % (sleepsecs / 60, sleepsecs % 60))
        BlinkenBase.sleep(s, sleepsecs)

    def sleeping(s, sleepsecs, remainingsecs):
        return BlinkenBase.sleeping(s, sleepsecs, remainingsecs)

    def _rescroll(s):
        s.text.see(END)
        lo, hi = s.text.vbar.get()
        s.text.vbar.set(1.0 - (hi - lo), 1.0)

    def _msg(s, msg):
        if "\n" in msg:
            for thisline in msg.split("\n"):
                s._msg(thisline)
            return
        #VerboseUI._msg(s, msg)
        color = s.gettf().getcolor()
        rescroll = 1
        s.textlock.acquire()
        try:
            if s.text.vbar.get()[1] != 1.0:
                rescroll = 0
            s.text.config(state = NORMAL)
            if not color in s.tags:
                s.text.tag_config(color, foreground = color)
                s.tags.append(color)
            s.text.insert(END, "\n" + msg, color)

            # Trim down.  Not quite sure why I have to say 7 instead of 5,
            # but so it is.
            while float(s.text.index(END)) > s.bufferlines + 2.0:
                s.text.delete(1.0, 2.0)

            if rescroll:
                s._rescroll()
        finally:
            s.text.config(state = DISABLED)
            s.textlock.release()

    
