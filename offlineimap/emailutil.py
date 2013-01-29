# Some useful functions to extract data out of emails
# Copyright (C) 2002-2012 John Goerzen & contributors
# Copyright (C) 2013 Cyril Russo
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

import email
import time

def getmessagedate(content, header = 'Date', rtime=None):
    """Parses mail and returns an struct_time tuple

    It will use information in the following order, falling back as an attempt fails:
    - rtime parameter
    - Date header of email

    We return None, if we couldn't find a valid date. 

    :param rtime: epoch timestamp to be used rather than analyzing
           the email.
    :param header: the header to use for the message time
    :returns: date tuple or `None` in case of failure."""
    if rtime is None:
        message = email.message_from_string(content)
        dateheader = message.get(header)
        # parsedate_tz returns a 10-tuple that can be passed to mktime_tz
        # Will be None if missing or not in a valid format.  Note that
        # indexes 6, 7, and 8 of the result tuple are not usable.
        datetuple = email.utils.parsedate_tz(dateheader)
        if datetuple is None:
            #could not determine the date, use the local time.
            return None
        #make it a real struct_time, so we have named attributes
        datetuple = time.localtime(email.utils.mktime_tz(datetuple))
    else:
        #rtime is set, use that instead
        datetuple = time.localtime(rtime)

    return datetuple


def checkdatetuple(datetuple):
    """ Check the given date tuple for incoherent value.
    :param :datetuple the tuple to check against
    :return the datetuple if it seems correct, `None` otherwise."""
    try:
        # Check for invalid dates
        if datetuple[0] < 1981:
            raise ValueError

        # Check for invalid dates
        datetuple_check = time.localtime(time.mktime(datetuple))
        if datetuple[:2] != datetuple_check[:2]:
            raise ValueError

    except (ValueError, OverflowError):
        return None

    return datetuple
