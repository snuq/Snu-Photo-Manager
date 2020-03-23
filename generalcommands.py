import os
import math
import time
import datetime
from configparser import ConfigParser
from PIL import Image
from shutil import copy2
import filecmp

months_full = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def find_dictionary(list_of_dicts, key_name, key_match):
    for dictionary in list_of_dicts:
        if dictionary[key_name] == key_match:
            return dictionary
    return None


def get_keys_from_list(presets, key='name'):
    names = []
    for preset in presets:
        names.append(preset[key])
    return names


def to_bool(value):
    """Function to convert various Non-Boolean true/false values to Boolean.
    Inputs that return True are:
        'Yes', 'yes', 'True', 'True', 'T', 't', '1', 1, 'Down', 'down'
    Any other value returns a False.
    """

    return str(value).lower() in ('yes', 'true', 't', '1', 'down')


def float_to_hex(value):
    """Converts a 0-1 float into a hex value"""

    value = abs(value)
    if value > 1:
        value = 1
    value = int(round(255 * value))
    value = format(value, 'X').zfill(2)
    return value


def hex_to_float(value):
    """Converts a 2 digit hex value into a 0-1 float"""

    value = int(value, 16)
    value = value / 255
    return value


def naming(naming_method, title='My Photos', year=None, month=None, day=None):
    """Generates a folder name appropriate for a photo directory using various settings.
    Arguments:
        naming_method: Folder formatting options.
        title: Album title.
        year: Year photos were taken.  4 digit format (YYYY).  If not given, current year will be used.
        month: Month photos were taken.  Numerical format (MM or M).  If not given, current month will be used.
        day: Day photos were taken.  Numerical format (DD or D).  If not given, current day will be used.
    Returns: Fully formatted folder name string.
    """

    date = datetime.date.today()
    if not year:
        year = date.year
    if not month:
        month = date.month
    if not day:
        day = date.day

    year_digits = str(year)                      #%Y
    year_digits_short = year_digits[2:]          #%y
    month_name = months_full[month-1]            #%B
    month_name_short = months_short[month-1]     #%b
    month_digits = str(month).zfill(2)           #%M
    month_digits_short = str(month)              #%m
    day_digits = str(day).zfill(2)               #%D
    day_digits_short = str(day)                  #%d
    title_normal = title                         #%T
    title_underscores = title.replace(' ', '_')  #%t

    less_than = naming_method.find('<')
    greater_than = naming_method.find('>')
    if (less_than >= 0) and (greater_than > less_than) and (not title):
        renaming = naming_method[0:less_than]+naming_method[greater_than+1:]
    else:
        renaming = naming_method
    renaming = renaming.replace('<', '')
    renaming = renaming.replace('>', '')
    renaming = renaming.replace('%Y', year_digits)
    renaming = renaming.replace('%y', year_digits_short)
    renaming = renaming.replace('%B', month_name)
    renaming = renaming.replace('%b', month_name_short)
    renaming = renaming.replace('%M', month_digits)
    renaming = renaming.replace('%m', month_digits_short)
    renaming = renaming.replace('%D', day_digits)
    renaming = renaming.replace('%d', day_digits_short)
    renaming = renaming.replace('%T', title_normal)
    renaming = renaming.replace('%t', title_underscores)
    renaming = renaming.replace('%%', '%')

    return renaming


