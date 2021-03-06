import os
from TermColors import TermColors
import re
# import time
from datetime import date, datetime, timedelta
from gi.repository import GExiv2

def normalize_path(path):
    return path.replace('\\', '/')

# exif date string format
DATE_FORMAT = '%Y:%m:%d %H:%M:%S'

def date_format(date):
    return datetime.strftime(date, DATE_FORMAT)


class ExifFolderTagger:
    def __init__(self, do_exif=True, do_write=False):
        # Default Values for control parameters
        # User should set these as necessary after instantiating a ExifFolderTagger object

        # control whether the code makes file changes and whether it looks at exif tags
        self.do_exif = do_exif
        self.do_write = do_write

        # root folder to start scan from
        # windows file names also supported
        self.root_folder = os.path.abspath("/mnt/E_DRIVE/PhotosWithTagsTmp")

        # exif tags to look at - the first is checked for existing text which is appended to the folder description
        self.tag_names = [
            "Exif.Image.ImageDescription",
            "Xmp.dc.Description",
            "Xmp.dc.Title",
        ]
        self.tag_dates = [
            'Exif.Photo.DateTimeOriginal',
            'Exif.Photo.DateTimeDigitized',
            'Xmp.xmp.CreateDate'
        ]

        # expressions to apply to the full path in a tuple with the folder description formatter to apply if this
        # expression matchesExportGooglePhotos.py
        # These default expressions match files from the following examples
        #       "root/2015/2015-12-25 Christmas Family Visit/photo1.jpg"
        #       "root/2015/1225 Christmas Family Visit/photo1.jpg"
        #       "root/2015/Work Stuff/photo1.jpg"
        #       "root/2015/photo1.jpg"
        # and builds folder descriptions of the form:-
        #       Y2015 M12 D25 Christmas Family Visit
        # (where Mxx and Dxx will not be provided fot the last two)
        # Sub-folders further down are also supported but we replace "/" with " - "
        # This scheme has been shown to make the files usefully searchable in Google photos
        self.expressions = [
            (re.compile('(\d\d\d\d)/\d\d\d\d-(\d\d)-(\d\d).(.*)'), 'Y%s M%s D%s %s'),
            (re.compile('(\d\d\d\d)/(\d\d)(\d\d).(.*)'), 'Y%s M%s D%s %s'),
            (re.compile('(\d\d\d\d)[/ -](.*)'), 'Y%s %s'),
            (re.compile('(\d\d\d\d)'), 'Y%s'),
        ]

        # an expression that matches all folder description formatters above - used to detect an already processed tag
        self.already_renamed_exp = re.compile('Y\d\d\d\d.*')

        # expressions for extracting date from folder names - for date checking
        self.folder_expressions = [
            (re.compile('(\d\d\d\d)/\d\d\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]).*'), 'Y%s M%s D%s'),
            (re.compile('(\d\d\d\d)/(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]).*'), 'Y%s M%s D%s'),
        ]

        # expressions for extracting date from file names - for date checking
        self.file_expressions = [
            (re.compile('(\d\d\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) (\d\d).(\d\d).(\d\d).*'),
             '%s %s %s %s %s %s'),
            (re.compile('.*(19|20\d\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_(\d\d)(\d\d)(\d\d).*'),
             '%s %s %s %s %s %s'),
        ]

        # list of file extension to which we apply exif tags (use lower case only)
        self.extensions_to_exif_tag = [
            '.jpg'
        ]

        # list of file extensions to rename - these file-types are uploaded to google photos but have no exif -
        # google photos does search on filename so these will still be searchable (use lower case only)
        self.extensions_to_rename = [
            '.tif', '.gif', '.mpg', '.mp4', '.avi', '.bmp', '.mov', '.png', '.wmv', '.3gp', '.ico'
        ]

        # if the first exif tag contains one of these strings then do not preserve - just overwrite
        # (e.g. descriptions that were auto added by some cameras and do not add any info)
        self.descriptions_to_ignore = [
        ]

        # clean these files out of the photo folders (use lower case only)
        self.extensions_to_remove = [
        ]

        # ignore these folders
        self.folders_to_exclude = [
            'Downloaded Albums', '9999'
        ]

        # default values for controls parameters specific to date verification
        self.day_count_tolerance = 30
        self.seconds_tolerance = 10
        self.use_file_names = True
        self.set_dates_to_match_folder = False

        # Initialize members for gathering results
        self.out_extensions_found = set([])
        self.out_bad_folders = ""
        self.out_count_jpg = 0
        self.out_count_non_jpg = 0
        self.out_renamed = 0
        self.out_ignored = 0
        self.out_skipped = 0
        self.out_exif_changed = 0
        self.out_removed = 0

        self.out_bad_dates = 0
        self.out_ok_dates = 0
        self.out_bad_times = 0
        self.out_ok_times = 0

    def tag_files(self):
        for dirName, subdirList, fileList in os.walk(self.root_folder):
            folder_name = os.path.relpath(dirName, self.root_folder)
            if any(folder_name.startswith(s) for s in self.folders_to_exclude):
                print("FOLDER {0} Skipped ...".format(dirName))
                continue
            description = ""
            for reg, pat in self.expressions:
                m = reg.match(normalize_path(folder_name))
                if m:
                    description = pat % m.groups()
                    description = description.replace('/', ' - ')
                    print(description)
                    break
            if description == "":
                self.out_bad_folders += folder_name + "\n"
            for filename in fileList:
                fullname = os.path.join(dirName, filename)
                root, ext = os.path.splitext(filename)
                if ext.lower() in self.extensions_to_exif_tag:
                    self.out_count_jpg += 1
                    if self.do_exif:
                        metadata = GExiv2.Metadata(fullname)
                        new_meta_desc = description
                        tag = metadata.get(self.tag_names[0], None)
                        if tag and len(tag) > 0:
                            # if the first tag_name already exists then we check to see if it was previously processed
                            # (i.e. matches already_renamed_exp) if not we add the folder description to the
                            # existing tag name and write it to all tag_names. We also check against the list
                            # descriptions_to_ignore which we overwrite with description only
                            meta_desc = str(tag).strip()
                            # only add to meta data if not already added done in a previous run
                            if self.already_renamed_exp.match(meta_desc):
                                self.out_skipped += 1
                                continue  # we updated this in a previous run
                            else:
                                if not (len(meta_desc) == 0 or
                                            any(s in meta_desc for s in self.descriptions_to_ignore)):
                                    new_meta_desc = description + '\n' + meta_desc
                                    print(TermColors.FAIL + "%s : >%s< --> >%s<" %
                                          (fullname, meta_desc, new_meta_desc) + TermColors.END_C)
                        if self.do_write:
                            file_time = os.path.getmtime(fullname)
                            for tag_name in self.tag_names:
                                metadata[tag_name] = new_meta_desc
                            metadata.save_file()
                            # restore original modified date
                            os.utime(fullname, (file_time, file_time))
                        self.out_exif_changed += 1
                else:
                    if ext.lower() in self.extensions_to_rename:
                        base = os.path.basename(fullname)
                        # only rename on the first pass - if already done then leave it
                        if not self.already_renamed_exp.match(base):
                            new_name = description + ' - ' + base
                            new_fullname = os.path.join(os.path.dirname(fullname), new_name)
                            self.out_renamed += 1
                            print('mv "%s" "%s"' % (base, new_name))
                            if self.do_write:
                                os.rename(fullname, new_fullname)
                    else:
                        if ext.lower() in self.extensions_to_remove:
                            print('rm %s' % fullname)
                            if self.do_write:
                                os.remove(fullname)
                            self.out_removed += 1
                        else:
                            self.out_extensions_found.add(ext.lower())
                            self.out_ignored += 1
                            print(TermColors.OK_BLUE + "IGNORED: %s" % fullname + TermColors.END_C)
                    self.out_count_non_jpg += 1

    def report_tag(self):
        print(TermColors.OK_BLUE)
        print("non matching folders = \n" + str(self.out_bad_folders))
        print(TermColors.END_C)
        print("\n\nTOTAL Exif=%d NON-Exif=%d, SUM=%d" % (self.out_count_jpg, self.out_count_non_jpg,
                                                         self.out_count_jpg + self.out_count_non_jpg))
        print("\nTOTAL ignored=%d" % self.out_ignored)
        print("TOTAL renamed=%d" % self.out_renamed)
        print("TOTAL exif skipped=%d" % self.out_skipped)
        print("TOTAL exif updated=%d" % self.out_exif_changed)
        print("TOTAL deleted=%d" % self.out_removed)
        print("\nunknown extensions = " + str(self.out_extensions_found))

    def check_dates(self):
        for dirName, subdirList, fileList in os.walk(self.root_folder):
            folder_name = os.path.relpath(dirName, self.root_folder)
            if any(folder_name.startswith(s) for s in self.folders_to_exclude):
                print("FOLDER {0} Skipped ...".format(dirName))
                continue

            # get the date as expressed in the folder hierarchy
            matched = False
            for reg, pat in self.folder_expressions:
                m = reg.match(normalize_path(folder_name))
                if m:
                    time_string = pat % m.groups()
                    folder_date = datetime.strptime(time_string, "Y%Y M%m D%d")
                    print('{3}FOLDER name = {0}, tag = {1}, date = {2}{4}'.format(
                        folder_name, time_string, date_format(folder_date), TermColors.OK_BLUE, TermColors.END_C))
                    matched = True
                    break
            if not matched:
                print("{1}FOLDER with NO DATE parsed: {0}{2}".format(
                    folder_name, TermColors.BOLD + TermColors.OK_BLUE + TermColors.UNDERLINE, TermColors.END_C))

            for filename in fileList:
                fullname = os.path.join(dirName, filename)
                file_date = datetime.fromtimestamp(os.path.getmtime(fullname))

                file_is_exif = False
                metadata = None
                exif_date = ''
                if self.do_exif:
                    root, ext = os.path.splitext(filename)
                    if ext.lower() in self.extensions_to_exif_tag:
                        file_is_exif = True
                        metadata = GExiv2.Metadata(fullname)
                        for date_tag in self.tag_dates:
                            tag = metadata.get(date_tag, None)
                            if tag and len(tag) > 0:
                                # exif dates are considered to override file modification date
                                try:
                                    file_date = datetime.strptime(tag, "%Y:%m:%d %H:%M:%S")
                                    exif_date = '(exif)'
                                    break
                                except Exception:
                                    print("{2}ERROR:- bad date in {0}, {1}{3}".format(
                                          fullname, tag, TermColors.FAIL, TermColors.END_C))
                                    self.set_file_date(fullname, file_date, metadata, file_is_exif)

                if matched:
                    error = self.date_difference(file_date, folder_date).days
                    if error > self.day_count_tolerance:
                        print('Folder Mismatch. File{3} = {1} , filename = {2}. Out  by {0} days'.format(
                            error, date_format(file_date), filename, exif_date))
                        if self.set_dates_to_match_folder:
                            # fix mismatched files to be right at the end of the date range allowed
                            fix_date = folder_date + timedelta(days=self.day_count_tolerance, seconds=-10)
                            self.set_file_date(fullname, fix_date, metadata, file_is_exif)
                        self.out_bad_dates += 1
                    else:
                        self.out_ok_dates += 1

                if self.use_file_names:
                    for reg, pat in self.file_expressions:
                        m = reg.match(filename)
                        if m:
                            time_string = pat % m.groups()
                            file_name_date = datetime.strptime(time_string, "%Y %m %d %H %M %S")
                            error = self.date_difference(file_name_date, file_date).seconds
                            if error > self.seconds_tolerance:
                                print(
                                    'Filename Mismatch. Modify{4},Name Date = {1}, {2},filename = {3}. Out by {0} seconds'.
                                        format(error, date_format(file_date), date_format(file_name_date),
                                               filename, exif_date))
                                self.out_bad_times += 1
                                self.set_file_date(fullname, file_name_date, metadata, file_is_exif)
                            else:
                                self.out_ok_times += 1

    def set_file_date(self, fullname, file_date, metadata, file_is_exif=True):
        if self.do_write:
            if file_is_exif:
                for tag_name in self.tag_dates:
                    metadata[tag_name] = file_date.strftime(DATE_FORMAT)
                metadata.save_file()
            os.utime(fullname, (file_date.timestamp(), file_date.timestamp()))

    def date_difference(self, date1, date2):
        if date1 > date2:
            diff = (date1 - date2)
        else:
            diff = (date2 - date1)
        return diff

    def report_dates(self):
        print('bad dates =', self.out_bad_dates)
        print('OK dates  =', self.out_ok_dates)
        print('bad filename times =', self.out_bad_times)
        print('OK filename times  =', self.out_ok_times)