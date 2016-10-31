# Mailbox name generator
# Copyright (C) 2002-2016 John Goerzen & contributors
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


import codecs
import re   # For folderfilter.
import json
from threading import Lock
from os import listdir, makedirs, path, unlink
from sys import exc_info
try:
    from ConfigParser import NoSectionError
except ImportError: # Py3.
    from configparser import NoSectionError


_mbLock = Lock()
_mbnames = None


def add(accountname, folder_root, foldername):
    global _mbnames
    if _mbnames.is_enabled() is not True:
        return

    with _mbLock:
        _mbnames.addAccountFolder(accountname, folder_root, foldername)


def init(conf, ui, dry_run):
    global _mbnames
    if _mbnames is None:
        _mbnames = _Mbnames(conf, ui, dry_run)


def prune(accounts):
    global _mbnames
    if _mbnames.is_enabled() is True:
        _mbnames.prune(accounts)
    else:
        _mbnames.pruneAll()


def write():
    """Write the mbnames file."""

    global _mbnames
    if _mbnames.is_enabled() is not True:
        return

    if _mbnames.get_incremental() is not True:
        _mbnames.write()


def writeIntermediateFile(accountname):
    """Write intermediate mbnames file."""

    global _mbnames
    if _mbnames.is_enabled() is not True:
        return

    _mbnames.writeIntermediateFile(accountname)
    if _mbnames.get_incremental() is True:
        _mbnames.write()


class _IntermediateMbnames(object):
    """mbnames data for one account."""

    def __init__(self, accountname, folder_root, mbnamesdir, folderfilter,
            dry_run, ui):

        self.ui = ui
        self._foldernames = []
        self._accountname = accountname
        self._folder_root = folder_root
        self._folderfilter = folderfilter
        self._path = path.join(mbnamesdir, "%s.json"% accountname)
        self._dryrun = dry_run

    def add(self, foldername):
        self._foldernames.append(foldername)

    def get_folder_root(self):
        return self._folder_root

    def write(self):
        """Write intermediate mbnames file in JSON format."""

        itemlist = []

        for foldername in self._foldernames:
            if self._folderfilter(self._accountname, foldername):
                itemlist.append({
                    'accountname': self._accountname,
                    'foldername': foldername.decode('utf-8'),
                    'localfolders': self._folder_root,
                })

        if self._dryrun:
            self.ui.info("mbnames would write %s"% self._path)
        else:
            with codecs.open(
                self._path, "wt", encoding='UTF-8') as intermediateFD:
                json.dump(itemlist, intermediateFD)


class _Mbnames(object):
    def __init__(self, config, ui, dry_run):

        self._config = config
        self.ui = ui
        self._dryrun = dry_run

        self._enabled = None
        # Keys: accountname, values: _IntermediateMbnames instance.
        self._intermediates = {}
        self._incremental = None
        self._mbnamesdir = None
        self._path = None
        self._folderfilter = lambda accountname, foldername: True
        self._func_sortkey = lambda d: (d['accountname'], d['foldername'])
        localeval = config.getlocaleval()
        mbnamesdir = path.join(config.getmetadatadir(), "mbnames")
        self._peritem = None
        self._header = None
        self._sep = None
        self._footer = None

        try:
            if not self._dryrun:
                makedirs(mbnamesdir)
        except OSError:
            pass
        self._mbnamesdir = mbnamesdir

        try:
            self._enabled = self._config.getdefaultboolean(
                "mbnames", "enabled", False)
            self._peritem = self._config.get("mbnames", "peritem", raw=1)
            self._header = localeval.eval(config.get("mbnames", "header"))
            self._sep = localeval.eval(config.get("mbnames", "sep"))
            self._footer = localeval.eval(config.get("mbnames", "footer"))

            xforms = [path.expanduser, path.expandvars]
            self._path = config.apply_xforms(
                config.get("mbnames", "filename"), xforms)

            if self._config.has_option("mbnames", "sort_keyfunc"):
                self._func_sortkey = localeval.eval(
                    self._config.get("mbnames", "sort_keyfunc"), {'re': re})

            if self._config.has_option("mbnames", "folderfilter"):
                self._folderfilter = localeval.eval(
                    self._config.get("mbnames", "folderfilter"), {'re': re})
        except NoSectionError:
            pass

    def _iterIntermediateFiles(self):
        for foo in listdir(self._mbnamesdir):
            foo = path.join(self._mbnamesdir, foo)
            if path.isfile(foo) and foo[-5:] == '.json':
                yield foo

    def _removeIntermediateFile(self, path):
        if self._dryrun:
            self.ui.info("mbnames would remove %s"% path)
        else:
            unlink(path)
            self.ui.info("removed %s"% path)

    def addAccountFolder(self, accountname, folder_root, foldername):
        """Add foldername entry for an account."""

        if accountname not in self._intermediates:
            self._intermediates[accountname] = _IntermediateMbnames(
                accountname,
                folder_root,
                self._mbnamesdir,
                self._folderfilter,
                self._dryrun,
                self.ui,
            )

        self._intermediates[accountname].add(foldername)

    def get_incremental(self):
        if self._incremental is None:
            self._incremental = self._config.getdefaultboolean(
                "mbnames", "incremental", False)

        return self._incremental

    def is_enabled(self):
        return self._enabled

    def prune(self, accounts):
        removals = False
        for intermediateFile in self._iterIntermediateFiles():
            filename = path.basename(intermediateFile)
            accountname = filename[:-5]
            if accountname not in accounts:
                removals = True
                self._removeIntermediateFile(intermediateFile)

        if removals is False:
            self.ui.info("no cache file to remove")

    def pruneAll(self):
        for intermediateFile in self._iterIntermediateFiles():
            self._removeIntermediateFile(intermediateFile)

    def write(self):
        itemlist = []

        for intermediateFile in self._iterIntermediateFiles():
            try:
                with codecs.open(
                    intermediateFile, 'rt', encoding="UTF-8") as intermediateFD:
                    for item in json.load(intermediateFD):
                        itemlist.append(item)
            except (OSError, IOError) as e:
                self.ui.error("could not read intermediate mbnames file '%s':"
                    "%s"% (intermediateFile, str(e)))
            except Exception as e:
                self.ui.error(
                    e,
                    exc_info()[2],
                    ("intermediate mbnames file %s not properly read"%
                        intermediateFile)
                )

        itemlist.sort(key=self._func_sortkey)
        itemlist = [self._peritem % d for d in itemlist]

        if self._dryrun:
            self.ui.info("mbnames would write %s"% self._path)
        else:
            try:
                with codecs.open(
                    self._path, 'wt', encoding='UTF-8') as mbnamesFile:
                    mbnamesFile.write(self._header)
                    mbnamesFile.write(self._sep.join(itemlist))
                    mbnamesFile.write(self._footer)
            except (OSError, IOError) as e:
                self.ui.error(
                    e,
                    exc_info()[2],
                    "mbnames file %s not properly written"% self._path
                )

    def writeIntermediateFile(self, accountname):
        try:
            self._intermediates[accountname].write()
        except (OSError, IOError) as e:
            self.ui.error(
                e,
                exc_info()[2],
                "intermediate mbnames file %s not properly written"% self._path
            )
