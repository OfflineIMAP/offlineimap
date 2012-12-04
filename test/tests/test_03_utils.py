# Copyright (C) 2012- Michael Vogt
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
import os

import offlineimap.utils 


class TestUtils(unittest.TestCase):

    def test_get_system_default_cacertfile_ubuntu(self):
        offlineimap.utils.DISTRO_CODENAME = "Ubuntu"
        self.assertEqual(
            offlineimap.utils.get_system_default_cacertfile(),
            "/etc/ssl/certs/ca-certificates.crt")

    def test_get_system_default_cacertfile_unknown(self):
        offlineimap.utils.DISTRO_CODENAME = None
        self.assertEqual(
            offlineimap.utils.get_system_default_cacertfile(), None)

    def test_get_system_default_cacertfile_unsupported(self):
        offlineimap.utils.DISTRO_CODENAME = 'mvo-linux'
        self.assertEqual(
            offlineimap.utils.get_system_default_cacertfile(), None)


if __name__ == "__main__":
    unittest.main()
