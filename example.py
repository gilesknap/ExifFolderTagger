#! /usr/bin/python3.4

import sys, traceback
from ExifFolderTagger import ExifFolderTagger
from FolderCompare import FolderCompare

__author__ = 'hgv27681'

def doTagScan():
    # use a try catch block so I can eat stderr and still see exceptions to stdout
    # this is because we get lots of warnings about unknown exif folders from proprietary extensions
    try:
        tagger = ExifFolderTagger()

        tagger.root_folder = '/mnt/E_DRIVE/PhotosWithTags/Pictures'

        tagger.extensions_to_remove = [
                    '.db', '.ini', '.info', '.exe', '.url', '.tmp',  '.thm',
                    '.rss', '.eml', '.rtf', '.dat',  '.ivr', '.psd', '.jbf', '.mix', '.scn',
                ]
        # also had these but they are part of record '.pdf', '.doc', '.wav', '.txt',

        tagger.descriptions_to_ignore = [
                    'DCP', 'DIGITAL CAMERA', 'Camera',
                ]

        tagger.folders_to_exclude = [
            '2002/0101-bits and peices',
            '2002/0405-Office not dated',
            '2009/1106 Hair',
            '2014/0106 Boyz',
            '2014/1010 Hemdean Extension',
        ]

        # the following 2 settings would switch to doing file renames only, and not use exif tags
        #tagger.extensions_to_exif_tag = []
        #tagger.extensions_to_rename.append('.jpg')

        tagger.day_count_tolerance = 60
        tagger.do_exif = True
        tagger.do_write = True
        tagger.set_dates_to_match_folder = True

    #    tagger.check_dates()
    #    tagger.report_dates()

        tagger.tag_files()
        tagger.report_tag()

    except Exception as e:
        print("Exception =", e)
        traceback.print_exc(file=sys.stdout)

def doFolderScan():
    try:
        c = FolderCompare()
        c.compare('/media/500GB\ Freecom/BigData/Pictures', '/media/500GB\ Freecom/BigData/Pictures')

    except Exception as e:
        print("Exception =", e)
        traceback.print_exc(file=sys.stdout)

doFolderScan()
