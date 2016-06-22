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


import re   # For folderfilter.
import json
from threading import Lock
from os import listdir, makedirs, path
from sys import exc_info
try:
    import UserDict
except ImportError:
    # Py3
    from collections import UserDict


_mbLock = Lock()
_mbnames = None


def add(accountname, folder_root, foldername):
    global _mbnames
    if _mbnames is None:
        return

    with _mbLock:
        _mbnames.addAccountFolder(accountname, folder_root, foldername)

def init(conf, ui, dry_run):
    global _mbnames
    enabled = conf.getdefaultboolean("mbnames", "enabled", False)
    if enabled is True and _mbnames is None:
        _mbnames = _Mbnames(conf, ui, dry_run)

def write():
    """Write the mbnames file."""

    global _mbnames
    if _mbnames is None:
        return

    if _mbnames.get_incremental() is not True:
        _mbnames.write()

def writeIntermediateFile(accountname):
    """Write intermediate mbnames file."""

    global _mbnames
    if _mbnames is None:
        return

    _mbnames.writeIntermediateFile(accountname)
    if _mbnames.get_incremental() is True:
        _mbnames.write()


class _IntermediateMbnames(object):
    """mbnames data for one account."""

    def __init__(self, accountname, folder_root, mbnamesdir, folderfilter,
            dry_run):

        self._foldernames = []
        self._accountname = accountname
        self._folder_root = folder_root
        self._folderfilter = folderfilter
        self._path = path.join(mbnamesdir, "%s.yml"% accountname)
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
                    'foldername': foldername,
                    'localfolders': self._folder_root,
                })

        if not self._dryrun:
            with open(self._path, "wt") as intermediateFile:
                json.dump(itemlist, intermediateFile)


class _Mbnames(object):
    def __init__(self, config, ui, dry_run):

        self._config = config
        self._dryrun = dry_run
        self.ui = ui

        # Keys: accountname, values: _IntermediateMbnames instance
        self._intermediates = {}
        self._incremental = None
        self._mbnamesdir = None
        self._path = None
        self._folderfilter = lambda accountname, foldername: True
        self._func_sortkey = lambda d: (d['accountname'], d['foldername'])
        self._peritem = self._config.get("mbnames", "peritem", raw=1)

        localeval = config.getlocaleval()
        self._header = localeval.eval(config.get("mbnames", "header"))
        self._sep = localeval.eval(config.get("mbnames", "sep"))
        self._footer = localeval.eval(config.get("mbnames", "footer"))

        mbnamesdir = path.join(config.getmetadatadir(), "mbnames")
        try:
            if not self._dryrun:
                makedirs(mbnamesdir)
        except OSError:
            pass
        self._mbnamesdir = mbnamesdir

        xforms = [path.expanduser, path.expandvars]
        self._path = config.apply_xforms(
            config.get("mbnames", "filename"), xforms)

        if self._config.has_option("mbnames", "sort_keyfunc"):
            self._func_sortkey = localeval.eval(
                self._config.get("mbnames", "sort_keyfunc"), {'re': re})

        if self._config.has_option("mbnames", "folderfilter"):
            self._folderfilter = localeval.eval(
                self._config.get("mbnames", "folderfilter"), {'re': re})

    def addAccountFolder(self, accountname, folder_root, foldername):
        """Add foldername entry for an account."""

        if accountname not in self._intermediates:
            self._intermediates[accountname] = _IntermediateMbnames(
                accountname,
                folder_root,
                self._mbnamesdir,
                self._folderfilter,
                self._dryrun,
            )

        self._intermediates[accountname].add(foldername)

    def get_incremental(self):
        if self._incremental is None:
            self._incremental = self._config.getdefaultboolean(
                "mbnames", "incremental", False)

        return self._incremental

    def write(self):
        itemlist = []

        try:
            for foo in listdir(self._mbnamesdir):
                foo = path.join(self._mbnamesdir, foo)
                if path.isfile(foo) and foo[-5:] == '.json':
                    try:
                        with open(foo, 'rt') as intermediateFile:
                            for item in json.load(intermediateFile):
                                itemlist.append(item)
                    except Exception as e:
                        self.ui.error(
                            e,
                            exc_info()[2],
                            "intermediate mbnames file %s not properly read"% foo
                        )
        except OSError:
            pass

        itemlist.sort(key=self._func_sortkey)
        itemlist = [self._peritem % d for d in itemlist]

        if not self._dryrun:
            try:
                with open(self._path, 'wt') as mbnamesFile:
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