def rotated_rect_with_max_area(width, height, angle):
    """Given a rectangle of size (width, height) that has been rotated by angle, computes the width and height of
    the largest possible axis-aligned rectangle (maximal area) within the rotated rectangle.
    Arguments:
        width: Width of the bounding box rectangle.
        height: Height of the bounding box rectangle.
        angle: Angle of rotation in radians.
    """

    if width <= 0 or height <= 0:
        return 0, 0

    width_is_longer = width >= height
    side_long, side_short = (width, height) if width_is_longer else (height, width)

    #Since the solutions for angle, -angle and 180-angle are all the same, it suffices to look at the first quadrant
    #and the absolute values of sin,cos:
    sin_a, cos_a = abs(math.sin(angle)), abs(math.cos(angle))
    if side_short <= 2.*sin_a*cos_a*side_long:
        #Half constrained case: two crop corners touch the longer side, the other two corners are on the mid-line
        #parallel to the longer line
        x = 0.5*side_short
        wr, hr = (x/sin_a, x/cos_a) if width_is_longer else (x/cos_a, x/sin_a)
    else:
        #Fully constrained case: crop touches all 4 sides
        cos_2a = cos_a*cos_a - sin_a*sin_a
        wr, hr = (width*cos_a - height*sin_a)/cos_2a, (height*cos_a - width*sin_a)/cos_2a

    return wr, hr


def format_size(size):
    """Formats a file size in bytes to human-readable format.
    Accepts a numerical value, returns a string.
    """

    if size >= 1024:
        size = size/1024
        if size >= 1024:
            size = size/1024
            if size >= 1024:
                size = size/1024
                return str(round(size, 2))+' GB'
            else:
                return str(round(size, 2))+' MB'
        else:
            return str(round(size, 2))+' KB'
    else:
        return str(round(size, 2))+' Bytes'


def interpolate(start, stop, length, minimum, maximum, before=None, before_distance=1, after=None, after_distance=1, mode='linear'):
    """Returns a list of a given length, of float values interpolated between two given values.
    Arguments:
        start: Starting Y value.
        stop: Ending Y value.
        length: Integer, the number of steps that will be interpolated.
        minimum: Lowest allowed Y value, any lower values will be clipped to this.
        maximum: Highest allowed Y value, any higher values will be clipped to this.
        before: Used in 'cubic' and 'catmull' modes, the Y value of the previous point before the start point.
            If set to None, it will be extrapolated linearly from the start and stop points.
        before_distance: Distance from the current points that the previous point is.
        after: Used in 'cubic' and 'catmull' modes, the Y value of the next point after the stop point.
            If set to None, it will be extrapolated linearly from the start and stop points.
        after_distance: Distance from the current points that the next point is.
        mode: String, the interpolation mode.  May be set to: 'linear', 'cosine', 'cubic', 'catmull'
    Returns: A list of float values.
    """

    minimum_distance = 40
    if length == 0:
        return []
    values = []
    y = start
    difference = stop - start
    step = difference/length
    if mode == 'cubic' or mode == 'catmull':
        if before is None:
            before = start - stop
            before_distance = length
        if after is None:
            after = stop + (stop - start)
            after_distance = length
        if after_distance < minimum_distance:
            after_distance = minimum_distance
        if before_distance < minimum_distance:
            before_distance = minimum_distance
        after_distance = after_distance / length
        before_distance = before_distance / length
        before = before / before_distance
        after = after / after_distance
    if mode == 'catmull':
        a = -0.5*before + 1.5*start - 1.5*stop + 0.5*after
        b = before - 2.5*start + 2*stop - 0.5*after
        c = -0.5*before + 0.5*stop
        d = start
    elif mode == 'cubic':
        a = after - stop - before + start
        b = before - start - a
        c = stop - before
        d = start
    else:
        a = 1
        b = 1
        c = 1
        d = 1
    for x in range(length):
        values.append(y)
        if mode == 'cubic' or mode == 'catmull':
            mu = x / length
            muu = mu * mu
            y = (a*mu*muu)+(b*muu)+(c*mu)+d
        elif mode == 'cosine':
            mu = x / length
            muu = (1-math.cos(mu*math.pi))/2
            y = start*(1-muu)+(stop*muu)
        else:
            y = y + step
        if y > maximum:
            y = maximum
        if y < minimum:
            y = minimum
    return values


def isfile2(path):
    if not os.path.isfile(path):
        return False
    directory, filename = os.path.split(path)
    return filename in os.listdir(directory)


