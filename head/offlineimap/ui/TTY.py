import UIBase
from getpass import getpass

class TTYUI(UIBase.UIBase):
    def _msg(s, msg):
        print msg

    def getpass(s, accountname, host, port, user):
        return getpass("%s: Password required for %s on %s" %
                       (accountname, user, host))
    
