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
import random
import unittest
import logging
import os, sys
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
    OLITestLib.delete_test_dir()

#Stuff that can be used
#self.assertEqual(self.seq, range(10))
# should raise an exception for an immutable sequence
#self.assertRaises(TypeError, random.shuffle, (1,2,3))
#self.assertTrue(element in self.seq)
#self.assertFalse(element in self.seq)

class TestBasicFunctions(unittest.TestCase):
    #@classmethod
    #def setUpClass(cls):
    #This is run before all tests in this class
    #    cls._connection = createExpensiveConnectionObject()

    #@classmethod
    #This is run after all tests in this class
    #def tearDownClass(cls):
    #    cls._connection.destroy()

    # This will be run before each test
    #def setUp(self):
    #    self.seq = range(10)

    def test_01_olistartup(self):
        """Tests if OLI can be invoked without exceptions

        Cleans existing remote tet folders. Then syncs all "OLItest*
        (specified in the default config) to our local Maildir. The
        result should be 0 folders and 0 mails."""
        OLITestLib.delete_remote_testfolders()
        code, res = OLITestLib.run_OLI()
        self.assertEqual(res, "")
        boxes, mails = OLITestLib.count_maildir_mails('')
        self.assertTrue((boxes, mails)==(0,0), msg="Expected 0 folders and 0 "
            "mails, but sync led to {} folders and {} mails".format(
                boxes, mails))

    def test_02_createdir(self):
        """Create local OLItest 1 & OLItest "1" maildir, sync

        Folder names with quotes used to fail and have been fixed, so
        one is included here as a small challenge."""
        OLITestLib.create_maildir('INBOX.OLItest 1')
        OLITestLib.create_maildir('INBOX.OLItest "1"')
        code, res = OLITestLib.run_OLI()
        #logging.warn("%s %s "% (code, res))
        self.assertEqual(res, "")
        boxes, mails = OLITestLib.count_maildir_mails('')
        self.assertTrue((boxes, mails)==(2,0), msg="Expected 2 folders and 0"
            "mails, but sync led to {} folders and {} mails".format(
                boxes, mails))

    def test_03_nametransmismatch(self):
        """Create mismatching remote and local nametrans rules

        This should raise an error."""
        config = OLITestLib.get_default_config()
        config.set('Repository IMAP', 'nametrans',
                   'lambda f: f' )
        config.set('Repository Maildir', 'nametrans',
                   'lambda f: f + "moo"' )
        OLITestLib.write_config_file(config)
        code, res = OLITestLib.run_OLI()
        #logging.warn("%s %s "% (code, res))
        # We expect an INFINITE FOLDER CREATION WARNING HERE....
        mismatch = "ERROR: INFINITE FOLDER CREATION DETECTED!" in res
        self.assertEqual(mismatch, True, msg="Mismatching nametrans rules did "
            "NOT trigger an 'infinite folder generation' error. Output was:\n"
             "{}".format(res))

