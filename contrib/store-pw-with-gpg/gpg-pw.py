#!/usr/bin/python
# Originally taken from: http://stevelosh.com/blog/2012/10/the-homely-mutt/
# by Steve Losh
# Modified by Lorenzo Grespan on Jan, 2014

import re
import subprocess
from sys import argv
import logging
from os.path import expanduser
import unittest
import os
import sys

logging.basicConfig(level=logging.INFO)


DEFAULT_PASSWORDS_FILE = os.path.join(
    os.path.expanduser('~/Mail'),
    'passwords.gpg')


def get_keychain_pass(account=None, server=None):
    '''Mac OSX keychain password extraction'''
    params = {
        'security': '/usr/bin/security',
        'command': 'find-internet-password',
        'account': account,
        'server': server,
        'keychain': expanduser('~') + '/Library/Keychains/login.keychain',
    }
    command = ("%(security)s -v %(command)s"
               " -g -a %(account)s -s %(server)s %(keychain)s" % params)
    output = subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT)
    outtext = [l for l in output.splitlines()
               if l.startswith('password: ')][0]
    return find_password(outtext)


def find_password(text):
    '''Helper method for osx password extraction'''
    # a non-capturing group
    r = re.match(r'password: (?:0x[A-F0-9]+  )?"(.*)"', text)
    if r:
        return r.group(1)
    else:
        logging.warn("Not found")
        return None


def get_gpg_pass(account, storage):
    '''GPG method'''
    command = ("gpg", "-d", storage)
    # get attention
    print '\a'  # BEL
    output = subprocess.check_output(command)
    # p = subprocess.Popen(command, stdout=subprocess.PIPE)
    # output, err = p.communicate()
    for line in output.split('\n'):
        r = re.match(r'{} ([a-zA-Z0-9]+)'.format(account), line)
        if r:
            return r.group(1)
    return None


def get_pass(account=None, server=None, passwd_file=None):
    '''Main method'''
    if not passwd_file:
        storage = DEFAULT_PASSWORDS_FILE
    else:
        storage = os.path.join(
            os.path.expanduser('~/Mail'),
            passwd_file)
    if os.path.exists('/usr/bin/security'):
        return get_keychain_pass(account, server)
    if os.path.exists(storage):
        logging.info("Using {}".format(storage))
        return get_gpg_pass(account, storage)
    else:
        logging.warn("No password file found")
        sys.exit(1)
    return None


# test with: python -m unittest <this module name>
# really basic tests.. nothing to see. move along
class Tester(unittest.TestCase):
    def testMatchSimple(self):
        text = 'password: "exampleonetimepass "'
        self.assertTrue(find_password(text))

    def testMatchComplex(self):
        text = r'password: 0x74676D62646D736B646970766C66696B0A  "anotherexamplepass\012"'
        self.assertTrue(find_password(text))


if __name__ == "__main__":
    print get_pass(argv[1], argv[2], argv[3])
