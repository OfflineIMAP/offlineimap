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
import thread
from offlineimap import threadutil
from Queue import Queue
import UIBase

class PasswordDialog:
    def __init__(self, accountname, config, master=None):
        self.top = Toplevel(master)
        self.label = Label(self.frame,
                           text = "%s: Enter password for %s on %s: " % \
                           (accountname, config.get(accountname, "remoteuser"),
                            config.get(accountname, "remotehost")))
        self.label.pack()

        self.entry = Entry(self.top, show='*')
        self.entry.pack()

        self.button = Button(self.top, text = "OK", command=self.ok)
        self.button.pack()

        self.top.wait_window(self.label)

    def ok(self):
        self.password = self.entry.get()
        self.top.destroy()

    def createwidgets(self):
        self.text = Text

    def getpassword(self):
        return self.password

class ThreadFrame(Frame):
    def __init__(self, master=None):
        self.thread = currentThread()
        self.threadid = thread.get_ident()
        Frame.__init__(self, master)
        self.pack()
        self.threadlabel = Label(self, text ="Thread %d (%s)" % (self.threadid,
                                                     self.thread.getName()))
        self.threadlabel.pack()

        self.account = "Unknown"
        self.mailbox = "Unknown"
        self.loclabel = Label(self, text = "Account/mailbox information unknown")
        self.loclabel.pack()

        self.updateloclabel()

        self.messages = Label(self, text="Messages will appear here.\n")
        self.messages.pack()

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
    def __init__(self):
        self.top = Tk()
        self.threadframes = {}
        
    def getpass(s, accountname, config):
        pd = PasswordDialog(accountname, config, Tk())
        return pd.getpassword()

    def gettf(s):
        threadid = thread.get_ident()
        if threadid in self.threadframes:
            return s.threadframes[threadid]
        tf = ThreadFrame(s.top)
        s.threadframes[threadid] = tf
        return tf

    def _msg(s, msg):
        s.gettf().setmessage(msg)

    def threadExited(s, thread):
        threadid = self.threadid
        if threadid in self.threadframes:
            tf = self.threadframes[threadid]
            tf.destroy()
            del tf[threadid]
    
    
