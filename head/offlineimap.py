#!/usr/bin/python2.2 -i

# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
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

from imapsync import imaplib
import re
import getpass

host = raw_input('Host: ')
user = raw_input('Username: ')
passwd = getpass.getpass('Password: ')

imapobj = imaplib.IMAP4_SSL(host)
imapobj.login(user, passwd)

def imapsplit(string):
    workstr = string
    retval = []
    while len(workstr):
        if re.search('^\s', workstr):
            workstr = re.search('^\s(.*)$', workstr).group(1)
        elif workstr[0] == '(':
            parenlist = re.search('^(\([^)]*\))', workstr).group(1)
            workstr = workstr[len(parenlist):]
            retval.append(parenlist)
        elif workstr[0] == '"':
            quotelist = re.search('^("[^"]*")', workstr).group(1)
            workstr = workstr[len(quotelist):]
            retval.append(quotelist)
        else:
            unq = re.search('^(\S+)', workstr).group(1)
            workstr = workstr[len(unq):]
            retval.append(unq)
    return retval
            
            

def parselistresult(liststr):
    return re.match('^(\(.*\))\s+(\".*\")\s+(\".*\")$', liststr).groups()

delim, root = parselistresult(imapobj.list('""', '""')[1][0])[1:]
