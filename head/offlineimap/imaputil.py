# IMAP utility module
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

import re

def dequote(string):
    """Takes a string which may or may not be quoted and returns it, unquoted.
    This function does NOT consider parenthised lists to be quoted.
    """

    if not (string[0] == '"' and string[-1] == '"'):
        return string
    string = string[1:-1]               # Strip off quotes.
    string = string.replace('\\"', '"')
    string = string.replace('\\\\', '\\')
    return string

def flagsplit(string):
    if string[0] != '(' or string[-1] != ')':
        raise ValueError, "Passed string '%s' is not a flag list" % string
    return imapsplit(string[1:-1])

def options2hash(list):
    retval = {}
    counter = 0
    while (counter < len(list)):
        retval[list[counter]] = list[counter + 1]
        counter += 2
    return retval

def flags2hash(string):
    return options2hash(flagsplit(string))

def imapsplit(string):
    """Takes a string from an IMAP conversation and returns a list containing
    its components.  One example string is:

    (\\HasNoChildren) "." "INBOX.Sent"

    The result from parsing this will be:

    ['(\\HasNoChildren)', '"."', '"INBOX.Sent"']"""
    
    workstr = string
    retval = []
    while len(workstr):
        if re.search('^\s', workstr):
            workstr = re.search('^\s(.*)$', workstr).group(1)
        elif workstr[0] == '(':
            parenlist = re.search('^(\(.*\))', workstr).group(1)
            workstr = workstr[len(parenlist):]
            retval.append(parenlist)
        elif workstr[0] == '"':
            quotelist = re.search('^("(?:[^"]|\\\\")*")', workstr).group(1)
            workstr = workstr[len(quotelist):]
            retval.append(quotelist)
        else:
            unq = re.search('^(\S+)', workstr).group(1)
            workstr = workstr[len(unq):]
            retval.append(unq)
    return retval
            
def flagsimap2maildir(string):
    flagmap = {'\\Seen': 'S',
               '\\Answered': 'R',
               '\\Flagged': 'F',
               '\\Deleted': 'T',
               '\\Draft': 'D'}
    retval = []
    imapflaglist = flagsplit(string)
    for imapflag in imapflaglist:
        if flagmap.has_key(imapflag):
            retval.append(flagmap[imapflag])
    retval.sort()
    return retval

def flagsmaildir2imap(list):
    flagmap = {'S': '\\Seen',
               'R': '\\Answered',
               'F': '\\Flagged',
               'T': '\\Deleted',
               'D': '\\Draft'}
    retval = []
    for mdflag in list:
        if flagmap.has_key(mdflag):
            retval.append(flagmap[mdflag])
    retval.sort()
    return retval

