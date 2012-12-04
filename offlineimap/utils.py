# imaplib utilities
# Copyright (C) 2012 Michael Vogt <mvo@debian.org>
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

import platform
import os

DISTRO_CODENAME = platform.linux_distribution()[0]

DISTRO_TO_CA_CERTFILE_MAPPING = {
    'ubuntu': '/etc/ssl/certs/ca-certificates.crt',
    'debian': '/etc/ssl/certs/ca-certificates.crt',
    'fedora': '/etc/pki/tls/certs/ca-bundle.crt',
    'redhat': '/etc/pki/tls/certs/ca-bundle.crt',
    'suse': '/etc/ssl/ca-bundle.pem',
}


def get_system_default_cacertfile(ui):
    if not DISTRO_CODENAME:
        return None
    system_ca_certfile = DISTRO_TO_CA_CERTFILE_MAPPING.get(
        DISTRO_CODENAME.lower(), None)
    if system_ca_certfile is None:
        ui.info("No ca-cert default location known for '%s'" % DISTRO_CODENAME)
        return None
    if not os.path.exists(system_ca_certfile):
        ui.info("No file found on expected ca-cert location '%s'" % 
                system_ca_certfile)
        return None
    return system_ca_certfile
