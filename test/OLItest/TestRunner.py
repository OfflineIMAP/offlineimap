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
import imaplib
import unittest
import logging
import os
import re
import sys
import shutil
import subprocess
import tempfile
import random
random.seed()

from offlineimap.CustomConfig import CustomConfigParser
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
        assert cls.cred_file != None
        # creating temporary dir for testing in same dir as credentials.conf
        cls.testdir = os.path.abspath(
            tempfile.mkdtemp(prefix='tmp_%s_'%suffix,
                             dir=os.path.dirname(cls.cred_file)))
        cls.write_config_file()
        return cls.testdir

    @classmethod
    def get_default_config(cls):
        """Creates a default ConfigParser file and returns it

        The returned config can be manipulated and then saved with
        write_config_file()"""
        #TODO, only do first time and cache then for subsequent calls?
        assert cls.cred_file != None
        assert cls.testdir != None
        config = CustomConfigParser()
        config.readfp(default_conf)
        default_conf.seek(0) # rewind config_file to start
        config.read(cls.cred_file)
        config.set("general", "metadata", cls.testdir)
        return config

    @classmethod
    def write_config_file(cls, config=None):
        """Creates a OLI configuration file

        It is created in testdir (so create_test_dir has to be called
        earlier) using the credentials information given (so they had
        to be set earlier). Failure to do either of them will raise an
        AssertionException. If config is None, a default one will be
        used via get_default_config, otherwise it needs to be a config
        object derived from that."""
        if config is None:
            config = cls.get_default_config()
        localfolders = os.path.join(cls.testdir, 'mail')
        config.set("Repository Maildir", "localfolders", localfolders)
        with open(os.path.join(cls.testdir, 'offlineimap.conf'), "wt") as f:
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

        :returns: (rescode, stdout (as unicode))
        """
        try:
            output = subprocess.check_output(
                [cls.cmd,
                 "-c%s" % os.path.join(cls.testdir, 'offlineimap.conf')],
                shell=False)
        except subprocess.CalledProcessError as e:
            return (e.returncode, e.output.decode('utf-8'))
        return (0, output.decode('utf-8'))

    @classmethod
    def delete_remote_testfolders(cls, reponame=None):
        """Delete all INBOX.OLITEST* folders on the remote IMAP repository

        reponame: All on `reponame` or all IMAP-type repositories if None"""
        config = cls.get_default_config()
        if reponame:
            sections = ['Repository {0}'.format(reponame)]
        else:
            sections = [r for r in config.sections() \
                            if r.startswith('Repository')]
            sections = [s for s in sections if config.get(s, 'Type').lower() == 'imap']
        for sec in sections:
            # Connect to each IMAP repo and delete all folders
            # matching the folderfilter setting. We only allow basic
            # settings and no fancy password getting here...
            # 1) connect and get dir listing
            host = config.get(sec, 'remotehost')
            user = config.get(sec, 'remoteuser')
            passwd = config.get(sec, 'remotepass')
            imapobj = imaplib.IMAP4(host)
            imapobj.login(user, passwd)
            res_t, data = imapobj.list()
            assert res_t == 'OK'
            dirs = []
            for d in data:
                if d == '':
                    continue
                if isinstance(d, tuple):
                    # literal (unquoted)
                    folder = b'"%s"' % d[1].replace('"', '\\"')
                else:
                    m = re.search(br'''
                        [ ]                     # space
                        (?P<dir>
                        (?P<quote>"?)           # starting quote
                        ([^"]|\\")*             # a non-quote or a backslashded quote
                        (?P=quote))$            # ending quote
                        ''', d, flags=re.VERBOSE)
                    folder = bytearray(m.group('dir'))
                    if not m.group('quote'):
                        folder = '"%s"' % folder
                #folder = folder.replace(br'\"', b'"') # remove quoting
                dirs.append(folder)
            # 2) filter out those not starting with INBOX.OLItest and del...
            dirs = [d for d in dirs if d.startswith(b'"INBOX.OLItest') or d.startswith(b'"INBOX/OLItest')]
            for folder in dirs:
                res_t, data = imapobj.delete(folder)
                assert res_t == 'OK', "Folder deletion of {0} failed with error"\
                    ":\n{1} {2}".format(folder.decode('utf-8'), res_t, data)
            imapobj.logout()

    @classmethod
    def create_maildir(cls, folder):
        """Create empty maildir 'folder' in our test maildir

        Does not fail if it already exists"""
        assert cls.testdir != None
        maildir = os.path.join(cls.testdir, 'mail', folder)
        for subdir in ('','tmp','cur','new'):
            try:
                os.makedirs(os.path.join(maildir, subdir))
            except OSError as e:
                if e.errno != 17: # 'already exists' is ok.
                    raise

    @classmethod
    def delete_maildir(cls, folder):
        """Delete maildir 'folder' in our test maildir

        Does not fail if not existing"""
        assert cls.testdir != None
        maildir = os.path.join(cls.testdir, 'mail', folder)
        shutil.rmtree(maildir, ignore_errors=True)

    @classmethod
    def create_mail(cls, folder, mailfile=None, content=None):
        """Create a mail in  maildir 'folder'/new

        Use default mailfilename if not given.
        Use some default content if not given"""
        assert cls.testdir != None
        while True:  # Loop till we found a unique filename
            mailfile = '{0}:2,'.format(random.randint(0,999999999))
            mailfilepath = os.path.join(cls.testdir, 'mail',
                                        folder, 'new', mailfile)
            if not os.path.isfile(mailfilepath):
                break
        with open(mailfilepath,"wb") as mailf:
                mailf.write(b'''From: test <test@offlineimap.org>
Subject: Boo
Date: 1 Jan 1980
To: test@offlineimap.org

Content here.''')

    @classmethod
    def count_maildir_mails(cls, folder):
        """Returns the number of mails in maildir 'folder'

        Counting only those in cur&new (ignoring tmp)."""
        assert cls.testdir != None
        maildir = os.path.join(cls.testdir, 'mail', folder)

        boxes, mails = 0, 0
        for dirpath, dirs, files in os.walk(maildir, False):
            if set(dirs) == set(['cur', 'new', 'tmp']):
                # New maildir folder
                boxes += 1
                #raise RuntimeError("%s is not Maildir" % maildir)
            if dirpath.endswith(('/cur', '/new')):
                mails += len(files)
        return boxes, mails

    # find UID in a maildir filename
    re_uidmatch = re.compile(',U=(\d+)')

    @classmethod
    def get_maildir_uids(cls, folder):
        """Returns a list of maildir mail uids, 'None' if no valid uid"""
        assert cls.testdir != None
        mailfilepath = os.path.join(cls.testdir, 'mail', folder)
        assert os.path.isdir(mailfilepath)
        ret = []
        for dirpath, dirs, files in os.walk(mailfilepath):
            if not dirpath.endswith((os.path.sep + 'new', os.path.sep + 'cur')):
                continue # only /new /cur are interesting
            for file in files:
                m = cls.re_uidmatch.search(file)
                uid = m.group(1) if m else None
                ret.append(uid)
        return ret
