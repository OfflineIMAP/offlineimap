
import requests

def internetConnected(httpshost="www.google.com"):
   try:
    r = requests.get("https://" + httpshost)
  except Exception as ex:
    return False
  return True

