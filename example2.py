#! /usr/bin/python3.4

import sys, traceback
from FolderCompare import FolderCompare

__author__ = 'hgv27681'


def doFolderScan():
    try:
        c = FolderCompare()
        c.compare('/mnt/E_DRIVE/Pictures/2006', '/mnt/E_DRIVE/PhotosWithTags/Pictures/2006')

    except Exception as e:
        print("Exception =", e)
        traceback.print_exc(file=sys.stdout)

doFolderScan()

