# UI base class
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

import offlineimap.ui
import sys

def findUI(config, chosenUI=None):
    uistrlist = ['Tk.Blinkenlights', 'Tk.VerboseUI', 'TTY.TTYUI',
                 'Noninteractive.Basic', 'Noninteractive.Quiet']
    namespace={}
    for ui in dir(offlineimap.ui):
        if ui.startswith('_') or ui=='detector':
            continue
        namespace[ui]=getattr(offlineimap.ui, ui)

    if chosenUI is not None:
        uistrlist = [chosenUI]
    elif config.has_option("general", "ui"):
        uistrlist = config.get("general", "ui").replace(" ", "").split(",")

    for uistr in uistrlist:
        uimod = getUImod(uistr, config.getlocaleval(), namespace)
        if uimod:
            uiinstance = uimod(config)
            if uiinstance.isusable():
                return uiinstance
    sys.stderr.write("ERROR: No UIs were found usable!\n")
    sys.exit(200)
    
def getUImod(uistr, localeval, namespace):
    try:
        uimod = localeval.eval(uistr, namespace)
    except (AttributeError, NameError), e:
        #raise
        return None
    return uimod
