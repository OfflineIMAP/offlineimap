from UIBase import UIBase
from getpass import getpass
import select, sys

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

    def sleeping(s, sleepsecs, remainingsecs):
        if remainingsecs > 0:
            sys.stdout.write("Next sync in %d:%02d (press Enter to sync now)   \r" % \
                             (remainingsecs / 60, remainingsecs % 60))
            sys.stdout.flush()
        else:
            sys.stdout.write("Wait done, proceeding with sync....            ")

        if sleepsecs > 0:
            if len(select.select([sys.stdin], [], [], sleepsecs)[0]):
                return 1
        return 0
    
            
