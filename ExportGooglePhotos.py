#! /usr/bin/python
__author__ = 'giles'

class ExportGooglePhotos:
    pass

from gdata import gd
import getpass

user = 'gilesknap@gmail.com'
pwd = getpass.getpass('password for {0} : '.format(user))

gd_client = gdata.photos.service.PhotosService()
gd_client.email = user
gd_client.password = pwd
gd_client.source = 'destipak' #Not sure about that
feed_url = "/data/feed/api/user/"
entry_url = "/data/entry/api/user/"
gd_client.ProgrammaticLogin()