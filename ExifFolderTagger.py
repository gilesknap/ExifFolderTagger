import os
from TermColors import TermColors
import re


class ExifFolderTagger:
    def __init__(self, do_write=False, do_exif=True):
        self.do_exif = do_exif
        self.do_write = do_write
        # Default Values for control parameters
        # User should set these as necessary after instantiating a ExifFolderTagger object

        # root folder to start scan from
        # windows file names also supported
        self.root_folder = os.path.abspath("/mnt/E_DRIVE/PhotosWithTagsTmp")

        # exif tags to look at - the first is checked for existing text which is appended to the folder description
        self.tag_names = [
            "Exif.Image.ImageDescription",
            "Xmp.dc.Description",
            "Xmp.dc.Title",
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

        if do_exif:
            from gi.repository import GExiv2

    @staticmethod
    def normalize_path(path):
        return path.replace('\\', '/')

    def go(self):
        for dirName, subdirList, fileList in os.walk(self.root_folder):
            folder_name = os.path.relpath(dirName, self.root_folder)
            description = ""
            for reg, pat in self.expressions:
                m = reg.match(ExifFolderTagger.normalize_path(folder_name))
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
                            for tag_name in self.tag_names:
                                metadata[tag_name] = new_meta_desc
                            metadata.save_file()
                        self.out_exif_changed += 1
                else:
                    if ext.lower() in self.extensions_to_rename:
                        base = os.path.basename(fullname)
                        # only rename on the first pass - if already done then leave it
                        if not self.already_renamed_exp.match(base):
                            new_name = os.path.join(os.path.dirname(fullname), description + ' - ' + base)
                            self.out_renamed += 1
                            print('mv %s %s' % (fullname, new_name))
                            if self.do_write:
                                os.rename(fullname, new_name)
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
        print("TOTAL exif updated=%d" % self.out_removed)
        print("\nunknown extensions = " + str(self.out_extensions_found))
