# Copyright 2014 Eygene A. Ryabinkin.
#
# Module that supports distribution-specific functions.

import platform
import os


# Each dictionary value is either string or some iterable.
# 
# For the former we will just return the value, for an iterable
# we will walk through the values and will return the first
# one that corresponds to the existing file.
__DEF_OS_LOCATIONS = {
    'freebsd': '/usr/local/share/certs/ca-root-nss.crt',
    'openbsd': '/etc/ssl/cert.pem',
    'dragonfly': '/etc/ssl/cert.pem',
    'darwin': [
      # MacPorts, port curl-ca-bundle
      '/opt/local/share/curl/curl-ca-bundle.crt',
    ],
    'linux-ubuntu': '/etc/ssl/certs/ca-certificates.crt',
    'linux-debian': '/etc/ssl/certs/ca-certificates.crt',
    'linux-fedora': '/etc/pki/tls/certs/ca-bundle.crt',
    'linux-redhat': '/etc/pki/tls/certs/ca-bundle.crt',
    'linux-suse': '/etc/ssl/ca-bundle.pem',
}


def get_os_name():
    """
    Finds out OS name.  For non-Linux system it will be just a plain
    OS name (like FreeBSD), for Linux it will be "linux-<distro>",
    where <distro> is the name of the distribution, as returned by
    the first component of platform.linux_distribution.

    Return value will be all-lowercase to avoid confusion about
    proper name capitalisation.

    """
    OS = platform.system().lower()

    if OS.startswith('linux'):
        DISTRO = platform.linux_distribution()[0]
        if DISTRO:
          OS = OS + "-%s" % DISTRO.lower()

    return OS

def get_os_sslcertfile_searchpath():
    """Returns search path for CA bundle for the current OS.
    
    We will return an iterable even if configuration has just
    a single value: it is easier for our callers to be sure
    that they can iterate over result.

    Returned value of None means that there is no search path
    at all.
    """

    OS = get_os_name()

    l = None
    if OS in __DEF_OS_LOCATIONS:
        l = __DEF_OS_LOCATIONS[OS]
        if not hasattr(l, '__iter__'):
            l = (l, )
    return l


def get_os_sslcertfile():
    """
    Finds out the location for the distribution-specific
    CA certificate file bundle.

    Returns the location of the file or None if there is
    no known CA certificate file or all known locations
    correspond to non-existing filesystem objects.
    """

    l = get_os_sslcertfile_searchpath()
    if l == None:
        return None

    for f in l:
      assert (type(f) == type(""))
      if os.path.exists(f) and \
        (os.path.isfile(f) or os.path.islink(f)):
          return f

    return None
