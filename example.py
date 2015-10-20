from ExifFolderTagger import ExifFolderTagger

__author__ = 'hgv27681'


tagger = ExifFolderTagger(False, False)

tagger.root_folder = '/media/500GB Freecom/BigData/Pictures'
#tagger.root_folder = '/media/500GB Freecom/BigData/Pictures/2012/0811 More Noah/2012-08-11 Noah'

tagger.extensions_to_remove = [
            '.db', '.ini', '.info', '.exe', '.url', '.jpg2768', '.jpg4332', '.tmp', '.wav', '.txt', '.thm',
            '.rss', '.eml', '.rtf', '.dat', '.pdf', '.doc', '.ivr', '.psd', '.jbf', '.mix', '.scn',
        ]
tagger.descriptions_to_ignore = [
            'DCP', 'DIGITAL CAMERA', 'Camera',
        ]

# the following 2 settings would switch to doing file renames only, and not use exif tags
#tagger.extensions_to_exif_tag = []
#tagger.extensions_to_rename.append('.jpg')

tagger.check_dates(day_count_tolerance=60, use_file_names=True, seconds_tolerance=20)

#tagger.go()
#tagger.report()
