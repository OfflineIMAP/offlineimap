# Tk UI
# Copyright (C) 2002 John Goerzen
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

from Tkinter import *
from threading import *
import thread, traceback, time
from StringIO import StringIO
from ScrolledText import ScrolledText
from offlineimap import threadutil, version
from Queue import Queue
from UIBase import UIBase

class PasswordDialog:
    def __init__(self, accountname, config, master=None):
        self.top = Toplevel(master)
        self.top.title(version.productname + " Password Entry")
        self.label = Label(self.top,
                           text = "%s: Enter password for %s on %s: " % \
                           (accountname, config.get(accountname, "remoteuser"),
                            config.get(accountname, "remotehost")))
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
        

class TkUI(UIBase):
    def isusable(s):
        try:
            Tk().destroy()
            return 1
        except TclError:
            return 0

    def _createTopWindow(self):
        self.top = Tk()
        self.top.title(version.productname + " " + version.versionstr)
        self.threadframes = {}
        self.availablethreadframes = []
        self.tflock = Lock()
        self.notdeleted = 1

        t = threadutil.ExitNotifyThread(target = self._runmainloop,
                                        name = "Tk Mainloop")
        t.setDaemon(1)
        t.start()

        t = threadutil.ExitNotifyThread(target = self.idlevacuum,
                                        name = "Tk idle vacuum")
        t.setDaemon(1)
        t.start()

    def _runmainloop(s):
        s.top.mainloop()
        s.notdeleted = 0
    
    def getpass(s, accountname, config):
        pd = PasswordDialog(accountname, config)
        return pd.getpassword()

    def gettf(s):
        threadid = thread.get_ident()
        s.tflock.acquire()
        try:
            if threadid in s.threadframes:
                return s.threadframes[threadid]
            if len(s.availablethreadframes):
                tf = s.availablethreadframes.pop(0)
                tf.setthread(currentThread())
            else:
                tf = ThreadFrame(s.top)
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

    def idlevacuum(s):
        while s.notdeleted:
            time.sleep(10)
            s.tflock.acquire()
            while len(s.availablethreadframes):
                tf = s.availablethreadframes.pop()
                tf.destroy()
            s.tflock.release()
            
    def threadException(s, thread):
        msg =  "Thread '%s' terminated with exception:\n%s" % \
              (thread.getName(), thread.getExitStackTrace())
        print msg
    
        s.top.destroy()
        s.top = None
        TextOKDialog("Thread Exception", msg)
        s.terminate(100)

    def mainException(s):
        sbuf = StringIO()
        traceback.print_exc(file = sbuf)
        msg = "Main program terminated with exception:\n" + sbuf.getvalue()
        print msg

        s.top.destroy()
        s.top = None
        TextOKDialog("Main Program Exception", msg)

    def warn(s, msg):
        TextOKDialog("OfflineIMAP Warning", msg)

    def init_banner(s):
        s._createTopWindow()
        s._msg(version.productname + " " + version.versionstr + ", " +\
               version.copyright)
        tf = s.gettf().getthreadextraframe()

        def showlicense():
            TextOKDialog(version.productname + " License",
                         version.bigcopyright + "\n" +
                         version.homepage + "\n\n" + version.license,
                         blocking = 0, master = tf)
        b = Button(tf, text = "About", command = showlicense)
        b.pack(side = LEFT)
        
        b = Button(tf, text = "Exit", command = s.terminate)
        b.pack(side = RIGHT)

    def deletingmessages(s, uidlist, destlist):
        ds = s.folderlist(destlist)
        s._msg("Deleting %d messages in %s" % (len(uidlist), ds))

    def _sleep_cancel(s, args = None):
        s.sleeping_abort = 1

    def sleep(s, sleepsecs):
        s.sleeping_abort = 0
        tf = s.gettf().getthreadextraframe()

        sleepbut = Button(tf, text = 'Sync immediately',
                          command = s._sleep_cancel)
        sleepbut.pack()
        UIBase.sleep(s, sleepsecs)
        
    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs:
            s._msg("Next sync in %d:%02d" % (remainingsecs / 60,
                                             remainingsecs % 60))
        else:
            s._msg("Wait done; synchronizing now.")
            s.gettf().destroythreadextraframe()
        time.sleep(sleepsecs)
        return s.sleeping_abort


