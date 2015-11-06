import os
from TermColors import TermColors
import re
from datetime import date, datetime, timedelta

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
        self.file_expressions = [
            (re.compile('(\d\d\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) (\d\d).(\d\d).(\d\d).*'),
             '%s %s %s %s %s %s'),
            (re.compile('.*(19|20\d\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_(\d\d)(\d\d)(\d\d).*'),
             '%s %s %s %s %s %s'),
        ]
        self.list_names = ['left', 'right']
        self.file_lists = {}
        self.file_duplicates = {}
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
            if first_count <> this_count:
                print('mismatch on file "{0}". {1} count={2}, {3} count={4}'.format(
                    file_name,first_name, first_count, compare_name, this_count)
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
                    if file_name in self.file_lists[list_name].keys():
                        self.file_duplicates[list_name] += 1
                        self.file_lists[list_name][file_name].append((folder_name,file_date))
                    else:
                        self.file_lists[list_name][file_name] = [(folder_name,file_date)]

        for list_name in self.list_names:
            print('unique files read for {0} = {1}, duplicates = {2}'.format(
                list_name, len(self.file_lists[list_name]),self.file_duplicates[list_name]))

        # check for matches
        first_name = self.list_names[0]
        for compare_name in self.list_names[1:]:
            self.dictionary_compare(first_name, compare_name)
            self.dictionary_compare(compare_name, first_name)



