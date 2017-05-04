#!/usr/bin/env python

import urllib3
import certifi

def isInternetConnected(url="www.ietf.org"):
  result = False
  http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED', # Force certificate check.
    ca_certs=certifi.where(),  # Path to the Certifi bundle.
  )
  try:
    r = http.request('HEAD', 'https://' + url)
    result = True
  except Exception as e:  # urllib3.exceptions.SSLError
    result = False
  return result

print isInternetConnected()
