import os
from TermColors import TermColors
import re


class ExifFolderTagger:
    def __init__(self, do_write=False, do_exif=True):
        self.do_exif = do_exif
        self.do_write = do_write
        # Default Values for control parameters
        # User should set these as necessary
        self.root_folder = os.path.abspath("/mnt/E_DRIVE/PhotosWithTagsTmp")
        self.tag_names = [
            "Exif.Image.ImageDescription",
            "Xmp.dc.Description",
            "Xmp.dc.Title",
        ]
        self.expressions = [
            (re.compile('(\d\d\d\d)/\d\d\d\d-(\d\d)-(\d\d).(.*)'), 'Y%s M%s D%s %s'),
            (re.compile('(\d\d\d\d)/(\d\d)(\d\d).(.*)'), 'Y%s M%s D%s %s'),
            (re.compile('(\d\d\d\d)[/ -](.*)'), 'Y%s %s'),
            (re.compile('(\d\d\d\d)'), 'Y%s'),
        ]
        self.already_renamed_exp = re.compile('Y\d\d\d\d.*')
        self.extensions_to_rename = [
            '.tif', '.gif', '.mpg', '.mp4', '.avi', '.bmp', '.mov', '.png', '.wmv', '.3gp', '.ico'
        ]
        self.descriptions_to_ignore = [
            'DCP', 'DIGITAL CAMERA', 'Camera',
        ]
        self.extensions_to_remove = [
            '.db', '.ini', '.info', '.exe', '.url', '.jpg2768', '.jpg4332', '.tmp', '.wav', '.txt', '.thm',
            '.rss', '.eml', '.rtf', '.dat', '.pdf', '.doc', '.ivr', '.psd', '.jbf', '.mix', '.scn',
        ]

        # Initialize members for gathering results
        self.out_extensions_found = set([])
        self.out_bad_folders = ""
        self.out_count_jpg = 0
        self.out_count_non_jpg = 0
        self.out_renamed = 0

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
                if ext.lower() == '.jpg':
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
                        else:
                            self.out_extensions_found.add(ext.lower())
                            print(TermColors.OK_BLUE + "IGNORED: %s" % fullname + TermColors.END_C)
                    self.out_count_non_jpg += 1


    def report(self):
        print(TermColors.OK_BLUE)
        print("non matching folders = \n" + str(self.out_bad_folders))
        print(TermColors.END_C)
        print("\n\nTOTAL JPG=%d NON-JPG=%d, SUM=%d" % (self.out_count_jpg, self.out_count_non_jpg,
                                                       self.out_count_jpg + self.out_count_non_jpg))
        print("TOTAL renamed=%d" % self.out_renamed)
        print("\nunknown extensions = " + str(self.out_extensions_found))