def time_index(seconds):
    all_minutes, final_seconds = divmod(seconds, 60)
    all_hours, final_minutes = divmod(all_minutes, 60)
    all_days, final_hours = divmod(all_hours, 24)
    time_remaining = str(int(all_days)).zfill(2) + ':' + str(int(final_hours)).zfill(2) + ':' + str(int(final_minutes)).zfill(2) + ':' + str(int(final_seconds)).zfill(2)
    return time_remaining


def verify_copy(copy_from, copy_to):
    if not os.path.exists(copy_to):
        copy2(copy_from, copy_to)
    compare = filecmp.cmp(copy_from, copy_to, shallow=False)
    return compare


def agnostic_path(path):
    """Returns a path with the '/' separator instead of anything else."""
    return str(path.replace('\\', '/'))


def local_paths(photo_list):
    """Takes a list of photo info objects and formats all paths to whatever is appropriate for the current os."""

    return_list = []
    if photo_list:
        for photo in photo_list:
            return_list.append(local_photoinfo(list(photo)))
    return return_list


def local_path(path):
    """Formats a path string using separatorns appropriate for the os."""
    return str(path.replace('/', os.path.sep))


def local_photoinfo(photoinfo):
    photoinfo[0] = local_path(photoinfo[0])
    photoinfo[1] = local_path(photoinfo[1])
    photoinfo[2] = local_path(photoinfo[2])
    photoinfo[10] = local_path(photoinfo[10])
    return photoinfo


def agnostic_photoinfo(photoinfo):
    photoinfo[0] = agnostic_path(photoinfo[0])
    photoinfo[1] = agnostic_path(photoinfo[1])
    photoinfo[2] = agnostic_path(photoinfo[2])
    photoinfo[10] = agnostic_path(photoinfo[10])
    return photoinfo


def local_thumbnail(thumbnail):
    thumbnail[0] = local_path(thumbnail[0])
    return thumbnail


def agnostic_thumbnail(thumbnail):
    thumbnail[0] = agnostic_path(thumbnail[0])
    return thumbnail


def list_folders(folder):
    """Function that returns a list of all nested subfolders within a given folder.
    Argument:
        folder: The folder name to look in
    Returns: A list of strings, full paths to each subfolder.
    """

    walk = os.walk
    join = os.path.join
    relpath = os.path.relpath
    folder_list = []
    firstroot = False
    for root, directories, files in walk(folder, topdown=True):
        if not firstroot:
            firstroot = root
        filefolder = relpath(root, firstroot)
        if filefolder == '.':
            filefolder = ''
        for directory in directories:
            folder_list.append(join(filefolder, directory))
    return folder_list


def list_files(folder):
    """Function that returns a list of every nested file within a folder.
    Argument:
        folder: The folder name to look in
    Returns: A list of file lists, each list containing:
        Full path to the file, relative to the root directory.
        Root directory for all files.
    """

    file_list = []
    firstroot = False
    for root, dirs, files in os.walk(folder, topdown=True):
        if not firstroot:
            firstroot = root
        filefolder = os.path.relpath(root, firstroot)
        if filefolder == '.':
            filefolder = ''
        for file in files:
            file_list.append([os.path.join(filefolder, file), firstroot])
    return file_list


def get_folder_info(folder, databases):
    """Checks a folder for info files that may contain album information.
    Reads '.picasa.ini' files generated by Google's Picasa, and '.photoinfo.ini' files generated by this program.

    Arguments:
        folder: Database subfolder to check, string.
        databases: List of database root folder strings.
    Returns:
        A list containing:
            folder: Given folder.
            title: Folder title if it can be recovered from an info file, empty string if not.
            description: Folder description if it can be recovered from an info file, empty string if not.
    """

    title = ''
    description = ''
    for database in databases:
        full_folder = os.path.join(database, folder)
        if os.path.isdir(full_folder):
            inifile = os.path.join(full_folder, '.picasa.ini')
            if os.path.exists(inifile):
                configfile = ConfigParser(interpolation=None)
                try:
                    configitems = dict(configfile.items('Picasa'))
                    if 'name' in configitems:
                        title = configitems['name']
                    if 'description' in configitems:
                        description = configitems['description']
                except:
                    pass
            inifile = os.path.join(full_folder, '.photoinfo.ini')
            if os.path.exists(inifile):
                configfile = ConfigParser(interpolation=None)
                try:
                    configfile.read(inifile)
                    configitems = dict(configfile.items('Album'))
                    if 'title' in configitems:
                        title = configitems['title']
                    if 'description' in configitems:
                        description = configitems['description']
                except:
                    pass
    return [folder, title, description]


