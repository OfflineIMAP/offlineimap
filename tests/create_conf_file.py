#!/bin/env python
# Copyright 2018 Espace LLC/espacenetworks.com.  Written by @chris001.
# This must be run from the main directory of the offlineimap project.
# Typically this script will be run by Travis to create the config files needed for running the automated tests.
# python ./tests/create_conf_file.py
# Input: Seven shell environment variables.
# Output: it writes the config settings to "filename" (./oli-travis.conf) and "additionalfilename" (./test/credentials.conf).
# "filename" is used by normal run of ./offlineimap -c ./oli-travis.conf , "additionalfilename" is used by "pytest".
# They are the same conf file, copie to two different locations for convenience.

import os
import shutil
try:
  import ConfigParser
  Config = ConfigParser.ConfigParser()
except ImportError:
  import configparser
  Config = configparser.ConfigParser()

filename = "./oli-travis.conf"
additionalfilename = "./test/credentials.conf"  # for the 'pytest' which automatically finds and runs the unittests.

#TODO: detect OS we running on now, and set sslcacertfile location accordingly.
sslcacertfile = "/etc/pki/tls/cert.pem" # CentOS 7
sslcacertfile = "" # TODO: https://gist.github.com/1stvamp/2158128  Current Mac OSX now must download the cacertfile.
sslcacertfile = "/etc/ssl/certs/ca-certificates.crt" # Ubuntu Trusty 14.04 (Travis linux test container 2018.)
if os.environ["TRAVIS_OS_NAME"] == "osx":
  sslcacertfile = os.environ["OSX_BREW_SSLCACERTFILE"]

# lets create that config file.
cfgfile = open(filename,'w')

# add the settings to the structure of the file, and lets write it out.
sect = 'general'
Config.add_section(sect)
Config.set(sect,'accounts','Test')
Config.set(sect,'maxsyncaccounts', '1')

sect = 'Account Test'
Config.add_section(sect)
Config.set(sect,'localrepository','IMAP')  # Outlook.
Config.set(sect,'remoterepository', 'Gmail')

###  "Repository IMAP" is hardcoded in test/OLItest/TestRunner.py it should dynamically get the Repository names but it doesn't.
sect = 'Repository IMAP'  # Outlook.
Config.add_section(sect)
Config.set(sect,'type','IMAP')
Config.set(sect,'remotehost', 'imap-mail.outlook.com')
Config.set(sect,'remoteport', '993')
Config.set(sect,'auth_mechanisms', os.environ["OUTLOOK_AUTH"])
Config.set(sect,'ssl', 'True')
#Config.set(sect,'tls_level', 'tls_compat')  #Default is 'tls_compat'.
#Config.set(sect,'ssl_version', 'tls1_2') # Leave this unset. Will auto select between tls1_1 and tls1_2 for tls_secure.
Config.set(sect,'sslcacertfile', sslcacertfile)
Config.set(sect,'remoteuser', os.environ["secure_outlook_email_address"])
Config.set(sect,'remotepass', os.environ["secure_outlook_email_pw"])
Config.set(sect,'createfolders', 'True')
Config.set(sect,'folderfilter', 'lambda f: f not in ["Inbox", "[Gmail]/All Mail"]') #Capitalization of Inbox INBOX was causing runtime failure.
#Config.set(sect,'folderfilter', 'lambda f: f not in ["[Gmail]/All Mail"]')


### "Repository Gmail" is also hardcoded into test/OLItest/TestRunner.py
sect = 'Repository Gmail'
Config.add_section(sect)
Config.set(sect,'type', 'Gmail')
Config.set(sect,'remoteport', '993')
Config.set(sect,'auth_mechanisms', os.environ["GMAIL_AUTH"])
Config.set(sect,'oauth2_client_id',     os.environ["secure_gmail_oauth2_client_id"])
Config.set(sect,'oauth2_client_secret', os.environ["secure_gmail_oauth2_client_secret"])
Config.set(sect,'oauth2_refresh_token', os.environ["secure_gmail_oauth2_refresh_token"])
Config.set(sect,'remoteuser', os.environ["secure_gmail_email_address"])
Config.set(sect,'ssl', 'True')
#Config.set(sect,'tls_level', 'tls_compat')
#Config.set(sect,'ssl_version', 'tls1_2')
Config.set(sect,'sslcacertfile', sslcacertfile)
Config.set(sect,'createfolders', 'True')
Config.set(sect,'folderfilter', 'lambda f: f not in ["INBOX", "[Gmail]/All Mail"]')

Config.write(cfgfile)
cfgfile.close()

shutil.copy(filename, additionalfilename)
