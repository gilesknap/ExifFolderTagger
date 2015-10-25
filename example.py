#! /usr/bin/python3.4

from ExifFolderTagger import ExifFolderTagger

__author__ = 'hgv27681'


tagger = ExifFolderTagger()

#tagger.root_folder = '/media/500GB Freecom/BigData/Pictures'
#tagger.root_folder = '/media/500GB Freecom/BigData/Pictures/2012/0811 More Noah/2012-08-11 Noah'
tagger.root_folder = '/mnt/E_DRIVE/PhotosWithTags/Pictures'
tagger.root_folder = '/mnt/E_DRIVE/PhotosWithTags/Pictures/2015/0801- Aug  Sep TBS'
#tagger.root_folder = '/mnt/E_DRIVE/PhotosWithTags/Pictures/2015'

tagger.extensions_to_remove = [
            '.db', '.ini', '.info', '.exe', '.url', '.tmp', '.wav', '.txt', '.thm',
            '.rss', '.eml', '.rtf', '.dat', '.pdf', '.doc', '.ivr', '.psd', '.jbf', '.mix', '.scn',
        ]
tagger.descriptions_to_ignore = [
            'DCP', 'DIGITAL CAMERA', 'Camera',
        ]

# the following 2 settings would switch to doing file renames only, and not use exif tags
#tagger.extensions_to_exif_tag = []
#tagger.extensions_to_rename.append('.jpg')

tagger.day_count_tolerance = 60
tagger.do_exif = True
tagger.do_write = True
tagger.check_dates()

#tagger.go()
#tagger.report()
