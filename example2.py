#! /usr/bin/python3.4

import sys, traceback
from FolderCompare import FolderCompare

__author__ = 'hgv27681'


def doFolderScan():
    try:
        c = FolderCompare()
        c.compare('/media/500GB Freecom/BigData/Pictures', '/media/500GB Freecom/torrent')

    except Exception as e:
        print("Exception =", e)
        traceback.print_exc(file=sys.stdout)

doFolderScan()