def get_file_info(file_info, import_mode=False, modified_date=False):
    """Reads a photo file and determines all the basic information about it.
    Will attempt to read info files generated by Google's Picasa or by this program, other information is read directly
    from the file.

    Arguments:
        file_info: A list containing file information:
            Relative path to the file from the database directory
            Database root directory
        import_mode: When reading the file from a camera or other import source, don't try to find any info files.
        modified_date: if this is already found, can be passed in to save time

    Returns: A photoinfo list.
    """

    filepath, filename = os.path.split(file_info[0])
    database_folder = file_info[1]
    full_folder = os.path.join(database_folder, filepath)
    full_filename = os.path.join(full_folder, filename)
    full_folder = os.path.join(database_folder, filepath)
    original_file = filename
    original_date = int(os.path.getmtime(full_filename))
    original_size = int(os.path.getsize(full_filename))
    import_date = int(time.time() - time.timezone)
    if not modified_date:
        modified_date = int(os.path.getmtime(full_filename))
    tags = ''
    edited = 0
    owner = ''
    export = 1
    rename = filename

    if not import_mode:
        # Try to read various information from info files that may exist.
        infofile = os.path.join(full_folder, '.picasaoriginals')
        if os.path.isdir(infofile):
            originals = os.listdir(infofile)
            if filename in originals:
                original_file = os.path.join('.picasaoriginals', filename)
                full_original_file = os.path.join(full_folder, original_file)
                original_date = int(os.path.getmtime(full_original_file))
                original_size = int(os.path.getsize(full_original_file))
                edited = 1
        infofile = os.path.join(full_folder, '.originals')
        if os.path.isdir(infofile):
            originals = os.listdir(infofile)
            if filename in originals:
                original_file = os.path.join('.originals', filename)
                full_original_file = os.path.join(full_folder, original_file)
                original_date = int(os.path.getmtime(full_original_file))
                original_size = int(os.path.getsize(full_original_file))
                edited = 1
        infofile = os.path.join(full_folder, '.picasa.ini')
        if os.path.isfile(infofile):
            configfile = ConfigParser(interpolation=None)
            try:
                configfile.read(infofile)
                configitems = configfile.items(filename)
                if ('star', 'yes') in configitems:
                    tags = 'favorite'
            except:
                pass
        infofile = os.path.join(full_folder, '.photoinfo.ini')
        if os.path.isfile(infofile):
            configfile = ConfigParser(interpolation=None)
            try:
                configfile.read(infofile)
                configitems = dict(configfile.items(filename))
                if 'tags' in configitems:
                    tags = configitems['tags']
                if 'owner' in configitems:
                    owner = configitems['owner']
                if 'edited' in configitems:
                    edited = int(configitems['edited'])
                if 'import_date' in configitems:
                    import_date = int(configitems['import_date'])
                if 'rename' in configitems:
                    rename = configitems['rename']
                if 'export' in configitems:
                    export = int(configitems['export'])
            except:
                pass

    # try to read the photo orientation from the exif tag
    orientation = 1
    try:
        exif_tag = Image.open(full_filename)._getexif()
        if 274 in exif_tag:
            orientation = exif_tag[274]
    except:
        pass

    return [os.path.join(filepath, filename), filepath, database_folder, original_date, original_size, rename, import_date, modified_date, tags, edited, original_file, owner, export, orientation]
