# Some useful functions to extract data out of emails
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

import email
from email.parser import Parser as MailParser

def get_message_date(content, header='Date'):
    """Parses mail and returns resulting timestamp.

    :param header: the header to extract date from;
    :returns: timestamp or `None` in the case of failure.
    """

    message = MailParser().parsestr(content, True)
    dateheader = message.get(header)
    # parsedate_tz returns a 10-tuple that can be passed to mktime_tz
    # Will be None if missing or not in a valid format.  Note that
    # indexes 6, 7, and 8 of the result tuple are not usable.
    datetuple = email.utils.parsedate_tz(dateheader)
    if datetuple is None:
        return None
    return email.utils.mktime_tz(datetuple)
