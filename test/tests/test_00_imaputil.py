# Copyright (C) 2012- Sebastian Spaeth & contributors
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
import unittest
import logging

from offlineimap import imaputil
from offlineimap.ui import UI_LIST, setglobalui
from offlineimap.CustomConfig import CustomConfigParser

from test.OLItest import OLITestLib

# Things need to be setup first, usually setup.py initializes everything.
# but if e.g. called from command line, we take care of default values here:
if not OLITestLib.cred_file:
    OLITestLib(cred_file='./test/credentials.conf', cmd='./offlineimap.py')

def setUpModule():
    logging.info("Set Up test module %s" % __name__)
    tdir = OLITestLib.create_test_dir(suffix=__name__)

def tearDownModule():
    logging.info("Tear Down test module")
    # comment out next line to keep testdir after test runs. TODO: make nicer
    OLITestLib.delete_test_dir()

#Stuff that can be used
#self.assertEqual(self.seq, range(10))
# should raise an exception for an immutable sequence
#self.assertRaises(TypeError, random.shuffle, (1,2,3))
#self.assertTrue(element in self.seq)
#self.assertFalse(element in self.seq)

class TestInternalFunctions(unittest.TestCase):
    """While the other test files test OfflineImap as a program, these
    tests directly invoke internal helper functions to guarantee that
    they deliver results as expected"""

    @classmethod
    def setUpClass(cls):
        #This is run before all tests in this class
        config= OLITestLib.get_default_config()
        setglobalui(UI_LIST['quiet'](config))

    def test_01_imapsplit(self):
        """Test imaputil.imapsplit()"""
        res = imaputil.imapsplit(b'(\\HasNoChildren) "." "INBOX.Sent"')
        self.assertEqual(res, [b'(\\HasNoChildren)', b'"."', b'"INBOX.Sent"'])

        res = imaputil.imapsplit(b'"mo\\" o" sdfsdf')
        self.assertEqual(res, [b'"mo\\" o"', b'sdfsdf'])

    def test_02_flagsplit(self):
        """Test imaputil.flagsplit()"""
        res = imaputil.flagsplit(b'(\\Draft \\Deleted)')
        self.assertEqual(res, [b'\\Draft', b'\\Deleted'])

        res = imaputil.flagsplit(b'(FLAGS (\\Seen Old) UID 4807)')
        self.assertEqual(res, [b'FLAGS', b'(\\Seen Old)', b'UID', b'4807'])

    def test_04_flags2hash(self):
        """Test imaputil.flags2hash()"""
        res = imaputil.flags2hash(b'(FLAGS (\\Seen Old) UID 4807)')
        self.assertEqual(res, {b'FLAGS': b'(\\Seen Old)', b'UID': b'4807'})

    def test_05_flagsimap2maildir(self):
        """Test imaputil.flagsimap2maildir()"""
        res = imaputil.flagsimap2maildir(b'(\\Draft \\Deleted)')
        self.assertEqual(res, set(b'DT'))

    def test_06_flagsmaildir2imap(self):
        """Test imaputil.flagsmaildir2imap()"""
        res = imaputil.flagsmaildir2imap(set(b'DR'))
        self.assertEqual(res, b'(\\Answered \\Draft)')
        # test all possible flags
        res = imaputil.flagsmaildir2imap(set(b'SRFTD'))
        self.assertEqual(res, b'(\\Answered \\Deleted \\Draft \\Flagged \\Seen)')

    def test_07_uid_sequence(self):
        """Test imaputil.uid_sequence()"""
        res = imaputil.uid_sequence([1,2,3,4,5,10,12,13])
        self.assertEqual(res, b'1:5,10,12:13')
