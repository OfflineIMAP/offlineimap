# UI module
# Copyright (C) 2010-2011 Sebastian Spaeth & contributors
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

from offlineimap.ui.UIBase import getglobalui, setglobalui
from offlineimap.ui import TTY, Noninteractive, Machine

UI_LIST = {'ttyui': TTY.TTYUI,
           'basic': Noninteractive.Basic,
           'quiet': Noninteractive.Quiet,
           'syslog': Noninteractive.Syslog,
           'machineui': Machine.MachineUI}

#add Blinkenlights UI if it imports correctly (curses installed)
try:
    from offlineimap.ui import Curses
    UI_LIST['blinkenlights'] = Curses.Blinkenlights
except ImportError:
    pass
