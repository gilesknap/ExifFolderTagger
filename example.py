from ExifFolderTagger import ExifFolderTagger

__author__ = 'hgv27681'


tagger = ExifFolderTagger(False, False)

tagger.root_folder = '/media/500GB Freecom/BigData/Pictures'

tagger.go()
tagger.report()
