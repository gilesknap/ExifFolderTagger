#! /usr/bin/python2.7

import sys, traceback
from FolderCompare import FolderCompare

__author__ = 'hgv27681'


def doFolderScan():
    try:
        c = FolderCompare()
        c.folders_to_exclude = ['2015']
        c.useExif = False
        c.extensions_to_ignore.extend(['.gif','.wav', '.png', '.bmp', '.db', '.tmp', '.ini', '.mix', '.mts', 'doc', '.tif', '.ico'])

        #c.compare(r'/mnt/E_DRIVE/GoogleDrive/Google Photos/2004/12', r'/mnt/E_DRIVE/Google Upload/2004/1203 MS Contractors Night')

        # c.compare(r'/mnt/E_DRIVE/GoogleDrive/Google Photos', r'/mnt/E_DRIVE/Google Upload', r'/mnt/E_DRIVE/Retry')
        c.compare(r'/mnt/E_DRIVE/GoogleDrive/Google Photos', r'/mnt/E_DRIVE/Google Upload')

    except Exception as e:
        print("Exception =", e)
        traceback.print_exc(file=sys.stdout)

doFolderScan()

