import os
from TermColors import TermColors
import re

#root_folder = os.path.abspath("/scratch/Pictures")
#root_folder = os.path.abspath("E:/PhotosWithTags/Pictures")
root_folder = os.path.abspath("/mnt/E_DRIVE/PhotosWithTagsTmp")
do_write = True
do_exif = True
tag_name = "Exif.Image.ImageDescription"
tag_name2 = "Xmp.dc.Description"
tag_name3 = "Xmp.dc.Title"
# tag_name = "Exif.Photo.UserComment"

expressions = [
    (re.compile('(\d\d\d\d)/\d\d\d\d-(\d\d)-(\d\d).(.*)'), 'Y%s M%s D%s %s'),
    (re.compile('(\d\d\d\d)/(\d\d)(\d\d).(.*)'), 'Y%s M%s D%s %s'),
    (re.compile('(\d\d\d\d)[/ -](.*)'), 'Y%s %s'),
    (re.compile('(\d\d\d\d)'), 'Y%s'),
]
renamed_exp = re.compile('Y\d\d\d\d.*')

rename_extensions = [
    '.tif', '.gif', '.mpg', '.mp4', '.avi', '.bmp', '.mov', '.png', '.wmv', '.3gp', '.ico'
]

descriptions_to_ignore = [
    'DCP','DIGITAL CAMERA', 'Camera',
]

remove_extensions = [
    '.db', '.ini', '.info', '.exe', '.url', '.jpg2768', '.jpg4332', '.tmp', '.wav', '.txt', '.thm',
    '.rss', '.eml', '.rtf', '.dat', '.pdf', '.doc', '.ivr', '.psd', '.jbf', '.mix', '.scn',
]

if do_exif:
    import gi.repository
    from gi.repository import GExiv2


def norm_path(path):
    return path.replace('\\','/')


def scan_folder_for_photos(folder):
    out_extensions = set([])
    out_bad_folders = ""
    out_count_jpg = 0
    out_count_non_jpg = 0
    out_renamed = 0
    for dirName, subdirList, fileList in os.walk(folder):
        folder_name = os.path.relpath(dirName, folder)
        description = ""
        for reg, pat in expressions:
            m = reg.match(norm_path(folder_name))
            if m:
                description = pat % m.groups()
                description = description.replace('/', ' - ')
                print description
                break
        if description == "":
            out_bad_folders += folder_name + "\n"
        for filename in fileList:
            fullname = os.path.join(dirName, filename)
            root, ext = os.path.splitext(filename)
            if ext.lower() == '.jpg':
                out_count_jpg += 1
                if do_exif:
                    metadata = GExiv2.Metadata(fullname)
                    new_meta_desc = description
                    if tag_name in metadata.get_tags():
                        tag = metadata[tag_name]
                    else:
                        tag = ''
                    if tag_name:
                        meta_desc = str(tag).strip()
                        # only add to meta data if not already added done in a previous run
                        if renamed_exp.match(meta_desc):
                            continue  # we updated this in a previous run
                        else:
                            if not (len(m ,eta_desc) == 0 or any(s in meta_desc for s in descriptions_to_ignore)):
                                new_meta_desc = description + '\n' + meta_desc
                                print TermColors.FAIL + "%s : >%s< --> >%s<" % \
                                                            (fullname, meta_desc, new_meta_desc) + TermColors.END_C
                    if do_write:
                        metadata[tag_name] = new_meta_desc
                        metadata[tag_name2] = new_meta_desc
                        metadata[tag_name3] = new_meta_desc
                        metadata.save_file()
            else:
                if ext.lower() in rename_extensions:
                    base = os.path.basename(fullname)
                    # only rename on the first pass - if already done then leave it
                    if not renamed_exp.match(base):
                        new_name = os.path.join(os.path.dirname(fullname), description + ' - ' + base)
                        out_renamed += 1
                        print 'mv %s %s' % (fullname, new_name)
                        if do_write:
                            os.rename(fullname, new_name)
                else:
                    out_extensions.add(ext.lower())
                    if ext.lower() in remove_extensions:
                        print 'rm %s' % fullname
                        if do_write:
                            os.remove(fullname)
                    else:
                        print TermColors.OK_BLUE +  "IGNORED: %s" % fullname + TermColors.END_C
                out_count_non_jpg += 1


    return out_count_jpg, out_count_non_jpg, out_extensions, out_bad_folders, out_renamed

jpg_count, non_jpg_count, extension_list, folders, renamed = scan_folder_for_photos(root_folder)

print TermColors.OK_BLUE
print "non matching folders = \n" + str(folders)
print TermColors.END_C
print "\n\nTOTAL JPG=%d NON-JPG=%d, SUM=%d" % (jpg_count, non_jpg_count, jpg_count+non_jpg_count)
print "TOTAL renamed=%d" % renamed
print "\nunknown extensions = " + str(extension_list)
