# IMAP utility module
# Copyright (C) 2002-2015 John Goerzen & contributors
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

import re
import string
from offlineimap.ui import getglobalui


## Globals

# Message headers that use space as the separator (for label storage)
SPACE_SEPARATED_LABEL_HEADERS = ('X-Label', 'Keywords')

# Find the modified UTF-7 shifts of an international mailbox name.
MUTF7_SHIFT_RE = re.compile(r'&[^-]*-|\+')


def __debug(*args):
    msg = []
    for arg in args:
        msg.append(str(arg))
    getglobalui().debug('imap', " ".join(msg))

def dequote(s):
    """Takes string which may or may not be quoted and unquotes it.

    It only considers double quotes. This function does NOT consider
    parenthised lists to be quoted."""

    if s and s.startswith('"') and s.endswith('"'):
        s = s[1:-1]  # Strip off the surrounding quotes.
        s = s.replace('\\"', '"')
        s = s.replace('\\\\', '\\')
    return s

def quote(s):
    """Takes an unquoted string and quotes it.

    It only adds double quotes. This function does NOT consider
    parenthised lists to be quoted."""

    s = s.replace('"', '\\"')
    s = s.replace('\\', '\\\\')
    return '"%s"'% s

def flagsplit(s):
    """Converts a string of IMAP flags to a list

    :returns: E.g. '(\\Draft \\Deleted)' returns  ['\\Draft','\\Deleted'].
        (FLAGS (\\Seen Old) UID 4807) returns
        ['FLAGS,'(\\Seen Old)','UID', '4807']
    """

    if s[0] != '(' or s[-1] != ')':
        raise ValueError("Passed s '%s' is not a flag list"% s)
    return imapsplit(s[1:-1])

def __options2hash(list):
    """convert list [1,2,3,4,5,6] to {1:2, 3:4, 5:6}"""

    # effectively this does dict(zip(l[::2],l[1::2])), however
    # measurements seemed to have indicated that the manual variant is
    # faster for mosly small lists.
    retval = {}
    counter = 0
    while (counter < len(list)):
        retval[list[counter]] = list[counter + 1]
        counter += 2
    __debug("__options2hash returning:", retval)
    return retval

def flags2hash(flags):
    """Converts IMAP response string from eg IMAP4.fetch() to a hash.

    E.g. '(FLAGS (\\Seen Old) UID 4807)' leads to
    {'FLAGS': '(\\Seen Old)', 'UID': '4807'}"""

    return __options2hash(flagsplit(flags))

def imapsplit(imapstring):
    """Takes a string from an IMAP conversation and returns a list containing
    its components.  One example string is:

    (\\HasNoChildren) "." "INBOX.Sent"

    The result from parsing this will be:

    ['(\\HasNoChildren)', '"."', '"INBOX.Sent"']"""

    if not isinstance(imapstring, str):
        __debug("imapsplit() got a non-string input; working around.")
        # Sometimes, imaplib will throw us a tuple if the input
        # contains a literal.  See Python bug
        # #619732 at https://sourceforge.net/tracker/index.php?func=detail&aid=619732&group_id=5470&atid=105470
        # One example is:
        # result[0] = '() "\\\\" Admin'
        # result[1] = ('() "\\\\" {19}', 'Folder\\2')
        #
        # This function will effectively get result[0] or result[1], so
        # if we get the result[1] version, we need to parse apart the tuple
        # and figure out what to do with it.  Each even-numbered
        # part of it should end with the {} number, and each odd-numbered
        # part should be directly a part of the result.  We'll
        # artificially quote it to help out.
        retval = []
        for i in range(len(imapstring)):
            if i % 2:                   # Odd: quote then append.
                arg = imapstring[i]
                # Quote code lifted from imaplib
                arg = arg.replace('\\', '\\\\')
                arg = arg.replace('"', '\\"')
                arg = '"%s"' % arg
                __debug("imapsplit() non-string [%d]: Appending %s"% (i, arg))
                retval.append(arg)
            else:
                # Even -- we have a string that ends with a literal
                # size specifier.  We need to strip off that, then run
                # what remains through the regular imapsplit parser.
                # Recursion to the rescue.
                arg = imapstring[i]
                arg = re.sub('\{\d+\}$', '', arg)
                __debug("imapsplit() non-string [%d]: Feeding %s to recursion"%\
                    (i, arg))
                retval.extend(imapsplit(arg))
        __debug("imapsplit() non-string: returning %s" % str(retval))
        return retval

    workstr = imapstring.strip()
    retval = []
    while len(workstr):
        # handle parenthized fragments (...()...)
        if workstr[0] == '(':
            rparenc = 1 # count of right parenthesis to match
            rpareni = 1 # position to examine
            while rparenc: # Find the end of the group.
                if workstr[rpareni] == ')':  # end of a group
                    rparenc -= 1
                elif workstr[rpareni] == '(':  # start of a group
                    rparenc += 1
                rpareni += 1  # Move to next character.
            parenlist = workstr[0:rpareni]
            workstr = workstr[rpareni:].lstrip()
            retval.append(parenlist)
        elif workstr[0] == '"':
            # quoted fragments '"...\"..."'
            (quoted, rest) = __split_quoted(workstr)
            retval.append(quoted)
            workstr = rest
        else:
            splits = None
            # Python2
            if hasattr(string, 'split'):
                splits = string.split(workstr, maxsplit = 1)
            # Python3
            else:
                splits = str.split(workstr, maxsplit = 1)
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

