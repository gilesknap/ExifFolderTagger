import os
from TermColors import TermColors
import re
from datetime import date, datetime, timedelta


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

    def compare(self, left, right):
        roots = locals()
        for list_name in self.list_names:
            root_folder = os.path.abspath(roots[list_name])
            print("reading files from directory {0}".format(root_folder))
            for dirName, subdirList, fileList in os.walk(root_folder):
                folder_name = os.path.relpath(dirName, root_folder)
                for file_name in fileList:
                    if file_name in self.file_lists[list_name].keys():
                        self.file_duplicates[list_name] += 1
                        print("duplicate name {0}, folder {1}".format(file_name, folder_name))
                        self.file_lists[list_name][file_name].append(folder_name)
                    else:
                        self.file_lists[list_name][file_name] = [folder_name]

        for list_name in self.list_names:
            print("unique files read for {0} = {1}, duplicates = {2}".format(
                list_name, len(self.file_lists[list_name]),self.file_duplicates[list_name]))
