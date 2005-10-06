"""oflpy.py - for offlineimaprc use"""
__revision__ = '1.0'

import re

# --------------------------------
folder_s = """\.\.\/|,\ |\/\.|\*|\ \&-\ |\'|\.|\)|\("""
folder_re = re.compile( folder_s )

def getfoldername(foldername):
    """substitute for a possibly-buggy IMAP folder name"""
    return folder_re.sub('_', foldername)

def test_gfn():
    """test: substitute for a possibly-buggy IMAP folder name"""
    from namet import bad_folders

    for f_name in bad_folders:
        #print f_name, '\t\t', getfoldername(f_name)
        print getfoldername(f_name)

# --------------------------------
filter_s = """^Public Folders|^Calendar|^Contacts|^Tasks|^Drafts|^Journal|^[a-zA-Z0-9 _\-/!]+/\.$"""
filter_s = """^Public Folders|^Calendar|^Contacts|^Tasks|^Drafts|^Journal"""
filter_re = re.compile( filter_s )

def filterfolders(foldername):
    """test for, and filter out some IMAP folders"""
    res = filter_re.match(foldername)

    if res:
        return None
    else:
        return foldername


def test_ff():
    """test: test for, and filter out some IMAP folders"""
    from namet2 import some_bad

    for f_name in some_bad:
        #print f_name, '\t\t', getfoldername(f_name)
        print filterfolders(f_name)

#test_gfn()
#
#test_ff()

# Then in .offlineimaprc:
# 
#[general]
# pythonfile = ~/.offlineimap.py
#
#[Repository Remote]
# nametrans = getfoldername
#
# folderfilter = filterfolders
