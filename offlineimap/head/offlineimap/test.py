#!/usr/bin/python2.2 -i
import hmac
def getpassword():
    return 'tanstaaftanstaaf'

def md5handler(response):
        challenge = response.strip()
        print "challenge is", challenge
        msg = getpassword()
        reply = hmac.new(challenge, msg)
        retval = 'tim' + ' ' + \
                     reply.hexdigest()
        while len(retval) < 64:
            retval += "\0"

        print "md5handler returning", retval
        return retval
