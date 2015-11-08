import os
from TermColors import TermColors
import re
from datetime import date, datetime, timedelta
from gi.repository import GExiv2

# this class is used to compare two sets of photo collections
# one of which has come down from google drive via google photo uploads
# the other of which is local files or files that have been uploaded to
# Dropbox and synced down to the file system
# Google will completely rearrange the folder hierarchy so we look for
# individual file name/date matches
# also google photo upload renames files so we need to match on date only
# for such files
# (More explanation required)

class FolderCompare:
    def __init__(self):
        # expressions for extracting date from file names - for date checking
        self.google_duplicates_expr = re.compile(r'(.*) \(\d*\)(\..*)')
        self.date_filename_pattern = '%s-%s-%s %s:%s:%s.%s'
        self.date_filename_pattern_noext = '%s-%s-%s %s:%s:%s'
        self.tag_dates = [
            'Exif.Photo.DateTimeOriginal',
            'Exif.Photo.DateTimeDigitized',
            'Xmp.xmp.CreateDate'
        ]
        self.file_expressions = [
            (re.compile('(19|20\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) (\d\d).(\d\d).(\d\d).*\.(...)'), False),
            (re.compile('.*_(19|20\d\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_(\d\d)(\d\d)(\d\d).*\.(...)'), True),
        ]
        self.list_names = ['left', 'right']
        self.file_lists = {}
        self.file_duplicates = {}
        self.mismatch_count = 0
        for name in self.list_names:
            self.file_lists[name] = {}
            self.file_duplicates[name] = 0

    def dictionary_compare(self, first_name, compare_name):
        print("comparing {0} with {1}".format(first_name, compare_name))

        for file_name,folder_dates in self.file_lists[first_name].iteritems():
            next_list = self.file_lists[compare_name]
            first_count = len(folder_dates)
            if file_name in next_list:
                this_folder_dates = next_list[file_name]
                this_count = len(this_folder_dates)
            else:
                this_count = 0
            if first_count > this_count:   # use > so that mismatches are counted only once since we compare both ways
                self.mismatch_count += 1
                for this_full_name,this_date in folder_dates:
                    print('mismatch on file "{0}". {1} count={2}, {3} count={4}'.format(
                        this_full_name, first_name, first_count, compare_name, this_count)
                    )

    def compare(self, left, right):
        roots = locals()
        for list_name in self.list_names:
            root_folder = os.path.abspath(roots[list_name])
            print("reading files from directory {0}".format(root_folder))
            for dirName, subdirList, fileList in os.walk(root_folder):
                folder_name = os.path.relpath(dirName, root_folder)
                for file_name in fileList:
                    full_name = os.path.join(dirName, file_name)
                    file_date = datetime.fromtimestamp(os.path.getmtime(full_name))
                    # if google uploader gets duplicate names in a month it adds (1) (2) ... so treat these as the same
                    m = self.google_duplicates_expr.match(file_name)
                    if m:
                        file_name = m.group(1) + m.group(2)
                    # normalize file names for those named by google or dropbox autoupload
                    for reg, google in self.file_expressions:
                        m = reg.match(file_name)
                        if m:
                            file_name = self.date_filename_pattern % m.groups()
                            if google:
                                # google file name dates are wrong by a few seconds, read the metadata instead for these
                                metadata = GExiv2.Metadata(full_name)
                                if metadata:
                                    for date_tag in self.tag_dates:
                                        tag = metadata.get(date_tag, None)
                                        if tag is not None:
                                            file_date = datetime.strptime(tag, "%Y:%m:%d %H:%M:%S")
                                            file_name = file_date.strftime(self.date_filename_pattern_noext) \
                                                + '.' + m.group(6)
                                            print ('google file {0} converted to {1}'.format(full_name,file_name))
                                            break

                    if file_name in self.file_lists[list_name].keys():
                        self.file_duplicates[list_name] += 1
                        self.file_lists[list_name][file_name].append((full_name,file_date))
                    else:
                        self.file_lists[list_name][file_name] = [(full_name,file_date)]

        # check for matches
        first_name = self.list_names[0]
        for compare_name in self.list_names[1:]:
            self.dictionary_compare(first_name, compare_name)
            self.dictionary_compare(compare_name, first_name)

        for list_name in self.list_names:
            print('unique files read for {0} = {1}, duplicates = {2}'.format(
                list_name, len(self.file_lists[list_name]),self.file_duplicates[list_name]))
        print("mismatches = {0}".format(self.mismatch_count))


