import os
from TermColors import TermColors
import re
import time
from datetime import date, datetime


def normalize_path(path):
    return path.replace('\\', '/')


def date_format(date):
        return datetime.strftime(date, '%Y:%m:%d %H:%M:%S')


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
        # 'Exif.Photo.CreateDate',
            'Exif.Photo.DateTimeOriginal',
            'Exif.Photo.DateTimeDigitized',
        ]

        # expressions to apply to the full path in a tuple with the folder description formatter to apply if this
        # expression matches
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

        # default values for controls parameters specific to date verification
        self.day_count_tolerance=30
        self.seconds_tolerance=10
        self.use_file_names=True

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

        if self.do_exif:
            from gi.repository import GExiv2

    def go(self):
        for dirName, subdirList, fileList in os.walk(self.root_folder):
            folder_name = os.path.relpath(dirName, self.root_folder)
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
                        if self.tag_names[0] in metadata.get_tags():
                            tag = metadata[self.tag_names[0]]
                        else:
                            tag = ''
                        if len(tag) > 0:
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
                            os.utime(fullname, (file_time,file_time))
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

    def report(self):
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
        # todo move these expressions to class level?
        folder_expressions = [
            (re.compile('(\d\d\d\d)/\d\d\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]).*'), 'Y%s M%s D%s'),
            (re.compile('(\d\d\d\d)/(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]).*'), 'Y%s M%s D%s'),
        ]
        file_expressions = [
            (re.compile('(\d\d\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) (\d\d).(\d\d).(\d\d).*'),
             '%s %s %s %s %s %s'),
        ]

        if self.do_exif:
            from gi.repository import GExiv2

        for dirName, subdirList, fileList in os.walk(self.root_folder):
            folder_name = os.path.relpath(dirName, self.root_folder)
            # get the date as expressed in the folder hierarchy
            matched = False
            for reg, pat in folder_expressions:
                m = reg.match(normalize_path(folder_name))
                if m:
                    time_string = pat % m.groups()
                    folder_date = datetime.strptime(time_string, "Y%Y M%m D%d")
                    print('{2}FOLDER tag = {0}, date = {1}{3}'.format(time_string, date_format(folder_date),
                          TermColors.OK_BLUE, TermColors.END_C))
                    matched = True
                    break
            if not matched:
                print("{1}FOLDER with NO DATE parsed: {0}{2}".format(
                    folder_name, TermColors.WARNING, TermColors.END_C))

            for filename in fileList:
                fullname = os.path.join(dirName, filename)
                file_date = datetime.fromtimestamp(os.path.getmtime(fullname))

                if self.do_exif:
                    root, ext = os.path.splitext(filename)
                    if ext.lower() in self.extensions_to_exif_tag:
                        metadata = GExiv2.Metadata(fullname)
                        for date_tag in self.tag_dates:
                            if date_tag in metadata.get_tags():
                                tag = metadata[date_tag]
                                if tag and len(tag) > 0:
                                    # exif dates are considered to override file modification date
                                    try:
                                        file_date = datetime.strptime(tag, "%Y:%m:%d %H:%M:%S")
                                        break
                                    except:
                                        print ("ERROR:- bad date in", tag, fullname)

                if matched:
                    if file_date > folder_date:
                        error = (file_date - folder_date).days
                    else:
                        error = (folder_date - file_date).days
                    if error > self.day_count_tolerance:
                        print('Folder Mismatch by {0} days. Modify Date = {1} , filename = {2}'.format(
                            error, date_format(file_date), filename))
                        self.out_bad_dates += 1
                    else:
                        self.out_ok_dates += 1

                if self.use_file_names:
                    for reg, pat in file_expressions:
                        m = reg.match(filename)
                        if m:
                            time_string = pat % m.groups()
                            file_name_date = datetime.strptime(time_string, "%Y %m %d %H %M %S")
                            if file_name_date > file_date:
                                error = (file_name_date - file_date).seconds
                            else:
                                error = (file_date - file_name_date).seconds
                            if error > self.seconds_tolerance:
                                print ('Filename Mismatch by {0} seconds. Modify,Name Date = {1}, {2}, filename = {3}'.format(
                                    error, date_format(file_date), date_format(file_name_date), filename))
                                self.out_bad_times +=1
                            else:
                                self.out_ok_times += 1

        print('bad dates =',  self.out_bad_dates)
        print('OK dates  =',  self.out_ok_dates)
        print('bad filename times =',  self.out_bad_times)
        print('OK filename times  =',  self.out_ok_times)
