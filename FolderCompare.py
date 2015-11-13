import os
from TermColors import TermColors
import re
from datetime import date, datetime, timedelta
from gi.repository import GExiv2
import shutil
# this class is used to compare two sets of photo collections
# one of which has come down from google drive via google photo uploads
# the other of which is local files or files that have been uploaded to
# Dropbox and synced down to the file system
# Google will completely rearrange the folder hierarchy so we look for
# individual file name/date matches
# also google photo upload renames files so we need to match on date only
# for such files
# (More explanation required)

# exif date string format
DATE_FORMAT = '%Y:%m:%d %H:%M:%S'


class FolderCompare:
    def __init__(self):
        # expressions for extracting date from file names - for date checking
        self.google_duplicates_expr = re.compile(r'(.*) \(\d*\)(\..*)')
        self.date_filename_pattern = '%s:%s:%s %s:%s:%s.%s'
        self.tag_dates = [
            'Exif.Photo.DateTimeOriginal',
            'Exif.Photo.DateTimeDigitized',
            'Xmp.xmp.CreateDate'
        ]
        self.file_expressions = [
            (re.compile('(19|20\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) (\d\d).(\d\d).(\d\d).*\.(...)'), False),
            # TODO TODO - change below to True for google rename handling (required for 2015 photos)
            (re.compile('.*_(19|20\d\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_(\d\d)(\d\d)(\d\d).*\.(...)'), False),
        ]
        self.list_names = ['left', 'right']
        self.file_lists = {}
        self.file_duplicates = {}
        self.mismatch_count = {}
        self.folders_to_exclude = []
        for name in self.list_names:
            self.file_lists[name] = {}
            self.file_duplicates[name] = 0
            self.mismatch_count[name] = 0

        # control parameters
        self.extensions_to_ignore = [
            '.txt', '.pdf',
        ]
        self.useExif = True
        self.folders_to_exclude = []

    def dictionary_compare(self, first_name, compare_name, retry_folder):
        print("comparing {0} with {1}".format(first_name, compare_name))

        for file_name, file_full_names in self.file_lists[first_name].iteritems():
            next_list = self.file_lists[compare_name]
            first_count = len(file_full_names)
            if file_name in next_list:
                this_files = next_list[file_name]
                this_count = len(this_files)
            else:
                this_count = 0
            if first_count > this_count:   # use > so that mismatches are counted only once since we compare both ways
                self.mismatch_count[first_name] += 1
                for file_full_name in file_full_names:
                    print('mismatch on index "{4}", {0} count={1}, {2} count={3}, full={5}'.format(
                        first_name, first_count, compare_name, this_count, file_name, file_full_name)
                    )
                    if retry_folder is not None:
                        shutil.copy(file_full_name, retry_folder)

    def compare(self, left, right, retry_folder=None):
        print("skipping extensions {0}".format(self.extensions_to_ignore))
        print("skipping folders {0}".format(self.folders_to_exclude))
        print('using exif = {0}'.format(self.useExif))
        roots = locals()
        for list_name in self.list_names:
            root_folder = os.path.abspath(roots[list_name])
            print("reading files from directory {0}".format(root_folder))
            for dirName, subdirList, fileList in os.walk(root_folder):
                folder_name = os.path.relpath(dirName, root_folder)
                if any(folder_name.startswith(s) for s in self.folders_to_exclude):
                    print("FOLDER {0} Skipped ...".format(dirName))
                    continue
                for file_name in fileList:
                    root, ext = os.path.splitext(file_name)
                    if ext.lower() in self.extensions_to_ignore:
                        continue
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
                            if google and self.useExif:
                                # google file name dates are wrong by a few seconds, read the metadata instead for these
                                metadata = GExiv2.Metadata(full_name)
                                if metadata:
                                    for date_tag in self.tag_dates:
                                        tag = metadata.get(date_tag, None)
                                        if tag is not None:
                                            file_date = datetime.strptime(tag, DATE_FORMAT)
                                            file_name = file_date.strftime(DATE_FORMAT) \
                                                + '.' + m.group(7)
                                            # print ('google file {0} with exif {1} converted to {2}'
                                            #       .format(full_name, file_date, file_name))
                                            break

                    if file_name in self.file_lists[list_name].keys():
                        self.file_duplicates[list_name] += 1
                        self.file_lists[list_name][file_name].append(full_name)
                    else:
                        self.file_lists[list_name][file_name] = [full_name]

        # check for matches
        first_name = self.list_names[0]
        for compare_name in self.list_names[1:]:
            # self.dictionary_compare(first_name, compare_name)
            print('############################################################################################')
            print('############################################################################################')
            self.dictionary_compare(compare_name, first_name, retry_folder)

        for list_name in self.list_names:
            print('unique files read for {0} = {1}, duplicates = {2}, mismatches = {3}'.format(
                list_name, len(self.file_lists[list_name]), self.file_duplicates[list_name],
                self.mismatch_count[list_name]
            ))
