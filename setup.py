#!/usr/bin/env python

# $Id: setup.py,v 1.1 2002/06/21 18:10:49 jgoerzen Exp $

# IMAP synchronization
# Module: installer
# COPYRIGHT #
# Copyright (C) 2002 - 2006 John Goerzen
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

import os
from distutils.core import setup, Command
import offlineimap
import logging
from test.OLItest import TextTestRunner, TestLoader, OLITestLib

class TestCommand(Command):
    """runs the OLI testsuite"""
    description = """Runs the test suite. In order to execute only a single
        test, you could also issue e.g. 'python -m unittest
        test.tests.test_01_basic.TestBasicFunctions.test_01_olistartup' on the
        command line."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        logging.basicConfig(format='%(message)s')
        # set credentials and OfflineImap command to be executed:
        OLITestLib(cred_file='./test/credentials.conf', cmd='./offlineimap.py')
        suite = TestLoader().discover('./test/tests')
        #TODO: failfast does not seem to exist in python2.6?
        TextTestRunner(verbosity=2,failfast=True).run(suite)


setup(name = "offlineimap",
      version = offlineimap.__version__,
      description = offlineimap.__description__,
      author = offlineimap.__author__,
      author_email = offlineimap.__author_email__,
      url = offlineimap.__homepage__,
      packages = ['offlineimap', 'offlineimap.folder',
                  'offlineimap.repository', 'offlineimap.ui',
                  'offlineimap.utils'],
      scripts = ['bin/offlineimap'],
      license = offlineimap.__copyright__ + \
                ", Licensed under the GPL version 2",
      cmdclass = { 'test': TestCommand}
)

