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
import os
import sys
import shutil
import subprocess
import tempfile
from ConfigParser import SafeConfigParser
from . import default_conf

class OLITestLib():
    cred_file = None
    testdir = None
    """Absolute path of the current temporary test directory"""
    cmd = None
    """command that will be executed to invoke offlineimap"""

    def __init__(self, cred_file = None, cmd='offlineimap'):
        """

        :param cred_file: file of the configuration
            snippet for authenticating against the test IMAP server(s).
        :param cmd: command that will be executed to invoke offlineimap"""
        OLITestLib.cred_file = cred_file
        if not os.path.isfile(cred_file):
            raise UserWarning("Please copy 'credentials.conf.sample' to '%s' "
                "and set your credentials there." % cred_file)
        OLITestLib.cmd = cmd

    @classmethod
    def create_test_dir(cls, suffix=''):
        """Creates a test directory and places OLI config there

        Note that this is a class method. There can only be one test
        directory at a time. OLITestLib is not suited for running
        several tests in parallel.  The user is responsible for
        cleaning that up herself."""
        # creating temporary directory for testing in current dir
        cls.testdir = os.path.abspath(
            tempfile.mkdtemp(prefix='tmp_%s_'%suffix, dir='.'))
        cls.create_config_file()
        return cls.testdir

    @classmethod
    def create_config_file(cls):
        """Creates a OLI configuration file

        It is created in testdir (so create_test_dir has to be called
        earlier) using the credentials information given (so they had to
        be set earlier). Failure to do either of them will raise an
        AssertionException."""
        assert cls.cred_file != None
        assert cls.testdir != None
        config = SafeConfigParser()
        config.readfp(default_conf)
        config.read(cls.cred_file)
        config.set("general", "metadata", cls.testdir)
        localfolders = os.path.join(cls.testdir, 'mail')
        config.set("Repository Maildir", "localfolders", localfolders)
        with open(os.path.join(cls.testdir, 'offlineimap.conf'), "wa") as f:
            config.write(f)

    @classmethod
    def delete_test_dir(cls):
        """Deletes the current test directory

        The users is responsible for cleaning that up herself."""
        if os.path.isdir(cls.testdir):
            shutil.rmtree(cls.testdir)

    @classmethod
    def run_OLI(cls):
        """Runs OfflineImap

        :returns: (rescode, stdout)
        """
        try:
            output = subprocess.check_output(
                [cls.cmd,
                 "-c%s" % os.path.join(cls.testdir, 'offlineimap.conf')],
                shell=False)
        except subprocess.CalledProcessError as e:
            return (e.returncode, e.output)
        return (0, output)

class OLITextTestRunner(unittest.TextTestRunner):

    def __init__(self,*args, **kwargs):
        logging.warning("OfflineImap testsuite")
        return super(OLITextTestRunner, self).__init__(*args, **kwargs)