flagmap = [('\\Seen', 'S'),
           ('\\Answered', 'R'),
           ('\\Flagged', 'F'),
           ('\\Deleted', 'T'),
           ('\\Draft', 'D')]

def flagsimap2maildir(flagstring):
    """Convert string '(\\Draft \\Deleted)' into a flags set(DR)."""

    retval = set()
    imapflaglist = flagstring[1:-1].split()
    for imapflag, maildirflag in flagmap:
        if imapflag in imapflaglist:
            retval.add(maildirflag)
    return retval

def flagsimap2keywords(flagstring):
    """Convert string '(\\Draft \\Deleted somekeyword otherkeyword)' into a
    keyword set (somekeyword otherkeyword)."""

    imapflagset = set(flagstring[1:-1].split())
    serverflagset = set([flag for (flag, c) in flagmap])
    return imapflagset - serverflagset

def flagsmaildir2imap(maildirflaglist):
    """Convert set of flags ([DR]) into a string '(\\Deleted \\Draft)'."""

    retval = []
    for imapflag, maildirflag in flagmap:
        if maildirflag in maildirflaglist:
            retval.append(imapflag)
    return '(' + ' '.join(sorted(retval)) + ')'

def uid_sequence(uidlist):
    """Collapse UID lists into shorter sequence sets

    [1,2,3,4,5,10,12,13] will return "1:5,10,12:13".  This function sorts
    the list, and only collapses if subsequent entries form a range.
    :returns: The collapsed UID list as string."""

    def getrange(start, end):
        if start == end:
            return(str(start))
        return "%s:%s"% (start, end)

    if not len(uidlist): return '' # Empty list, return
    start, end = None, None
    retval = []
    # Force items to be longs and sort them
    sorted_uids = sorted(map(int, uidlist))

    for item in iter(sorted_uids):
        item = int(item)
        if start == None:     # First item
            start, end = item, item
        elif item == end + 1: # Next item in a range
            end = item
        else:                 # Starting a new range
            retval.append(getrange(start, end))
            start, end = item, item

    retval.append(getrange(start, end)) # Add final range/item
    return ",".join(retval)


def __split_quoted(s):
    """Looks for the ending quote character in the string that starts
    with quote character, splitting out quoted component and the
    rest of the string (without possible space between these two
    parts.

    First character of the string is taken to be quote character.

    Examples:
     - "this is \" a test" (\\None) => ("this is \" a test", (\\None))
     - "\\" => ("\\", )
    """

    if len(s) == 0:
        return ('', '')

    q = quoted = s[0]
    rest = s[1:]
    while True:
        next_q = rest.find(q)
        if next_q == -1:
            raise ValueError("can't find ending quote '%s' in '%s'"% (q, s))
        # If quote is preceeded by even number of backslashes,
        # then it is the ending quote, otherwise the quote
        # character is escaped by backslash, so we should
        # continue our search.
        is_escaped = False
        i = next_q - 1
        while i >= 0 and rest[i] == '\\':
            i -= 1
            is_escaped = not is_escaped
        quoted += rest[0:next_q + 1]
        rest = rest[next_q + 1:]
        if not is_escaped:
            return (quoted, rest.lstrip())


def format_labels_string(header, labels):
    """Formats labels for embedding into a message,
    with format according to header name.

    Headers from SPACE_SEPARATED_LABEL_HEADERS keep space-separated list
    of labels, the rest uses comma (',') as the separator.

    Also see parse_labels_string() and modify it accordingly
    if logics here gets changed."""

    if header in SPACE_SEPARATED_LABEL_HEADERS:
        sep = ' '
    else:
        sep = ','

    return sep.join(labels)


def parse_labels_string(header, labels_str):
    """Parses a string into a set of labels, with a format according to
    the name of the header.

    See __format_labels_string() for explanation on header handling
    and keep these two functions synced with each other.

    TODO: add test to ensure that
    - format_labels_string * parse_labels_string is unity
    and
    - parse_labels_string * format_labels_string is unity
    """

    if header in SPACE_SEPARATED_LABEL_HEADERS:
        sep = ' '
    else:
        sep = ','

    labels = labels_str.strip().split(sep)

    return set([l.strip() for l in labels if l.strip()])


def labels_from_header(header_name, header_value):
    """Helper that builds label set from the corresponding header value.

    Arguments:
    - header_name: name of the header that keeps labels;
    - header_value: value of the said header, can be None

    Returns: set of labels parsed from the header (or empty set).
    """

    if header_value:
        labels = parse_labels_string(header_name, header_value)
    else:
        labels = set()

    return labels


def decode_mailbox_name(name):
    """Decodes a modified UTF-7 mailbox name.

    If the string cannot be decoded, it is returned unmodified.

    See RFC 3501, sec. 5.1.3.

    Arguments:
    - name: string, possibly encoded with modified UTF-7

    Returns: decoded UTF-8 string.
    """
    def demodify(m):
        s = m.group()
        if s == '+':
            return '+-'
        return '+' + s[1:-1].replace(',', '/') + '-'

    ret = MUTF7_SHIFT_RE.sub(demodify, name)

    try:
        return ret.decode('utf-7').encode('utf-8')
    except UnicodeEncodeError:
        return name
