#! /usr/bin/python2.7

import sys, traceback
from FolderCompare import FolderCompare

__author__ = 'hgv27681'


def doFolderScan():
    try:
        c = FolderCompare()
        # c.compare('/mnt/E_DRIVE/Pictures/2006', '/mnt/E_DRIVE/PhotosWithTags/Pictures/2006')
        #for i in range(1996,2015):
           # c.compare(r'E:\GoogleDrive\Google Photos\{0}'.format(i), r'E:\Ubuntu\Pictures\{0}'.format(i))
        #     c.compare(r'/mnt/E_DRIVE/GoogleDrive/Google Photos/{0}'.format(i), r'/mnt/E_DRIVE/Ubuntu/Pictures/{0}'.format(i))
        #c.compare(r'/mnt/E_DRIVE/GoogleDrive/Google Photos/2015', r'/mnt/E_DRIVE/Ubuntu/Pictures/2015')
        c.folders_to_exclude = ['2015']
        c.useExif = False
        c.extensions_to_ignore.extend(['.gif','.wav', '.png', '.bmp', '.db', '.tmp', '.ini', '.mix', '.mts', 'doc', '.tif'])
        c.compare(r'/mnt/E_DRIVE/GoogleDrive/Google Photos', r'/mnt/E_DRIVE/Ubuntu/Pictures')

    except Exception as e:
        print("Exception =", e)
        traceback.print_exc(file=sys.stdout)

doFolderScan()

