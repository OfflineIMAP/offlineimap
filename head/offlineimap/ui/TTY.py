from UIBase import UIBase
from getpass import getpass

class TTYUI(UIBase):
    def __init__(self, verbose = 0):
        self.verbose = 0
        
    def _msg(s, msg):
        print msg

    def getpass(s, accountname, host, port, user):
        return getpass("%s: Enter password for %s on %s: " %
                       (accountname, user, host))

    def syncingmessages(s, sr, sf, dr, df):
        if s.verbose:
            UIBase.syncingmessages(s, sr, sf, dr, df)

    def loadmessagelist(s, repos, folder):
        if s.verbose:
            UIBase.syncingmessages(s, repos, folder)
    
    def messagelistloaded(s, repos, folder, count):
        if s.verbose:
            UIBase.messagelistloaded(s, repos, folder, count)
