from ExifFolderTagger import ExifFolderTagger

__author__ = 'hgv27681'


tagger = ExifFolderTagger(False, False)

tagger.root_folder = '/media/500GB Freecom/BigData/Pictures'

tagger.extensions_to_remove = [
            '.db', '.ini', '.info', '.exe', '.url', '.jpg2768', '.jpg4332', '.tmp', '.wav', '.txt', '.thm',
            '.rss', '.eml', '.rtf', '.dat', '.pdf', '.doc', '.ivr', '.psd', '.jbf', '.mix', '.scn',
        ]
tagger.descriptions_to_ignore = [
            'DCP', 'DIGITAL CAMERA', 'Camera',
        ]

#tagger.extensions_to_exif_tag = []
#tagger.extensions_to_rename.append('.jpg')

tagger.go()
tagger.report()
