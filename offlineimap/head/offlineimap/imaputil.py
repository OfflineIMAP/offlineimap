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

import re, string
quotere = re.compile('^("(?:[^"]|\\\\")*")')

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

def imapsplit(imapstring):
    """Takes a string from an IMAP conversation and returns a list containing
    its components.  One example string is:

    (\\HasNoChildren) "." "INBOX.Sent"

    The result from parsing this will be:

    ['(\\HasNoChildren)', '"."', '"INBOX.Sent"']"""
    
    workstr = imapstring.strip()
    retval = []
    while len(workstr):
        if workstr[0] == '(':
            # Needs rindex to properly process eg (FLAGS () UID 123)
            rpareni = workstr.rindex(')') + 1
            parenlist = workstr[0:rpareni]
            workstr = workstr[rpareni:].lstrip()
            retval.append(parenlist)
        elif workstr[0] == '"':
            quotelist = quotere.search(workstr).group(1)
            workstr = workstr[len(quotelist):].lstrip()
            retval.append(quotelist)
        else:
            splits = string.split(workstr, maxsplit = 1)
            splitslen = len(splits)
            # The unquoted word is splits[0]; the remainder is splits[1]
            if splitslen == 2:
                # There's an unquoted word, and more string follows.
                retval.append(splits[0])
                workstr = splits[1]    # split will have already lstripped it
                continue
            elif splitslen == 1:
                # We got a last unquoted word, but nothing else
                retval.append(splits[0])
                # Nothing remains.  workstr would be ''
                break
            elif splitslen == 0:
                # There was not even an unquoted word.
                break
    return retval
            
def flagsimap2maildir(string):
    flagmap = {'\\seen': 'S',
               '\\answered': 'R',
               '\\flagged': 'F',
               '\\deleted': 'T',
               '\\draft': 'D'}
    retval = []
    imapflaglist = [x.lower() for x in flagsplit(string)]
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
    return '(' + ' '.join(retval) + ')'

def listjoin(list):
    start = None
    end = None
    retval = []

    def getlist(start, end):
        if start == end:
            return(str(start))
        else:
            return(str(start) + ":" + str(end))
        

    for item in list:
        if start == None:
            # First item.
            start = item
            end = item
        elif item == end + 1:
            # An addition to the list.
            end = item
        else:
            # Here on: starting a new list.
            retval.append(getlist(start, end))
            start = item
            end = item

    if start != None:
        retval.append(getlist(start, end))

    return ",".join(retval)



            
        
