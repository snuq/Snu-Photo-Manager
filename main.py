"""
Bugs:
    android: issues with input with minnuum keyboard - due to kivy not using all input methods... have to wait for fix
    make the ShortLabel truncate when too long, currently it will push widgets off screen...
    some interface elements will not display properly with large buttons or large text

Todo:
    Add a "find source files" function, searches database directories for the source files that may have been moved.
    preview videos and photos on import screen (click once to pop up preview)
    search function
    set video in and out points before reencoding
    simplified interface mode - redo sorting and new/delete/rename to be smaller somehow
    android: need to include ffmpeg executable
    create collage feature
    rework importing to allow multiple folders with the same name (in subfolders)

Possible Todo (Later On):
    multi-thread video processing
    export to facebook - https://github.com/mobolic/facebook-sdk , https://blog.kivy.org/2013/08/using-facebook-sdk-with-python-for-android-kivy/
    RAW import if possible - https://github.com/photoshell/rawkit , need to get libraw working
"""


try:
    import numpy
    import cv2
    opencv = True
except:
    opencv = False
import math
import json
import sys
import fnmatch
import PIL
from PIL import Image, ImageEnhance, ImageOps, ImageChops, ImageDraw, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import sqlite3
import os
import string
import re
#os.environ['KIVY_IMAGE'] = 'pil'
os.environ['KIVY_VIDEO'] = 'ffpyplayer'
from configparser import ConfigParser
from io import BytesIO
import datetime
from shutil import copy2
from shutil import copyfile
from shutil import rmtree
from shutil import move
try:
    from shutil import disk_usage
except:
    disk_usage = None
from collections import OrderedDict
from subprocess import call
import subprocess
import time
from operator import itemgetter

#all these are needed to get ffpyplayer working on linux
import ffpyplayer.threading
import ffpyplayer.player.queue
import ffpyplayer.player.frame_queue
import ffpyplayer.player.decoder
import ffpyplayer.player.clock
import ffpyplayer.player.core

from ffpyplayer.player import MediaPlayer
from ffpyplayer.pic import SWScale
from ffpyplayer import tools as fftools
import threading
import kivy
from kivy.config import Config
Config.window_icon = "data/icon.png"
from kivy.app import App
from kivy.clock import Clock
from kivy.cache import Cache
from kivy.base import EventLoop
from kivy.graphics.transformation import Matrix
from kivy.uix.behaviors import ButtonBehavior, DragBehavior, CompoundSelectionBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.settings import Settings, SettingItem
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.splitter import Splitter
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.treeview import TreeViewLabel, TreeViewNode, TreeView
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.core.image import ImageLoader
from kivy.uix.video import Video
from kivy.uix.videoplayer import VideoPlayer
from kivy.uix.scrollview import ScrollView
from kivy.loader import Loader as ThumbLoader
from kivy.core.image.img_pil import ImageLoaderPIL
from kivy.loader import Loader
from kivy.graphics import Rectangle, Color, Line
from kivy.utils import platform
from kivy.uix.stencilview import StencilView

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from colorpickercustom import ColorPickerCustom
from functools import partial
from send2trash import send2trash
from resizablebehavior import ResizableBehavior
import filecmp
from queue import Queue
try:
    import win32timezone
except:
    pass

version = sys.version_info
kivy.require('1.10.0')
#os.environ['KIVY_IMAGE'] = 'pil,sdl2'
lock = threading.Lock()

if platform in ['win', 'linux', 'macosx', 'unknown']:
    desktop = True
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    #Config.set('kivy', 'keyboard_mode', 'system')
    Window.maximize()
else:
    desktop = False
    Window.softinput_mode = 'below_target'
if platform == 'win':
    from ctypes import windll, create_unicode_buffer
scale_size_to_options = OrderedDict([('long', 'Long Side'), ('short', 'Short Side'),
                                     ('height', 'Height'), ('width', 'Width')])
naming_method_default = '%Y-%M-%D< - %T>'
avoidfolders = ['.picasaoriginals', '.thumbnails', '.originals']
imagetypes = ['.jpg', '.png', '.jpeg', '.bmp', '.gif', '.pcx']
movietypes = ['.avi', '.mov', '.mp4', '.mpeg4', '.mts']
months_full = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
               'November', 'December']
months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
negative_kelvin = [(255, 115, 0), (255, 124, 0), (255, 121, 0), (255, 130, 0), (255, 126, 0), (255, 135, 0), (255, 131, 0), (255, 141, 11), (255, 137, 18), (255, 146, 29), (255, 142, 33), (255, 152, 41), (255, 147, 44), (255, 157, 51), (255, 152, 54), (255, 162, 60), (255, 157, 63), (255, 166, 69), (255, 161, 72), (255, 170, 77), (255, 165, 79), (255, 174, 84), (255, 169, 87), (255, 178, 91), (255, 173, 94), (255, 182, 98), (255, 177, 101), (255, 185, 105), (255, 180, 107), (255, 189, 111), (255, 184, 114), (255, 192, 118), (255, 187, 120), (255, 195, 124), (255, 190, 126), (255, 198, 130), (255, 193, 132), (255, 201, 135), (255, 196, 137), (255, 203, 141), (255, 199, 143), (255, 206, 146), (255, 201, 148), (255, 208, 151), (255, 204, 153), (255, 211, 156), (255, 206, 159), (255, 213, 161), (255, 209, 163), (255, 215, 166), (255, 211, 168), (255, 217, 171), (255, 213, 173), (255, 219, 175), (255, 215, 177), (255, 221, 180), (255, 217, 182), (255, 223, 184), (255, 219, 186), (255, 225, 188), (255, 221, 190), (255, 226, 192), (255, 223, 194), (255, 228, 196), (255, 225, 198), (255, 229, 200), (255, 227, 202), (255, 231, 204), (255, 228, 206), (255, 232, 208), (255, 230, 210), (255, 234, 211), (255, 232, 213), (255, 235, 215), (255, 233, 217), (255, 237, 218), (255, 235, 220), (255, 238, 222), (255, 236, 224), (255, 239, 225), (255, 238, 227), (255, 240, 228), (255, 239, 230), (255, 241, 231), (255, 240, 233), (255, 243, 234), (255, 242, 236), (255, 244, 237), (255, 243, 239), (255, 245, 240), (255, 244, 242), (255, 246, 243), (255, 245, 245), (255, 247, 245), (255, 246, 248), (255, 248, 248), (255, 248, 251), (255, 249, 251), (255, 249, 253), (255, 249, 253)]
positive_kelvin = [(254, 249, 255), (254, 250, 255), (252, 247, 255), (252, 248, 255), (249, 246, 255), (250, 247, 255), (247, 245, 255), (247, 245, 255), (245, 243, 255), (245, 244, 255), (243, 242, 255), (243, 243, 255), (240, 241, 255), (241, 241, 255), (239, 240, 255), (239, 240, 255), (237, 239, 255), (238, 239, 255), (235, 238, 255), (236, 238, 255), (233, 237, 255), (234, 237, 255), (231, 236, 255), (233, 236, 255), (230, 235, 255), (231, 234, 255), (228, 234, 255), (229, 233, 255), (227, 233, 255), (228, 233, 255), (225, 232, 255), (227, 232, 255), (224, 231, 255), (225, 231, 255), (222, 230, 255), (224, 230, 255), (221, 230, 255), (223, 229, 255), (220, 229, 255), (221, 228, 255), (218, 228, 255), (220, 227, 255), (217, 227, 255), (219, 226, 255), (216, 227, 255), (218, 226, 255), (215, 226, 255), (217, 225, 255), (214, 225, 255), (216, 224, 255), (212, 225, 255), (215, 223, 255), (211, 224, 255), (214, 223, 255), (210, 223, 255), (213, 222, 255), (209, 223, 255), (212, 221, 255), (208, 222, 255), (211, 221, 255), (207, 221, 255), (210, 220, 255), (207, 221, 255), (209, 220, 255), (206, 220, 255), (208, 219, 255), (205, 220, 255), (207, 218, 255), (204, 219, 255), (207, 218, 255), (203, 219, 255), (206, 217, 255), (202, 218, 255), (205, 217, 255), (201, 218, 255), (204, 216, 255), (201, 217, 255), (204, 216, 255), (200, 217, 255), (203, 215, 255), (199, 216, 255), (202, 215, 255), (199, 216, 255), (202, 214, 255), (198, 216, 255), (201, 214, 255), (197, 215, 255), (200, 213, 255), (196, 215, 255), (200, 213, 255), (196, 214, 255), (199, 212, 255), (195, 214, 255), (198, 212, 255), (195, 214, 255), (198, 212, 255), (194, 213, 255), (197, 211, 255), (193, 213, 255), (197, 211, 255)]

containers = ['mp4', 'matroska', 'mov', 'ogg', 'avi']
containers_friendly = ['MP4', 'Matroska', 'Quicktime', 'Ogg', 'AVI']
containers_extensions = ['mp4', 'mkv', 'mov', 'ogv', 'avi']
video_codecs = ['libx264', 'mpeg4', 'mpeg2video', 'libtheora']
video_codecs_friendly = ['H.264', 'MPEG 4', 'MPEG 2', 'Ogg Theora']
audio_codecs = ['aac', 'ac3', 'libmp3lame', 'flac', 'libvorbis']
audio_codecs_friendly = ['AAC', 'AC-3', 'MP3', 'FLAC', 'Ogg Vorbis']
interface_multiplier = 22
drag_delay = .5

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


def interpolate(start, stop, length, minimum, maximum, previous=None, previous_distance=1, next=None, next_distance=1, mode='linear'):
    """Returns a list of a given length, of float values interpolated between two given values.
    Arguments:
        start: Starting Y value.
        stop: Ending Y value.
        length: Integer, the number of steps that will be interpolated.
        minimum: Lowest allowed Y value, any lower values will be clipped to this.
        maximum: Highest allowed Y value, any higher values will be clipped to this.
        previous: Used in 'cubic' and 'catmull' modes, the Y value of the previous point before the start point.
            If set to None, it will be extrapolated linearly from the start and stop points.
        next: Used in 'cubic' and 'catmull' modes, the Y value of the next point after the stop point.
            If set to None, it will be extrapolated linearly from the start and stop points.
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
        if previous is None:
            previous = start - stop
            previous_distance = length
        if next is None:
            next = stop + (stop - start)
            next_distance = length
        if next_distance < minimum_distance:
            next_distance = minimum_distance
        if previous_distance < minimum_distance:
            previous_distance = minimum_distance
        next_distance = next_distance / length
        previous_distance = previous_distance / length
        previous = previous / previous_distance
        next = next / next_distance
    if mode == 'catmull':
        a = -0.5*previous + 1.5*start - 1.5*stop + 0.5*next
        b = previous - 2.5*start + 2*stop - 0.5*next
        c = -0.5*previous + 0.5*stop
        d = start
    elif mode == 'cubic':
        a = next - stop - previous + start
        b = previous - start - a
        c = stop - previous
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


def agnostic_path(string):
    """Returns a path with the '/' separator instead of anything else."""
    return str(string.replace('\\', '/'))


def local_paths(photo_list):
    """Takes a list of photo info objects and formats all paths to whatever is appropriate for the current os."""

    return_list = []
    if photo_list:
        for photo in photo_list:
            return_list.append(local_photoinfo(list(photo)))
    return return_list


def local_path(string):
    """Formats a path string using separatorns appropriate for the os."""
    return str(string.replace('/', os.path.sep))


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


def to_bool(value):
    """Function to convert various Non-Boolean true/false values to Boolean.
    Inputs that return True are:
        'Yes', 'yes', 'True', 'True', 'T', 't', '1', 1, 'Down', 'down'
    Any other value returns a False.
    """

    return str(value).lower() in ('yes', 'true', 't', '1', 'down')


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


def list_folders(folder):
    """Function that returns a list of all nested subfolders within a given folder.
    Argument:
        folder: The folder name to look in
    Returns: A list of strings, full paths to each subfolder.
    """

    folder_list = []
    firstroot = False
    for root, directories, files in os.walk(folder, topdown=True):
        if not firstroot:
            firstroot = root
        filefolder = os.path.relpath(root, firstroot)
        if filefolder == '.':
            filefolder = ''
        for directory in directories:
            folder_list.append(os.path.join(filefolder, directory))
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

    return [os.path.join(filepath, filename), filepath, database_folder, original_date, original_size, rename,
            import_date, modified_date, tags, edited, original_file, owner, export, orientation]


def generate_thumbnail(fullpath, database_folder):
    """Creates a thumbnail image for a photo.

    Arguments:
        fullpath: Path to file, relative to the database folder.
        database_folder: Database root folder where the file is.
    Returns:
        A thumbnail jpeg
    """

    app = App.get_running_app()
    thumbnail = ''
    full_filename = os.path.join(database_folder, fullpath)
    extension = os.path.splitext(fullpath)[1].lower()

    try:
        if extension in imagetypes:
            #This is an image file, use PIL to generate a thumnail
            image = Image.open(full_filename)
            image.thumbnail((app.thumbsize, app.thumbsize), Image.ANTIALIAS)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            output = BytesIO()
            image.save(output, 'jpeg')
            thumbnail = output.getvalue()

        elif extension in movietypes:
            #This is a video file, use ffpyplayer to generate a thumbnail
            player = MediaPlayer(full_filename, ff_opts={'paused': True, 'ss': 1.0, 'an': True})
            frame = None
            while not frame:
                frame, value = player.get_frame(force_refresh=True)
            player.close_player()
            player = None
            frame = frame[0]
            frame_size = frame.get_size()
            frame_converter = SWScale(frame_size[0], frame_size[1], frame.get_pixel_format(), ofmt='rgb24')
            new_frame = frame_converter.scale(frame)
            image_data = bytes(new_frame.to_bytearray()[0])

            image = Image.frombuffer(mode='RGB', size=(frame_size[0], frame_size[1]), data=image_data, decoder_name='raw')
            image = image.transpose(1)

            image.thumbnail((app.thumbsize, app.thumbsize), Image.ANTIALIAS)
            output = BytesIO()
            image.save(output, 'jpeg')
            thumbnail = output.getvalue()
        return thumbnail
    except:
        return None


def get_drives():
    drives = []
    if platform == 'win':
        for path in ['Desktop', 'Documents', 'Pictures']:
            drives.append((os.path.expanduser(u'~') + os.path.sep + path + os.path.sep, path))
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                name = create_unicode_buffer(64)
                # get name of the drive
                drive = letter + u':'
                res = windll.kernel32.GetVolumeInformationW(drive + os.path.sep, name, 64, None, None, None, None, 0)
                drive_name = drive
                if name.value:
                    drive_name = drive_name + '(' + name.value + ')'
                drives.append((drive + os.path.sep, drive_name))
            bitmask >>= 1
    elif platform == 'linux':
        drives.append((os.path.sep, os.path.sep))
        drives.append((os.path.expanduser(u'~') + os.path.sep, 'Home'))
        drives.append((os.path.sep + u'mnt' + os.path.sep, os.path.sep + u'mnt'))
        places = (os.path.sep + u'mnt' + os.path.sep, os.path.sep + u'media')
        for place in places:
            if os.path.isdir(place):
                for directory in next(os.walk(place))[1]:
                    drives.append((place + os.path.sep + directory + os.path.sep, directory))
    elif platform == 'macosx' or platform == 'ios':
        drives.append((os.path.expanduser(u'~') + os.path.sep, 'Home'))
        vol = os.path.sep + u'Volume'
        if os.path.isdir(vol):
            for drive in next(os.walk(vol))[1]:
                drives.append((vol + os.path.sep + drive + os.path.sep, drive))
    elif platform == 'android':
        drives.append((os.path.sep, os.path.sep))
        drives.append((os.path.sep + u'mnt' + os.path.sep, '/mnt'))
        drives.append((os.path.sep + u'mnt' + os.path.sep + 'sdcard' + os.path.sep, 'Internal Memory'))
    return drives


def isfile2(path):
    if not os.path.isfile(path):
        return False
    directory, filename = os.path.split(path)
    return filename in os.listdir(directory)


class FileBrowser(BoxLayout):

    __events__ = ('on_cancel', 'on_ok')
    path = StringProperty()
    file = StringProperty()
    filename = StringProperty()
    root = StringProperty()

    popup = ObjectProperty(None, allownone=True)

    allow_new = BooleanProperty(True)
    allow_delete = BooleanProperty(True)
    new_folder = StringProperty('')
    start_in = StringProperty()
    directory_select = BooleanProperty(False)
    file_editable = BooleanProperty(False)
    filters = ListProperty([])
    target_selected = BooleanProperty(False)

    header_text = StringProperty('Select A File')
    cancel_text = StringProperty('Cancel')
    ok_text = StringProperty('OK')

    def __init__(self, **kwargs):
        if not self.start_in:
            self.start_in = '/'
        Clock.schedule_once(self.refresh_locations)
        super(FileBrowser, self).__init__(**kwargs)

    def dismiss_popup(self):
        """If this dialog has a popup, closes it and removes it."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def add_folder(self):
        """Starts the add folder process, creates an input text popup."""

        content = InputPopup(hint='Folder Name', text='Enter A Folder Name:')
        app = App.get_running_app()
        content.bind(on_answer=self.add_folder_answer)
        self.popup = NormalPopup(title='Create Folder', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 5),
                                 auto_dismiss=False)
        self.popup.open()

    def add_folder_answer(self, instance, answer):
        """Tells the app to rename the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be created, all other answers will just close the dialog.
        """

        if answer == 'yes':
            text = instance.ids['input'].text.strip(' ')
            if text:
                app = App.get_running_app()
                folder = os.path.join(self.path, text)
                created = False
                try:
                    if not os.path.isdir(folder):
                        os.makedirs(folder)
                        created = True
                except:
                    pass
                if created:
                    app.message("Created the folder '"+folder+"'")
                    self.path = folder
                    self.refresh_folder()
                else:
                    app.message("Could Not Create Folder.")
        self.dismiss_popup()

    def delete_folder(self):
        """Starts the delete folder process, creates the confirmation popup."""

        app = App.get_running_app()
        if not os.listdir(self.path):
            text = "Delete The Selected Folder?"
            content = ConfirmPopup(text=text, yes_text='Delete', no_text="Don't Delete", warn_yes=True)
            content.bind(on_answer=self.delete_folder_answer)
            self.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None),
                                     size=(app.popup_x, app.button_scale * 4),
                                     auto_dismiss=False)
            self.popup.open()
        else:
            app.message("Folder Is Not Empty.")

    def delete_folder_answer(self, instance, answer):
        """Tells the app to delete the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be deleted, all other answers will just close the dialog.
        """

        del instance
        if answer == 'yes':
            app = App.get_running_app()
            try:
                os.rmdir(self.path)
                app.message("Deleted Folder: \""+self.path+"\"")
                self.go_up()
            except:
                app.message("Could Not Delete Folder...")
        self.dismiss_popup()

    def refresh_locations(self, *_):
        locations_list = self.ids['locationsList']
        locations = get_drives()
        self.root = locations[0][0]
        data = []
        for location in locations:
            data.append({
                'text': location[1],
                'fullpath': location[0],
                'path': location[0],
                'type': 'folder',
                'owner': self
            })
        locations_list.data = data
        if not self.path:
            self.path = locations[0][0]
        self.refresh_folder()

    def refresh_folder(self, *_):
        file_list = self.ids['fileList']
        data = []
        files = []
        dirs = []
        if os.path.isdir(self.path):
            try:
                for file in os.listdir(self.path):
                    fullpath = os.path.join(self.path, file)
                    if os.path.isfile(fullpath):
                        files.append(file)
                    elif os.path.isdir(fullpath):
                        dirs.append(file)
            except:
                self.go_up()
                return
            dirs = sorted(dirs, key=lambda s: s.lower())
            for directory in dirs:
                fullpath = os.path.join(self.path, directory)
                data.append({
                    'text': directory,
                    'fullpath': fullpath,
                    'path': fullpath + os.path.sep,
                    'type': 'folder',
                    'owner': self,
                    'selected': False
                })
            if not self.directory_select:
                if self.filters:
                    filtered_files = []
                    for filter in self.filters:
                        filtered_files += fnmatch.filter(files, filter)
                    files = filtered_files
                files = sorted(files, key=lambda s: s.lower())
                for file in files:
                    data.append({
                        'text': file,
                        'fullpath': os.path.join(self.path, file),
                        'path': self.path,
                        'type': file,
                        'file': file,
                        'owner': self,
                        'selected': False
                    })

        file_list.data = data
        if not self.directory_select:
            self.file = ''
            self.target_selected = False
        else:
            self.filename = self.path
            self.target_selected = True

    def go_up(self, *_):
        up_path = os.path.realpath(os.path.join(self.path, '..'))
        if not up_path.endswith(os.path.sep):
            up_path += os.path.sep
        if up_path == self.path:
            up_path = self.root
        self.path = up_path
        self.refresh_folder()

    def select(self, button):
        if button.type == 'folder':
            self.path = button.path
            self.refresh_folder()
            if self.directory_select:
                self.filename = button.fullpath
                self.target_selected = True
            else:
                self.filename = ''
                self.target_selected = False
        else:
            self.filename = button.fullpath
            self.file = button.file
            self.target_selected = True

    def on_cancel(self):
        pass

    def on_ok(self):
        pass


class RecycleItem(RecycleDataViewBehavior, BoxLayout):
    bgcolor = ListProperty([0, 0, 0, 0])
    owner = ObjectProperty()
    text = StringProperty()
    selected = BooleanProperty(False)
    index = None
    data = {}

    def on_selected(self, *_):
        self.set_color()

    def set_color(self):
        app = App.get_running_app()

        if self.selected:
            self.bgcolor = app.selected_color
        else:
            if self.index % 2 == 0:
                self.bgcolor = app.color_even
            else:
                self.bgcolor = app.color_odd

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.data = data
        self.set_color()
        return super(RecycleItem, self).refresh_view_attrs(rv, index, data)

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected

    def on_touch_down(self, touch):
        if super(RecycleItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            self.parent.selected = self.data
            try:
                self.owner.select(self)
            except:
                pass
            return True


class FileBrowserItem(RecycleItem):
    path = StringProperty()
    fullpath = StringProperty()
    file = StringProperty()
    type = StringProperty('folder')


class SelectableRecycleBoxLayout(RecycleBoxLayout):
    """Adds selection and focus behavior to the view."""
    selected = DictProperty()
    selects = ListProperty([])
    multiselect = BooleanProperty(False)

    def toggle_select(self, *_):
        if self.multiselect:
            if self.selects:
                self.selects = []
            else:
                all_selects = self.parent.data
                for select in all_selects:
                    self.selects.append(select)
        else:
            if self.selected:
                self.selected = {}
        self.update_selected()

    def on_selected(self, *_):
        if self.selected:
            if self.multiselect:
                if self.selected in self.selects:
                    self.selects.remove(self.selected)
                else:
                    self.selects.append(self.selected)
            self.update_selected()

    def on_children(self, *_):
        self.update_selected()

    def update_selected(self):
        for child in self.children:
            if self.multiselect:
                if child.data in self.selects:
                    child.selected = True
                else:
                    child.selected = False
            else:
                if child.data == self.selected:
                    child.selected = True
                else:
                    child.selected = False


class PhotoListRecycleView(RecycleView):
    selected_index = NumericProperty(0)

    def scroll_to_selected(self):
        box = self.children[0]
        selected = box.selected
        for i, item in enumerate(self.data):
            if item == selected:
                self.selected_index = i
                break
        index = self.selected_index
        pos_index = (box.default_size[1] + box.spacing) * index
        scroll = self.convert_distance_to_scroll(0, pos_index - (self.height * 0.5))[1]
        if scroll > 1.0:
            scroll = 1.0
        elif scroll < 0.0:
            scroll = 0.0
        self.scroll_y = 1.0 - scroll

    def convert_distance_to_scroll(self, dx, dy):
        box = self.children[0]
        wheight = box.default_size[1] + box.spacing

        if not self._viewport:
            return 0, 0
        vp = self._viewport
        vp_height = len(self.data) * wheight
        if vp.width > self.width:
            sw = vp.width - self.width
            sx = dx / float(sw)
        else:
            sx = 0
        if vp_height > self.height:
            sh = vp_height - self.height
            sy = dy / float(sh)
        else:
            sy = 1
        return sx, sy


class MultiThreadOK(threading.Thread):
    """Slightly modified version of sqlite multithread support by Louis RIVIERE"""

    def __init__(self, db):
        super(MultiThreadOK, self).__init__()
        self.db = db
        self.reqs = Queue()
        self.start()

    def run(self):
        cnx = sqlite3.connect(self.db)
        cursor = cnx.cursor()
        while True:
            req, arg, res = self.reqs.get()
            if req == '--commit--':
                cnx.commit()
            if req == '--close--':
                break
            try:
                cursor.execute(req, arg)
            except:
                pass
            if res:
                for rec in cursor:
                    res.put(rec)
                res.put('--no more--')
        cursor.close()
        cnx.commit()
        cnx.close()

    def execute(self, req, arg=None, res=None):
        self.reqs.put((req, arg or tuple(), res))

    def select(self, req, arg=None):
        res = Queue()
        self.execute(req, arg, res)
        while True:
            rec = res.get()
            if rec == '--no more--':
                break
            yield rec

    def commit(self):
        self.execute('--commit--')

    def close(self):
        self.execute('--close--')


class FloatInput(TextInput):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


class IntegerInput(TextInput):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.sub(pat, '', substring)
        return super(IntegerInput, self).insert_text(s, from_undo=from_undo)


class NormalPopup(Popup):
    """Basic popup widget."""
    pass


class NormalButton(Button):
    """Basic button widget."""
    pass


class WideButton(Button):
    """Full width button widget"""

    warn = BooleanProperty(False)


class ShortLabel(Label):
    """Label that only takes up as much space as needed."""
    pass


class InfoLabel(ShortLabel):
    bgcolor = ListProperty([0, 0, 0, 0])
    blinker = ObjectProperty()

    def on_text(self, instance, text):
        del instance
        if self.blinker:
            self.blinker.cancel()
        self.reset_bgcolor()
        if text:
            self.blinker = Clock.schedule_interval(self.toggle_bgcolor, .33)
            Clock.schedule_once(self.stop_blinking, 5)

    def toggle_bgcolor(self, *_):
        if self.bgcolor == [0, 0, 0, 0]:
            self.hilight_bgcolor()
        else:
            self.reset_bgcolor()

    def stop_blinking(self, *_):
        if self.blinker:
            self.blinker.cancel()
        Clock.schedule_once(self.reset_bgcolor)

    def hilight_bgcolor(self, *_):
        self.bgcolor = [1, 1, 0, .75]

    def reset_bgcolor(self, *_):
        self.bgcolor = [0, 0, 0, 0]


class CustomImage(KivyImage):
    """Custom image display widget.
    Enables editing operations, displaying them in real-time using a low resolution preview of the original image file.
    All editing variables are watched by the widget and it will automatically update the preview when they are changed.
    """

    pixel_format = ''
    length = NumericProperty(0)
    framerate = ListProperty()
    video = BooleanProperty(False)
    player = ObjectProperty(None, allownone=True)
    position = NumericProperty(0.5)
    original_image = ObjectProperty()
    photoinfo = ListProperty()
    original_width = NumericProperty(0)
    original_height = NumericProperty(0)
    flip_horizontal = BooleanProperty(False)
    flip_vertical = BooleanProperty(False)
    mirror = BooleanProperty(False)
    angle = NumericProperty(0)
    rotate_angle = NumericProperty(0)
    fine_angle = NumericProperty(0)
    brightness = NumericProperty(0)
    shadow = NumericProperty(0)
    contrast = NumericProperty(0)
    gamma = NumericProperty(0)
    saturation = NumericProperty(0)
    temperature = NumericProperty(0)
    tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    curve = ListProperty()
    crop_top = NumericProperty(0)
    crop_bottom = NumericProperty(0)
    crop_left = NumericProperty(0)
    crop_right = NumericProperty(0)
    filter = StringProperty('')
    filter_amount = NumericProperty(0)
    autocontrast = BooleanProperty(False)
    equalize = NumericProperty(0)
    histogram = ListProperty()
    edit_image = ObjectProperty()
    cropping = BooleanProperty(False)
    touch_point = ObjectProperty()
    active_cropping = BooleanProperty(False)
    crop_start = ListProperty()
    sharpen = NumericProperty(0)
    bilateral = NumericProperty(0.5)
    bilateral_amount = NumericProperty(0)
    median_blur = NumericProperty(0)
    vignette_amount = NumericProperty(0)
    vignette_size = NumericProperty(.5)
    edge_blur_amount = NumericProperty(0)
    edge_blur_size = NumericProperty(.5)
    edge_blur_intensity = NumericProperty(.5)
    cropper = ObjectProperty()  #Holder for the cropper overlay
    crop_controls = ObjectProperty()  #Holder for the cropper edit panel object
    adaptive_clip = NumericProperty(0)
    border_opacity = NumericProperty(1)
    border_image = ListProperty()
    border_tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    border_x_scale = NumericProperty(.5)
    border_y_scale = NumericProperty(.5)
    crop_min = NumericProperty(100)
    size_multiple = NumericProperty(1)

    #Denoising variables
    denoise = BooleanProperty(False)
    luminance_denoise = NumericProperty(10)
    color_denoise = NumericProperty(10)
    search_window = NumericProperty(15)
    block_size = NumericProperty(5)

    def start_video_convert(self):
        self.close_video()
        self.player = MediaPlayer(self.source, ff_opts={'paused': True, 'ss': 1.0, 'an': True})
        self.player.set_volume(0)

    def get_converted_frame(self):
        self.player.set_pause(False)
        frame = None
        while not frame:
            frame, value = self.player.get_frame(force_refresh=False)
            if value == 'eof':
                return None
        self.player.set_pause(True)
        frame_image = frame[0]
        frame_size = frame_image.get_size()
        frame_converter = SWScale(frame_size[0], frame_size[1], frame_image.get_pixel_format(), ofmt='rgb24')
        new_frame = frame_converter.scale(frame_image)
        image_data = bytes(new_frame.to_bytearray()[0])
        image = Image.frombuffer(mode='RGB', size=(frame_size[0], frame_size[1]), data=image_data, decoder_name='raw')
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image = self.adjust_image(image, preview=False)
        return [image, frame[1]]

    def close_video(self):
        if self.player:
            self.player.close_player()
            self.player = None

    def open_video(self):
        self.player = MediaPlayer(self.source, ff_opts={'paused': True, 'ss': 1.0, 'an': True})
        frame = None
        while not frame:
            frame, value = self.player.get_frame(force_refresh=True)
        data = self.player.get_metadata()
        self.length = data['duration']
        self.framerate = data['frame_rate']
        self.pixel_format = data['src_pix_fmt']

    def set_aspect(self, aspect_x, aspect_y):
        """Adjusts the cropping of the image to be a given aspect ratio.
        Attempts to keep the image as large as possible
        Arguments:
            aspect_x: Horizontal aspect ratio element, numerical value.
            aspect_y: Vertical aspect ratio element, numerical value.
        """

        width = self.original_width - self.crop_left - self.crop_right
        height = self.original_height - self.crop_top - self.crop_bottom
        if aspect_x != width or aspect_y != height:
            current_ratio = width / height
            target_ratio = aspect_x / aspect_y
            if target_ratio > current_ratio:
                #crop top/bottom, width is the same
                new_height = width / target_ratio
                height_difference = height - new_height
                crop_right = 0
                crop_left = 0
                crop_top = height_difference / 2
                crop_bottom = crop_top
            else:
                #crop sides, height is the same
                new_width = height * target_ratio
                width_difference = width - new_width
                crop_top = 0
                crop_bottom = 0
                crop_left = width_difference / 2
                crop_right = crop_left
        else:
            crop_top = 0
            crop_right = 0
            crop_bottom = 0
            crop_left = 0
        self.crop_top = self.crop_top + crop_top
        self.crop_right = self.crop_right + crop_right
        self.crop_bottom = self.crop_bottom + crop_bottom
        self.crop_left = self.crop_left + crop_left
        self.reset_cropper()

    def crop_percent(self, side, percent):
        texture_width = self.original_width
        texture_height = self.original_height
        crop_min = self.crop_min

        if side == 'top':
            crop_amount = texture_height * percent
            if (texture_height - crop_amount - self.crop_bottom) < crop_min:
                crop_amount = texture_height - self.crop_bottom - crop_min
            self.crop_top = crop_amount
        elif side == 'right':
            crop_amount = texture_width * percent
            if (texture_width - crop_amount - self.crop_left) < crop_min:
                crop_amount = texture_width - self.crop_left - crop_min
            self.crop_right = crop_amount
        elif side == 'bottom':
            crop_amount = texture_height * percent
            if (texture_height - crop_amount - self.crop_top) < crop_min:
                crop_amount = texture_height - self.crop_top - crop_min
            self.crop_bottom = crop_amount
        else:
            crop_amount = texture_width * percent
            if (texture_width - crop_amount - self.crop_right) < crop_min:
                crop_amount = texture_width - self.crop_right - crop_min
            self.crop_left = crop_amount
        self.reset_cropper()
        if self.crop_controls:
            self.crop_controls.update_crop()

    def get_crop_percent(self):
        width = self.original_width
        height = self.original_height
        top_percent = self.crop_top / height
        right_percent = self.crop_right / width
        bottom_percent = self.crop_bottom / height
        left_percent = self.crop_left / width
        return [top_percent, right_percent, bottom_percent, left_percent]

    def get_crop_size(self):
        new_width = self.original_width - self.crop_left - self.crop_right
        new_height = self.original_height - self.crop_top - self.crop_bottom
        new_aspect = new_width / new_height
        old_aspect = self.original_width / self.original_height
        return "Size: "+str(int(new_width))+"x"+str(int(new_height))+", Aspect: "+str(round(new_aspect, 2))+" (Original: "+str(round(old_aspect, 2))+")"

    def reset_crop(self):
        """Sets the crop values back to 0 for all sides"""

        self.crop_top = 0
        self.crop_bottom = 0
        self.crop_left = 0
        self.crop_right = 0
        self.reset_cropper(setup=True)

    def reset_cropper(self, setup=False):
        """Updates the position and size of the cropper overlay object."""

        if self.cropper:
            texture_size = self.get_texture_size()
            texture_top_edge = texture_size[0]
            texture_right_edge = texture_size[1]
            texture_bottom_edge = texture_size[2]
            texture_left_edge = texture_size[3]

            texture_width = (texture_right_edge - texture_left_edge)
            #texture_height = (texture_top_edge - texture_bottom_edge)

            divisor = self.original_width / texture_width
            top_edge = texture_top_edge - (self.crop_top / divisor)
            bottom_edge = texture_bottom_edge + (self.crop_bottom / divisor)
            left_edge = texture_left_edge + (self.crop_left / divisor)
            right_edge = texture_right_edge - (self.crop_right / divisor)
            width = right_edge - left_edge
            height = top_edge - bottom_edge

            self.cropper.pos = [left_edge, bottom_edge]
            self.cropper.size = [width, height]
            if setup:
                self.cropper.max_resizable_width = width
                self.cropper.max_resizable_height = height

    def get_texture_size(self):
        """Returns a list of the texture size coordinates.
        Returns:
            List of numbers: [Top edge, Right edge, Bottom edge, Left edge]
        """

        left_edge = (self.size[0] / 2) - (self.norm_image_size[0] / 2)
        right_edge = left_edge + self.norm_image_size[0]
        bottom_edge = (self.size[1] / 2) - (self.norm_image_size[1] / 2)
        top_edge = bottom_edge + self.norm_image_size[1]
        return [top_edge, right_edge, bottom_edge, left_edge]

    def point_over_texture(self, pos):
        """Checks if the given pos (x,y) value is over the image texture.
        Returns False if not over texture, returns point transformed to texture coordinates if over texture.
        """

        texture_size = self.get_texture_size()
        top_edge = texture_size[0]
        right_edge = texture_size[1]
        bottom_edge = texture_size[2]
        left_edge = texture_size[3]
        if pos[0] > left_edge and pos[0] < right_edge:
            if pos[1] > bottom_edge and pos[1] < top_edge:
                texture_x = pos[0] - left_edge
                texture_y = pos[1] - bottom_edge
                return [texture_x, texture_y]
        return False

    def detect_crop_edges(self, first, second):
        """Given two points, this will detect the proper crop area for the image.
        Arguments:
            first: First crop corner.
            second: Second crop corner.
        Returns a list of cropping values:
            [crop_top, crop_bottom, crop_left, crop_right]
        """

        if first[0] < second[0]:
            left = first[0]
            right = second[0]
        else:
            left = second[0]
            right = first[0]
        if first[1] < second[1]:
            top = second[1]
            bottom = first[1]
        else:
            top = first[1]
            bottom = second[1]
        scale = self.original_width / self.norm_image_size[0]
        crop_top = (self.norm_image_size[1] - top) * scale
        crop_bottom = bottom * scale
        crop_left = left * scale
        crop_right = (self.norm_image_size[0] - right) * scale
        return [crop_top, crop_bottom, crop_left, crop_right]

    def set_crop(self, posx, posy, width, height):
        """Sets the crop values based on the cropper widget."""

        texture_size = self.get_texture_size()
        texture_top_edge = texture_size[0]
        texture_right_edge = texture_size[1]
        texture_bottom_edge = texture_size[2]
        texture_left_edge = texture_size[3]

        left_crop = posx - texture_left_edge
        bottom_crop = posy - texture_bottom_edge
        right_crop = texture_right_edge - width - posx
        top_crop = texture_top_edge - height - posy

        texture_width = (texture_right_edge - texture_left_edge)
        divisor = self.original_width / texture_width
        if left_crop < 0:
            self.crop_left = 0
        else:
            self.crop_left = left_crop * divisor
        if right_crop < 0:
            self.crop_right = 0
        else:
            self.crop_right = right_crop * divisor
        if top_crop < 0:
            self.crop_top = 0
        else:
            self.crop_top = top_crop * divisor
        if bottom_crop < 0:
            self.crop_bottom = 0
        else:
            self.crop_bottom = bottom_crop * divisor
        #self.update_preview(recrop=False)
        if self.crop_controls:
            self.crop_controls.update_crop()

    def on_sharpen(self, *_):
        self.update_preview()

    def on_bilateral(self, *_):
        self.update_preview()

    def on_bilateral_amount(self, *_):
        self.update_preview()

    def on_median_blur(self, *_):
        self.update_preview()

    def on_border_opacity(self, *_):
        self.update_preview()

    def on_border_image(self, *_):
        self.update_preview()

    def on_border_x_scale(self, *_):
        self.update_preview()

    def on_border_y_scale(self, *_):
        self.update_preview()

    def on_vignette_amount(self, *_):
        self.update_preview()

    def on_vignette_size(self, *_):
        self.update_preview()

    def on_edge_blur_amount(self, *_):
        self.update_preview()

    def on_edge_blur_size(self, *_):
        self.update_preview()

    def on_edge_blur_intensity(self, *_):
        self.update_preview()

    def on_rotate_angle(self, *_):
        self.update_preview()

    def on_fine_angle(self, *_):
        self.update_preview()

    def on_flip_horizontal(self, *_):
        self.update_preview()

    def on_flip_vertical(self, *_):
        self.update_preview()

    def on_autocontrast(self, *_):
        self.update_preview()

    def on_adaptive_clip(self, *_):
        self.update_preview()

    def on_equalize(self, *_):
        self.update_preview()

    def on_brightness(self, *_):
        self.update_preview()

    def on_shadow(self, *_):
        self.update_preview()

    def on_gamma(self, *_):
        self.update_preview()

    def on_contrast(self, *_):
        self.update_preview()

    def on_saturation(self, *_):
        self.update_preview()

    def on_temperature(self, *_):
        self.update_preview()

    def on_curve(self, *_):
        self.update_preview()

    def on_tint(self, *_):
        self.update_preview()

    def on_border_tint(self, *_):
        self.update_preview()

    def on_size(self, *_):
        """The image widget has been resized, regenerate the preview image."""

        self.reload_edit_image()
        self.update_preview()

    def on_source(self, *_):
        """The source file has been changed, reload image and regenerate preview."""

        self.video = os.path.splitext(self.source)[1].lower() in movietypes
        if self.video:
            self.open_video()
        self.reload_edit_image()
        self.update_preview()

    def on_position(self, *_):
        self.reload_edit_image()
        self.update_preview()

    def reload_edit_image(self):
        """Regenerate the edit preview image."""
        if self.video:
            location = self.length * self.position
            self.player.seek(pts=location, relative=False)
            frame = None
            while not frame:
                frame, value = self.player.get_frame(force_refresh=True)
            frame = frame[0]
            frame_size = frame.get_size()
            frame_converter = SWScale(frame_size[0], frame_size[1], frame.get_pixel_format(), ofmt='rgb24')
            new_frame = frame_converter.scale(frame)
            image_data = bytes(new_frame.to_bytearray()[0])

            original_image = Image.frombuffer(mode='RGB', size=(frame_size[0], frame_size[1]), data=image_data, decoder_name='raw')
            self.original_width = original_image.size[0]
            self.original_height = original_image.size[1]
            image = original_image.copy()

        else:
            original_image = Image.open(self.source)
            if self.angle != 0:
                if self.angle == 90:
                    original_image = original_image.transpose(PIL.Image.ROTATE_90)
                if self.angle == 180:
                    original_image = original_image.transpose(PIL.Image.ROTATE_180)
                if self.angle == 270:
                    original_image = original_image.transpose(PIL.Image.ROTATE_270)
            self.original_width = original_image.size[0]
            self.original_height = original_image.size[1]
            image = original_image.copy()
            self.original_image = original_image.copy()
            original_image.close()
        width = int(self.width)
        height = int(self.width*(image.size[1]/image.size[0]))
        if width < 10:
            width = 10
        if height < 10:
            height = 10
        image = image.resize((width, height))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        self.size_multiple = self.original_width / image.size[0]
        self.edit_image = image
        self.histogram = image.histogram()

    def on_texture(self, instance, value):
        if value is not None:
            self.texture_size = list(value.size)
        if self.mirror:
            self.texture.flip_horizontal()

    def denoise_preview(self, width, height, pos_x, pos_y):
        left = pos_x
        right = pos_x + width
        lower = pos_y + width
        upper = pos_y
        preview = self.original_image.crop(box=(left, upper, right, lower))
        if preview.mode != 'RGB':
            preview = preview.convert('RGB')
        preview_cv = cv2.cvtColor(numpy.array(preview), cv2.COLOR_RGB2BGR)
        preview_cv = cv2.fastNlMeansDenoisingColored(preview_cv, None, self.luminance_denoise, self.color_denoise, self.search_window, self.block_size)
        preview_cv = cv2.cvtColor(preview_cv, cv2.COLOR_BGR2RGB)
        preview = Image.fromarray(preview_cv)
        preview_bytes = BytesIO()
        preview.save(preview_bytes, 'jpeg')
        preview_bytes.seek(0)
        return preview_bytes

    def update_preview(self, denoise=False, recrop=True):
        """Update the preview image."""

        image = self.adjust_image(self.edit_image)
        if denoise and opencv:
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            open_cv_image = cv2.fastNlMeansDenoisingColored(open_cv_image, None, self.luminance_denoise, self.color_denoise, self.search_window, self.block_size)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(open_cv_image)

        self.update_texture(image)
        self.histogram = image.histogram()
        if recrop:
            self.reset_cropper(setup=True)

    def adjust_image(self, image, preview=True):
        """Applies all current editing opterations to an image.
        Arguments:
            image: A PIL image.
            preview: Generate edit image in preview mode (faster)
        Returns: A PIL image.
        """

        if not preview:
            orientation = self.photoinfo[13]
            if orientation == 3 or orientation == 4:
                image = image.transpose(PIL.Image.ROTATE_180)
            elif orientation == 5 or orientation == 6:
                image = image.transpose(PIL.Image.ROTATE_90)
            elif orientation == 7 or orientation == 8:
                image = image.transpose(PIL.Image.ROTATE_270)
            if orientation in [2, 4, 5, 7]:
                image = image.transpose(PIL.Image.FLIP_LEFT_RIGHT)
            size_multiple = self.size_multiple
        else:
            size_multiple = 1
        #for some reason, video frames are read upside-down? fix it here...
        if self.video:
            image = image.transpose(PIL.Image.FLIP_TOP_BOTTOM)

        if self.sharpen != 0:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(self.sharpen+1)
        if self.median_blur != 0 and opencv:
            max_median = 10 * size_multiple
            median = int(self.median_blur * max_median)
            if median % 2 == 0:
                median = median + 1
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            open_cv_image = cv2.medianBlur(open_cv_image, median)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(open_cv_image)
        if self.bilateral != 0 and self.bilateral_amount != 0 and opencv:
            diameter = int(self.bilateral * 10 * size_multiple)
            sigma_color = self.bilateral_amount * 100 * size_multiple
            sigma_space = sigma_color
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            open_cv_image = cv2.bilateralFilter(open_cv_image, diameter, sigma_color, sigma_space)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(open_cv_image)
        if self.vignette_amount > 0 and self.vignette_size > 0:
            vignette = Image.new(mode='RGB', size=image.size, color=(0, 0, 0))
            filter_color = int((1-self.vignette_amount)*255)
            vignette_mixer = Image.new(mode='L', size=image.size, color=filter_color)
            draw = ImageDraw.Draw(vignette_mixer)
            shrink_x = int((self.vignette_size * (image.size[0]/2)) - (image.size[0]/4))
            shrink_y = int((self.vignette_size * (image.size[1]/2)) - (image.size[1]/4))
            draw.ellipse([0+shrink_x, 0+shrink_y, image.size[0]-shrink_x, image.size[1]-shrink_y], fill=255)
            vignette_mixer = vignette_mixer.filter(ImageFilter.GaussianBlur(radius=(self.vignette_amount*60)+60))
            image = Image.composite(image, vignette, vignette_mixer)
        if self.edge_blur_amount > 0 and self.edge_blur_intensity > 0 and self.edge_blur_size > 0:
            blur_image = image.filter(ImageFilter.GaussianBlur(radius=(self.edge_blur_amount*30)))
            filter_color = int((1-self.edge_blur_intensity)*255)
            blur_mixer = Image.new(mode='L', size=image.size, color=filter_color)
            draw = ImageDraw.Draw(blur_mixer)
            shrink_x = int((self.edge_blur_size * (image.size[0]/2)) - (image.size[0]/4))
            shrink_y = int((self.edge_blur_size * (image.size[1]/2)) - (image.size[1]/4))
            draw.ellipse([0+shrink_x, 0+shrink_y, image.size[0]-shrink_x, image.size[1]-shrink_y], fill=255)
            blur_mixer = blur_mixer.filter(ImageFilter.GaussianBlur(radius=(self.edge_blur_amount*30)))
            image = Image.composite(image, blur_image, blur_mixer)
        if self.crop_top != 0 or self.crop_bottom != 0 or self.crop_left != 0 or self.crop_right != 0:
            if preview:
                overlay = Image.new(mode='RGB', size=image.size, color=(0, 0, 0))
                divisor = self.original_width / image.size[0]
                draw = ImageDraw.Draw(overlay)
                draw.rectangle([0, 0, (self.crop_left / divisor), image.size[1]], fill=(255, 255, 255))
                draw.rectangle([0, 0, image.size[0], (self.crop_top / divisor)], fill=(255, 255, 255))
                draw.rectangle([(image.size[0] - (self.crop_right / divisor)), 0, (image.size[0]), image.size[1]],
                               fill=(255, 255, 255))
                draw.rectangle([0, (image.size[1] - (self.crop_bottom / divisor)), image.size[0], image.size[1]],
                               fill=(255, 255, 255))
                bright = ImageEnhance.Brightness(overlay)
                overlay = bright.enhance(.333)
                image = ImageChops.subtract(image, overlay)
            else:
                if self.crop_left >= image.size[0]:
                    crop_left = 0
                else:
                    crop_left = self.crop_left
                if self.crop_top >= image.size[1]:
                    crop_top = 0
                else:
                    crop_top = self.crop_top
                if self.crop_right >= image.size[0]:
                    crop_right = image.size[0]
                else:
                    crop_right = image.size[0] - self.crop_right
                if self.crop_bottom >= image.size[1]:
                    crop_bottom = image.size[1]
                else:
                    crop_bottom = image.size[1] - self.crop_bottom
                image = image.crop((int(crop_left), int(crop_top), int(crop_right), int(crop_bottom)))
        if self.flip_horizontal:
            image = image.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        if self.flip_vertical:
            image = image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
        if self.rotate_angle != 0:
            if self.rotate_angle == 90:
                image = image.transpose(PIL.Image.ROTATE_270)
            if self.rotate_angle == 180:
                image = image.transpose(PIL.Image.ROTATE_180)
            if self.rotate_angle == 270:
                image = image.transpose(PIL.Image.ROTATE_90)
        if self.fine_angle != 0:
            total_angle = -self.fine_angle*10
            angle_radians = math.radians(abs(total_angle))
            width, height = rotated_rect_with_max_area(image.size[0], image.size[1], angle_radians)
            x = int((image.size[0] - width) / 2)
            y = int((image.size[1] - height) / 2)
            if preview:
                image = image.rotate(total_angle, expand=False)
            else:
                image = image.rotate(total_angle, resample=PIL.Image.BICUBIC, expand=False)
            image = image.crop((x, y, image.size[0] - x, image.size[1] - y))
        if self.autocontrast:
            image = ImageOps.autocontrast(image)
        if self.equalize != 0:
            equalize_image = ImageOps.equalize(image)
            image = Image.blend(image, equalize_image, self.equalize)
        temperature = int(round(abs(self.temperature)*100))
        if temperature != 0:
            temperature = temperature-1
            if self.temperature > 0:
                kelvin = negative_kelvin[99-temperature]
            else:
                kelvin = positive_kelvin[temperature]
            matrix = ((kelvin[0]/255.0), 0.0, 0.0, 0.0,
                      0.0, (kelvin[1]/255.0), 0.0, 0.0,
                      0.0, 0.0, (kelvin[2]/255.0), 0.0)
            image = image.convert('RGB', matrix)
        if self.brightness != 0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1+self.brightness)
        if self.shadow != 0:
            if self.shadow < 0:
                floor = int(abs(self.shadow) * 128)
                table = [0] * floor
                remaining_length = 256 - floor
                for index in range(0, remaining_length):
                    value = int(round((index / remaining_length) * 256))
                    table.append(value)
                lut = table * 3
            else:
                floor = int(abs(self.shadow) * 128)
                table = []
                for index in range(0, 256):
                    percent = 1 - (index / 255)
                    value = int(round(index + (floor * percent)))
                    table.append(value)
                lut = table * 3
            image = image.point(lut)

        if self.gamma != 0:
            if self.gamma == -1:
                gamma = 99999999999999999
            elif self.gamma < 0:
                gamma = 1/(self.gamma+1)
            elif self.gamma > 0:
                gamma = 1/((self.gamma+1)*(self.gamma+1))
            else:
                gamma = 1
            lut = [pow(x/255, gamma) * 255 for x in range(256)]
            lut = lut*3
            image = image.point(lut)
        if self.contrast != 0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1 + self.contrast)
        if self.saturation != 0:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1+self.saturation)
        if self.tint != [1.0, 1.0, 1.0, 1.0]:
            matrix = (self.tint[0], 0.0, 0.0, 0.0,
                      0.0, self.tint[1], 0.0, 0.0,
                      0.0, 0.0, self.tint[2], 0.0)
            image = image.convert('RGB', matrix)
        if self.curve:
            lut = self.curve*3
            image = image.point(lut)

        if self.denoise and not preview and opencv:
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            open_cv_image = cv2.fastNlMeansDenoisingColored(open_cv_image, None, self.luminance_denoise, self.color_denoise, self.search_window, self.block_size)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(open_cv_image)

        if self.adaptive_clip > 0 and opencv:
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2Lab)
            channels = cv2.split(open_cv_image)
            clahe = cv2.createCLAHE(clipLimit=(self.adaptive_clip * 4), tileGridSize=(8, 8))
            clahe_image = clahe.apply(channels[0])
            channels[0] = clahe_image
            open_cv_image = cv2.merge(channels)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_Lab2RGB)
            image = Image.fromarray(open_cv_image)

        if self.border_image:
            image_aspect = image.size[0]/image.size[1]
            closest_aspect = min(self.border_image[1], key=lambda x: abs(x-image_aspect))
            index = self.border_image[1].index(closest_aspect)
            image_file = os.path.join('borders', self.border_image[2][index])
            if preview:
                resample = PIL.Image.NEAREST
            else:
                resample = PIL.Image.BICUBIC
            border_image = Image.open(image_file)
            border_crop_x = int(border_image.size[0] * ((self.border_x_scale + 1) / 15))
            border_crop_y = int(border_image.size[1] * ((self.border_y_scale + 1) / 15))
            border_image = border_image.crop((border_crop_x, border_crop_y, border_image.size[0] - border_crop_x,
                                              border_image.size[1] - border_crop_y))
            border_image = border_image.resize(image.size, resample)

            if os.path.splitext(image_file)[1].lower() == '.jpg':
                alpha_file = os.path.splitext(image_file)[0]+'-mask.jpg'
                if not os.path.exists(alpha_file):
                    alpha_file = image_file
                alpha = Image.open(alpha_file)
                alpha = alpha.convert('L')
                alpha = alpha.crop((border_crop_x, border_crop_y, alpha.size[0] - border_crop_x,
                                    alpha.size[1] - border_crop_y))
                alpha = alpha.resize(image.size, resample)
            else:
                alpha = border_image.split()[-1]
                border_image = border_image.convert('RGB')
            if self.border_tint != [1.0, 1.0, 1.0, 1.0]:
                matrix = (self.border_tint[0], 0.0, 0.0, 1.0,
                          0.0, self.border_tint[1], 0.0, 1.0,
                          0.0, 0.0, self.border_tint[2], 1.0)
                border_image = border_image.convert('RGB', matrix)

            enhancer = ImageEnhance.Brightness(alpha)
            alpha = enhancer.enhance(self.border_opacity)
            image = Image.composite(border_image, image, alpha)

        return image

    def update_texture(self, image):
        """Saves a PIL image to the visible texture.
        Argument:
            image: A PIL image
        """

        image_bytes = BytesIO()
        image.save(image_bytes, 'jpeg')
        image_bytes.seek(0)
        self._coreimage = CoreImage(image_bytes, ext='jpg')
        self._on_tex_change()

    def get_full_quality(self):
        """Generate a full sized and full quality version of the source image.
        Returns: A PIL image.
        """

        image = self.original_image.copy()
        if not self.video:
            if self.angle != 0:
                if self.angle == 90:
                    image = image.transpose(PIL.Image.ROTATE_90)
                if self.angle == 180:
                    image = image.transpose(PIL.Image.ROTATE_180)
                if self.angle == 270:
                    image = image.transpose(PIL.Image.ROTATE_270)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image = self.adjust_image(image, preview=False)
        return image


class AsyncThumbnail(KivyImage):
    """AsyncThumbnail is a modified version of the kivy AsyncImage class,
    used to automatically generate and save thumbnails of a specified image.
    """

    loadfullsize = BooleanProperty(False)  #Enable loading the full-sized image, thumbnail will be displayed temporarily
    temporary = BooleanProperty(False)  #This image is a temporary file, not in the database
    photoinfo = ListProperty()  #Photo data of the image
    mirror = BooleanProperty(False)
    loadanyway = BooleanProperty(False)  #Force generating thumbnail even if this widget isnt added to a parent widget
    thumbsize = None
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        self._coreimage = None
        self._fullimage = None
        super(AsyncThumbnail, self).__init__(**kwargs)
        self.bind(source=self._load_source)
        if self.source:
            self._load_source()

    def load_thumbnail(self, filename):
        """Load from thumbnail database, or generate a new thumbnail of the given image filename.
        Argument:
            filename: Image filename.
        Returns: A Kivy image"""

        #i dont think this is needed anymore, i hope...
        #root_widget = self.parent.parent.parent.parent
        root_widget = True
        if root_widget or self.loadanyway:
            app = App.get_running_app()
            full_filename = filename
            photo = self.photoinfo

            file_found = isfile2(full_filename)
            if file_found:
                modified_date = int(os.path.getmtime(full_filename))
                if modified_date > photo[7]:
                    #if not self.temporary:
                    #    app.database_item_update(photo)
                    #    app.update_photoinfo(folders=[photo[1]])
                    app.database_thumbnail_update(photo[0], photo[2], modified_date, photo[13],
                                                  temporary=self.temporary)
            thumbnail_image = app.database_thumbnail_get(photo[0], temporary=self.temporary)
            if thumbnail_image:
                imagedata = bytes(thumbnail_image[2])
                data = BytesIO()
                data.write(imagedata)
                data.seek(0)
                image = CoreImage(data, ext='jpg')
            else:
                if file_found:
                    updated = app.database_thumbnail_update(photo[0], photo[2], modified_date, photo[13],
                                                            temporary=self.temporary)
                    if updated:
                        thumbnail_image = app.database_thumbnail_get(photo[0], temporary=self.temporary)
                        data = BytesIO(thumbnail_image[2])
                        image = CoreImage(data, ext='jpg')
                    else:
                        image = ImageLoader.load(full_filename)
                else:
                    image = ImageLoader.load('data/null.jpg')
            return image
        else:
            return ImageLoader.load('data/null.jpg')

    def set_angle(self):
        orientation = self.photoinfo[13]
        if orientation in [2, 4, 5, 7]:
            self.mirror = True
        else:
            self.mirror = False
        if self.mirror:
            self.texture.flip_horizontal()

        if orientation == 3 or orientation == 4:
            self.angle = 180
        elif orientation == 5 or orientation == 6:
            self.angle = 270
        elif orientation == 7 or orientation == 8:
            self.angle = 90
        else:
            self.angle = 0

    def _load_source(self, *_):
        self.set_angle()
        source = self.source
        photo = self.photoinfo
        self.nocache = True
        if not source and not photo:
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            self.texture = None
            self._coreimage = None
        elif not photo:
            Clock.schedule_once(lambda *dt: self._load_source(), .25)
        else:
            ThumbLoader.max_upload_per_frame = 50
            ThumbLoader.num_workers = 4
            ThumbLoader.loading_image = 'data/loadingthumbnail.png'
            self._coreimage = image = ThumbLoader.image(source, load_callback=self.load_thumbnail, nocache=self.nocache,
                                                        mipmap=self.mipmap, anim_delay=self.anim_delay)
            image.bind(on_load=self._on_source_load)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

    def _on_source_load(self, *_):
        image = self._coreimage.image
        if not image:
            return
        self.thumbsize = image.size
        self.texture = image.texture

        if self.loadfullsize:
            Cache.remove('kv.image', self.source)
            try:
                self._coreimage.image.remove_from_cache()
                self._coreimage.remove_from_cache()
            except:
                pass
            Clock.schedule_once(lambda dt: self._load_fullsize())

    def _load_fullsize(self):
        app = App.get_running_app()
        low_memory = to_bool(app.config.get("Settings", "lowmem"))
        if not low_memory:
            if os.path.splitext(self.source)[1].lower() == '.bmp':
                #default image loader messes up bmp files, use pil instead
                self._coreimage = ImageLoaderPIL(self.source)
            else:
                self._coreimage = KivyImage(source=self.source)
        else:
            #load and rescale image
            original_image = Image.open(self.source)
            image = original_image.copy()
            original_image.close()
            resize_width = Window.size[0]
            if image.size[0] > resize_width:
                width = int(resize_width)
                height = int(resize_width * (image.size[1] / image.size[0]))
                if width < 10:
                    width = 10
                if height < 10:
                    height = 10
                image = image.resize((width, height))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image_bytes = BytesIO()
            image.save(image_bytes, 'jpeg')
            image_bytes.seek(0)
            self._coreimage = CoreImage(image_bytes, ext='jpg')

        self.texture = self._coreimage.texture
        if self.mirror:
            self.texture.flip_horizontal()

    def _on_tex_change(self, *largs):
        if self._coreimage:
            self.texture = self._coreimage.texture

    def texture_update(self, *largs):
        pass


class DenoisePreview(RelativeLayout):
    finished = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_finished')
        super(DenoisePreview, self).__init__(**kwargs)

    def on_finished(self, *_):
        print('on finished')
        self.root.update_preview()


class ScrollViewCentered(ScrollView):
    """Special ScrollView that begins centered"""

    def __init__(self, **kwargs):
        self.scroll_x = 0.5
        self.scroll_y = 0.5
        super(ScrollViewCentered, self).__init__(**kwargs)

    def window_to_parent(self, x, y, relative=False):
        return self.to_parent(*self.to_widget(x, y))


class VideoThumbnail(FloatLayout):
    source = ObjectProperty(None)
    video = ObjectProperty(None)
    click_done = BooleanProperty(False)
    photoinfo = ListProperty()
    favorite = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.click_done:
            self.click_done = True
            self.video.state = 'play'
        return True


class Scroller(ScrollView):
    """Generic scroller container widget."""
    pass


class ScrollerContainer(Scroller):
    def on_touch_down(self, touch):
        #Modified to allow one sub object to not be scrolled
        try:
            subscroller = self.children[0].children[0].ids['wrapper']
            coords = subscroller.window_to_parent(*touch.pos)
            collide = subscroller.collide_point(*coords)
            if collide:
                touch.apply_transform_2d(subscroller.window_to_parent)
                subscroller.on_touch_down(touch)
                return True
        except:
            pass
        super(ScrollerContainer, self).on_touch_down(touch)


class AlbumDetails(BoxLayout):
    """Widget to display information about an album"""

    owner = ObjectProperty()


class FolderDetails(BoxLayout):
    """Widget to display information about a folder of photos"""

    owner = ObjectProperty()


class NormalDropDown(DropDown):
    """Base dropdown menu class."""
    pass


class DatabaseSortDropDown(NormalDropDown):
    """Drop-down menu for database folder sorting"""
    pass


class AlbumSortDropDown(NormalDropDown):
    """Drop-down menu for sorting album elements"""
    pass


class AspectRatioDropDown(NormalDropDown):
    """Drop-down menu for sorting aspect ratio presets"""
    pass


class InterpolationDropDown(NormalDropDown):
    """Drop-down menu for curves interpolation options"""
    pass


class SplitterPanel(Splitter):
    """Base class for the left and right adjustable panels"""
    pass


class SplitterPanelLeft(SplitterPanel):
    """Left-side adjustable width panel."""
    hidden = BooleanProperty(False)
    display_width = NumericProperty(0)

    def __init__(self, **kwargs):
        app = App.get_running_app()
        self.display_width = app.left_panel_width()
        super(SplitterPanelLeft, self).__init__(**kwargs)

    def on_hidden(self, *_):
        if self.hidden:
            self.width = 0
        else:
            app = App.get_running_app()
            self.display_width = app.left_panel_width()
            self.width = self.display_width

    def on_width(self, instance, width):
        """When the width of the panel is changed, save to the app settings."""

        del instance
        if width > 0:
            app = App.get_running_app()
            widthpercent = (width/Window.width)
            app.config.set('Settings', 'leftpanel', widthpercent)
        if self.hidden:
            self.width = 0


class SplitterPanelRight(SplitterPanel):
    """Right-side adjustable width panel."""
    hidden = BooleanProperty(True)
    display_width = NumericProperty(0)

    def __init__(self, **kwargs):
        app = App.get_running_app()
        self.display_width = app.right_panel_width()
        super(SplitterPanelRight, self).__init__(**kwargs)

    def on_hidden(self, *_):
        if self.hidden:
            self.width = 0
        else:
            app = App.get_running_app()
            self.display_width = app.right_panel_width()
            self.width = self.display_width

    def on_width(self, instance, width):
        """When the width of the panel is changed, save to the app settings."""

        del instance
        if width > 0:
            app = App.get_running_app()
            widthpercent = (width/Window.width)
            app.config.set('Settings', 'rightpanel', widthpercent)
        if self.hidden:
            self.width = 0


class MessagePopup(GridLayout):
    """Basic popup message with a message and 'ok' button."""

    button_text = StringProperty('OK')
    text = StringProperty()

    def close(self, *_):
        app = App.get_running_app()
        app.popup.dismiss()


class AboutPopup(Popup):
    """Basic popup message with a message and 'ok' button."""

    button_text = StringProperty('OK')

    def close(self, *_):
        app = App.get_running_app()
        app.popup.dismiss()


class InputPopup(GridLayout):
    """Basic text input popup message.  Calls 'on_answer' when either button is clicked."""

    input_text = StringProperty()
    text = StringProperty()  #Text that the user has input
    hint = StringProperty()  #Grayed-out hint text in the input field

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(InputPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class InputPopupTag(GridLayout):
    """Basic text input popup message.  Calls 'on_answer' when either button is clicked."""

    input_text = StringProperty()
    text = StringProperty()  #Text that the user has input
    hint = StringProperty()  #Grayed-out hint text in the input field

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(InputPopupTag, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class ConfirmPopup(GridLayout):
    """Basic Yes/No popup message.  Calls 'on_answer' when either button is clicked."""

    text = StringProperty()
    yes_text = StringProperty('Yes')
    no_text = StringProperty('No')
    warn_yes = BooleanProperty(False)
    warn_no = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class RemoveButton(NormalButton):
    """Base class for a button to remove an item from a list."""

    remove = True
    to_remove = StringProperty()
    remove_from = StringProperty()
    owner = ObjectProperty()


class RemoveProgramButton(RemoveButton):
    """Button to remove a program from the external programs list."""

    def on_press(self):
        app = App.get_running_app()
        app.program_remove(int(self.to_remove))
        self.owner.update_programs()


class HiddenRemoveTagButton(ShortLabel):
    """Dummy remove tag button, used specifically for the 'favorite' tag that cannot be removed."""

    remove = True
    to_remove = StringProperty()
    remove_from = StringProperty()
    owner = ObjectProperty()


class RemoveTagButton(RemoveButton):
    """Button to remove a tag from the tags list.  Will popup a confirm dialog before removing."""

    def on_press(self):
        app = App.get_running_app()
        content = ConfirmPopup(text='Delete The Tag "'+self.to_remove+'"?', yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        content.bind(on_answer=self.on_answer)
        self.owner.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None),
                                       size=(app.popup_x, app.button_scale * 4),
                                       auto_dismiss=False)
        self.owner.popup.open()

    def on_answer(self, instance, answer):
        del instance
        if answer == 'yes':
            app = App.get_running_app()
            app.remove_tag(self.to_remove)
            self.owner.update_treeview()
        self.owner.dismiss_popup()


class RemoveFromTagButton(RemoveButton):
    """Button to remove a tag from the current photo."""

    def on_press(self):
        app = App.get_running_app()
        app.database_remove_tag(self.remove_from, self.to_remove, message=True)
        self.owner.update_treeview()


class RemoveAlbumButton(RemoveButton):
    """Button to remove an album.  Pops up a confirmation dialog."""

    def on_press(self):
        app = App.get_running_app()
        content = ConfirmPopup(text='Delete The Album "'+self.to_remove+'"?', yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        content.bind(on_answer=self.on_answer)
        self.owner.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None),
                                       size=(app.popup_x, app.button_scale * 4),
                                       auto_dismiss=False)
        self.owner.popup.open()

    def on_answer(self, instance, answer):
        del instance
        if answer == 'yes':
            app = App.get_running_app()
            index = app.album_find(self.to_remove)
            if index >= 0:
                app.album_delete(index)
            self.owner.update_treeview()
        self.owner.dismiss_popup()


class PhotoRecycleViewButton(RecycleItem):
    video = BooleanProperty(False)
    favorite = BooleanProperty(False)
    fullpath = StringProperty()
    photoinfo = ListProperty()
    source = StringProperty()
    selectable = BooleanProperty(True)
    found = BooleanProperty(True)

    def on_source(self, *_):
        """Sets up the display image when first loaded."""

        found = isfile2(self.source)
        self.found = found

    def refresh_view_attrs(self, rv, index, data):
        super(PhotoRecycleViewButton, self).refresh_view_attrs(rv, index, data)
        thumbnail = self.ids['thumbnail']
        thumbnail.photoinfo = self.data['photoinfo']
        thumbnail.source = self.data['source']

    def on_touch_down(self, touch):
        super(PhotoRecycleViewButton, self).on_touch_down(touch)
        if self.collide_point(*touch.pos) and self.selectable:
            self.owner.fullpath = self.fullpath
            self.owner.photo = self.source
            self.parent.selected = self.data
            return True


class TreenodeDrag(BoxLayout):
    """Widget that looks like a treenode thumbnail, used for showing the position of the drag-n-drop."""

    fullpath = StringProperty()
    text = StringProperty()
    subtext = StringProperty()


class RecycleTreeViewButton(ButtonBehavior, RecycleItem):
    """Widget that displays a specific folder, album, or tag in the database treeview.
    Responds to clicks and double-clicks.
    """

    displayable = BooleanProperty(True)
    target = StringProperty()  #Folder, Album, or Tag
    fullpath = StringProperty()  #Folder name, used only on folder type targets
    folder = StringProperty()
    database_folder = StringProperty()
    type = StringProperty()  #The type the target is: folder, album, tag, extra
    total_photos = StringProperty()
    folder_name = StringProperty()
    subtext = StringProperty()
    total_photos_numeric = NumericProperty(0)
    drag = False
    dragable = BooleanProperty(False)
    droptype = StringProperty('folder')
    indent = NumericProperty(0)
    expanded = BooleanProperty(True)
    expandable = BooleanProperty(False)
    end = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        """Called when widget is loaded into recycleview layout"""

        app = App.get_running_app()
        self.total_photos_numeric = 0
        if data['displayable']:
            photo_type = data['type']
            if photo_type == 'Folder':
                fullpath = data['fullpath']
                if fullpath:
                    photos = app.database_get_folder(data['fullpath'])
                    self.total_photos_numeric = len(photos)
            elif photo_type == 'Album':
                for album in app.albums:
                    if album['name'] == data['target']:
                        self.total_photos_numeric = len(album['photos'])
                        break
            elif photo_type == 'Tag':
                photos = app.database_get_tag(data['target'])
                self.total_photos_numeric = len(photos)
        if self.total_photos_numeric > 0:
            self.total_photos = '(' + str(self.total_photos_numeric) + ')'
        else:
            self.total_photos = ''
        self.ids['mainText'].text = data['folder_name'] + '   [b]' + self.total_photos + '[/b]'
        return super(RecycleTreeViewButton, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                if self.displayable:
                    if self.total_photos_numeric > 0:
                        app = App.get_running_app()
                        if not app.shift_pressed:
                            app.show_album(self)
            else:
                self.parent.selected = {}
                self.parent.selected = self.data
                self.on_press()
            if self.dragable:
                self.drag = True
                app = App.get_running_app()
                temp_coords = self.to_parent(touch.opos[0], touch.opos[1])
                widget_coords = (temp_coords[0]-self.pos[0], temp_coords[1]-self.pos[1])
                window_coords = self.to_window(touch.opos[0], touch.opos[1])
                app.drag_treeview(self, 'start', window_coords, offset=widget_coords)

    def on_press(self):
        self.owner.type = self.type
        self.owner.displayable = self.displayable
        #self.owner.set_selected(self.target)
        self.owner.selected = ''
        self.owner.selected = self.target

    def on_release(self):
        if self.expandable:
            if self.type == 'Album':
                self.owner.expanded_albums = not self.owner.expanded_albums
            elif self.type == 'Tag':
                self.owner.expanded_tags = not self.owner.expanded_tags
            elif self.type == 'Folder':
                self.owner.toggle_expanded_folder(self.target)
            self.owner.update_treeview()

    def on_touch_move(self, touch):
        if self.drag:
            delay = time.time() - touch.time_start
            if delay >= drag_delay:
                app = App.get_running_app()
                window_coords = self.to_window(touch.pos[0], touch.pos[1])
                app.drag_treeview(self, 'move', window_coords)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.collide_point(*touch.opos):
            self.on_release()
        if self.drag:
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag_treeview(self, 'end', window_coords)
            self.drag = False


class TreeViewButton(ButtonBehavior, BoxLayout, TreeViewNode):
    """Widget that displays a specific folder, album, or tag in the database treeview.
    Responds to clicks and double-clicks.
    """

    displayable = BooleanProperty(True)
    target = StringProperty()  #Folder, Album, or Tag
    fullpath = StringProperty()  #Folder name, used only on folder type targets
    folder = StringProperty()
    database_folder = StringProperty()
    type = StringProperty()  #The type the target is: folder, album, tag, extra
    total_photos = StringProperty()
    folder_name = StringProperty()
    subtext = StringProperty()
    total_photos_numeric = NumericProperty(0)
    view_album = BooleanProperty(True)
    drag = False
    dragable = BooleanProperty(False)
    owner = ObjectProperty()
    droptype = StringProperty('folder')

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                if self.view_album:
                    if self.total_photos_numeric > 0:
                        app = App.get_running_app()
                        if not app.shift_pressed:
                            app.show_album(self)
            else:
                self.on_press()
            if self.dragable:
                self.drag = True
                app = App.get_running_app()
                temp_coords = self.to_parent(touch.opos[0], touch.opos[1])
                widget_coords = (temp_coords[0]-self.pos[0], temp_coords[1]-self.pos[1])
                window_coords = self.to_window(touch.opos[0], touch.opos[1])
                app.drag_treeview(self, 'start', window_coords, offset=widget_coords)

    def on_press(self):
        self.owner.type = self.type
        self.owner.displayable = self.displayable
        self.owner.selected = ''
        self.owner.selected = self.target

    def on_release(self):
        if self.dragable:
            try:
                self.parent.toggle_node(self)
            except:
                pass

    def on_touch_move(self, touch):
        if self.drag:
            delay = time.time() - touch.time_start
            if delay >= drag_delay:
                app = App.get_running_app()
                window_coords = self.to_window(touch.pos[0], touch.pos[1])
                app.drag_treeview(self, 'move', window_coords)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.on_release()
        if self.drag:
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag_treeview(self, 'end', window_coords)
            self.drag = False


class TreeViewInfo(BoxLayout, TreeViewNode):
    """Simple treeview node to display a line of text.
    Has two elements, they will be shown as: 'title: content'"""

    title = StringProperty()
    content = StringProperty()


class ExternalProgramEditor(GridLayout):
    """Widget to display and edit an external program command."""

    name = StringProperty()  #Command name
    command = StringProperty()  #Command to run
    argument = StringProperty()  #Command argument, added to the end of 'command'
    owner = ObjectProperty()
    index = NumericProperty()

    def save_program(self):
        self.owner.save_program(self.index, self.name, self.command, self.argument)

    def set_name(self, instance):
        if not instance.focus:
            self.name = instance.text
            self.save_program()

    def set_argument(self, instance):
        if not instance.focus:
            self.argument = instance.text
            self.save_program()

    def select_command(self):
        """Opens a popup filebrowser to select a program to run."""

        content = FileBrowser(ok_text='Select', filters=['*'])
        content.bind(on_cancel=lambda x: self.owner.owner.dismiss_popup())
        content.bind(on_ok=self.select_command_confirm)
        self.owner.owner.popup = filepopup = NormalPopup(title='Select A Program', content=content,
                                                         size_hint=(0.9, 0.9))
        filepopup.open()

    def select_command_confirm(self, *_):
        """Called when the filebrowser dialog is successfully closed."""

        self.command = self.owner.owner.popup.content.filename
        self.owner.owner.dismiss_popup()
        self.save_program()


class ExpandableButton(GridLayout):
    """Base class for a button with a checkbox to enable/disable an extra area.
    It also features an 'x' remove button that calls 'on_remove' when clicked."""

    text = StringProperty()  #Text shown in the main button area
    expanded = BooleanProperty(False)  #Determines if the expanded area is displayed
    content = ObjectProperty()  #Widget to be displayed when expanded is enabled
    index = NumericProperty()  #The button's index in the list - useful for the remove function

    def __init__(self, **kwargs):
        super(ExpandableButton, self).__init__(**kwargs)
        self.register_event_type('on_press')
        self.register_event_type('on_expanded')
        self.register_event_type('on_remove')

    def set_expanded(self, expanded):
        self.expanded = expanded

    def on_expanded(self, *_):
        if self.content:
            content_container = self.ids['contentContainer']
            if self.expanded:
                content_container.add_widget(self.content)
            else:
                content_container.clear_widgets()

    def on_press(self):
        pass

    def on_remove(self):
        pass


class TagSelectButton(WideButton):
    """Tag display button - used for adding a tag to a photo"""

    remove = False
    target = StringProperty()
    type = StringProperty('None')
    owner = ObjectProperty()

    def on_press(self):
        self.owner.add_to_tag(self.target)


class AlbumSelectButton(WideButton):
    """Album display button - used for adding a photo to an album."""

    remove = False
    target = StringProperty()
    type = StringProperty('None')
    owner = ObjectProperty()

    def on_press(self):
        self.owner.add_to_album(self.target)


class MultiTreeView(TreeView):
    def toggle_select(self):
        deselect = False
        for node in self.iterate_all_nodes():
            if node.is_selected:
                deselect = True
                node.is_selected = False
        if not deselect:
            for node in self.iterate_all_nodes():
                node.is_selected = True

    def select_node(self, node):
        """Modified to allow multiple nodes to be selected and toggled"""

        if node.no_selection:
            return
        if node.is_selected:
            node.is_selected = False
        else:
            node.is_selected = True
            app = App.get_running_app()
            if app.shift_pressed:
                #find the closest selected node
                nodes = list(self.iterate_all_nodes())
                node_index = nodes.index(node)
                next_select = node_index
                prev_select = node_index
                while next_select < len(nodes) - 1:
                    next_select = next_select + 1
                    if nodes[next_select].is_selected:
                        break
                while prev_select > 0:
                    prev_select = prev_select - 1
                    if nodes[prev_select].is_selected:
                        break
                next_delta = next_select - node_index
                prev_delta = node_index - prev_select
                if next_select == len(nodes) - 1 and prev_select != 0:
                    next_delta = len(nodes)
                if prev_select == 0 and next_select != len(nodes) - 1:
                    prev_delta = len(nodes)
                if prev_delta < next_delta:
                    #select between node and previous selected
                    for index in range(prev_select, node_index):
                        nodes[index].is_selected = True
                else:
                    #select between node and next selected
                    for index in range(node_index, next_select+1):
                        nodes[index].is_selected = True

        self._selected_node = node


class NormalRecycleView(RecycleView):
    def get_selected(self):
        selected = []
        for item in self.data:
            if item['selected']:
                selected.append(item)
        return selected


class SelectableRecycleGrid(LayoutSelectionBehavior, RecycleGridLayout):
    """Custom selectable grid layout widget."""

    def __init__(self, **kwargs):
        """ Use the initialize method to bind to the keyboard to enable
        keyboard interaction e.g. using shift and control for multi-select.
        """

        super(SelectableRecycleGrid, self).__init__(**kwargs)
        if str(platform) in ('linux', 'win', 'macosx'):
            keyboard = Window.request_keyboard(None, self)
            keyboard.bind(on_key_down=self.select_with_key_down, on_key_up=self.select_with_key_up)

    def select_all(self):
        for node in range(0, len(self.parent.data)):
            self.select_node(node)

    def select_with_touch(self, node, touch=None):
        self._shift_down = False
        super(SelectableRecycleGrid, self).select_with_touch(node, touch)

    def _select_range(self, multiselect, keep_anchor, node, idx):
        pass

    def select_range(self, select_index, touch):
        #find the closest selected button

        if self.selected_nodes:
            selected_nodes = self.selected_nodes
        else:
            selected_nodes = [0, len(self.parent.data)]
        closest_node = min(selected_nodes, key=lambda x: abs(x-select_index))

        for index in range(min(select_index, closest_node), max(select_index, closest_node)+1):
            self.select_node(index)


class NormalLabel(Label):
    """Basic label widget"""
    pass


class ShortLabel(NormalLabel):
    """Label widget that will remain the minimum width"""
    pass


class MenuButton(Button):
    """Basic class for a drop-down menu button item."""
    pass


class FolderSettingsItem(RecycleItem):
    """A Folder item displayed in a folder list popup dialog."""
    pass


class FolderSettingsList(RecycleView):
    pass


class SettingAboutButton(SettingItem):
    """Widget that opens an about dialog."""
    pass


class SettingMultiDirectory(SettingItem):
    """Widget for displaying and editing a multi-folder setting in the settings dialog.
    Supports a popup widget to display an editable list of folders.
    """

    popup = ObjectProperty(None, allownone=True)
    filepopup = ObjectProperty(None, allownone=True)
    textinput = ObjectProperty(None)
    folderlist = ObjectProperty(None)
    value = StringProperty('')
    modified = BooleanProperty(False)

    def remove_empty(self, elements):
        return_list = []
        for element in elements:
            if element != '':
                return_list.append(element)
        return return_list

    def on_panel(self, instance, value):
        del instance
        if value is None:
            return
        self.bind(on_release=self._create_popup)
        app = App.get_running_app()
        if not app.has_database():
            Clock.schedule_once(self._create_popup)

    def _dismiss(self, rescan=True, *_):
        if self.popup:
            self.popup.dismiss()
        self.popup = None
        if rescan:
            if self.modified:
                app = App.get_running_app()
                app.database_rescan()
                app.set_single_database()
            self.modified = False

    def _create_popup(self, *_):
        app = App.get_running_app()
        content = BoxLayout(orientation='vertical')
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = NormalPopup(title=self.title, content=content, size_hint=(None, 0.9), width=popup_width)
        if not self.value:
            content.add_widget(ShortLabel(height=app.button_scale * 3, text="You must set at least one database directory.\n\nThis is a folder where your photos are stored.\nNew photos will be imported to a database folder."))
            content.add_widget(BoxLayout())
        else:
            folders = filter(None, self.value.split(';'))
            folderdata = []
            for folder in folders:
                folderdata.append({'text': folder})
            self.folderlist = folderlist = FolderSettingsList(size_hint=(1, .8), id='folderlist')
            folderlist.data = folderdata
            content.add_widget(folderlist)
        buttons = BoxLayout(orientation='horizontal', size_hint=(1, None),
                            height=app.button_scale)
        addbutton = NormalButton(text='Add')
        addbutton.bind(on_press=self.add_path)
        removebutton = NormalButton(text='Remove')
        removebutton.bind(on_press=self.remove_path)
        okbutton = NormalButton(text='OK')
        okbutton.bind(on_press=self._dismiss)
        buttons.add_widget(addbutton)
        buttons.add_widget(removebutton)
        buttons.add_widget(okbutton)
        content.add_widget(buttons)
        popup.open()

    def add_path(self, *_):
        self.filechooser_popup()

    def remove_path(self, *_):
        self.modified = True
        listed_folders = self.folderlist.data
        all_folders = []
        for folder in listed_folders:
            if folder != self.folderlist.children[0].selected:
                all_folders.append(folder['text'])
        self.value = u';'.join(all_folders)
        self.refresh()

    def refresh(self):
        self._dismiss(rescan=False)
        self._create_popup(self)

    def filechooser_popup(self):
        content = FileBrowser(ok_text='Add', directory_select=True)
        content.bind(on_cancel=self.filepopup_dismiss)
        content.bind(on_ok=self.add_directory)
        self.filepopup = filepopup = NormalPopup(title=self.title, content=content, size_hint=(0.9, 0.9))
        filepopup.open()

    def filepopup_dismiss(self, *_):
        if self.filepopup:
            self.filepopup.dismiss()
        self.filepopup = None

    def add_directory(self, *_):
        self.modified = True
        all_folders = self.value.split(';')
        all_folders.append(agnostic_path(self.filepopup.content.filename))
        all_folders = self.remove_empty(all_folders)
        self.value = u';'.join(all_folders)
        self.filepopup_dismiss()
        self.refresh()


class SettingDatabaseImport(SettingItem):
    """Database scan/import widget for the settings screen."""
    def database_import(self):
        app = App.get_running_app()
        app.database_import()


class SettingDatabaseClean(SettingItem):
    """Database deep-clean widget for the settings screen."""
    def database_clean(self):
        app = App.get_running_app()
        app.database_clean(deep=True)


class SettingDatabaseRestore(SettingItem):
    """Database backup restore widget for the settings screen."""
    def database_restore(self):
        app = App.get_running_app()
        app.database_restore()


class SettingDatabaseBackup(SettingItem):
    """Database backup restore widget for the settings screen."""
    def database_backup(self):
        app = App.get_running_app()
        app.database_backup()


class MoveConfirmPopup(NormalPopup):
    """Popup that asks to confirm a file or folder move."""
    target = StringProperty()
    photos = ListProperty()
    origin = StringProperty()


class ScanningPopup(NormalPopup):
    """Popup for displaying database scanning progress."""
    scanning_percentage = NumericProperty(0)
    scanning_text = StringProperty('Building File List...')


class PhotoManagerSettings(Settings):
    """Expanded settings class to add new settings buttons and types."""

    def __init__(self, **kwargs):
        super(PhotoManagerSettings, self).__init__(**kwargs)
        self.register_type('multidirectory', SettingMultiDirectory)
        self.register_type('databaseimport', SettingDatabaseImport)
        self.register_type('databaseclean', SettingDatabaseClean)
        self.register_type('aboutbutton', SettingAboutButton)
        self.register_type('databaserestore', SettingDatabaseRestore)
        self.register_type('databasebackup', SettingDatabaseBackup)


class PhotoDrag(KivyImage):
    """Special image widget for displaying the drag-n-drop location."""

    angle = NumericProperty()
    offset = []
    opacity = .5
    fullpath = StringProperty()


class PhotoThumbLabel(NormalLabel):
    pass


class PhotoRecycleThumb(DragBehavior, BoxLayout, RecycleDataViewBehavior):
    """Wrapper widget for image thumbnails.  Used for displaying images in grid views."""

    found = BooleanProperty(True)  # Used to add a red overlay to the thumbnail if the source file doesn't exist
    owner = ObjectProperty()
    target = StringProperty()
    type = StringProperty('None')
    filename = StringProperty()
    fullpath = StringProperty()
    folder = StringProperty()
    database_folder = StringProperty()
    selected = BooleanProperty(False)
    drag = False
    dragable = BooleanProperty(True)
    image = ObjectProperty()
    photo_orientation = NumericProperty(1)
    angle = NumericProperty(0)  # used to display the correct orientation of the image
    favorite = BooleanProperty(False)  # if True, a star overlay will be displayed on the image
    video = BooleanProperty(False)
    source = StringProperty()
    photoinfo = ListProperty()
    temporary = BooleanProperty(False)
    title = StringProperty('')
    view_album = BooleanProperty(True)
    mirror = BooleanProperty(False)
    index = NumericProperty(0)
    data = {}

    def refresh_view_attrs(self, rv, index, data):
        """Called when widget is loaded into recycleview layout"""
        self.index = index
        self.data = data
        thumbnail = self.ids['thumbnail']
        thumbnail.temporary = self.data['temporary']
        thumbnail.photoinfo = self.data['photoinfo']
        thumbnail.source = self.data['source']
        self.image = thumbnail
        return super(PhotoRecycleThumb, self).refresh_view_attrs(rv, index, data)

    def on_source(self, *_):
        """Sets up the display image when first loaded."""

        found = isfile2(self.source)
        self.found = found
        if self.photo_orientation in [2, 4, 5, 7]:
            self.mirror = True
        else:
            self.mirror = False
        if self.photo_orientation == 3 or self.photo_orientation == 4:
            self.angle = 180
        elif self.photo_orientation == 5 or self.photo_orientation == 6:
            self.angle = 270
        elif self.photo_orientation == 7 or self.photo_orientation == 8:
            self.angle = 90
        else:
            self.angle = 0

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                if not self.temporary and self.view_album:
                    app = App.get_running_app()
                    if not app.shift_pressed:
                        app.show_album(self)
                        return
            app = App.get_running_app()
            if app.shift_pressed:
                self.parent.select_range(self.index, touch)
                return
            self.parent.select_with_touch(self.index, touch)
            self.owner.update_selected()
            if self.dragable:
                self.drag = True
                app = App.get_running_app()
                temp_coords = self.to_parent(touch.opos[0], touch.opos[1])
                widget_coords = (temp_coords[0] - self.pos[0], temp_coords[1] - self.pos[1])
                window_coords = self.to_window(touch.pos[0], touch.pos[1])
                app.drag(self, 'start', window_coords, image=self.image, offset=widget_coords, fullpath=self.fullpath)

    def on_touch_move(self, touch):
        if self.drag:
            if not self.selected:
                self.parent.select_node(self.index)
                self.owner.update_selected()
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag(self, 'move', window_coords)

    def on_touch_up(self, touch):
        if self.drag:
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag(self, 'end', window_coords)
            self.drag = False


class PhotoRecycleThumbWide(PhotoRecycleThumb):
    pass


class StencilViewTouch(StencilView):
    """Custom StencilView that stencils touches as well as visual elements."""

    def on_touch_down(self, touch):
        """Modified to only register touch down events when inside stencil area."""
        if self.collide_point(*touch.pos):
            super(StencilViewTouch, self).on_touch_down(touch)


class LimitedScatterLayout(ScatterLayout):
    """Custom ScatterLayout that won't allow sub-widgets to be moved out of the visible area,
    and will not respond to touches outside of the visible area.  
    """

    bypass = BooleanProperty(False)

    def on_bypass(self, instance, bypass):
        if bypass:
            self.transform = Matrix()

    def on_transform_with_touch(self, touch):
        """Modified to not allow widgets to be moved out of the visible area."""

        width = self.bbox[1][0]
        height = self.bbox[1][1]
        scale = self.scale

        local_bottom = self.bbox[0][1]
        local_left = self.bbox[0][0]
        local_top = local_bottom+height
        local_right = local_left+width

        local_xmax = width/scale
        local_xmin = 0
        local_ymax = height/scale
        local_ymin = 0

        if local_right < local_xmax:
            self.transform[12] = local_xmin - (width - local_xmax)
        if local_left > local_xmin:
            self.transform[12] = local_xmin
        if local_top < local_ymax:
            self.transform[13] = local_ymin - (height - local_ymax)
        if local_bottom > local_ymin:
            self.transform[13] = local_ymin

    def on_touch_down(self, touch):
        """Modified to only register touches in visible area."""

        if self.bypass:
            for child in self.children[:]:
                if child.dispatch('on_touch_down', touch):
                    return True
        else:
            if self.collide_point(*touch.pos):
                super(LimitedScatterLayout, self).on_touch_down(touch)


class PhotoShow(ButtonBehavior, RelativeLayout):
    """Widget that holds the image widget.  Used for catching double and tripple clicks."""

    filename = StringProperty()
    fullpath = StringProperty()
    current_touch = None
    bypass = BooleanProperty(False)

    def on_touch_down(self, touch):
        if touch.is_double_tap and not self.bypass:
            app = App.get_running_app()
            if not app.shift_pressed:
                photowrapper = self.parent.parent
                photocontainer = photowrapper.parent.parent
                if photowrapper.scale > 1:
                    photocontainer.zoom = 0
                else:
                    zoompos = self.to_local(touch.pos[0], touch.pos[1])
                    photocontainer.zoompos = zoompos
                    photocontainer.zoom = 1
        elif touch.is_triple_tap and not self.bypass:
            app = App.get_running_app()
            if not app.shift_pressed:
                app.show_photo()
        else:
            super(PhotoShow, self).on_touch_down(touch)


class TreeViewNodeSpacer(BoxLayout, TreeViewNode):
    """Provides a spacer for treeview elements.  Defaults to app.button_scale height."""
    pass


class ImportPresetArea(GridLayout):
    """Widget to display and edit all settings for a particular import preset."""

    title = StringProperty()
    import_to = StringProperty('')
    naming_method = StringProperty('')
    last_naming_method = StringProperty('')
    delete_originals = BooleanProperty(False)
    single_folder = BooleanProperty(False)
    preset_index = NumericProperty()
    naming_example = StringProperty('Naming Example')
    owner = ObjectProperty()
    import_from = ListProperty()
    index = NumericProperty()

    def __init__(self, **kwargs):
        super(ImportPresetArea, self).__init__(**kwargs)
        Clock.schedule_once(self.update_import_from)
        app = App.get_running_app()
        self.imports_dropdown = NormalDropDown()
        database_folders = app.config.get('Database Directories', 'paths')
        database_folders = local_path(database_folders)
        if database_folders.strip(' '):
            databases = database_folders.split(';')
        else:
            databases = []
        for database in databases:
            menu_button = MenuButton(text=database)
            menu_button.bind(on_release=self.change_import_to)
            self.imports_dropdown.add_widget(menu_button)

    def update_preset(self):
        """Updates the app preset setting with the current data."""

        app = App.get_running_app()
        import_preset = {}
        import_preset['title'] = self.title
        import_preset['import_to'] = self.import_to
        import_preset['naming_method'] = self.naming_method
        import_preset['delete_originals'] = self.delete_originals
        import_preset['import_from'] = self.import_from
        import_preset['single_folder'] = self.single_folder
        app.imports[self.index] = import_preset
        self.owner.owner.selected_import = self.index

    def set_title(self, instance):
        if not instance.focus:
            self.title = instance.text
            self.update_preset()
            self.owner.owner.update_treeview()

    def test_naming_method(self, string, *_):
        return "".join(i for i in string if i not in "#%&*{}\\/:?<>+|\"=][;")

    def new_naming_method(self, instance):
        if not instance.focus:
            if not naming(instance.text, title=''):
                self.naming_method = self.last_naming_method
                instance.text = self.last_naming_method
            else:
                self.last_naming_method = instance.text
                self.naming_method = instance.text
                self.naming_example = naming(self.naming_method)
                self.update_preset()

    def set_single_folder(self, state):
        if state == 'down':
            self.single_folder = True
        else:
            self.single_folder = False
        self.update_preset()

    def set_delete_originals(self, state):
        if state == 'down':
            self.delete_originals = True
        else:
            self.delete_originals = False
        self.update_preset()

    def remove_folder(self, index):
        del self.import_from[index]
        self.update_preset()
        self.update_import_from()

    def change_import_to(self, instance):
        self.imports_dropdown.dismiss()
        self.import_to = instance.text
        self.update_preset()

    def add_folder(self):
        content = FileBrowser(ok_text='Add', directory_select=True)
        content.bind(on_cancel=self.owner.owner.dismiss_popup)
        content.bind(on_ok=self.add_folder_confirm)
        self.owner.owner.popup = filepopup = NormalPopup(title='Select A Folder To Import From', content=content,
                                                         size_hint=(0.9, 0.9))
        filepopup.open()

    def add_folder_confirm(self, *_):
        folder = self.owner.owner.popup.content.filename
        self.import_from.append(folder)
        self.owner.owner.dismiss_popup()
        self.update_preset()
        self.update_import_from()

    def update_import_from(self, *_):
        preset_folders = self.ids['importPresetFolders']
        nodes = list(preset_folders.iterate_all_nodes())
        for node in nodes:
            preset_folders.remove_node(node)
        for index, folder in enumerate(self.import_from):
            preset_folders.add_node(ImportPresetFolder(folder=folder, owner=self, index=index))
        #self.update_preset()


class ScaleSettings(GridLayout):
    """Widget layout for the scale settings on the export dialog."""
    owner = ObjectProperty()


class WatermarkSettings(GridLayout):
    """Widget layout for the watermark settings on the export dialog."""
    owner = ObjectProperty()


class FolderToggleSettings(GridLayout):
    """Widget layout for the export to folder settings on the export dialog."""
    owner = ObjectProperty()


class FTPToggleSettings(GridLayout):
    """Widget layout for the export to ftp settings on the export dialog."""
    owner = ObjectProperty()


class ImportPreset(ExpandableButton):
    data = DictProperty()
    owner = ObjectProperty()
    import_to = StringProperty('')

    def on_data(self, *_):
        import_preset = self.data
        naming_method = import_preset['naming_method']
        self.content = ImportPresetArea(index=self.index, title=import_preset['title'], import_to=import_preset['import_to'], naming_method=naming_method, naming_example=naming(naming_method), last_naming_method=naming_method, single_folder=import_preset['single_folder'], delete_originals=import_preset['delete_originals'], import_from=import_preset['import_from'], owner=self)

    def on_remove(self):
        app = App.get_running_app()
        app.import_preset_remove(self.index)
        self.owner.selected_import = -1
        self.owner.update_treeview()

    def on_press(self):
        self.owner.selected_import = self.index
        self.owner.import_preset()


class ExportPreset(ExpandableButton):
    data = DictProperty()
    owner = ObjectProperty()

    def on_data(self, *_):
        export_preset = self.data
        self.content = ExportPresetArea(owner=self, index=self.index, name=export_preset['name'], export=export_preset['export'], ftp_address=export_preset['ftp_address'], ftp_user=export_preset['ftp_user'], ftp_password=export_preset['ftp_password'], ftp_passive=export_preset['ftp_passive'], ftp_port=export_preset['ftp_port'], export_folder=export_preset['export_folder'], create_subfolder=export_preset['create_subfolder'], export_info=export_preset['export_info'], scale_image=export_preset['scale_image'], scale_size=export_preset['scale_size'], scale_size_to=export_preset['scale_size_to'], jpeg_quality=export_preset['jpeg_quality'], watermark=export_preset['watermark'], watermark_image=export_preset['watermark_image'], watermark_opacity=export_preset['watermark_opacity'], watermark_horizontal=export_preset['watermark_horizontal'], watermark_vertical=export_preset['watermark_vertical'], watermark_size=export_preset['watermark_size'], ignore_tags=' '.join(export_preset['ignore_tags']), export_videos=export_preset['export_videos'])

    def on_expanded(self, *_):
        if self.content:
            content_container = self.ids['contentContainer']
            if self.expanded:
                content_container.add_widget(self.content)
                Clock.schedule_once(self.content.update_test_image)
            else:
                content_container.clear_widgets()

    def on_remove(self):
        app = App.get_running_app()
        app.export_preset_remove(self.index)
        self.owner.selected_preset = -1
        self.owner.update_treeview()

    def on_press(self):
        self.owner.selected_preset = self.index
        self.owner.export()


class ExportPresetArea(GridLayout):
    """Widget for displaying and editing settings for an export preset."""

    owner = ObjectProperty()
    name = StringProperty('')
    export_folder = StringProperty('')
    last_export_folder = StringProperty('')
    create_subfolder = BooleanProperty(True)
    export_info = BooleanProperty(True)
    scale_image = BooleanProperty(False)
    scale_size = NumericProperty(1000)
    scale_size_to = StringProperty('long')
    jpeg_quality = NumericProperty(90)
    watermark = BooleanProperty(False)
    watermark_image = StringProperty()
    watermark_opacity = NumericProperty(50)
    watermark_horizontal = NumericProperty(80)
    watermark_vertical = NumericProperty(20)
    watermark_size = NumericProperty(25)
    export_videos = BooleanProperty(False)
    ignore_tags = StringProperty()
    scale_size_to_text = StringProperty('Long Side')
    scale_settings = ObjectProperty()
    watermark_settings = ObjectProperty()
    export = StringProperty('folder')
    ftp_address = StringProperty()
    ftp_user = StringProperty()
    ftp_password = StringProperty()
    ftp_passive = BooleanProperty(True)
    ftp_port = NumericProperty(21)
    index = NumericProperty(0)

    def __init__(self, **kwargs):
        super(ExportPresetArea, self).__init__(**kwargs)
        self.scale_size_to_dropdown = NormalDropDown()
        self.last_export_folder = self.export_folder
        if self.scale_image:
            self.add_scale_settings()
        if self.watermark:
            self.add_watermark_settings()
        for option in scale_size_to_options:
            menu_button = MenuButton(text=scale_size_to_options[option])
            menu_button.bind(on_release=self.change_scale_to)
            menu_button.target = option
            self.scale_size_to_dropdown.add_widget(menu_button)
        self.add_export_settings()

    def update_preset(self):
        """Updates this export preset in the app."""

        app = App.get_running_app()
        export_preset = {}
        export_preset['name'] = self.name
        export_preset['export'] = self.export
        export_preset['ftp_address'] = self.ftp_address
        export_preset['ftp_user'] = self.ftp_user
        export_preset['ftp_password'] = self.ftp_password
        export_preset['ftp_passive'] = self.ftp_passive
        export_preset['ftp_port'] = self.ftp_port
        export_preset['export_folder'] = self.export_folder
        export_preset['create_subfolder'] = self.create_subfolder
        export_preset['export_info'] = self.export_info
        export_preset['scale_image'] = self.scale_image
        export_preset['scale_size'] = self.scale_size
        export_preset['scale_size_to'] = self.scale_size_to
        export_preset['jpeg_quality'] = self.jpeg_quality
        export_preset['watermark'] = self.watermark
        export_preset['watermark_image'] = self.watermark_image
        export_preset['watermark_opacity'] = self.watermark_opacity
        export_preset['watermark_horizontal'] = self.watermark_horizontal
        export_preset['watermark_vertical'] = self.watermark_vertical
        export_preset['watermark_size'] = self.watermark_size
        ignore_tags = self.ignore_tags.split(',')
        ignore_tags = list(filter(bool, ignore_tags))
        export_preset['ignore_tags'] = ignore_tags
        export_preset['export_videos'] = self.export_videos
        app.exports[self.index] = export_preset
        self.owner.owner.selected_preset = self.index
        app.export_preset_write()

    def toggle_exports(self, button):
        """Switch between folder and ftp export."""

        if button.text == 'FTP':
            self.export = 'ftp'
        else:
            self.export = 'folder'
        self.add_export_settings()
        self.update_preset()

    def add_export_settings(self, *_):
        """Add the proper export settings to the export dialog."""

        if self.export == 'ftp':
            button = self.ids['toggleFTP']
            button.state = 'down'
            toggle_area = self.ids['toggleSettings']
            toggle_area.clear_widgets()
            toggle_area.add_widget(FTPToggleSettings(owner=self))
        else:
            button = self.ids['toggleFolder']
            button.state = 'down'
            toggle_area = self.ids['toggleSettings']
            toggle_area.clear_widgets()
            toggle_area.add_widget(FolderToggleSettings(owner=self))

    def update_test_image(self, *_):
        """Regenerate the watermark preview image."""

        if self.watermark_settings:
            test_image = self.watermark_settings.ids['testImage']
            test_image.clear_widgets()
            if os.path.isfile(self.watermark_image):
                image = KivyImage(source=self.watermark_image)
                size_x = test_image.size[0]*(self.watermark_size/100)
                size_y = test_image.size[1]*(self.watermark_size/100)
                image.size = (size_x, size_y)
                image.size_hint = (None, None)
                image.opacity = self.watermark_opacity/100
                x_pos = test_image.pos[0]+((test_image.size[0] - size_x)*(self.watermark_horizontal/100))
                y_pos = test_image.pos[1]+((test_image.size[1] - size_y)*(self.watermark_vertical/100))
                image.pos = (x_pos, y_pos)
                test_image.add_widget(image)

    def add_watermark_settings(self, *_):
        """Add the watermark settings widget to the proper area."""

        watermark_settings_widget = self.ids['watermarkSettings']
        self.watermark_settings = WatermarkSettings(owner=self)
        watermark_settings_widget.add_widget(self.watermark_settings)
        Clock.schedule_once(self.update_test_image)

    def add_scale_settings(self, *_):
        """Add the scale settings widget to the proper area."""

        scale_settings_widget = self.ids['scaleSettings']
        self.scale_settings = ScaleSettings(owner=self)
        scale_settings_widget.add_widget(self.scale_settings)

    def select_watermark(self):
        """Open a filebrowser to select the watermark image."""

        content = FileBrowser(ok_text='Select', filters=['*.png'])
        content.bind(on_cancel=self.owner.owner.dismiss_popup)
        content.bind(on_ok=self.select_watermark_confirm)
        self.owner.owner.popup = filepopup = NormalPopup(title='Select Watermark PNG Image', content=content,
                                                         size_hint=(0.9, 0.9))
        filepopup.open()

    def select_watermark_confirm(self, *_):
        """Called when the watermark file browse dialog is closed."""

        self.watermark_image = self.owner.owner.popup.content.filename
        self.owner.owner.dismiss_popup()
        self.update_preset()
        self.update_test_image()

    def set_scale_size(self, instance):
        """Apply the scale size setting, only when the input area loses focus."""

        if not instance.focus:
            self.scale_size = int(instance.text)
            self.update_preset()

    def on_scale_size_to(self, *_):
        self.scale_size_to_text = scale_size_to_options[self.scale_size_to]

    def set_watermark_opacity(self, instance):
        self.watermark_opacity = int(instance.value)
        value_display = self.watermark_settings.ids['watermarkOpacityValue']
        value_display.text = 'Watermark Opacity:'+str(self.watermark_opacity)+'%'
        self.update_preset()
        self.update_test_image()

    def set_watermark_horizontal(self, instance):
        self.watermark_horizontal = int(instance.value)
        value_display = self.watermark_settings.ids['watermarkHorizontalValue']
        value_display.text = 'Horizontal Position:'+str(self.watermark_horizontal)+'%'
        self.update_preset()
        self.update_test_image()

    def set_watermark_vertical(self, instance):
        self.watermark_vertical = int(instance.value)
        value_display = self.watermark_settings.ids['watermarkVerticalValue']
        value_display.text = 'Vertical Position:'+str(self.watermark_vertical)+'%'
        self.update_preset()
        self.update_test_image()

    def set_watermark_size(self, instance):
        self.watermark_size = int(instance.value)
        value_display = self.watermark_settings.ids['watermarkSizeValue']
        value_display.text = 'Watermark Size:'+str(self.watermark_size)+'%'
        self.update_preset()
        self.update_test_image()

    def set_jpeg_quality(self, instance):
        self.jpeg_quality = int(instance.value)
        value_display = self.scale_settings.ids['jpegQualityValue']
        value_display.text = 'JPEG Quality: '+str(self.jpeg_quality)+'%'
        self.update_preset()

    def change_scale_to(self, instance):
        self.scale_size_to_dropdown.dismiss()
        self.scale_size_to = instance.target
        self.update_preset()

    def set_scale_image(self, state):
        if state == 'down':
            self.scale_image = True
            self.add_scale_settings()
        else:
            self.scale_image = False
            scale_settings_widget = self.ids['scaleSettings']
            scale_settings_widget.clear_widgets()
        self.update_preset()

    def set_export_videos(self, state):
        if state == 'down':
            self.export_videos = True
        else:
            self.export_videos = False
        self.update_preset()

    def set_export_info(self, state):
        if state == 'down':
            self.export_info = True
        else:
            self.export_info = False
        self.update_preset()

    def set_watermark(self, state):
        if state == 'down':
            self.watermark = True
            self.add_watermark_settings()
        else:
            self.watermark = False
            watermark_settings_widget = self.ids['watermarkSettings']
            watermark_settings_widget.clear_widgets()
        self.update_preset()

    def set_create_subfolder(self, state):
        if state == 'down':
            self.create_subfolder = True
        else:
            self.create_subfolder = False
        self.update_preset()

    def test_tags(self, string, *_):
        return "".join(i for i in string if i not in "#%&*{}\\/:?<>+|\"=][;").lower()

    def set_ignore_tags(self, instance):
        if not instance.focus:
            self.ignore_tags = instance.text
            self.update_preset()

    def set_ftp_passive(self, instance):
        if instance.state == 'down':
            self.ftp_passive = True
            instance.text = 'Passive Mode'
        else:
            self.ftp_passive = False
            instance.text = 'Active Mode'
        self.update_preset()

    def set_title(self, instance):
        if not instance.focus:
            self.name = instance.text
            self.update_preset()
            self.owner.owner.update_treeview()

    def filename_filter(self, string, *_):
        remove_string = '\\/*?<>|,'.replace(os.path.sep, "")
        return "".join(i for i in string if i not in remove_string)

    def set_ftp_user(self, instance):
        if not instance.focus:
            self.ftp_user = instance.text
            self.update_preset()

    def set_ftp_password(self, instance):
        if not instance.focus:
            self.ftp_password = instance.text
            self.update_preset()

    def set_ftp_address(self, instance):
        if not instance.focus:
            self.ftp_address = instance.text
            self.update_preset()

    def set_ftp_port(self, instance):
        if not instance.focus:
            self.ftp_port = int(instance.text)
            self.update_preset()

    def ftp_filter(self, string, *_):
        remove_string = '\\:<>| "\''
        return "".join(i for i in string if i not in remove_string).lower()

    def set_export_folder(self, instance):
        if not instance.focus:
            if os.path.exists(instance.text):
                self.export_folder = instance.text
                self.last_export_folder = instance.text
            else:
                instance.text = self.last_export_folder
                self.export_folder = self.last_export_folder
            self.update_preset()

    def select_export(self):
        """Activates a popup folder browser dialog to select the export folder."""

        content = FileBrowser(ok_text='Select', directory_select=True)
        content.bind(on_cancel=self.owner.owner.dismiss_popup)
        content.bind(on_ok=self.select_export_confirm)
        self.owner.owner.popup = filepopup = NormalPopup(title='Select An Export Folder', content=content,
                                                         size_hint=(0.9, 0.9))
        filepopup.open()

    def select_export_confirm(self, *_):
        """Called when the export folder select dialog is closed successfully."""

        self.export_folder = self.owner.owner.popup.content.filename
        self.owner.owner.dismiss_popup()
        self.update_preset()


class ImportPresetFolder(ButtonBehavior, BoxLayout, TreeViewNode):
    """TreeView widget to display a folder scanned on the import process."""

    folder = StringProperty()
    index = NumericProperty()
    owner = ObjectProperty()

    def remove_folder(self):
        self.owner.remove_folder(self.index)


class RotationGrid(FloatLayout):
    """A grid display overlay used for alignment when an image is being rotated."""
    pass


class CropOverlay(ResizableBehavior, RelativeLayout):
    """Overlay widget for showing cropping area."""

    owner = ObjectProperty()
    drag_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(CropOverlay, self).__init__(**kwargs)
        self._drag_touch = None

    def on_mouse_move(self, _, pos):
        """need to override this because the original class will still change mouse cursor after it's removed..."""
        if self.parent:
            super(CropOverlay, self).on_mouse_move(_, pos)

    def on_size(self, instance, size):
        self.owner.set_crop(self.pos[0], self.pos[1], size[0], size[1])

    def on_pos(self, instance, pos):
        self.owner.set_crop(pos[0], pos[1], self.size[0], self.size[1])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.button == 'left':
                if self.check_resizable_side(*touch.pos):
                    self.drag_mode = False
                    super(CropOverlay, self).on_touch_down(touch)
                else:
                    self.drag_mode = True
            return True

    def on_touch_move(self, touch):
        if self.drag_mode:
            self.x += touch.dx
            self.y += touch.dy

        else:
            super(CropOverlay, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.drag_mode:
            self.drag_mode = False
        else:
            super(CropOverlay, self).on_touch_up(touch)

    def on_resizing(self, instance, resizing):
        pass


class PhotoViewer(BoxLayout):
    """Holds the fullsized photo image in album view mode."""

    photoinfo = ListProperty()
    favorite = BooleanProperty(False)
    angle = NumericProperty(0)
    mirror = BooleanProperty(False)
    file = StringProperty()
    scale_max = NumericProperty(1)
    edit_mode = StringProperty('main')
    edit_image = ObjectProperty()
    overlay = ObjectProperty(allownone=True)
    bypass = BooleanProperty(False)
    zoom = NumericProperty(0)
    zoompos = ListProperty([0, 0])
    set_fullscreen = BooleanProperty(False)

    def on_height(self, *_):
        self.reset_zoompos()

    def reset_zoompos(self):
        self.zoompos = [self.width / 2, self.height / 2]

    def on_zoom(self, *_):
        if self.zoom == 0:
            self.reset_zoompos()
        scale_max = self.scale_max
        scale_size = 1 + ((scale_max - 1) * self.zoom)
        scale = Matrix().scale(scale_size, scale_size, scale_size)
        wrapper = self.ids['wrapper']
        wrapper.transform = Matrix()
        zoompos = self.zoompos
        wrapper.apply_transform(scale, anchor=zoompos)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.edit_mode != 'main' and not self.overlay:
                self.edit_image.opacity = 0
                image = self.ids['image']
                image.opacity = 1
                return True
            else:
                return super(PhotoViewer, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if self.edit_mode != 'main' and not self.overlay:
                self.edit_image.opacity = 1
                image = self.ids['image']
                image.opacity = 0
                return True
            else:
                return super(PhotoViewer, self).on_touch_up(touch)

    def is_fullscreen(self):
        """Dummy function, only for video, but here in case it gets called on the wrong viewer type."""
        return False

    def refresh(self):
        """Updates the image subwidget's source file."""

        image = self.ids['image']
        image.source = self.file

    def on_edit_mode(self, *_):
        """Called when the user enters or exits edit mode.
        Adds the edit image widget, and overlay if need be, and sets them up."""

        image = self.ids['image']
        if self.edit_mode == 'main':
            image.opacity = 1
            viewer = self.ids['photoShow']
            if self.edit_image:
                viewer.remove_widget(self.edit_image)
            if self.overlay:
                viewer.remove_widget(self.overlay)
                self.overlay = None
        else:
            image.opacity = 0
            viewer = self.ids['photoShow']
            self.edit_image = CustomImage(source=self.file, mirror=self.mirror, angle=self.angle,
                                          photoinfo=self.photoinfo)
            viewer.add_widget(self.edit_image)
            if self.edit_mode == 'rotate':
                #add rotation grid overlay
                self.overlay = RotationGrid()
                viewer.add_widget(self.overlay)
            if self.edit_mode == 'crop':
                #add cropper overlay and set image to crop mode
                self.overlay = CropOverlay(owner=self.edit_image)
                viewer.add_widget(self.overlay)
                self.edit_image.cropping = True
                self.edit_image.cropper = self.overlay

    def stop(self):
        """Dummy function, only for video, but here in case it gets called on the wrong viewer type."""
        pass

    def fullscreen(self):
        """Switches the app to single image view."""

        app = App.get_running_app()
        app.show_photo()


class PauseableVideo(Video):
    """modified Video class to allow clicking anywhere to pause/resume."""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.state == 'play':
                self.state = 'pause'
            else:
                self.state = 'play'
            return True


class SpecialVideoPlayer(VideoPlayer):
    """Custom VideoPlayer class that replaces the default video widget with the 'PauseableVideo' widget."""

    photoinfo = ListProperty()
    mirror = BooleanProperty(False)
    favorite = BooleanProperty(False)

    def _load_thumbnail(self):
        if not self.container:
            return
        self.container.clear_widgets()
        if self.photoinfo:
            self._image = VideoThumbnail(photoinfo=self.photoinfo, source=self.source, favorite=self.favorite, video=self)
            self.container.add_widget(self._image)

    def on_fullscreen(self, instance, value):
        """Auto-play the video when set to fullscreen."""

        if self.fullscreen:
            self.state = 'play'
        return super(SpecialVideoPlayer, self).on_fullscreen(instance, value)

    def _do_video_load(self, *largs):
        """this function has been changed to replace the Video object with the special PauseableVideo object.
        Also, checks if auto-play videos are enabled in the settings.
        """

        if isfile2(self.source):
            self._video = PauseableVideo(source=self.source, state=self.state, volume=self.volume,
                                         pos_hint={'x': 0, 'y': 0}, **self.options)
            self._video.bind(texture=self._play_started, duration=self.setter('duration'), position=self.setter('position'),
                             volume=self.setter('volume'), state=self._set_state)
            app = App.get_running_app()
            if app.config.getboolean("Settings", "videoautoplay"):
                self._video.state = 'play'

    def on_touch_down(self, touch):
        """Checks if a double-click was detected, switches to fullscreen if it is."""

        if not self.disabled:
            if not self.collide_point(*touch.pos):
                return False
            if touch.is_double_tap and self.allow_fullscreen:
                self.fullscreen = not self.fullscreen
                return True
            return super(SpecialVideoPlayer, self).on_touch_down(touch)


class VideoViewer(FloatLayout):
    """Holds the fullsized video in album view mode."""

    photoinfo = ListProperty()
    favorite = BooleanProperty(False)
    angle = NumericProperty(0)
    mirror = BooleanProperty(False)
    file = StringProperty()
    edit_mode = StringProperty('main')
    bypass = BooleanProperty(False)
    edit_image = ObjectProperty(None, allownone=True)
    position = NumericProperty(0.5)

    def on_position(self, *_):
        if self.edit_image:
            self.edit_image.position = self.position

    def on_edit_mode(self, *_):
        """Called when the user enters or exits edit mode.
        Adds the edit image widget, and overlay if need be, and sets them up."""

        overlay = self.ids['overlay']
        player = self.ids['player']
        if self.edit_mode == 'main':
            player.opacity = 1
            overlay.opacity = 0
            viewer = self.ids['photoShow']
            if self.edit_image:
                self.edit_image.close_video()
                viewer.remove_widget(self.edit_image)
                self.edit_image = None
        else:
            overlay.opacity = 1
            player.opacity = 0
            viewer = self.ids['photoShow']
            self.edit_image = CustomImage(source=self.file, mirror=self.mirror, angle=self.angle,
                                          photoinfo=self.photoinfo)
            viewer.add_widget(self.edit_image)

    def is_fullscreen(self):
        """Checks if the embedded video is currently fullscreen, and returns that value.
        Returns: True or False
        """

        player = self.ids['player']
        return player.fullscreen

    def stop(self):
        """Stops the video playback."""

        player = self.ids['player']
        player.fullscreen = False
        player.state = 'stop'

    def fullscreen(self):
        """Toggles the video player to fullscreen mode."""

        player = self.ids['player']
        player.fullscreen = not player.fullscreen


class DatabaseScreen(Screen):
    """Screen layout for the main photo database."""

    type = StringProperty('folder')  #Currently selected type: folder, album, tag
    selected = StringProperty('')  #Currently selected album in the database, may be blank
    displayable = BooleanProperty(False)
    sort_dropdown = ObjectProperty()  #Database sorting menu
    sort_method = StringProperty('File Name')  #Currently selected database sort mode
    sort_reverse = BooleanProperty(False)  #Database sorting reversed or not
    album_sort_dropdown = ObjectProperty()  #Album sorting menu
    album_sort_method = StringProperty('File Name')  #Currently selected album sort mode
    album_sort_reverse = BooleanProperty(False)  #Album sorting reversed or not
    folder_details = ObjectProperty()  #Holder for the folder details widget
    album_details = ObjectProperty()  #Holder for the album details widget
    popup = None  #Holder for the popup dialog widget
    photos = []  #List of photo infos in the currently displayed album
    can_export = BooleanProperty(False)  #Controls if the export button in the album view area is enabled
    sort_reverse_button = StringProperty('normal')
    album_sort_reverse_button = StringProperty('normal')
    tag_menu = ObjectProperty()
    album_menu = ObjectProperty()
    data = ListProperty()
    expanded_albums = BooleanProperty(True)
    expanded_tags = BooleanProperty(True)
    expanded_folders = []
    folders = []
    update_folders = True

    def add_item(self, *_):
        if self.type == 'Album':
            self.new_album()

        elif self.type == 'Tag':
            self.new_tag()

        elif self.type == 'Folder':
            self.add_folder()
        else:
            pass

    def rename_item(self, *_):
        if self.type == 'Album':
            pass

        elif self.type == 'Tag':
            pass

        elif self.type == 'Folder':
            self.rename_folder()
        else:
            pass

    def delete_item(self, *_):
        if self.type == 'Album':
            self.delete_folder()

        elif self.type == 'Tag':
            self.delete_folder()

        elif self.type == 'Folder':
            self.delete_folder()
        else:
            pass

    def get_selected_photos(self, fullpath=False):
        photos = self.ids['photos']
        selected_indexes = photos.selected_nodes
        photos_container = self.ids['photosContainer']
        selected_photos = []
        for selected in selected_indexes:
            if fullpath:
                selected_photos.append(photos_container.data[selected]['fullpath'])
            else:
                selected_photos.append(photos_container.data[selected]['photoinfo'])
        return selected_photos

    def on_sort_reverse(self, *_):
        """Updates the sort reverse button's state variable, since kivy doesnt just use True/False for button states."""

        app = App.get_running_app()
        self.sort_reverse_button = 'down' if to_bool(app.config.get('Sorting', 'database_sort_reverse')) else 'normal'

    def on_album_sort_reverse(self, *_):
        """Updates the sort reverse button's state variable, since kivy doesnt just use True/False for button states."""

        app = App.get_running_app()
        sort_reverse = to_bool(app.config.get('Sorting', 'album_sort_reverse'))
        self.album_sort_reverse_button = 'down' if sort_reverse else 'normal'

    def export(self):
        """Switches the app to export mode with the current selected album."""

        if self.selected and self.type != 'None':
            app = App.get_running_app()
            app.export_target = self.selected
            app.export_type = self.type
            app.show_export()

    def text_input_active(self):
        """Checks if any 'NormalInput' or 'FloatInput' widgets are currently active (being typed in).
        Returns: True or False
        """

        input_active = False
        for widget in self.walk(restrict=True):
            if widget.__class__.__name__ == 'NormalInput' or widget.__class__.__name__ == 'FloatInput' or widget.__class__.__name__ == 'IntegerInput':
                if widget.focus:
                    input_active = True
                    break
        return input_active

    def has_popup(self):
        """Checks if the popup window is open for this screen.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_extra(self):
        """Dummy function, not valid for this screen, but the app calls it when escape is pressed."""
        return False

    def dismiss_popup(self):
        """If this screen has a popup, closes it and removes it."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def key(self, key):
        """Handles keyboard shortcuts, performs the actions needed.
        Argument:
            key: The name of the key command to perform.
        """

        if self.text_input_active():
            pass
        else:
            if not self.popup or (not self.popup.open):
                if key == 'left' or key == 'up':
                    self.previous_album()
                if key == 'right' or key == 'down':
                    self.next_album()
                if key == 'enter':
                    if self.type != 'None':
                        if len(self.photos) > 0:
                            app = App.get_running_app()
                            app.target = self.selected
                            app.photo = ''
                            app.fullpath = ''
                            app.type = self.type
                            app.show_album(button=None)
                if key == 'delete':
                    self.delete()
                if key == 'a':
                    self.toggle_select()
            elif self.popup and self.popup.open:
                if key == 'enter':
                    self.popup.content.dispatch('on_answer', 'yes')

    def previous_album(self):
        """Selects the previous album in the database."""

        database = self.ids['database']
        database_interior = self.ids['databaseInterior']
        selected = self.selected
        data = database.data
        current_index = None
        for i, node in enumerate(data):
            if node['target'] == selected and node['type'] == self.type:
                current_index = i
                break
        if current_index is not None:
            if current_index == 0:
                next_index = len(data) - 1
            else:
                next_index = current_index - 1
            new_folder = data[next_index]
            self.displayable = new_folder['displayable']
            self.type = new_folder['type']
            self.selected = new_folder['target']
            database_interior.selected = new_folder
            database.scroll_to_selected()

    def next_album(self):
        """Selects the next album in the database."""

        database = self.ids['database']
        database_interior = self.ids['databaseInterior']
        selected = self.selected
        data = database.data
        current_index = None
        for i, node in enumerate(data):
            if node['target'] == selected and node['type'] == self.type:
                current_index = i
                break
        if current_index is not None:
            if current_index == len(data) - 1:
                next_index = 0
            else:
                next_index = current_index + 1
            new_folder = data[next_index]
            self.displayable = new_folder['displayable']
            self.type = new_folder['type']
            self.selected = new_folder['target']
            database_interior.selected = new_folder
            database.scroll_to_selected()

    def show_selected(self):
        """Scrolls the treeview to the currently selected folder"""

        database = self.ids['database']
        database_interior = self.ids['databaseInterior']
        selected = self.selected
        data = database.data
        current_folder = None
        for i, node in enumerate(data):
            if node['target'] == selected and node['type'] == self.type:
                current_folder = node
                break
        if current_folder is not None:
            database_interior.selected = current_folder
            database.scroll_to_selected()

    def delete(self):
        """Begins the file delete process.  Will call 'delete_selected_confirm' if an album is active."""

        photos = self.ids['photos']
        if photos.selected_nodes:
            self.delete_selected_confirm()

    def delete_selected_confirm(self):
        """Step two of file delete process.  Opens a confirm popup dialog.
        Dialog will call 'delete_selected_answer' on close.
        """

        if self.type == 'Album':
            content = ConfirmPopup(text='Remove Selected Files From The Album "'+self.selected+'"?', yes_text='Remove', no_text="Don't Remove", warn_yes=True)
        elif self.type == 'Tag':
            content = ConfirmPopup(text='Remove The Tag "'+self.selected+'" From Selected Files?', yes_text='Remove', no_text="Don't Remove", warn_yes=True)
        else:
            content = ConfirmPopup(text='Delete The Selected Files?', yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        app = App.get_running_app()
        content.bind(on_answer=self.delete_selected_answer)
        self.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 4),
                                 auto_dismiss=False)
        self.popup.open()

    def delete_selected_answer(self, instance, answer):
        """Final step of the file delete process, if the answer was 'yes' will delete the selected files.
        Arguments:
            instance: The widget that called this command.
            answer: String, 'yes' if confirm, anything else on deny."""

        del instance
        if answer == 'yes':
            app = App.get_running_app()

            #get the selected photos
            selected_photos = self.get_selected_photos()
            selected_files = []
            for photo in selected_photos:
                full_filename = os.path.join(photo[2], photo[0])
                selected_files.append([photo[0], full_filename])

            #decide what to do with the photos
            if self.type == 'Album':
                index = app.album_find(self.selected)
                if index >= 0:
                    for photo in selected_files:
                        app.album_remove_photo(index, photo[0])
                    app.message("Removed "+str(len(selected_files))+" Files from the album '"+self.selected+"'")
            elif self.type == 'Tag':
                for photo in selected_files:
                    app.database_remove_tag(photo[0], self.selected, message=True)
                app.message("Removed the tag '"+self.selected+"' from "+str(len(selected_files))+" Files.")
            else:
                folders = []
                for photo in selected_files:
                    app.delete_photo(photo[0], photo[1])
                    folders.append(photo[1])
                app.update_photoinfo(folders=folders)
                app.message("Deleted "+str(len(selected_files))+" Files.")
            app.photos.commit()
            self.on_selected('', '')
        self.dismiss_popup()
        self.update_treeview()

    def drop_widget(self, fullpath, position, dropped_type='file'):
        """Called when a widget is dropped after being dragged.
        Determines what to do with the widget based on where it is dropped.
        Arguments:
            fullpath: String, file location of the object being dragged.
            position: List of X,Y window coordinates that the widget is dropped on.
            dropped_type: String, describes the object being dropped.  May be: 'folder' or 'file'
        """

        app = App.get_running_app()
        folder_list = self.ids['databaseInterior']
        folder_container = self.ids['database']
        if folder_container.collide_point(position[0], position[1]):  #check if dropped in the folders list
            #Now, determine exactly what the widget was dropped on
            offset_x, offset_y = folder_list.to_widget(position[0], position[1])
            for widget in folder_list.children:
                if widget.collide_point(position[0], offset_y):
                    if dropped_type == 'folder' and widget.type == 'Folder':
                        if not widget.displayable:
                            move_to = ''
                        else:
                            move_to = widget.fullpath
                        if move_to != fullpath:
                            if not move_to.startswith(fullpath):
                                question = 'Move "'+fullpath+'" into "'+widget.fullpath+'"?'
                                content = ConfirmPopup(text=question, yes_text='Move', no_text="Don't Move", warn_yes=True)
                                app = App.get_running_app()
                                content.bind(on_answer=partial(self.move_folder_answer, fullpath, move_to))
                                self.popup = NormalPopup(title='Confirm Move', content=content, size_hint=(None, None),
                                                         size=(app.popup_x, app.button_scale * 4),
                                                         auto_dismiss=False)
                                self.popup.open()
                        return

                    elif dropped_type == 'file':
                        if widget.type != 'None':
                            selected_photos = self.get_selected_photos(fullpath=True)
                            if fullpath not in selected_photos:
                                selected_photos.append(fullpath)
                            if widget.type == 'Album':
                                self.add_to_album(widget.target, selected_photos=selected_photos)
                            elif widget.type == 'Tag':
                                self.add_to_tag(widget.target, selected_photos=selected_photos)
                            elif widget.type == 'Folder':
                                content = ConfirmPopup(text='Move These Files To "'+widget.target+'"?', yes_text="Move", no_text="Don't Move", warn_yes=True)
                                content.bind(on_answer=self.move_files)
                                self.popup = MoveConfirmPopup(photos=selected_photos, target=widget.target,
                                                              title='Confirm Move', content=content,
                                                              size_hint=(None, None),
                                                              size=(app.popup_x, app.button_scale * 4),
                                                              auto_dismiss=False)
                                self.popup.open()
                                pass
                            break

    def move_files(self, instance, answer):
        """Calls the app's move_files command if the dialog was answered with a 'yes'.
        Arguments:
            instance: The button that called this function.
            answer: String, if it is 'yes', the function will activate, if anything else, nothing will happen.
        """

        del instance
        if answer == 'yes':
            app = App.get_running_app()
            app.move_files(self.popup.photos, self.popup.target)
            self.selected = self.popup.target
            self.update_treeview()
        self.dismiss_popup()

    def toggle_select(self):
        """Toggles the selection of photos in the current album."""

        photos = self.ids['photos']
        if photos.selected_nodes:
            selected = True
        else:
            selected = False
        photos.clear_selection()
        if not selected:
            photos.select_all()
        self.update_selected()

    def select_none(self):
        """Deselects all photos."""

        photos = self.ids['photos']
        photos.clear_selection()
        self.update_selected()

    def update_selected(self, *_):
        """Checks if any files are selected in the current album, and updates buttons that only work when files
        are selected."""

        if not self.ids:
            return

        photos = self.ids['photos']
        if photos.selected_nodes:
            selected = True
        else:
            selected = False
        delete_button = self.ids['deleteButton']
        delete_button.disabled = not selected
        album_button = self.ids['albumButton']
        album_button.disabled = not selected
        tag_button = self.ids['tagButton']
        tag_button.disabled = not selected

    def add_to_album(self, album_name, selected_photos=None):
        """Adds the current selected photos to an album.
        Arguments:
            album_name: String, album to move the photos into.
        """

        if not selected_photos:
            selected_photos = self.get_selected_photos(fullpath=True)
        app = App.get_running_app()
        added = 0
        for album in app.albums:
            if album['name'] == album_name:
                for photo in selected_photos:
                    if photo not in album['photos']:
                        album['photos'].append(photo)
                        added = added + 1
                app.album_save(album)
        self.select_none()
        if added:
            app.message("Added "+str(added)+" files to the album '"+album_name+"'")
        self.update_treeview()

    def add_to_album_menu(self, instance):
        self.add_to_album(instance.text)
        self.album_menu.dismiss()

    def add_to_tag(self, tag_name, selected_photos=None):
        """Adds a tag to the currently selected photos.
        Arguments:
            tag_name: Tag to add to selected photos.
        """

        if not selected_photos:
            selected_photos = self.get_selected_photos(fullpath=True)
        tag_name = tag_name.strip(' ')
        added_tag = 0
        if tag_name:
            app = App.get_running_app()
            for photo in selected_photos:
                added = app.database_add_tag(photo, tag_name)
                if added:
                    added_tag = added_tag + 1
            self.select_none()
            if added_tag:
                if tag_name == 'favorite':
                    self.on_selected()
                app.photos.commit()
                self.update_treeview()
                app.message("Added tag '"+tag_name+"' to "+str(added_tag)+" files.")

    def add_to_tag_menu(self, instance):
        self.add_to_tag(instance.text)
        self.tag_menu.dismiss()

    def can_add_tag(self, tag_name):
        """Checks if a new tag can be created.
        Argument:
            tag_name: The tag name to check.
        Returns: True or False.
        """

        app = App.get_running_app()
        tag_name = tag_name.lower().strip(' ')
        tags = app.tags
        if tag_name and (tag_name not in tags) and (tag_name.lower() != 'favorite'):
            return True
        else:
            return False

    def add_tag(self, instance=None, answer="yes"):
        """Adds the current input tag to the app tags."""

        if answer == "yes":
            if instance is not None:
                tag_name = instance.ids['input'].text.lower().strip(' ')
                if not tag_name:
                    self.dismiss_popup()
                    return
            else:
                tag_input = self.ids['newTag']
                tag_name = tag_input.text.lower().strip(' ')
                tag_input.text = ''
            app = App.get_running_app()
            app.tag_make(tag_name)
            self.update_treeview()
        self.dismiss_popup()

    def can_add_album(self, album_name):
        """Checks if a new album can be created.
        Argument:
            album_name: The album name to check.
        Returns: True or False.
        """

        app = App.get_running_app()
        albums = app.albums
        album_name = album_name.strip(' ')
        if not album_name:
            return False
        for album in albums:
            if album['name'].lower() == album_name.lower():
                return False
        return True

    def add_album(self, instance=None, answer="yes"):
        """Adds the current input album to the app albums."""

        if answer == 'yes':
            if instance is not None:
                album = instance.ids['input'].text.strip(' ')
                if not album:
                    self.dismiss_popup()
                    return
            else:
                album_input = self.ids['newAlbum']
                album = album_input.text
                album_input.text = ''
            app = App.get_running_app()
            app.album_make(album, '')
            self.update_treeview()
        self.dismiss_popup()

    def toggle_expanded_folder(self, folder):
        if folder in self.expanded_folders:
            self.expanded_folders.remove(folder)
        else:
            self.expanded_folders.append(folder)
        self.update_treeview()

    def update_treeview(self, *_):
        """Updates the treeview's data"""

        if not self.ids:
            return

        app = App.get_running_app()
        database = self.ids['database']

        database.data = []
        data = []

        #add the favorites item
        total_favorites = len(app.database_get_tag('favorite'))
        if total_favorites > 0:
            total_photos = '('+str(total_favorites)+')'
        else:
            total_photos = ''
        database_favorites = {
            'fullpath': 'Favorites',
            'target': 'favorite',
            'owner': self,
            'type': 'Tag',
            'folder_name': 'Favorites',
            'total_photos_numeric': total_favorites,
            'total_photos': total_photos,
            'expandable': False,
            'displayable': True,
            'indent': 0,
            'subtext': '',
            'height': app.button_scale + int(app.button_scale * 0.1),
            'end': True,
            'dragable': False
        }
        data.append(database_favorites)

        #add the tags tree item
        sorted_tags = sorted(app.tags)
        expandable_tags = True if len(sorted_tags) > 0 else False
        tag_root = {
            'fullpath': 'Tags',
            'folder_name': 'Tags',
            'target': 'Tags',
            'type': 'Tag',
            'total_photos': '',
            'displayable': False,
            'expandable': expandable_tags,
            'expanded': True if (self.expanded_tags and expandable_tags) else False,
            'owner': self,
            'indent': 0,
            'subtext': '',
            'height': app.button_scale,
            'end': False,
            'dragable': False
        }
        data.append(tag_root)
        self.tag_menu.clear_widgets()
        menu_button = MenuButton(text='favorite')
        menu_button.bind(on_release=self.add_to_tag_menu)
        self.tag_menu.add_widget(menu_button)
        for tag in sorted_tags:
            total_photos = len(app.database_get_tag(tag))
            menu_button = MenuButton(text=tag)
            menu_button.bind(on_release=self.add_to_tag_menu)
            self.tag_menu.add_widget(menu_button)
            if self.expanded_tags:
                if total_photos > 0:
                    total_photos_text = '('+str(total_photos)+')'
                else:
                    total_photos_text = ''
                tag_item = {
                    'fullpath': 'Tag',
                    'folder_name': tag,
                    'total_photos': total_photos_text,
                    'total_photos_numeric': total_photos,
                    'target': tag,
                    'type': 'Tag',
                    'expandable': False,
                    'displayable': True,
                    'owner': self,
                    'indent': 1,
                    'subtext': '',
                    'end': False,
                    'height': app.button_scale,
                    'dragable': False
                }
                data.append(tag_item)
        data[-1]['end'] = True
        data[-1]['height'] = data[-1]['height'] + int(app.button_scale * 0.1)

        #add the albums tree item
        albums = sorted(app.albums, key=lambda x: x['name'])
        expandable_albums = True if len(albums) > 0 else False
        album_root = {
            'fullpath': 'Albums',
            'folder_name': 'Albums',
            'target': 'Albums',
            'type': 'Album',
            'total_photos': '',
            'displayable': False,
            'expandable': expandable_albums,
            'expanded': True if (self.expanded_albums and expandable_albums) else False,
            'owner': self,
            'indent': 0,
            'subtext': '',
            'height': app.button_scale,
            'end': False,
            'dragable': False
        }
        data.append(album_root)
        self.album_menu.clear_widgets()
        for album in albums:
            total_photos = len(album['photos'])
            menu_button = MenuButton(text=album['name'])
            menu_button.bind(on_release=self.add_to_album_menu)
            self.album_menu.add_widget(menu_button)
            if self.expanded_albums:
                if total_photos > 0:
                    total_photos_text = '('+str(total_photos)+')'
                else:
                    total_photos_text = ''
                album_item = {
                    'fullpath': album['name'],
                    'folder_name': album['name'],
                    'total_photos': total_photos_text,
                    'total_photos_numeric': total_photos,
                    'target': album['name'],
                    'type': 'Album',
                    'displayable': True,
                    'expandable': False,
                    'owner': self,
                    'indent': 1,
                    'subtext': '',
                    'height': app.button_scale,
                    'end': False,
                    'dragable': False
                }
                data.append(album_item)
        data[-1]['end'] = True
        data[-1]['height'] = data[-1]['height'] + int(app.button_scale * 0.1)

        #Get and sort folder list
        all_folders = self.get_folders()

        #Add folders to tree
        folder_root = {
            'fullpath': 'Folders',
            'folder_name': 'Folders',
            'target': 'Folders',
            'type': 'Folder',
            'total_photos': '',
            'displayable': False,
            'expandable': False,
            'expanded': True,
            'owner': self,
            'indent': 0,
            'subtext': '',
            'height': app.button_scale,
            'end': False,
            'dragable': False
        }
        data.append(folder_root)

        #Parse and sort folders and subfolders
        root_folders = []
        for full_folder in all_folders:
            if full_folder and not any(avoidfolder in full_folder for avoidfolder in avoidfolders):
                newname = full_folder
                children = root_folders
                parent_folder = ''
                while os.path.sep in newname:
                    #split the base path and the leaf paths
                    root, leaf = newname.split(os.path.sep, 1)
                    parent_folder = os.path.join(parent_folder, root)

                    #check if the root path is already in the tree
                    root_element = False
                    for child in children:
                        if child['folder'] == root:
                            root_element = child
                    if not root_element:
                        children.append({'folder': root, 'full_folder': parent_folder, 'children': []})
                        root_element = children[-1]
                    children = root_element['children']
                    newname = leaf
                root_element = False
                for child in children:
                    if child['folder'] == newname:
                        root_element = child
                if not root_element:
                    children.append({'folder': newname, 'full_folder': full_folder, 'children': []})

        #ensure that selected folder is expanded up to
        selected_folder = self.selected
        while os.path.sep in selected_folder:
            selected_folder, leaf = selected_folder.rsplit(os.path.sep, 1)
            if selected_folder not in self.expanded_folders:
                self.expanded_folders.append(selected_folder)

        folder_data = self.populate_folders(root_folders, self.expanded_folders)
        data = data + folder_data

        database.data = data
        self.show_selected()

    def populate_folders(self, folder_root, expanded):
        app = App.get_running_app()
        folders = []
        folder_root = self.sort_folders(folder_root)
        for folder in folder_root:
            full_folder = folder['full_folder']
            expandable = True if len(folder['children']) > 0 else False
            is_expanded = True if full_folder in expanded else False
            folder_info = app.database_folder_exists(full_folder)
            if folder_info:
                subtext = folder_info[1]
            else:
                subtext = ''
            total_photos = ''
            folder_element = {
                'fullpath': full_folder,
                'folder_name': folder['folder'],
                'target': full_folder,
                'type': 'Folder',
                'total_photos': total_photos,
                'displayable': True,
                'expandable': expandable,
                'expanded': is_expanded,
                'owner': self,
                'indent': 1 + full_folder.count(os.path.sep),
                'subtext': subtext,
                'height': app.button_scale * (1.5 if subtext else 1),
                'end': False,
                'dragable': True
            }
            folders.append(folder_element)
            if is_expanded:
                if len(folder['children']) > 0:
                    more_folders = self.populate_folders(folder['children'], expanded)
                    folders = folders + more_folders
                    folders[-1]['end'] = True
                    folders[-1]['height'] = folders[-1]['height'] + int(app.button_scale * 0.1)
        return folders

    def sort_folders(self, sort_folders):
        if self.sort_method in ['Total Photos', 'Title', 'Import Date', 'Modified Date']:
            app = App.get_running_app()
            folders = []
            for folder in sort_folders:
                folderpath = folder['full_folder']
                if self.sort_method == 'Total Photos':
                    sortby = len(app.database_get_folder(folderpath))
                elif self.sort_method == 'Title':
                    folderinfo = app.database_folder_exists(folderpath)
                    if folderinfo:
                        sortby = folderinfo[1]
                    else:
                        sortby = folderpath
                elif self.sort_method == 'Import Date':
                    folder_photos = app.database_get_folder(folderpath)
                    sortby = 0
                    for folder_photo in folder_photos:
                        if folder_photo[6] > sortby:
                            sortby = folder_photo[6]
                elif self.sort_method == 'Modified Date':
                    folder_photos = app.database_get_folder(folderpath)
                    sortby = 0
                    for folder_photo in folder_photos:
                        if folder_photo[7] > sortby:
                            sortby = folder_photo[7]

                folders.append([sortby, folder])
            sorted_folders = sorted(folders, key=lambda x: x[0], reverse=self.sort_reverse)
            sorts, all_folders = zip(*sorted_folders)
        else:
            all_folders = sorted(sort_folders, key=lambda x: x['folder'], reverse=self.sort_reverse)

        return all_folders

    def get_folders(self, *_):
        if self.update_folders:
            app = App.get_running_app()
            all_folders = app.database_get_folders(quick=True)
            self.folders = all_folders
            self.update_folders = False
        return self.folders

    def rename_folder(self):
        """Starts the folder renaming process, creates an input text popup."""

        content = InputPopup(hint='Folder Name', text='Rename To:')
        content.input_text = os.path.split(self.selected)[1]
        app = App.get_running_app()
        content.bind(on_answer=self.rename_folder_answer)
        self.popup = NormalPopup(title='Rename Folder', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 5),
                                 auto_dismiss=False)
        self.popup.open()

    def rename_folder_answer(self, instance, answer):
        """Tells the app to rename the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be renamed, all other answers will just close the dialog.
        """

        if answer == 'yes':
            text = instance.ids['input'].text.strip(' ')
            app = App.get_running_app()
            app.rename_folder(self.selected, text)
            self.update_folders = True
            self.selected = text
        self.dismiss_popup()
        self.update_treeview()

    def new_tag(self):
        """Starts the new tag process, creates an input text popup."""

        content = InputPopupTag(hint='Tag Name', text='Enter A Tag:')
        app = App.get_running_app()
        content.bind(on_answer=self.add_tag)
        self.popup = NormalPopup(title='Create Tag', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 5),
                                 auto_dismiss=False)
        self.popup.open()

    def new_album(self):
        """Starts the new album process, creates an input text popup."""

        content = InputPopup(hint='Album Name', text='Enter An Album Name:')
        app = App.get_running_app()
        content.bind(on_answer=self.add_album)
        self.popup = NormalPopup(title='Create Album', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 5),
                                 auto_dismiss=False)
        self.popup.open()

    def add_folder(self):
        """Starts the add folder process, creates an input text popup."""

        content = InputPopup(hint='Folder Name', text='Enter A Folder Name:')
        app = App.get_running_app()
        content.bind(on_answer=self.add_folder_answer)
        self.popup = NormalPopup(title='Create Folder', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 5),
                                 auto_dismiss=False)
        self.popup.open()

    def add_folder_answer(self, instance, answer):
        """Tells the app to rename the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be created, all other answers will just close the dialog.
        """

        if answer == 'yes':
            text = instance.ids['input'].text.strip(' ')
            if text:
                app = App.get_running_app()
                app.add_folder(text)
                self.update_folders = True
        self.dismiss_popup()
        self.update_treeview()

    def delete_folder(self):
        """Starts the delete folder process, creates the confirmation popup."""

        text = "Delete The Selected "+self.type+"?"
        if self.type.lower() == 'folder':
            text = text+"\nAll Included Photos And Videos Will Be Deleted."
        else:
            text = text+"\nThe Contained Files Will Not Be Deleted."
        content = ConfirmPopup(text=text, yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        app = App.get_running_app()
        content.bind(on_answer=self.delete_folder_answer)
        self.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 4),
                                 auto_dismiss=False)
        self.popup.open()

    def delete_folder_answer(self, instance, answer):
        """Tells the app to delete the folder if the dialog is confirmed.
        Arguments:
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be deleted, all other answers will just close the dialog.
        """

        del instance
        if answer == 'yes':
            app = App.get_running_app()
            delete_type = self.type
            delete_item = self.selected
            if delete_type == 'Album':
                album_index = app.album_find(delete_item)
                if album_index >= 0:
                    app.album_delete(album_index)
            elif delete_type == 'Tag':
                app.remove_tag(delete_item)
            elif delete_type == 'Folder':
                app.delete_folder(delete_item)
            self.previous_album()
            self.update_folders = True
        self.dismiss_popup()
        self.update_treeview()

    def move_folder_answer(self, folder, move_to, instance, answer):
        """Tells the app to move the folder if the dialog is confirmed.
        Arguments:
            folder: String, the path of the folder to be moved.
            move_to: String, the path to move the folder into.
            instance: The dialog that called this function.
            answer: String, if 'yes', the folder will be moved, all other answers will just close the dialog.
        """

        del instance
        if answer == 'yes':
            app = App.get_running_app()
            app.move_folder(folder, move_to)
            self.previous_album()
            self.update_folders = True
        self.dismiss_popup()
        self.update_treeview()

    def on_selected(self, *_):
        """Called when the selected folder/album/tag is changed.
        Clears and draws the photo list.
        """

        if self.parent and self.ids:
            dragable = False
            photos_area = self.ids['photos']
            photos_area.clear_selection()
            app = App.get_running_app()
            folder_title_type = self.ids['folderType']
            folder_details = self.ids['folderDetails']
            folder_details.clear_widgets()
            folder_path = self.ids['folderPath']
            delete_folder_button = self.ids['deleteFolder']
            rename_folder_button = self.ids['renameFolder']
            new_folder_button = self.ids['newFolder']
            operation_label = self.ids['operationType']
            Cache.remove('kv.loader')
            photos = []
            delete_button = self.ids['deleteButton']
            app.config.set("Settings", "viewtype", self.type)
            app.config.set("Settings", "viewtarget", self.selected)
            app.config.set("Settings", "viewdisplayable", self.displayable)

            if not self.displayable or not self.selected:  #Nothing is selected, fill with dummy data.
                operation_label.text = ''
                rename_folder_button.disabled = True
                delete_folder_button.disabled = True
                #new_folder_button.disabled = True
                self.can_export = False
                folder_title_type.text = ''
                folder_path.text = ''
                delete_button.text = 'Delete Selected'
                self.data = []
                if self.type == 'Album':
                    operation_label.text = 'Album:'
                elif self.type == 'Tag':
                    operation_label.text = 'Tag:'
                elif self.type == 'Folder':
                    operation_label.text = 'Folder:'
            else:
                new_folder_button.disabled = False
                delete_folder_button.disabled = False
                if self.type == 'Album':
                    operation_label.text = 'Album:'
                    rename_folder_button.disabled = True
                    folder_details.add_widget(self.album_details)
                    delete_button.text = 'Remove Selected'
                    folder_title_type.text = 'Album: '
                    folder_path.text = self.selected
                    for albuminfo in app.albums:
                        if albuminfo['name'] == self.selected:
                            folder_description = self.album_details.ids['albumDescription']
                            folder_description.text = albuminfo['description']
                            photo_paths = albuminfo['photos']
                            for fullpath in photo_paths:
                                photoinfo = app.database_exists(fullpath)
                                if photoinfo:
                                    photos.append(photoinfo)
                elif self.type == 'Tag':
                    operation_label.text = 'Tag:'
                    rename_folder_button.disabled = True
                    if self.selected == 'favorite':
                        delete_folder_button.disabled = True
                    delete_button.text = 'Remove Selected'
                    folder_title_type.text = 'Tagged As: '
                    folder_path.text = self.selected
                    photos = app.database_get_tag(self.selected)
                else:  #self.type == 'Folder'
                    operation_label.text = 'Folder:'
                    dragable = True
                    rename_folder_button.disabled = False
                    delete_button.text = 'Delete Selected'
                    folder_title_type.text = 'Folder: '
                    folder_path.text = self.selected
                    folder_details.add_widget(self.folder_details)
                    folder_title = self.folder_details.ids['folderTitle']
                    folder_description = self.folder_details.ids['folderDescription']

                    photos = app.database_get_folder(self.selected)

                    folderinfo = app.database_folder_exists(self.selected)
                    if folderinfo:
                        folder_title.text = folderinfo[1]
                        folder_description.text = folderinfo[2]
                    else:
                        database_folders = local_path(app.config.get('Database Directories', 'paths'))
                        databases = database_folders.split(';')
                        folderinfo = get_folder_info(self.selected, databases)
                        app.database_folder_add(folderinfo)
                        app.update_photoinfo(folderinfo[0])

                if self.album_sort_method == 'Import Date':
                    sorted_photos = sorted(photos, key=lambda x: x[6], reverse=self.album_sort_reverse)
                elif self.album_sort_method == 'Modified Date':
                    sorted_photos = sorted(photos, key=lambda x: x[7], reverse=self.album_sort_reverse)
                elif self.album_sort_method == 'Owner':
                    sorted_photos = sorted(photos, key=lambda x: x[11], reverse=self.album_sort_reverse)
                elif self.album_sort_method == 'File Name':
                    sorted_photos = sorted(photos, key=lambda x: os.path.basename(x[0]), reverse=self.album_sort_reverse)
                else:
                    sorted_photos = sorted(photos, key=lambda x: x[0], reverse=self.album_sort_reverse)

                self.photos = sorted_photos
                if sorted_photos:
                    self.can_export = True
                datas = []
                for photo in sorted_photos:
                    full_filename = os.path.join(photo[2], photo[0])
                    tags = photo[8].split(',')
                    favorite = True if 'favorite' in tags else False
                    fullpath = photo[0]
                    database_folder = photo[2]
                    video = os.path.splitext(full_filename)[1].lower() in movietypes
                    data = {
                        'fullpath': fullpath,
                        'photoinfo': photo,
                        'folder': self.selected,
                        'database_folder': database_folder,
                        'filename': full_filename,
                        'target': self.selected,
                        'type': self.type,
                        'owner': self,
                        'favorite': favorite,
                        'video': video,
                        'photo_orientation': photo[13],
                        'source': full_filename,
                        'temporary': False,
                        'selected': False,
                        'selectable': True,
                        'dragable': dragable
                    }
                    datas.append(data)
                self.data = datas
                app.thumbnails.commit()
            self.update_selected()

    def resort_method(self, method):
        """Sets the database sort method.
        Argument:
            method: String, the sort method to set.
        """

        self.sort_method = method
        app = App.get_running_app()
        app.config.set('Sorting', 'database_sort', method)
        self.update_folders = True
        self.update_treeview()

    def resort_reverse(self, reverse):
        """Sets the database sort reverse.
        Argument:
            reverse: String, if 'down', reverse will be enabled, disabled on any other string.
        """

        app = App.get_running_app()
        sort_reverse = True if reverse == 'down' else False
        app.config.set('Sorting', 'database_sort_reverse', sort_reverse)
        self.sort_reverse = sort_reverse
        self.update_folders = True
        self.update_treeview()

    def album_resort_method(self, method):
        """Sets the album sort method.
        Argument:
            method: String, the sort method to use
        """

        self.album_sort_method = method
        app = App.get_running_app()
        app.config.set('Sorting', 'album_sort', method)
        self.on_selected('', '')

    def album_resort_reverse(self, reverse):
        """Sets the album sort reverse.
        Argument:
            reverse: String, if 'down', reverse will be enabled, disabled on any other string.
        """

        app = App.get_running_app()
        album_sort_reverse = True if reverse == 'down' else False
        app.config.set('Sorting', 'album_sort_reverse', album_sort_reverse)
        self.album_sort_reverse = album_sort_reverse
        self.on_selected('', '')

    def on_enter(self, *_):
        """Called when the screen is entered.
        Sets up variables and widgets, and gets the screen ready to be filled with information."""

        app = App.get_running_app()
        app.fullpath = ''
        self.tag_menu = NormalDropDown()
        self.album_menu = NormalDropDown()
        self.ids['leftpanel'].width = app.left_panel_width()

        #self.can_export = False
        self.folder_details = FolderDetails(owner=self)
        self.album_details = AlbumDetails(owner=self)

        #Set up database sorting
        self.sort_dropdown = DatabaseSortDropDown()
        self.sort_dropdown.bind(on_select=lambda instance, x: self.resort_method(x))
        self.sort_method = app.config.get('Sorting', 'database_sort')
        self.sort_reverse = to_bool(app.config.get('Sorting', 'database_sort_reverse'))

        #Set up album sorting
        self.album_sort_dropdown = AlbumSortDropDown()
        self.album_sort_dropdown.bind(on_select=lambda instance, x: self.album_resort_method(x))
        self.album_sort_method = app.config.get('Sorting', 'album_sort')
        self.album_sort_reverse = to_bool(app.config.get('Sorting', 'album_sort_reverse'))
        self.update_folders = True
        self.update_treeview()
        self.on_selected()


class AlbumScreen(Screen):
    """Screen layout of the album viewer."""

    view_panel = StringProperty('')
    sort_reverse_button = StringProperty('normal')
    opencv = BooleanProperty()
    folder_title = StringProperty('Album Viewer')
    canprint = BooleanProperty(True)

    #Video reencode settings
    encoding = BooleanProperty(False)
    total_frames = NumericProperty()
    current_frame = NumericProperty()
    cancel_encoding = BooleanProperty()
    encoding_settings = {}
    encodingthread = ObjectProperty()
    encoding_process_thread = ObjectProperty()

    #Widget holder variables
    sort_dropdown = ObjectProperty()  #Holder for the sort method dropdown menu
    popup = None  #Holder for the screen's popup dialog
    edit_panel = StringProperty('main')  #The type of edit panel currently loaded
    edit_panel_object = ObjectProperty()  #Holder for the edit panel widget
    viewer = ObjectProperty()  #Holder for the photo viewer widget
    imagecache = None  #Holder for the image cacher thread

    #Variables relating to the photo list view on the left
    selected = StringProperty('')  #The current folder/album/tag being displayed
    type = StringProperty('None')  #'Folder', 'Album', 'Tag'
    target = StringProperty()  #The identifier of the album/folder/tag that is being viewed
    photos = []  #Photoinfo of all photos in the album
    sort_method = StringProperty('File Name')  #Current album sort method
    sort_reverse = BooleanProperty(False)

    #Variables relating to the photo view
    photoinfo = []  #photoinfo for the currently viewed photo
    photo = StringProperty('')  #The absolute path to the currently visible photo
    fullpath = StringProperty()  #The database-relative path of the current visible photo
    orientation = NumericProperty(1)  #EXIF Orientation of the currently viewed photo
    angle = NumericProperty(0)  #Corrective angle rotation of the currently viewed photo
    mirror = BooleanProperty(False)  #Corrective mirroring of the currently viewed photo
    favorite = BooleanProperty(False)  #True if the currently viewed photo is favorited
    view_image = BooleanProperty(True)  #True if the currently viewed photo is an image, false if it is a video
    image_x = NumericProperty(0)  #Set when the image is loaded, used for orientation of cropping
    image_y = NumericProperty(0)  #Set when the image is loaded, used for orientation of cropping

    #Stored variables for editing
    edit_color = BooleanProperty(False)
    equalize = NumericProperty(0)
    autocontrast = BooleanProperty(False)
    adaptive = NumericProperty(0)
    brightness = NumericProperty(0)
    gamma = NumericProperty(0)
    shadow = NumericProperty(0)
    contrast = NumericProperty(0)
    saturation = NumericProperty(0)
    temperature = NumericProperty(0)
    edit_advanced = BooleanProperty(False)
    tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    curve = ListProperty([[0, 0], [1, 1]])
    edit_filter = BooleanProperty(False)
    sharpen = NumericProperty(0)
    median = NumericProperty(0)
    bilateral = NumericProperty(0.5)
    bilateral_amount = NumericProperty(0)
    vignette_amount = NumericProperty(0)
    vignette_size = NumericProperty(0.5)
    edge_blur_amount = NumericProperty(0)
    edge_blur_size = NumericProperty(0.5)
    edge_blur_intensity = NumericProperty(0.5)
    edit_border = BooleanProperty(False)
    border_selected = StringProperty()
    border_x_scale = NumericProperty(0)
    border_y_scale = NumericProperty(0)
    border_opacity = NumericProperty(1)
    border_tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    edit_denoise = BooleanProperty(False)
    luminance_denoise = StringProperty('10')
    color_denoise = StringProperty('10')
    search_window = StringProperty('15')
    block_size = StringProperty('5')
    edit_crop = BooleanProperty(False)
    crop_top = NumericProperty(0)
    crop_right = NumericProperty(0)
    crop_bottom = NumericProperty(0)
    crop_left = NumericProperty(0)

    def show_tags_panel(self, *_):
        self.set_edit_panel('main')
        right_panel = self.ids['rightpanel']
        if self.view_panel == 'tags':
            right_panel.hidden = True
            self.view_panel = ''
            self.show_left_panel()
        else:
            self.view_panel = 'tags'
            right_panel.hidden = False
            app = App.get_running_app()
            if app.simple_interface:
                self.hide_left_panel()

    def show_info_panel(self, *_):
        self.set_edit_panel('main')
        right_panel = self.ids['rightpanel']
        if self.view_panel == 'info':
            right_panel.hidden = True
            self.view_panel = ''
            self.show_left_panel()
        else:
            self.view_panel = 'info'
            right_panel.hidden = False
            app = App.get_running_app()
            if app.simple_interface:
                self.hide_left_panel()

    def show_edit_panel(self, *_):
        self.set_edit_panel('main')
        right_panel = self.ids['rightpanel']
        if self.view_panel == 'edit':
            right_panel.hidden = True
            self.view_panel = ''
            self.show_left_panel()
        else:
            self.view_panel = 'edit'
            right_panel.hidden = False
            app = App.get_running_app()
            if app.simple_interface:
                self.hide_left_panel()

    def show_left_panel(self, *_):
        left_panel = self.ids['leftpanel']
        left_panel.hidden = False

    def hide_left_panel(self, *_):
        left_panel = self.ids['leftpanel']
        left_panel.hidden = True

    def cancel_encode(self, *_):
        """Signal to cancel the encodig process."""

        self.encoding = False
        self.cancel_encoding = True
        if self.encoding_process_thread:
            self.encoding_process_thread.kill()
        app = App.get_running_app()
        app.message("Canceled encoding.")

    def begin_encode(self):
        """Begins the encoding process, asks the user for confirmation with a popup."""

        self.set_edit_panel('main')
        self.encode_answer(self, 'yes')

    def encode_answer(self, instance, answer):
        """Continues the encoding process.
        If the answer was 'yes' will begin reencoding by starting the process thread.

        Arguments:
            instance: The widget that called this command.
            answer: String, 'yes' if confirm, anything else on deny.
        """

        del instance
        self.dismiss_popup()
        if answer == 'yes':
            app = App.get_running_app()
            self.viewer.stop()

            # Create popup to show progress
            self.cancel_encoding = False
            self.popup = ScanningPopup(title='Converting Video', auto_dismiss=False, size_hint=(None, None),
                                             size=(app.popup_x, app.button_scale * 4))
            self.popup.scanning_text = ''
            self.popup.open()
            encoding_button = self.popup.ids['scanningButton']
            encoding_button.bind(on_press=self.cancel_encode)

            # Start encoding thread
            self.encodingthread = threading.Thread(target=self.encode_process)
            self.encodingthread.start()

    def get_ffmpeg_audio_command(self, video_input_folder, video_input_filename, audio_input_folder, audio_input_filename, output_file_folder, encoding_settings=None):
        if not encoding_settings:
            encoding_settings = self.encoding_settings
        file_format = containers[containers_friendly.index(encoding_settings['file_format'])]
        audio_codec = audio_codecs[audio_codecs_friendly.index(encoding_settings['audio_codec'])]
        audio_bitrate = encoding_settings['audio_bitrate']
        extension = containers_extensions[containers.index(file_format)]

        video_file = video_input_folder+os.path.sep+video_input_filename
        audio_file = audio_input_folder+os.path.sep+audio_input_filename
        output_filename = os.path.splitext(video_input_filename)[0]+'-mux.'+extension
        output_file = output_file_folder+os.path.sep+output_filename
        audio_bitrate_settings = "-b:a " + audio_bitrate + "k"
        audio_codec_settings = "-c:a " + audio_codec + " -strict -2"

        command = 'ffmpeg -i "'+video_file+'" -i "'+audio_file+'" -map 0:v -map 1:a -codec copy '+audio_codec_settings+' '+audio_bitrate_settings+' -shortest "'+output_file+'"'
        return [True, command, output_filename]

    def get_ffmpeg_command(self, input_folder, input_filename, output_file_folder, noaudio=False, input_images=False, input_file=None, input_size=None, input_framerate=None, input_pixel_format=None, encoding_settings=None):
        if not encoding_settings:
            encoding_settings = self.encoding_settings
        file_format = containers[containers_friendly.index(encoding_settings['file_format'])]
        video_codec = video_codecs[video_codecs_friendly.index(encoding_settings['video_codec'])]
        audio_codec = audio_codecs[audio_codecs_friendly.index(encoding_settings['audio_codec'])]
        video_bitrate = encoding_settings['video_bitrate']
        audio_bitrate = encoding_settings['audio_bitrate']
        encoding_speed = encoding_settings['encoding_speed'].lower()
        deinterlace = encoding_settings['deinterlace']
        resize = encoding_settings['resize']
        resize_width = encoding_settings['width']
        resize_height = encoding_settings['height']
        encoding_command = encoding_settings['command_line']
        extension = containers_extensions[containers.index(file_format)]
        if not input_file:
            input_file = input_folder+os.path.sep+input_filename
        if input_framerate:
            output_framerate = self.new_framerate(video_codec, input_framerate)
        else:
            output_framerate = False
        if output_framerate:
            framerate_setting = "-r "+str(output_framerate[0] / output_framerate[1])
        else:
            framerate_setting = ""
        if input_images:
            input_format_settings = '-f image2pipe -vcodec mjpeg ' + framerate_setting
        else:
            input_format_settings = ''
        if input_pixel_format:
            output_pixel_format = self.new_pixel_format(video_codec, input_pixel_format)
        else:
            output_pixel_format = False
        if output_pixel_format:
            pixel_format_setting = "-pix_fmt "+str(output_pixel_format)
        else:
            pixel_format_setting = ""

        if video_codec == 'libx264':
            speed_setting = "-preset "+encoding_speed
        else:
            speed_setting = ''

        video_bitrate_settings = "-b:v "+video_bitrate+"k"
        if not noaudio:
            audio_bitrate_settings = "-b:a "+audio_bitrate+"k"
            audio_codec_settings = "-c:a " + audio_codec + " -strict -2"
        else:
            audio_bitrate_settings = ''
            audio_codec_settings = ''
        video_codec_settings = "-c:v "+video_codec
        file_format_settings = "-f "+file_format

        if input_size:
            if resize and (input_size[0] > int(resize_width) or input_size[1] > int(resize_height)):
                resize_settings = 'scale='+resize_width+":"+resize_height
            else:
                resize_settings = ''
        else:
            resize_settings = ''
        if deinterlace:
            deinterlace_settings = "yadif"
        else:
            deinterlace_settings = ""
        if deinterlace_settings or resize_settings:
            filter_settings = ' -vf "'
            if deinterlace_settings:
                filter_settings = filter_settings+deinterlace_settings
                if resize_settings:
                    filter_settings = filter_settings+', '+resize_settings
            else:
                filter_settings = filter_settings+resize_settings
            filter_settings = filter_settings+'" '
        else:
            filter_settings = ""

        if encoding_command:
            #check if encoding command is valid

            if '%i' not in encoding_command:
                return [False, 'Input file must be specified', '']
            if '%c' not in encoding_command:
                extension = ''
                if '-f' in encoding_command:
                    detect_format = encoding_command[encoding_command.find('-f')+2:].strip().split(' ')[0].lower()
                    supported_formats = fftools.get_fmts(output=True)
                    if detect_format in supported_formats[0]:
                        format_index = supported_formats[0].index(detect_format)
                        extension_list = supported_formats[2][format_index]
                        if extension_list:
                            extension = extension_list[0]
                if not extension:
                    return [False, 'Could not determine ffmpeg container format.', '']
            output_filename = os.path.splitext(input_filename)[0]+'.'+extension
            output_file = output_file_folder+os.path.sep+output_filename
            input_settings = ' -i "'+input_file+'" '
            encoding_command_reformat = encoding_command.replace('%c', file_format_settings).replace('%v', video_codec_settings).replace('%a', audio_codec_settings).replace('%f', framerate_setting).replace('%p', pixel_format_setting).replace('%b', video_bitrate_settings).replace('%d', audio_bitrate_settings).replace('%i', input_settings).replace('%%', '%')
            command = 'ffmpeg '+input_format_settings+encoding_command_reformat+' "'+output_file+'"'
        else:
            output_filename = os.path.splitext(input_filename)[0]+'.'+extension
            output_file = output_file_folder+os.path.sep+output_filename
            #command = 'ffmpeg '+file_format_settings+' -i "'+input_file+'"'+filter_settings+' -sn '+speed_setting+' '+video_codec_settings+' '+audio_codec_settings+' '+framerate_setting+' '+pixel_format_setting+' '+video_bitrate_settings+' '+audio_bitrate_settings+' "'+output_file+'"'
            command = 'ffmpeg '+input_format_settings+' -i "'+input_file+'" '+file_format_settings+' '+filter_settings+' -sn '+speed_setting+' '+video_codec_settings+' '+audio_codec_settings+' '+framerate_setting+' '+pixel_format_setting+' '+video_bitrate_settings+' '+audio_bitrate_settings+' "'+output_file+'"'
        return [True, command, output_filename]

    def encode_process(self):
        """Uses ffmpeg command line to reencode the current video file to a new format."""

        app = App.get_running_app()
        self.encoding = True
        input_file = self.photo

        input_video = MediaPlayer(input_file, ff_opts={'paused': True, 'ss': 1.0, 'an': True})
        frame = None
        while not frame:
            frame, value = input_video.get_frame(force_refresh=True)
        input_metadata = input_video.get_metadata()
        input_video.close_player()
        input_video = None

        framerate = input_metadata['frame_rate']
        self.total_frames = input_metadata['duration'] * (framerate[0] / framerate[1])
        pixel_format = input_metadata['src_pix_fmt']
        input_size = input_metadata['src_vid_size']
        input_file_folder, input_filename = os.path.split(input_file)
        output_file_folder = input_file_folder+os.path.sep+'reencode'
        command_valid, command, output_filename = self.get_ffmpeg_command(input_file_folder, input_filename, output_file_folder, input_size=input_size, input_framerate=framerate, input_pixel_format=pixel_format)
        if not command_valid:
            self.cancel_encode()
            self.dismiss_popup()
            app.popup_message(text=command, title='Warning')
        print(command)

        output_file = output_file_folder+os.path.sep+output_filename
        if not os.path.isdir(output_file_folder):
            try:
                os.makedirs(output_file_folder)
            except:
                self.cancel_encode()
                self.dismiss_popup()
                app.popup_message(text='Could not create folder for encode.', title='Warning')
                return
        if os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except:
                self.cancel_encode()
                self.dismiss_popup()
                app.popup_message(text='Could not create new encode, file already exists.', title='Warning')
                return

        self.encoding_process_thread = subprocess.Popen(command, bufsize=1, stdout=subprocess.PIPE,
                                                        stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

        # Poll process for new output until finished
        progress = []
        while True:
            if self.cancel_encoding:
                self.encoding_process_thread.kill()
                if os.path.isfile(output_file):
                    self.delete_output(output_file)
                if not os.listdir(output_file_folder):
                    os.rmdir(output_file_folder)
                self.dismiss_popup()
                return
            nextline = self.encoding_process_thread.stdout.readline()
            if nextline == '' and self.encoding_process_thread.poll() is not None:
                break
            if nextline.startswith('frame= '):
                self.current_frame = int(nextline.split('frame=')[1].split('fps=')[0].strip())
                scanning_percentage = self.current_frame / self.total_frames * 100
                self.popup.scanning_percentage = scanning_percentage
                time_done = nextline.split('time=')[1].split('bitrate=')[0].strip()
                remaining_frames = self.total_frames - self.current_frame
                try:
                    fps = int(nextline.split('fps=')[1].split('q=')[0].strip())
                    seconds_left = remaining_frames / fps
                    time_remaining = time_index(seconds_left)
                    time_text = "  Time: "+time_done.split('.')[0]+"  Remaining: "+time_remaining
                except:
                    time_text = ""
                self.popup.scanning_text = str(str(int(scanning_percentage)))+"%"+time_text
                progress.append(self.current_frame)
            sys.stdout.write(nextline)
            sys.stdout.flush()

        output = self.encoding_process_thread.communicate()[0]
        exit_code = self.encoding_process_thread.returncode

        error_code = ''
        if exit_code == 0:
            #encoding completed
            self.dismiss_popup()
            good_file = True

            if os.path.isfile(output_file):
                output_video = MediaPlayer(output_file, ff_opts={'paused': True, 'ss': 1.0, 'an': True})
                frame = None
                while not frame:
                    frame, value = output_video.get_frame(force_refresh=True)
                output_metadata = output_video.get_metadata()
                output_video.close_player()
                output_video = None
                if output_metadata:
                    new_size = (int(self.encoding_settings['width']), int(self.encoding_settings['height']))
                    if output_metadata['src_vid_size'] != new_size:
                        error_code = ', Output size is incorrect'
                        good_file = False
                else:
                    error_code = ', Unable to find output file metadata'
                    good_file = False
            else:
                error_code = ', Output file not found'
                good_file = False

            if not good_file:
                Clock.schedule_once(lambda x: app.message('Warning: Encoded file may be bad'+error_code))

            new_original_file = input_file_folder+os.path.sep+'.originals'+os.path.sep+input_filename
            if not os.path.isdir(input_file_folder+os.path.sep+'.originals'):
                os.makedirs(input_file_folder+os.path.sep+'.originals')
            new_encoded_file = input_file_folder+os.path.sep+output_filename
            if not os.path.isfile(new_original_file) and os.path.isfile(output_file):
                try:
                    os.rename(input_file, new_original_file)
                    os.rename(output_file, new_encoded_file)
                    if not os.listdir(output_file_folder):
                        os.rmdir(output_file_folder)

                    #update database
                    extension = os.path.splitext(output_file)[1]
                    new_photoinfo = list(self.photoinfo)
                    new_photoinfo[0] = os.path.splitext(self.photoinfo[0])[0]+extension  #fix extension
                    new_photoinfo[7] = int(os.path.getmtime(new_encoded_file))  #update modified date
                    new_photoinfo[9] = 1  #set edited
                    new_photoinfo[10] = new_original_file  #set original file
                    app.database_item_rename(self.photoinfo[0], new_photoinfo[0], new_photoinfo[1])
                    app.database_item_update(new_photoinfo)

                    # reload video in ui
                    self.fullpath = local_path(new_photoinfo[0])
                    self.photo = os.path.join(local_path(new_photoinfo[2]), local_path(new_photoinfo[0]))
                    Clock.schedule_once(lambda *dt: self.refresh_all())

                except:
                    app.popup_message(text='Could not replace original file', title='Warning')
                    return
            else:
                app.popup_message(text='Target file name already exists! Encoded file left in "/reencode" subfolder', title='Warning')
                return
            Clock.schedule_once(lambda x: app.message("Completed encoding file '"+self.photo+"'"))
        else:
            self.dismiss_popup()
            if os.path.isfile(output_file):
                self.delete_output(output_file)
            if not os.listdir(output_file_folder):
                os.rmdir(output_file_folder)
            app.popup_message(text='File not encoded, FFMPEG gave exit code '+str(exit_code), title='Warning')

        self.encoding = False

    def delete_output(self, output_file, timeout=20):
        """Continuously try to delete a file until its done."""

        start_time = time.time()
        while os.path.isfile(output_file):
            try:
                os.remove(output_file)
            except:
                time.sleep(0.25)
            if timeout != 0:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    return False
        return True

    def new_framerate(self, codec, framerate):
        """Given the old framerate, determine what the closest supported framerate for the current video codec is.
        Argument:
            framerate: 2-Tuple, frame rate numerator, and denominator
        Returns: 2-Tuple, frame rate numerator, and denominator
        """

        framerates = fftools.get_supported_framerates(codec_name=codec, rate=framerate)
        if framerates:
            return framerates[0]
        else:
            #all framerates supported, just return the given one
            return framerate

    def new_pixel_format(self, codec, pixel_format):
        """Given the old pixel format, determine what the closest supported format for the current video codec is.
        Argument:
            pixel_format: String, a pixel format name
        Returns: String, a pixel format name, or False if none found.
        """

        available_pixel_formats = fftools.get_supported_pixfmts(codec_name=codec, pix_fmt=pixel_format)
        if available_pixel_formats:
            return available_pixel_formats[0]
        else:
            return False

    def on_sort_reverse(self, *_):
        """Updates the sort reverse button's state variable, since kivy doesnt just use True/False for button states."""

        app = App.get_running_app()
        self.sort_reverse_button = 'down' if to_bool(app.config.get('Sorting', 'album_sort_reverse')) else 'normal'

    def delete_original(self):
        """Tries to delete the original version of an edited photo."""

        app = App.get_running_app()
        app.delete_photo_original(self.photoinfo)
        self.set_edit_panel('main')
        app.message("Deleted original file.")

    def restore_original(self):
        """Tries to restore the original version of an edited photo."""

        self.viewer.stop()
        app = App.get_running_app()
        edited_file = self.photo
        original_file = local_path(self.photoinfo[10])
        original_filename = os.path.split(original_file)[1]
        edited_filename = os.path.split(edited_file)[1]
        new_original_file = os.path.join(os.path.split(edited_file)[0], original_filename)
        if os.path.isfile(original_file):
            if os.path.isfile(edited_file):
                try:
                    os.remove(edited_file)
                except:
                    pass
            if os.path.isfile(edited_file):
                app.popup_message(text='Could not restore original file', title='Warning')
                return
            try:
                os.rename(original_file, new_original_file)
            except:
                pass
            if os.path.isfile(original_file) or not os.path.isfile(new_original_file):
                app.popup_message(text='Could not restore original file', title='Warning')
                return

            #update photo info
            if original_filename != edited_filename:
                edited_fullpath = os.path.split(self.photoinfo[0])[0]+'/'+original_filename
                app.database_item_rename(self.photoinfo[0], edited_fullpath, self.photoinfo[1])
                self.photoinfo[0] = edited_fullpath

            self.photoinfo[10] = os.path.basename(new_original_file)
            orientation = 1
            try:
                exif_tag = Image.open(edited_file)._getexif()
                if 274 in exif_tag:
                    orientation = exif_tag[274]
            except:
                pass

            self.photoinfo[13] = orientation
            self.photoinfo[9] = 0
            self.photoinfo[7] = int(os.path.getmtime(new_original_file))
            app.database_item_update(self.photoinfo)
            app.save_photoinfo(target=self.photoinfo[1],
                               save_location=os.path.join(self.photoinfo[2], self.photoinfo[1]))

            #regenerate thumbnail
            app.database_thumbnail_update(self.photoinfo[0], self.photoinfo[2], self.photoinfo[7], self.photoinfo[13],
                                          force=True)

            #reload photo image in ui
            self.fullpath = self.photoinfo[0]
            self.refresh_all()
            self.photo = new_original_file
            self.on_photo()
            self.clear_cache()
            app.message("Restored original file.")
            self.set_edit_panel('main')

        else:
            app.popup_message(text='Could not find original file', title='Warning')

    def set_edit_panel(self, panelname):
        """Switches the current edit panel to another.
        Argument:
            panelname: String, the name of the panel.
        """

        self.edit_panel = panelname
        Clock.schedule_once(lambda *dt: self.update_edit_panel())

    def export(self):
        """Switches to export screen."""

        if self.photos:
            app = App.get_running_app()
            app.export_target = self.target
            app.export_type = self.type
            app.show_export()

    def drop_widget(self, fullpath, position, dropped_type='file'):
        """Dummy function.  Here because the app can possibly call this function for any screen."""
        pass

    def text_input_active(self):
        """Detects if any text input fields are currently active (being typed in).
        Returns: True or False
        """

        input_active = False
        for widget in self.walk(restrict=True):
            if widget.__class__.__name__ == 'NormalInput' or widget.__class__.__name__ == 'FloatInput' or widget.__class__.__name__ == 'IntegerInput':
                if widget.focus:
                    input_active = True
                    break
        return input_active

    def has_popup(self):
        """Detects if the current screen has a popup active.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_popup(self):
        """Close a currently open popup for this screen."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def dismiss_extra(self):
        """Deactivates fullscreen mode on the video viewer if applicable.
        Returns: True if it was deactivated, False if not.
        """

        if self.encoding:
            self.cancel_encode()
            return True
        if self.edit_panel != 'main':
            self.set_edit_panel('main')
            return True
        if not self.view_image:
            if self.viewer.is_fullscreen():
                self.viewer.stop()
                return True
        return False

    def key(self, key):
        """Handles keyboard shortcuts, performs the actions needed.
        Argument:
            key: The name of the key command to perform.
        """

        if self.text_input_active():
            pass
        else:
            if not self.popup or (not self.popup.open):
                if key == 'left' or key == 'up':
                    self.previous_photo()
                if key == 'right' or key == 'down':
                    self.next_photo()
                if key == 'enter':
                    self.viewer.fullscreen()
                if key == 'space':
                    self.set_favorite()
                if key == 'delete':
                    self.delete()
                if key == 'f2':
                    self.show_info_panel()
                if key == 'f3':
                    self.show_edit_panel()
                if key == 'f4':
                    self.show_tags_panel()
            elif self.popup and self.popup.open:
                if key == 'enter':
                    self.popup.content.dispatch('on_answer', 'yes')

    def first_panel(self):
        """Switches the right panel area to the first tab."""

        tab_panel = self.ids['tabPanel']
        tabs = tab_panel.tab_list
        tab_panel.switch_to(tabs[2])

    def second_panel(self):
        """Switches the right panel area to the second tab."""

        tab_panel = self.ids['tabPanel']
        tabs = tab_panel.tab_list
        tab_panel.switch_to(tabs[1])

    def third_panel(self):
        """Switches the right panel area to the third tab."""

        tab_panel = self.ids['tabPanel']
        tabs = tab_panel.tab_list
        tab_panel.switch_to(tabs[0])

    def next_photo(self):
        """Changes the viewed photo to the next photo in the album index."""

        current_photo_index = self.current_photo_index()
        if current_photo_index == len(self.photos) -1:
            next_photo_index = 0
        else:
            next_photo_index = current_photo_index + 1
        new_photo = self.photos[next_photo_index]
        self.fullpath = new_photo[0]
        self.photo = os.path.join(new_photo[2], new_photo[0])
        self.scroll_photolist()

    def previous_photo(self):
        """Changes the viewed photo to the previous photo in the album index."""

        current_photo_index = self.current_photo_index()
        new_photo = self.photos[current_photo_index-1]
        self.fullpath = new_photo[0]
        self.photo = os.path.join(new_photo[2], new_photo[0])
        self.scroll_photolist()

    def set_favorite(self):
        """Toggles the currently viewed photo as favorite."""

        if self.target != 'Favorite':
            app = App.get_running_app()
            app.database_toggle_tag(self.fullpath, 'favorite')
            photo_info = app.database_exists(self.fullpath)
            self.photos[self.current_photo_index()] = photo_info
            self.update_tags()
            self.refresh_all()
            self.viewer.favorite = self.favorite

    def delete(self):
        """Begins the delete process.  Just calls 'delete_selected_confirm'.
        Not really necessary, but is here to mirror the database screen delete function.
        """

        self.delete_selected_confirm()

    def delete_selected_confirm(self):
        """Creates a delete confirmation popup and opens it."""

        if self.type == 'Album':
            content = ConfirmPopup(text='Remove This Photo From The Album "'+self.target+'"?', yes_text='Remove', no_text="Don't Remove", warn_yes=True)
        elif self.type == 'Tag':
            content = ConfirmPopup(text='Remove The Tag "'+self.target+'" From Selected Photo?', yes_text='Remove', no_text="Don't Remove", warn_yes=True)
        else:
            content = ConfirmPopup(text='Delete The Selected File?', yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        app = App.get_running_app()
        content.bind(on_answer=self.delete_selected_answer)
        self.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 4),
                                 auto_dismiss=False)
        self.popup.open()

    def delete_selected_answer(self, instance, answer):
        """Final step of the file delete process, if the answer was 'yes' will delete the selected files.
        Arguments:
            instance: The widget that called this command.
            answer: String, 'yes' if confirm, anything else on deny.
        """

        del instance
        if answer == 'yes':
            app = App.get_running_app()
            fullpath = self.fullpath
            filename = self.photo
            if self.type == 'Album':
                index = app.album_find(self.target)
                if index >= 0:
                    app.album_remove_photo(index, fullpath, message=True)
            elif self.type == 'Tag':
                app.database_remove_tag(fullpath, self.target, message=True)
            else:
                photo_info = app.database_exists(fullpath)
                app.delete_photo(fullpath, filename, message=True)
                if photo_info:
                    app.update_photoinfo(folders=photo_info[1])
            app.photos.commit()
            if len(self.photos) == 1:
                app.show_database()
            else:
                self.next_photo()
                self.update_tags()
                self.update_treeview()
        self.dismiss_popup()

    def current_photo_index(self):
        """Determines the index of the currently viewed photo in the album photos.
        Returns: Integer index value.
        """

        for index, photo in enumerate(self.photos):
            if photo[0] == self.fullpath:
                return index
        return 0

    def add_to_tag(self, tag_name):
        """Adds a tag to the currently viewed photo.
        Arguments:
            tag_name: Tag to add to current photo.
        """

        tag_name = tag_name.strip(' ')
        if tag_name:
            app = App.get_running_app()
            app.database_add_tag(self.fullpath, tag_name)
            self.update_tags()
            if tag_name == 'favorite':
                self.update_treeview()

    def can_add_tag(self, tag_name):
        """Checks if a new tag can be created.
        Argument:
            tag_name: The tag name to check.
        Returns: True or False.
        """

        app = App.get_running_app()
        tags = app.tags
        tag_name = tag_name.lower().strip(' ')
        if tag_name and (tag_name not in tags) and (tag_name.lower() != 'favorite'):
            return True
        else:
            return False

    def add_tag(self):
        """Adds the current input tag to the app tags."""

        app = App.get_running_app()
        tag_input = self.ids['newTag']
        tag_name = tag_input.text
        tag_name = tag_name.lower().strip(' ')
        app.tag_make(tag_name)
        tag_input.text = ''
        self.update_tags()

    def update_tags(self):
        """Reads all tags from the current image, and all app tags and refreshes the tag list in the tags panel."""

        app = App.get_running_app()
        display_tags = self.ids['panelDisplayTags']
        display_tags.clear_widgets()
        photo_info = app.database_exists(self.fullpath)
        if photo_info:
            tags = photo_info[8].split(',')
            if 'favorite' in tags:
                self.favorite = True
            else:
                self.favorite = False
            for tag in tags:
                if tag.strip(' '):
                    display_tags.add_widget(NormalLabel(text=tag, size_hint_x=1))
                    display_tags.add_widget(RemoveFromTagButton(to_remove=tag, remove_from=photo_info[0], owner=self))

        tag_list = self.ids['panelTags']
        tag_list.clear_widgets()
        tag_list.add_widget(TagSelectButton(type='Tag', text='favorite', target='favorite', owner=self))
        tag_list.add_widget(ShortLabel())
        for tag in app.tags:
            tag_list.add_widget(TagSelectButton(type='Tag', text=tag, target=tag, owner=self))
            tag_list.add_widget(RemoveTagButton(to_remove=tag, owner=self))

    def fullscreen(self):
        """Tells the viewer to switch to fullscreen mode."""

        if self.viewer:
            self.viewer.fullscreen()

    def on_photo(self, *_):
        """Called when a new photo is viewed.
        Sets up the photo viewer widget and updates all necessary settings."""

        if self.viewer:
            self.viewer.stop()  #Ensure that an old video is no longer playing.
        app = App.get_running_app()
        app.fullpath = self.fullpath
        app.photo = self.photo
        self.update_tags()

        #Set up photo viewer
        container = self.ids['photoViewerContainer']
        container.clear_widgets()
        self.photoinfo = app.database_exists(self.fullpath)
        if self.photoinfo:
            self.orientation = self.photoinfo[13]
        else:
            self.orientation = 1
            self.photoinfo = app.null_image()
        if self.orientation == 3 or self.orientation == 4:
            self.angle = 180
        elif self.orientation == 5 or self.orientation == 6:
            self.angle = 270
        elif self.orientation == 7 or self.orientation == 8:
            self.angle = 90
        else:
            self.angle = 0
        if self.orientation in [2, 4, 5, 7]:
            self.mirror = True
        else:
            self.mirror = False
        if os.path.splitext(self.photo)[1].lower() in imagetypes:
            #a photo is selected
            self.view_image = True
            if app.canprint():
                print_button = self.ids['printButton']
                print_button.disabled = False
            if not self.photo:
                self.photo = 'data/null.jpg'
            self.viewer = PhotoViewer(favorite=self.favorite, angle=self.angle, mirror=self.mirror, file=self.photo,
                                      photoinfo=self.photoinfo)
            container.add_widget(self.viewer)
        else:
            #a video is selected
            self.view_image = False
            if app.canprint():
                print_button = self.ids['printButton']
                print_button.disabled = True
            if not self.photo:
                self.photo = 'data/null.jpg'
            self.viewer = VideoViewer(favorite=self.favorite, angle=self.angle, mirror=self.mirror, file=self.photo,
                                      photoinfo=self.photoinfo)
            container.add_widget(self.viewer)
        app.refresh_photo(self.fullpath)
        self.refresh_photo()
        if app.config.getboolean("Settings", "precache"):
            self.imagecache = threading.Thread(target=self.cache_nearby_images)
            self.imagecache.start()
        self.set_edit_panel('main')  #Clear the edit panel
        #self.ids['album'].selected = self.fullpath

    def cache_nearby_images(self):
        """Determines the next and previous images in the list, and caches them to speed up browsing."""

        current_photo_index = self.current_photo_index()
        if current_photo_index == len(self.photos) -1:
            next_photo_index = 0
        else:
            next_photo_index = current_photo_index + 1
        next_photo_info = self.photos[next_photo_index]
        prev_photo_info = self.photos[current_photo_index-1]
        next_photo_filename = os.path.join(next_photo_info[2], next_photo_info[0])
        prev_photo_filename = os.path.join(prev_photo_info[2], prev_photo_info[0])
        if next_photo_filename != self.photo and os.path.splitext(next_photo_filename)[1].lower() in imagetypes:
            try:
                if os.path.splitext(next_photo_filename)[1].lower() == '.bmp':
                    next_photo = ImageLoaderPIL(next_photo_filename)
                else:
                    next_photo = Loader.image(next_photo_filename)
            except:
                pass
        if prev_photo_filename != self.photo and os.path.splitext(prev_photo_filename)[1].lower() in imagetypes:
            try:
                if os.path.splitext(prev_photo_filename)[1].lower() == '.bmp':
                    next_photo = ImageLoaderPIL(prev_photo_filename)
                else:
                    prev_photo = Loader.image(prev_photo_filename)
            except:
                pass

    def show_selected(self):
        album_container = self.ids['albumContainer']
        album = self.ids['album']
        selected = self.fullpath
        data = album_container.data
        current_photo = None
        for i, node in enumerate(data):
            if node['fullpath'] == selected:
                current_photo = node
                break
        if current_photo is not None:
            album.selected = current_photo

    def scroll_photolist(self):
        """Scroll the right-side photo list to the current active photo."""

        photolist = self.ids['albumContainer']
        self.show_selected()
        photolist.scroll_to_selected()

    def refresh_all(self):
        self.refresh_photolist()
        self.refresh_photoview()

    def refresh_photolist(self):
        """Reloads and sorts the photo list"""

        app = App.get_running_app()

        #Get photo list
        self.photos = []
        if self.type == 'Album':
            self.folder_title = 'Album: "'+self.target+'"'
            for albuminfo in app.albums:
                if albuminfo['name'] == self.target:
                    photo_paths = albuminfo['photos']
                    for fullpath in photo_paths:
                        photoinfo = app.database_exists(fullpath)
                        if photoinfo:
                            self.photos.append(photoinfo)
        elif self.type == 'Tag':
            self.folder_title = 'Tagged As: "'+self.target+'"'
            self.photos = app.database_get_tag(self.target)
        else:
            self.folder_title = 'Folder: "'+self.target+'"'
            self.photos = app.database_get_folder(self.target)

        #Sort photos
        if self.sort_method == 'Import Date':
            sorted_photos = sorted(self.photos, key=lambda x: x[6], reverse=self.sort_reverse)
        elif self.sort_method == 'Modified Date':
            sorted_photos = sorted(self.photos, key=lambda x: x[7], reverse=self.sort_reverse)
        elif self.sort_method == 'Owner':
            sorted_photos = sorted(self.photos, key=lambda x: x[11], reverse=self.sort_reverse)
        elif self.sort_method == 'File Name':
            sorted_photos = sorted(self.photos, key=lambda x: os.path.basename(x[0]), reverse=self.sort_reverse)
        else:
            sorted_photos = sorted(self.photos, key=lambda x: x[0], reverse=self.sort_reverse)
        self.photos = sorted_photos

    def refresh_photoview(self):
        #refresh recycleview
        photolist = self.ids['albumContainer']
        photodatas = []
        for photo in self.photos:
            photodata = {}
            source = os.path.join(photo[2], photo[0])
            photodata['text'] = os.path.basename(photo[0])
            photodata['source'] = source
            photodata['photoinfo'] = photo
            photodata['owner'] = self
            photodata['favorite'] = True if 'favorite' in photo[8].split(',') else False
            photodata['fullpath'] = photo[0]
            photodata['video'] = os.path.splitext(source)[1].lower() in movietypes
            photodata['selectable'] = True
            #if self.fullpath == photo[0]:
            #    photodata['selected'] = True
            #else:
            #    photodata['selected'] = False
            photodatas.append(photodata)
        photolist.data = photodatas

    def full_photo_refresh(self):
        app = App.get_running_app()
        app.refresh_photo(self.fullpath, force=True)
        self.refresh_photo()

    def refresh_photo(self):
        """Displays all the info for the current photo in the photo info right tab."""

        app = App.get_running_app()

        #Clear old info
        info_panel = self.ids['panelInfo']
        nodes = list(info_panel.iterate_all_nodes())
        for node in nodes:
            info_panel.remove_node(node)

        #Add basic info
        photoinfo = app.database_exists(self.fullpath)
        container = self.ids['photoViewerContainer']
        full_filename = os.path.join(photoinfo[2], photoinfo[0])
        filename = os.path.basename(photoinfo[0])
        info_panel.add_node(TreeViewInfo(title='Filename:', content=filename))
        path = os.path.join(photoinfo[2], photoinfo[1])
        info_panel.add_node(TreeViewInfo(title='Path:', content=path))
        database_folder = photoinfo[2]
        info_panel.add_node(TreeViewInfo(title='Database:', content=database_folder))
        import_date = datetime.datetime.fromtimestamp(photoinfo[6]).strftime('%Y-%m-%d, %I:%M%p')
        info_panel.add_node(TreeViewInfo(title='Import Date:', content=import_date))
        modified_date = datetime.datetime.fromtimestamp(photoinfo[7]).strftime('%Y-%m-%d, %I:%M%p')
        info_panel.add_node(TreeViewInfo(title='Modified Date:', content=modified_date))
        if os.path.exists(full_filename):
            file_size = format_size(int(os.path.getsize(full_filename)))
        else:
            file_size = format_size(photoinfo[4])
        info_panel.add_node(TreeViewInfo(title='File Size:', content=file_size))

        #Add resolution info
        try:
            pil_image = Image.open(self.photo)
            exif = pil_image._getexif()
        except:
            pil_image = False
            exif = []
        if pil_image:
            self.image_x, self.image_y = pil_image.size
            wrapper_size = container.size
            if wrapper_size[0] > 0:
                xscale = self.image_x/wrapper_size[0]
            else:
                xscale = 1
            if wrapper_size[1] > 0:
                yscale = self.image_y/wrapper_size[1]
            else:
                yscale = 1
            if xscale > yscale:
                scale_max = xscale
            else:
                scale_max = yscale
            if scale_max < 2 or to_bool(app.config.get("Settings", "lowmem")):
                scale_max = 2
            self.viewer.scale_max = scale_max
            resolution = str(self.image_x) + ' * ' + str(self.image_y)
            megapixels = round(((self.image_x * self.image_y) / 1000000), 2)
            info_panel.add_node(TreeViewInfo(title='Resolution:', content=str(megapixels) + 'MP (' + resolution + ')'))
        else:
            self.image_x = 0
            self.image_y = 0

        #Add exif info
        if exif:
            if 271 in exif:
                camera_type = exif[271]+' '+exif[272]
                info_panel.add_node(TreeViewInfo(title='Camera:', content=camera_type))
            if 33432 in exif:
                copyright = exif[33432]
                info_panel.add_node(TreeViewInfo(title='Copyright:', content=copyright))
            if 36867 in exif:
                camera_date = exif[36867]
                info_panel.add_node(TreeViewInfo(title='Date Taken:', content=camera_date))
            if 33434 in exif:
                exposure = exif[33434]
                camera_exposure = str(exposure[0]/exposure[1])+'seconds'
                info_panel.add_node(TreeViewInfo(title='Exposure Time:', content=camera_exposure))
            if 37377 in exif:
                camera_shutter_speed = str(exif[37377][0]/exif[37377][1])
                info_panel.add_node(TreeViewInfo(title='Shutter Speed:', content=camera_shutter_speed))
            if 33437 in exif:
                f_stop = exif[33437]
                camera_f = str(f_stop[0]/f_stop[1])
                info_panel.add_node(TreeViewInfo(title='F Stop:', content=camera_f))
            if 37378 in exif:
                camera_aperture = str(exif[37378][0]/exif[37378][0])
                info_panel.add_node(TreeViewInfo(title='Aperture:', content=camera_aperture))
            if 34855 in exif:
                camera_iso = str(exif[34855])
                info_panel.add_node(TreeViewInfo(title='ISO Level:', content=camera_iso))
            if 37385 in exif:
                flash = bin(exif[37385])[2:].zfill(8)
                camera_flash = 'Not Used' if flash[1] == '0' else 'Used'
                info_panel.add_node(TreeViewInfo(title='Flash:', content=str(camera_flash)))
            if 37386 in exif:
                focal_length = str(exif[37386][0]/exif[37386][1])+'mm'
                if 41989 in exif:
                    film_focal = exif[41989]
                    if film_focal != 0:
                        focal_length = focal_length+' ('+str(film_focal)+' 35mm equiv.)'
                info_panel.add_node(TreeViewInfo(title='Focal Length:', content=focal_length))
            if 41988 in exif:
                digital_zoom = exif[41988]
                if digital_zoom[0] != 0:
                    digital_zoom_amount = str(round(digital_zoom[0]/digital_zoom[1],2))+'X'
                    info_panel.add_node(TreeViewInfo(title='Digital Zoom:', content=digital_zoom_amount))
            if 34850 in exif:
                exposure_program = exif[34850]
                if exposure_program > 0:
                    if exposure_program == 1:
                        program_name = 'Manual'
                    elif exposure_program == 2:
                        program_name = 'Normal'
                    elif exposure_program == 3:
                        program_name = 'Aperture Priority'
                    elif exposure_program == 4:
                        program_name = 'Shutter Priority'
                    elif exposure_program == 5:
                        program_name = 'Creative Program'
                    elif exposure_program == 6:
                        program_name = 'Action Program'
                    elif exposure_program == 7:
                        program_name = 'Portrait'
                    else:
                        program_name = 'Landscape'
                    info_panel.add_node(TreeViewInfo(title='Exposure Mode:', content=program_name))

    def resort_method(self, method):
        """Sets the album sort method.
        Argument:
            method: String, the sort method to use
        """

        self.sort_method = method
        app = App.get_running_app()
        app.config.set('Sorting', 'album_sort', method)
        self.refresh_all()
        Clock.schedule_once(lambda *dt: self.scroll_photolist())

    def resort_reverse(self, reverse):
        """Sets the album sort reverse.
        Argument:
            reverse: String, if 'down', reverse will be enabled, disabled on any other string.
        """

        app = App.get_running_app()
        sort_reverse = True if reverse == 'down' else False
        app.config.set('Sorting', 'album_sort_reverse', sort_reverse)
        self.sort_reverse = sort_reverse
        self.refresh_all()
        Clock.schedule_once(lambda *dt: self.scroll_photolist())

    def add_program(self):
        """Add a new external program to the programs panel."""

        app = App.get_running_app()
        app.program_add('Program Name', 'command', '%i')
        self.edit_panel_object.update_programs(expand=True)

    def on_leave(self):
        """Called when the screen is left.  Clean up some things."""

        if self.viewer:
            self.viewer.stop()
        app = App.get_running_app()
        right_panel = self.ids['rightpanel']
        right_panel.width = app.right_panel_width()
        right_panel.hidden = True
        self.view_panel = ''
        self.show_left_panel()

    def clear_cache(self):
        """Clears cached images and thumbnails, the app will redraw all images.
        Also redraws photolist and photo viewer."""

        if self.viewer:
            if self.view_image:
                photoimage = self.viewer.ids['image']
                photoimage.source = ''
                photoimage.source = self.photo
        Cache.remove('kv.loader')
        Cache.remove('kv.image')
        Cache.remove('kv.texture')
        self.on_photo()
        self.update_tags()
        self.refresh_all()

    def update_treeview(self):
        """Called by delete buttons."""

        self.on_enter()
        self.on_photo()

    def on_enter(self):
        """Called when the screen is entered.  Set up variables and widgets, and prepare to view images."""

        self.opencv = opencv
        app = App.get_running_app()
        self.ids['leftpanel'].width = app.left_panel_width()
        right_panel = self.ids['rightpanel']
        right_panel.width = app.right_panel_width()
        right_panel.hidden = True
        self.view_panel = ''
        self.show_left_panel()

        #set up printing button
        if not app.canprint():
            self.canprint = False
        else:
            self.canprint = True

        #import variables
        self.target = app.target
        self.type = app.type

        #set up sort buttons
        self.sort_dropdown = AlbumSortDropDown()
        self.sort_dropdown.bind(on_select=lambda instance, x: self.resort_method(x))
        self.sort_method = app.config.get('Sorting', 'album_sort')
        self.sort_reverse = to_bool(app.config.get('Sorting', 'album_sort_reverse'))

        #refresh views
        self.update_tags()
        self.refresh_photolist()

        if self.photos:
            check_fullpath = ''
            check_photo = ''
            if app.fullpath:
                check_fullpath = app.fullpath
                check_photo = app.photo
            elif self.fullpath:
                check_fullpath = self.fullpath
                check_photo = self.photo
            photo_in_list = False
            for photoinfo in self.photos:
                if photoinfo[0] == check_fullpath:
                    photo_in_list = True
                    break
            if photo_in_list:
                self.fullpath = check_fullpath
                self.photo = check_photo
            else:
                photoinfo = self.photos[0]
                self.fullpath = photoinfo[0]
                self.photo = os.path.join(photoinfo[2], photoinfo[0])
            Clock.schedule_once(lambda *dt: self.scroll_photolist())
        self.refresh_photoview()

        #reset edit panel
        self.encoding = False
        self.cancel_encoding = False

    def update_edit_panel(self):
        """Set up the edit panel with the current preset."""
        if self.viewer and isfile2(self.photo):
            if self.edit_panel_object:
                self.edit_panel_object.save_last()
            self.viewer.edit_mode = self.edit_panel
            edit_panel_container = self.ids['panelEdit']
            edit_panel_container.clear_widgets()
            if self.edit_panel == 'main':
                self.edit_panel_object = EditMain(owner=self)
                self.viewer.bypass = False
            else:
                self.viewer.bypass = True
                self.viewer.stop()
                if self.edit_panel == 'color':
                    self.edit_panel_object = EditColorImage(owner=self)
                    self.viewer.edit_image.bind(histogram=self.edit_panel_object.draw_histogram)
                elif self.edit_panel == 'advanced':
                    self.edit_panel_object = EditColorImageAdvanced(owner=self)
                    self.viewer.edit_image.bind(histogram=self.edit_panel_object.draw_histogram)
                elif self.edit_panel == 'filter':
                    self.edit_panel_object = EditFilterImage(owner=self)
                elif self.edit_panel == 'border':
                    self.edit_panel_object = EditBorderImage(owner=self)
                elif self.edit_panel == 'denoise':
                    if opencv:
                        if self.view_image:
                            self.edit_panel_object = EditDenoiseImage(owner=self, imagefile=self.photo, image_x=self.image_x, image_y=self.image_y)
                    else:
                        self.edit_panel = 'main'
                        app = App.get_running_app()
                        app.message("Could Not Denoise, OpenCV Not Found")
                elif self.edit_panel == 'crop':
                    if self.view_image:
                        self.edit_panel_object = EditCropImage(owner=self, image_x=self.image_x, image_y=self.image_y)
                        self.viewer.edit_image.crop_controls = self.edit_panel_object
                elif self.edit_panel == 'rotate':
                    if self.view_image:
                        self.edit_panel_object = EditRotateImage(owner=self)
                elif self.edit_panel == 'convert':
                    if self.view_image:
                        self.edit_panel_object = EditConvertImage(owner=self)
                    else:
                        self.edit_panel_object = EditConvertVideo(owner=self)
            edit_panel_container.add_widget(self.edit_panel_object)
        else:
            if self.edit_panel_object:
                self.edit_panel_object.save_last()
            self.viewer.edit_mode = self.edit_panel
            edit_panel_container = self.ids['panelEdit']
            edit_panel_container.clear_widgets()
            self.edit_panel_object = EditNone(owner=self)

    def save_edit(self):
        if self.view_image:
            self.save_image()
        else:
            self.save_video()

    def cancel_save_video(self, *_):
        """Signal to cancel the video processing process."""

        self.encoding = False
        self.cancel_encoding = True
        if self.encoding_process_thread:
            self.encoding_process_thread.kill()
        app = App.get_running_app()
        app.message("Canceled video processing.")

    def save_video(self):
        app = App.get_running_app()
        app.save_encoding_preset()
        self.viewer.stop()

        # Create popup to show progress
        self.cancel_encoding = False
        self.popup = ScanningPopup(title='Processing Video', auto_dismiss=False, size_hint=(None, None),
                                   size=(app.popup_x, app.button_scale * 4))
        self.popup.scanning_text = ''
        self.popup.open()
        encoding_button = self.popup.ids['scanningButton']
        encoding_button.bind(on_press=self.cancel_save_video)

        # Start encoding thread
        self.encodingthread = threading.Thread(target=self.save_video_process)
        self.encodingthread.start()

    def failed_encode(self, message):
        app = App.get_running_app()
        self.cancel_save_video()
        self.dismiss_popup()
        self.encoding = False
        app.popup_message(text=message, title='Warning')

    def set_photo(self, photo):
        self.photo = photo
        self.refresh_photoview()

    def save_video_process(self):
        self.viewer.stop()
        app = App.get_running_app()
        input_file = self.photo
        input_file_folder, input_filename = os.path.split(input_file)
        output_file_folder = input_file_folder+os.path.sep+'reencode'

        encoding_settings = None
        preset_name = app.selected_encoder_preset
        for preset in app.encoding_presets:
            if preset['name'] == preset_name:
                encoding_settings = preset
        if not encoding_settings:
            encoding_settings = app.encoding_presets[0]

        if not os.path.isdir(output_file_folder):
            try:
                os.makedirs(output_file_folder)
            except:
                self.failed_encode('File not encoded, could not create temporary "reencode" folder')
                return

        edit_image = self.viewer.edit_image
        pixel_format = edit_image.pixel_format
        input_size = [edit_image.original_width, edit_image.original_height]
        edit_image.start_video_convert()
        frame_number = 1
        length = edit_image.length
        framerate = edit_image.framerate
        self.total_frames = length * (framerate[0] / framerate[1])

        command_valid, command, output_filename = self.get_ffmpeg_command(input_file_folder, input_filename, output_file_folder, noaudio=True, input_file='-', input_images=True, input_size=input_size, input_framerate=framerate, input_pixel_format=pixel_format, encoding_settings=encoding_settings)
        if not command_valid:
            self.failed_encode('Command not valid: '+command)
            return
        output_file = output_file_folder+os.path.sep+output_filename
        deleted = self.delete_output(output_file)
        if not deleted:
            self.failed_encode('File not encoded, temporary file already exists, could not delete')
            return
        #command = 'ffmpeg -f image2pipe -vcodec mjpeg -i "-" -vcodec libx264 -r 30 -b:v 8000k "'+output_file+'"'
        print(command)

        start_time = time.time()
        self.encoding_process_thread = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                        universal_newlines=True, shell=True)
        # Poll process for new output until finished
        while True:
            if self.cancel_encoding:
                self.dismiss_popup()
                self.encoding_process_thread.kill()
                deleted = self.delete_output(output_file)
                if not os.listdir(output_file_folder):
                    os.rmdir(output_file_folder)
                return
            frameinfo = edit_image.get_converted_frame()
            if frameinfo is None:
                #finished encoding
                break
            frame, pts = frameinfo
            try:
                frame.save(self.encoding_process_thread.stdin, 'JPEG')
            except:
                if not self.cancel_encoding:
                    lines = self.encoding_process_thread.stdout.readlines()
                    for line in lines:
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    deleted = self.delete_output(output_file)
                    if not os.listdir(output_file_folder):
                        try:
                            os.rmdir(output_file_folder)
                        except:
                            pass
                    self.failed_encode('Ffmpeg shut down, failed encoding on frame: '+str(frame_number))
                    return
            #output_file = output_file_folder+os.path.sep+'image'+str(frame_number).zfill(4)+'.jpg'
            #frame.save(output_file, "JPEG", quality=95)
            frame_number = frame_number+1
            scanning_percentage = (pts/length) * 95
            self.popup.scanning_percentage = scanning_percentage
            elapsed_time = time.time() - start_time

            try:
                percentage_remaining = 95 - scanning_percentage
                seconds_left = (elapsed_time * percentage_remaining) / scanning_percentage
                time_done = time_index(elapsed_time)
                time_remaining = time_index(seconds_left)
                time_text = "  Time: " + time_done + "  Remaining: " + time_remaining
            except:
                time_text = ""
            self.popup.scanning_text = str(int(scanning_percentage))+"%"+time_text

        self.encoding_process_thread.stdin.close()
        self.encoding_process_thread.wait()

        #output = self.encoding_process_thread.communicate()[0]
        exit_code = self.encoding_process_thread.returncode

        if exit_code == 0:
            #encoding first file completed, add audio
            command_valid, command, output_temp_filename = self.get_ffmpeg_audio_command(output_file_folder, output_filename, input_file_folder, input_filename, output_file_folder, encoding_settings=encoding_settings)
            output_temp_file = output_file_folder + os.path.sep + output_temp_filename

            print(command)
            self.encoding_process_thread = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                            universal_newlines=True, bufsize=1, shell=True)
            # Poll process for new output until finished
            deleted = self.delete_output(output_temp_file)
            if not deleted:
                self.failed_encode('File not encoded, temporary file already existed and could not be replaced')
                return
            while True:
                if self.cancel_encoding:
                    self.dismiss_popup()
                    self.encoding_process_thread.kill()
                    deleted = self.delete_output(output_file)
                    deleted = self.delete_output(output_temp_file)
                    if not os.listdir(output_file_folder):
                        try:
                            os.rmdir(output_file_folder)
                        except:
                            pass
                    return

                nextline = self.encoding_process_thread.stdout.readline()
                if nextline == '' and self.encoding_process_thread.poll() is not None:
                    break
                if nextline.startswith('frame= '):
                    self.current_frame = int(nextline.split('frame=')[1].split('fps=')[0].strip())
                    scanning_percentage = 95 + (self.current_frame / self.total_frames * 5)
                    self.popup.scanning_percentage = scanning_percentage
                    elapsed_time = time.time() - start_time

                    try:
                        percentage_remaining = 95 - scanning_percentage
                        seconds_left = (elapsed_time * percentage_remaining) / scanning_percentage
                        time_done = time_index(elapsed_time)
                        time_remaining = time_index(seconds_left)
                        time_text = "  Time: " + time_done + "  Remaining: " + time_remaining
                    except:
                        time_text = ""
                    self.popup.scanning_text = str(int(scanning_percentage)) + "%" + time_text

                sys.stdout.write(nextline)
                sys.stdout.flush()

            output = self.encoding_process_thread.communicate()[0]
            exit_code = self.encoding_process_thread.returncode

            #delete output_file
            deleted = self.delete_output(output_file)

            if exit_code == 0:
                #second encoding completed
                self.viewer.edit_image.close_video()

                new_original_file = input_file_folder+os.path.sep+'.originals'+os.path.sep+input_filename
                if not os.path.isdir(input_file_folder+os.path.sep+'.originals'):
                    os.makedirs(input_file_folder+os.path.sep+'.originals')
                new_encoded_file = input_file_folder+os.path.sep+output_filename

                new_photoinfo = list(self.photoinfo)
                #check if original file has been backed up already
                if not os.path.isfile(self.photoinfo[10]):
                    #original file exists
                    try:
                        os.rename(input_file, new_original_file)
                    except:
                        self.failed_encode('Could not replace video, converted video left in "reencode" subfolder')
                        return
                    new_photoinfo[10] = new_original_file
                else:
                    deleted = self.delete_output(input_file)
                    if not deleted:
                        self.failed_encode('Could not replace video, converted video left in "reencode" subfolder')
                        return
                try:
                    os.rename(output_temp_file, new_encoded_file)
                except:
                    self.failed_encode('Could not replace video, original file may be deleted, converted video left in "reencode" subfolder')
                    return

                if not os.listdir(output_file_folder):
                    os.rmdir(output_file_folder)

                #update database
                extension = os.path.splitext(new_encoded_file)[1]
                new_photoinfo[0] = os.path.splitext(self.photoinfo[0])[0]+extension  #fix extension
                new_photoinfo[7] = int(os.path.getmtime(new_encoded_file))  #update modified date
                new_photoinfo[9] = 1  #set edited

                # regenerate thumbnail
                app.database_thumbnail_update(self.photoinfo[0], self.photoinfo[2], self.photoinfo[7], self.photoinfo[13])

                if self.photoinfo[0] != new_photoinfo[0]:
                    app.database_item_rename(self.photoinfo[0], new_photoinfo[0], new_photoinfo[1])
                app.database_item_update(new_photoinfo)

                self.dismiss_popup()

                # reload video in ui
                self.photoinfo = new_photoinfo
                self.fullpath = local_path(new_photoinfo[0])
                #self.photo = os.path.join(local_path(new_photoinfo[2]), local_path(new_photoinfo[0]))
                Clock.schedule_once(lambda *dt: self.set_photo(os.path.join(local_path(new_photoinfo[2]), local_path(new_photoinfo[0]))))

                #Clock.schedule_once(lambda *dt: self.refresh_photolist())
                Clock.schedule_once(lambda x: app.message("Completed encoding file '"+self.photo+"'"))
            else:
                #failed second encode, clean up
                self.dismiss_popup()
                self.delete_output(output_file)
                self.delete_output(output_temp_file)
                if not os.listdir(output_file_folder):
                    os.rmdir(output_file_folder)
                app.popup_message(text='Second file not encoded, FFMPEG gave exit code '+str(exit_code), title='Warning')
                return
        else:
            #failed first encode, clean up
            self.failed_encode('First file not encoded, FFMPEG gave exit code '+str(exit_code))
            deleted = self.delete_output(output_file)
            if not os.listdir(output_file_folder):
                try:
                    os.rmdir(output_file_folder)
                except:
                    pass
        if self.encoding_process_thread:
            self.encoding_process_thread.kill()
        self.encoding = False
        self.set_edit_panel('main')

    def save_image(self):
        """Saves any temporary edits on the currently viewed image."""

        app = App.get_running_app()

        #generate full quality image
        edit_image = self.viewer.edit_image.get_full_quality()

        #back up old image and save new edit
        photo_file = self.photo
        backup_directory = local_path(self.photoinfo[2])+os.path.sep+local_path(self.photoinfo[1])+os.path.sep+'.originals'
        if not os.path.exists(backup_directory):
            os.mkdir(backup_directory)
        if not os.path.exists(backup_directory):
            app.popup_message(text='Could not create backup directory', title='Warning')
            return
        backup_photo_file = backup_directory+os.path.sep+os.path.basename(self.photo)
        if not os.path.isfile(photo_file):
            app.popup_message(text='Photo file no longer exists', title='Warning')
            return
        if not os.path.isfile(backup_photo_file):
            try:
                os.rename(photo_file, backup_photo_file)
            except Exception as e:
                print(e)
                pass
        if not os.path.isfile(backup_photo_file):
            app.popup_message(text='Could not create backup photo', title='Warning')
            return
        if os.path.isfile(photo_file):
            try:
                os.remove(photo_file)
            except:
                pass
        if os.path.isfile(photo_file):
            app.popup_message(text='Could not save edited photo', title='Warning')
            return
        edit_image.save(photo_file, "JPEG", quality=95)
        if not os.path.isfile(photo_file):
            if os.path.isfile(backup_photo_file):
                copy2(backup_photo_file, photo_file)
                app.popup_message(text='Could not save edited photo, restoring backup', title='Warning')
            else:
                app.popup_message(text='Could not save edited photo', title='Warning')
            return

        #update photo info
        self.photoinfo[10] = agnostic_path(backup_photo_file)
        self.photoinfo[13] = 1
        self.photoinfo[9] = 1
        self.photoinfo[7] = int(os.path.getmtime(photo_file))
        update_photoinfo = list(self.photoinfo)
        update_photoinfo[0] = agnostic_path(update_photoinfo[0])
        update_photoinfo[1] = agnostic_path(update_photoinfo[1])
        update_photoinfo[2] = agnostic_path(update_photoinfo[2])
        app.database_item_update(update_photoinfo)
        app.save_photoinfo(target=self.photoinfo[1],
                           save_location=os.path.join(self.photoinfo[2], self.photoinfo[1]))

        #regenerate thumbnail
        app.database_thumbnail_update(self.photoinfo[0], self.photoinfo[2], self.photoinfo[7], self.photoinfo[13])

        #reload photo image in ui
        self.clear_cache()

        #close edit panel
        self.set_edit_panel('main')
        app.message("Saved edits to image")


class TransferScreen(Screen):
    """Database folder transfer screen layout."""

    popup = None
    database_dropdown_left = ObjectProperty()
    database_dropdown_right = ObjectProperty()
    left_database = StringProperty()
    right_database = StringProperty()
    left_sort_method = StringProperty()
    right_sort_method = StringProperty()
    left_sort_reverse = BooleanProperty()
    right_sort_reverse = BooleanProperty()
    left_sort_dropdown = ObjectProperty()
    right_sort_dropdown = ObjectProperty()
    quick = BooleanProperty(False)

    transfer_from = StringProperty()
    transfer_to = StringProperty()
    folders = ListProperty()

    cancel_copying = BooleanProperty(False)
    copying = BooleanProperty(False)
    copyingpopup = ObjectProperty()
    percent_completed = NumericProperty(0)
    copyingthread = ObjectProperty()

    selected = ''
    expanded_folders = []

    def has_popup(self):
        """Detects if the current screen has a popup active.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_extra(self):
        """Cancels the copy process if it is running"""

        if self.copying:
            self.cancel_copy()
            return True
        else:
            return False

    def dismiss_popup(self):
        """Close a currently open popup for this screen."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def key(self, key):
        """Dummy function, not valid for this screen but the app calls it."""

        if not self.popup or (not self.popup.open):
            del key

    def resort_method_left(self, method):
        self.left_sort_method = method
        self.refresh_left_database()

    def resort_method_right(self, method):
        self.right_sort_method = method
        self.refresh_right_database()

    def left_resort_reverse(self, reverse):
        sort_reverse = True if reverse == 'down' else False
        self.left_sort_reverse = sort_reverse
        self.refresh_left_database()

    def right_resort_reverse(self, reverse):
        sort_reverse = True if reverse == 'down' else False
        self.right_sort_reverse = sort_reverse
        self.refresh_right_database()

    def on_enter(self):
        """Called when screen is entered, set up the needed variables and image viewer."""

        app = App.get_running_app()

        #set up sort buttons
        self.left_sort_dropdown = DatabaseSortDropDown()
        self.left_sort_dropdown.bind(on_select=lambda instance, x: self.resort_method_left(x))
        self.left_sort_method = app.config.get('Sorting', 'database_sort')
        self.left_sort_reverse = to_bool(app.config.get('Sorting', 'database_sort_reverse'))
        self.right_sort_dropdown = DatabaseSortDropDown()
        self.right_sort_dropdown.bind(on_select=lambda instance, x: self.resort_method_right(x))
        self.right_sort_method = app.config.get('Sorting', 'database_sort')
        self.right_sort_reverse = to_bool(app.config.get('Sorting', 'database_sort_reverse'))

        databases = app.get_database_directories()
        self.database_dropdown_left = NormalDropDown()
        self.database_dropdown_right = NormalDropDown()
        for database in databases:
            database_button_left = MenuButton(text=database)
            database_button_left.bind(on_release=self.set_database_left)
            self.database_dropdown_left.add_widget(database_button_left)
            database_button_right = MenuButton(text=database)
            database_button_right.bind(on_release=self.set_database_right)
            self.database_dropdown_right.add_widget(database_button_right)
        self.left_database = databases[0]
        self.right_database = databases[1]
        self.refresh_databases()

    def set_database_left(self, button):
        self.database_dropdown_left.dismiss()
        if self.right_database == button.text:
            self.right_database = self.left_database
            self.refresh_right_database()
        self.left_database = button.text
        self.refresh_left_database()

    def set_database_right(self, button):
        self.database_dropdown_right.dismiss()
        if self.left_database == button.text:
            self.left_database = self.right_database
            self.refresh_left_database()
        self.right_database = button.text
        self.refresh_right_database()

    def refresh_left_database(self):
        database_area = self.ids['leftDatabaseHolder']
        self.refresh_database_area(database_area, self.left_database, self.left_sort_method, self.left_sort_reverse)

    def refresh_right_database(self):
        database_area = self.ids['rightDatabaseHolder']
        self.refresh_database_area(database_area, self.right_database, self.right_sort_method, self.right_sort_reverse)

    def drop_widget(self, fullpath, position, dropped_type):
        """Called when a widget is dropped after being dragged.
        Determines what to do with the widget based on where it is dropped.
        Arguments:
            fullpath: String, file location of the object being dragged.
            position: List of X,Y window coordinates that the widget is dropped on.
            dropped_type: String, describes the object's database origin directory
        """

        app = App.get_running_app()
        transfer_from = dropped_type
        left_database_holder = self.ids['leftDatabaseHolder']
        left_database_area = self.ids['leftDatabaseArea']
        right_database_holder = self.ids['rightDatabaseHolder']
        right_database_area = self.ids['rightDatabaseArea']
        transfer_to = False
        folders = []
        if left_database_holder.collide_point(position[0], position[1]):
            if transfer_from != self.left_database:
                selects = right_database_area.selects
                for select in selects:
                    folders.append(local_path(select['fullpath']))
                transfer_to = self.left_database
        elif right_database_holder.collide_point(position[0], position[1]):
            if transfer_from != self.right_database:
                selects = left_database_area.selects
                for select in selects:
                    folders.append(local_path(select['fullpath']))
                transfer_to = self.right_database
        if transfer_to:
            if fullpath not in folders:
                folders.append(fullpath)
            #remove subfolders
            removes = []
            for folder in folders:
                for fold in folders:
                    if folder.startswith(fold+os.path.sep):
                        removes.append(folder)
                        break
            reduced_folders = []
            for folder in folders:
                if folder not in removes:
                    reduced_folders.append(folder)

            content = ConfirmPopup(text='Move These Folders From "'+transfer_from+'" to "'+transfer_to+'"?', yes_text='Move', no_text="Don't Move", warn_yes=True)
            content.bind(on_answer=self.move_folders)
            self.transfer_to = transfer_to
            self.transfer_from = transfer_from
            self.folders = reduced_folders
            self.popup = MoveConfirmPopup(title='Confirm Move', content=content, size_hint=(None, None),
                                          size=(app.popup_x, app.button_scale * 4),
                                          auto_dismiss=False)
            self.popup.open()

    def cancel_copy(self, *_):
        self.cancel_copying = True

    def move_folders(self, instance, answer):
        del instance
        app = App.get_running_app()
        self.dismiss_popup()
        if answer == 'yes':
            self.cancel_copying = False
            self.copyingpopup = ScanningPopup(title='Moving Files', auto_dismiss=False, size_hint=(None, None),
                                              size=(app.popup_x, app.button_scale * 4))
            self.copyingpopup.open()
            scanning_button = self.copyingpopup.ids['scanningButton']
            scanning_button.bind(on_press=self.cancel_copy)

            # Start importing thread
            self.percent_completed = 0
            self.copyingthread = threading.Thread(target=self.move_process)
            self.copyingthread.start()

    def move_process(self):
        app = App.get_running_app()
        self.quick = app.config.get("Settings", "quicktransfer")
        transfer_from = self.transfer_from
        transfer_to = self.transfer_to
        folders = self.folders

        total_files = 0
        total_size = 0
        for folder in folders:
            origin = os.path.join(transfer_from, folder)
            for root, dirs, files in os.walk(origin):
                for file in files:
                    total_files = total_files + 1
                    total_size = total_size + os.path.getsize(os.path.join(root, file))

        current_files = 0
        current_size = 0
        for folder in folders:
            origin = os.path.join(transfer_from, folder)
            #target = os.path.join(transfer_to, folder)
            for root, dirs, files in os.walk(origin, topdown=False):
                for file in files:
                    copy_from = os.path.join(root, file)
                    fullpath = os.path.relpath(copy_from, transfer_from)
                    copy_to = os.path.join(transfer_to, fullpath)
                    directory = os.path.split(copy_to)[0]
                    if not os.path.isdir(directory):
                        os.makedirs(directory)
                    self.copyingpopup.scanning_text = "Moving "+str(current_files)+" of "+str(total_files)+"."
                    self.copyingpopup.scanning_percentage = (current_size / total_size) * 100

                    if self.cancel_copying:
                        app.message("Canceled Moving Files, "+str(current_files)+" Files Moved.")
                        app.photos.commit()
                        self.copyingpopup.dismiss()
                        return
                    fileinfo = app.database_exists(fullpath)
                    copied = False
                    if self.quick == '1':
                        try:
                            move(copy_from, copy_to)
                            copied = True
                        except:
                            pass
                    else:
                        result = verify_copy(copy_from, copy_to)
                        if result is True:
                            os.remove(copy_from)
                            copied = True
                    if copied:
                        if fileinfo:
                            fileinfo[2] = transfer_to
                            app.database_item_database_move(fileinfo)
                        current_files = current_files + 1
                        current_size = current_size + os.path.getsize(copy_to)
                    if os.path.isfile(copy_from):
                        if os.path.split(copy_from)[1] == '.photoinfo.ini':
                            os.remove(copy_from)
                try:
                    os.rmdir(root)
                except:
                    pass
        self.copyingpopup.dismiss()
        app.photos.commit()
        app.message("Finished Moving "+str(current_files)+" Files.")
        Clock.schedule_once(self.refresh_databases)

    def toggle_expanded_folder(self, folder):
        if folder in self.expanded_folders:
            self.expanded_folders.remove(folder)
        else:
            self.expanded_folders.append(folder)
        self.refresh_databases()

    def refresh_database_area(self, database, database_folder, sort_method, sort_reverse):
        app = App.get_running_app()

        database.data = []
        data = []

        #Get and sort folder list
        unsorted_folders = app.database_get_folders(database_folder=database_folder)
        if sort_method in ['Total Photos', 'Title', 'Import Date', 'Modified Date']:
            folders = []
            for folder in unsorted_folders:
                folderpath = folder
                if sort_method == 'Total Photos':
                    sortby = len(app.database_get_folder(folderpath, database=database_folder))
                elif sort_method == 'Title':
                    folderinfo = app.database_folder_exists(folderpath)
                    if folderinfo:
                        sortby = folderinfo[1]
                    else:
                        sortby = folderpath
                elif sort_method == 'Import Date':
                    folder_photos = app.database_get_folder(folderpath, database=database_folder)
                    sortby = 0
                    for folder_photo in folder_photos:
                        if folder_photo[6] > sortby:
                            sortby = folder_photo[6]
                elif sort_method == 'Modified Date':
                    folder_photos = app.database_get_folder(folderpath, database=database_folder)
                    sortby = 0
                    for folder_photo in folder_photos:
                        if folder_photo[7] > sortby:
                            sortby = folder_photo[7]

                folders.append([sortby, folderpath])
            sorted_folders = sorted(folders, key=lambda x: x[0], reverse=sort_reverse)
            sorts, all_folders = zip(*sorted_folders)
        else:
            all_folders = sorted(unsorted_folders, reverse=sort_reverse)

        #Parse and sort folders and subfolders
        root_folders = []
        for full_folder in all_folders:
            if full_folder and not any(avoidfolder in full_folder for avoidfolder in avoidfolders):
                newname = full_folder
                children = root_folders
                parent_folder = ''
                while os.path.sep in newname:
                    #split the base path and the leaf paths
                    root, leaf = newname.split(os.path.sep, 1)
                    parent_folder = os.path.join(parent_folder, root)

                    #check if the root path is already in the tree
                    root_element = False
                    for child in children:
                        if child['folder'] == root:
                            root_element = child
                    if not root_element:
                        children.append({'folder': root, 'full_folder': parent_folder, 'children': []})
                        root_element = children[-1]
                    children = root_element['children']
                    newname = leaf
                root_element = False
                for child in children:
                    if child['folder'] == newname:
                        root_element = child
                if not root_element:
                    children.append({'folder': newname, 'full_folder': full_folder, 'children': []})

        folder_data = self.populate_folders(root_folders, self.expanded_folders, sort_method, sort_reverse, database_folder)
        data = data + folder_data

        database.data = data

    def populate_folders(self, folder_root, expanded, sort_method, sort_reverse, database_folder):
        app = App.get_running_app()
        folders = []
        folder_root = self.sort_folders(folder_root, sort_method, sort_reverse)
        for folder in folder_root:
            full_folder = folder['full_folder']
            expandable = True if len(folder['children']) > 0 else False
            is_expanded = True if full_folder in expanded else False
            folder_info = app.database_folder_exists(full_folder)
            if folder_info:
                subtext = folder_info[1]
            else:
                subtext = ''
            folder_element = {
                'fullpath': full_folder,
                'folder_name': folder['folder'],
                'target': full_folder,
                'type': 'Folder',
                'total_photos': '',
                'total_photos_numeric': 0,
                'displayable': True,
                'expandable': expandable,
                'expanded': is_expanded,
                'owner': self,
                'indent': 1 + full_folder.count(os.path.sep),
                'subtext': subtext,
                'height': app.button_scale * (1.5 if subtext else 1),
                'end': False,
                'droptype': database_folder,
                'dragable': True
            }
            folders.append(folder_element)
            if is_expanded:
                if len(folder['children']) > 0:
                    more_folders = self.populate_folders(folder['children'], expanded)
                    folders = folders + more_folders
                    folders[-1]['end'] = True
                    folders[-1]['height'] = folders[-1]['height'] + int(app.button_scale * 0.1)
        return folders

    def sort_folders(self, sort_folders, sort_method, sort_reverse):
        if sort_method in ['Total Photos', 'Title', 'Import Date', 'Modified Date']:
            app = App.get_running_app()
            folders = []
            for folder in sort_folders:
                folderpath = folder['full_folder']
                if sort_method == 'Total Photos':
                    sortby = len(app.database_get_folder(folderpath))
                elif sort_method == 'Title':
                    folderinfo = app.database_folder_exists(folderpath)
                    if folderinfo:
                        sortby = folderinfo[1]
                    else:
                        sortby = folderpath
                elif sort_method == 'Import Date':
                    folder_photos = app.database_get_folder(folderpath)
                    sortby = 0
                    for folder_photo in folder_photos:
                        if folder_photo[6] > sortby:
                            sortby = folder_photo[6]
                elif sort_method == 'Modified Date':
                    folder_photos = app.database_get_folder(folderpath)
                    sortby = 0
                    for folder_photo in folder_photos:
                        if folder_photo[7] > sortby:
                            sortby = folder_photo[7]

                folders.append([sortby, folder])
            sorted_folders = sorted(folders, key=lambda x: x[0], reverse=sort_reverse)
            sorts, all_folders = zip(*sorted_folders)
        else:
            all_folders = sorted(sort_folders, key=lambda x: x['folder'], reverse=sort_reverse)

        return all_folders

    def refresh_databases(self, *_):
        self.refresh_left_database()
        self.refresh_right_database()


class Curves(FloatLayout):
    """Widget for viewing and generating color curves information."""

    points = ListProperty()  #List of curves points
    current_point = ListProperty()  #
    moving = BooleanProperty(False)  #
    touch_range = NumericProperty(0.1)  #
    scroll_timeout = NumericProperty()  #
    curve = ListProperty()  #
    resolution = 256  #Horizontal resolution of the curve
    bytes = 256  #Vertical resolution of the curve

    def __init__(self, **kwargs):
        super(Curves, self).__init__(**kwargs)
        self.bind(pos=self.refresh, size=self.refresh)
        self.points = [[0, 0], [1, 1]]

    def reset(self):
        """Clears the canvas and sets up the default curve."""

        self.points = [[0, 0], [1, 1]]
        self.refresh()

    def refresh(self, *_):
        """Sorts and redraws points on the canvas."""

        if len(self.points) < 2:
            self.reset()
        self.points = sorted(self.points, key=itemgetter(0))
        self.points[0][0] = 0
        self.points[-1][0] = 1

        canvas = self.canvas
        canvas.clear()
        canvas.before.add(Color(0, 0, 0))
        canvas.before.add(Rectangle(size=self.size, pos=self.pos))
        self.generate_curve()
        self.draw_line(canvas)

        for point in self.points:
            self.draw_point(canvas, point)

        if self.parent:
            if self.parent.parent:
                if self.parent.parent.parent:
                    image = self.parent.parent.parent.owner.viewer.edit_image
                    if self.points == [[0, 0], [1, 1]]:
                        image.curve = []
                    else:
                        image.curve = self.curve

    def relative_to_local(self, point):
        """Convert relative coordinates (0-1) into window coordinates.
        Argument:
            point: List, [x, y] coordinates.
        Returns: List, [x, y] coordinates.
        """

        x = point[0]*self.width + self.pos[0]
        y = point[1]*self.height + self.pos[1]
        return [x, y]

    def local_to_relative(self, point):
        """Convert window coordinates into relative coordinates (0-1).
        Argument:
            point: List, [x, y] coordinates.
        Returns: List, [x, y] coordinates.
        """

        x = (point[0] - self.pos[0])/self.width
        y = (point[1] - self.pos[1])/self.height
        return [x, y]

    def draw_line(self, canvas):
        """Draws the canvas display line from the current curves data.
        Argument:
            canvas: A Kivy canvas object
        """

        canvas.add(Color(1, 1, 1))
        step = self.width/self.resolution
        x = 0
        points = []
        vscale = self.height/(self.bytes-1)
        for point in self.curve:
            points.append(x + self.pos[0])
            points.append((point*vscale) + self.pos[1])
            x = x+step
        canvas.add(Line(points=points))

    def draw_point(self, canvas, point):
        """Draws a curve edit point graphic on the canvas.
        Arguments:
            canvas: A Kivy canvas object
            point: List containing relative coordinates of the point, x, y
        """

        size = 20
        real_point = self.relative_to_local(point)
        if point == self.current_point:
            source = 'data/curve_point_selected.png'
        else:
            source = 'data/curve_point.png'
        canvas.add(Rectangle(source=source, pos=(real_point[0]-(size/2), real_point[1]-(size/2)), size=(size, size)))

    def add_point(self, point):
        """Adds a new point to the curve and regenerates and redraws the curve.
        Argument:
            point: List containing relative coordinates of the point, x, y
        """

        x = point[0]
        y = point[1]

        #dont allow illegal values for x or y
        if x > 1 or y > 1 or x < 0 or y < 0:
            return

        #dont allow point on an x position that already exists
        for point in self.points:
            if point[0] == x:
                return
        self.points.append([x, y])
        self.current_point = [x, y]
        self.refresh()

    def remove_point(self):
        """Removes the last moved point and regenerates and redraws the curve."""

        if self.current_point:
            for index, point in enumerate(self.points):
                if point[0] == self.current_point[0] and point[1] == self.current_point[1]:
                    self.points.pop(index)
        self.refresh()

    def generate_curve(self):
        """Regenerates the curve data based on self.points."""

        app = App.get_running_app()
        self.curve = []
        resolution = self.resolution - 1
        total_bytes = self.bytes - 1
        interpolation = app.interpolation

        x = 0
        index = 0
        previous_point = False
        start_point = self.points[index]

        while x < resolution:
            if index < (len(self.points)-2):
                next_point = self.points[index+2]
            else:
                next_point = False
            stop_point = self.points[index+1]
            stop_x = int(stop_point[0]*resolution)
            distance = stop_x - x
            start_y = start_point[1] * total_bytes
            stop_y = stop_point[1] * total_bytes
            if previous_point != False:
                previous_y = previous_point[1] * total_bytes
                previous_distance = (start_point[0] - previous_point[0]) * total_bytes
            else:
                previous_y = None
                previous_distance = distance
            if next_point != False:
                next_y = next_point[1] * total_bytes
                next_distance = (next_point[0] - stop_point[0]) * total_bytes
            else:
                next_distance = distance
                next_y = None
            if interpolation == 'Catmull-Rom':
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, previous=previous_y,
                                 previous_distance=previous_distance, next=next_y, next_distance=next_distance,
                                 mode='catmull')
            elif interpolation == 'Cubic':
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, previous=previous_y,
                                 previous_distance=previous_distance, next=next_y, next_distance=next_distance,
                                 mode='cubic')
            elif interpolation == 'Cosine':
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, mode='cosine')
            else:
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes)
            self.curve = self.curve + ys
            x = stop_x
            index = index + 1
            previous_point = start_point
            start_point = stop_point
        self.curve.append(self.points[-1][1] * total_bytes)

    def near_x(self, first, second):
        """Check if two points on the x axis are near each other using self.touch_range.
        Arguments:
            first: First point
            second: Second point
        Returns: True or False
        """

        aspect = self.width/self.height
        touch_range = self.touch_range / aspect

        if abs(second-first) <= touch_range:
            return True
        else:
            return False

    def near_y(self, first, second):
        """Check if two points on the y axis are near each other using self.touch_range.
        Arguments:
            first: First point
            second: Second point
        Returns: True or False
        """

        touch_range = self.touch_range

        if abs(second-first) <= touch_range:
            return True
        else:
            return False

    def on_touch_down(self, touch):
        """Intercept touches and begin moving points.
        Will also modify scrolling in the parent scroller widget to improve usability.
        """

        edit_scroller = self.parent.parent.parent.owner.ids['editScroller']
        self.scroll_timeout = edit_scroller.scroll_timeout  #cache old scroll timeout

        #Handle touch
        if self.collide_point(*touch.pos):
            edit_scroller.scroll_timeout = 0  #Temporarily modify scrolling in parent widget
            self.moving = True
            point = self.local_to_relative(touch.pos)
            for existing in self.points:
                if self.near_x(point[0], existing[0]) and self.near_y(point[1], existing[1]):
                    #touch is over an existing point, select it so it can start to move
                    self.current_point = existing
                    self.refresh()
                    return

            self.add_point(point)
            return True

    def on_touch_move(self, touch):
        """Intercept touch move events and move point if one is active."""

        if self.collide_point(*touch.pos):
            new_point = self.local_to_relative(touch.pos)
            if self.moving:
                #We were already moving a point
                for index, point in enumerate(self.points):
                    if point[0] == self.current_point[0]:
                        too_close = False
                        for other_point in self.points:
                            if other_point != point:
                                if self.near_x(other_point[0], new_point[0]) and self.near_y(other_point[1], new_point[1]):
                                    too_close = True
                        if point[0] == 0:
                            new_point[0] = 0
                        elif new_point[0] <= 0:
                            too_close = True
                        if point[0] == 1:
                            new_point[0] = 1
                        elif new_point[0] >= 1:
                            too_close = True

                        if not too_close:
                            self.points[index] = new_point
                            self.current_point = new_point
                        self.refresh()
                        break
            return True

    def on_touch_up(self, touch):
        """Touch is released, turn off move mode regardless of if touch is over widget or not."""

        edit_scroller = self.parent.parent.parent.owner.ids['editScroller']
        edit_scroller.scroll_timeout = self.scroll_timeout  #Reset parent scroller object to normal operation
        self.moving = False
        if self.collide_point(*touch.pos):
            return True


class VideoEncodePreset(BoxLayout):
    preset_drop = ObjectProperty()
    preset_name = StringProperty()

    def __init__(self, **kwargs):
        self.preset_drop = NormalDropDown()
        app = App.get_running_app()
        for index, preset in enumerate(app.encoding_presets):
            menu_button = MenuButton(text=preset['name'])
            menu_button.bind(on_release=self.set_preset)
            self.preset_drop.add_widget(menu_button)
        if app.selected_encoder_preset:
            self.preset_name = app.selected_encoder_preset
        else:
            self.preset_name = app.encoding_presets[0]['name']
        super(VideoEncodePreset, self).__init__(**kwargs)

    def set_preset(self, instance):
        app = App.get_running_app()
        self.preset_name = instance.text
        self.preset_drop.dismiss()
        app.selected_encoder_preset = self.preset_name


class EditNone(GridLayout):
    owner = ObjectProperty()

    def save_last(self):
        pass

    def load_last(self):
        pass


class EditMain(GridLayout):
    """Main menu edit panel, contains buttons to activate the other edit panels."""

    owner = ObjectProperty()

    def __init__(self, **kwargs):
        super(EditMain, self).__init__(**kwargs)
        self.update_programs()
        self.update_undo()
        self.update_delete_original()

    def save_last(self):
        pass

    def load_last(self):
        pass

    def update_delete_original(self):
        """Checks if the current viewed photo has an original file, enables the 'Delete Original' button if so."""

        delete_original_button = self.ids['deleteOriginal']
        if os.path.isfile(self.owner.photoinfo[10]):
            delete_original_button.disabled = False
        else:
            delete_original_button.disabled = True

    def update_undo(self):
        """Checks if the current viewed photo has an original file, enables the 'Restore Original' button if so."""

        undo_button = self.ids['undoEdits']
        if os.path.isfile(self.owner.photoinfo[10]):
            undo_button.disabled = False
        else:
            undo_button.disabled = True

    def save_program(self, index, name, command, argument):
        """Saves an external program command to the app settings.
        Arguments:
            index: Index of the program to edit in the external program list.
            name: Name of the program
            command: Path to the executable file of the program
            argument: Extra arguments for the program command
        """

        app = App.get_running_app()
        app.program_save(index, name, command, argument)
        self.update_programs(expand=True, expand_index=index)

    def remove_program(self, index):
        """Removes a program from the external programs list.
        Argument:
            index: Index of the program to remove in the external program list.
        """

        app = App.get_running_app()
        app.program_remove(index)
        self.update_programs()

    def update_programs(self, expand=False, expand_index=-1):
        """Updates the external programs list in this panel.
        Arguments:
            expand: Boolean, set to True to set an external program to edit mode.
            expand_index: Integer, index of the external program to be in edit mode.
        """

        external_programs = self.ids['externalPrograms']
        app = App.get_running_app()
        external_programs.clear_widgets()

        if expand_index == -1:
            expand_index = len(app.programs)-1
        for index, preset in enumerate(app.programs):
            name, command, argument = preset
            program_button = ExpandableButton(text=name, index=index)
            program_button.bind(on_press=lambda button: app.program_run(button.index, button))
            program_button.bind(on_remove=lambda button: self.remove_program(button.index))
            program_button.content = ExternalProgramEditor(index=index, name=name, command=command, argument=argument,
                                                           owner=self)
            external_programs.add_widget(program_button)
            if index == expand_index and expand:
                program_button.expanded = True


class EditColorImage(GridLayout):
    """Panel to expose color editing options."""

    equalize = NumericProperty(0)
    autocontrast = BooleanProperty(False)
    adaptive = NumericProperty(0)
    brightness = NumericProperty(0)
    shadow = NumericProperty(0)
    gamma = NumericProperty(0)
    contrast = NumericProperty(0)
    saturation = NumericProperty(0)
    temperature = NumericProperty(0)

    owner = ObjectProperty()
    interpolation_drop_down = ObjectProperty()
    preset_name = StringProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.add_video_preset)
        super(EditColorImage, self).__init__(**kwargs)

    def add_video_preset(self, *_):
        if not self.owner.view_image:
            video_preset = self.ids['videoPreset']
            video_preset.add_widget(VideoEncodePreset())

    def save_last(self):
        self.owner.edit_color = True
        self.owner.equalize = self.equalize
        self.owner.autocontrast = self.autocontrast
        self.owner.adaptive = self.adaptive
        self.owner.brightness = self.brightness
        self.owner.gamma = self.gamma
        self.owner.contrast = self.contrast
        self.owner.saturation = self.saturation
        self.owner.temperature = self.temperature
        self.owner.shadow = self.shadow

    def load_last(self):
        self.equalize = self.owner.equalize
        self.autocontrast = self.owner.autocontrast
        self.adaptive = self.owner.adaptive
        self.brightness = self.owner.brightness
        self.gamma = self.owner.gamma
        self.contrast = self.owner.contrast
        self.saturation = self.owner.saturation
        self.temperature = self.owner.temperature
        self.shadow = self.owner.shadow

    def draw_histogram(self, *_):
        """Draws the histogram image and displays it."""

        histogram_data = self.owner.viewer.edit_image.histogram
        histogram = self.ids['histogram']
        histogram_max = max(histogram_data)
        data_red = histogram_data[0:256]
        data_green = histogram_data[256:512]
        data_blue = histogram_data[512:768]
        multiplier = 256.0/histogram_max

        #Draw red channel
        histogram_red = Image.new(mode='RGB', size=(256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(histogram_red)
        for index in range(256):
            value = int(data_red[index]*multiplier)
            draw.line((index, 256, index, 256-value), fill=(255, 0, 0))

        #Draw green channel
        histogram_green = Image.new(mode='RGB', size=(256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(histogram_green)
        for index in range(256):
            value = int(data_green[index]*multiplier)
            draw.line((index, 256, index, 256-value), fill=(0, 255, 0))

        #Draw blue channel
        histogram_blue = Image.new(mode='RGB', size=(256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(histogram_blue)
        for index in range(256):
            value = int(data_blue[index]*multiplier)
            draw.line((index, 256, index, 256-value), fill=(0, 0, 255))

        #Mix channels together
        histogram_red_green = ImageChops.add(histogram_red, histogram_green)
        histogram_image = ImageChops.add(histogram_red_green, histogram_blue)

        #Convert and display image
        image_bytes = BytesIO()
        histogram_image.save(image_bytes, 'jpeg')
        image_bytes.seek(0)
        histogram._coreimage = CoreImage(image_bytes, ext='jpg')
        histogram._on_tex_change()

    def on_equalize(self, *_):
        self.owner.viewer.edit_image.equalize = self.equalize

    def update_equalize(self, value):
        if value == 'down':
            self.equalize = True
        else:
            self.equalize = False
        self.draw_histogram()

    def reset_equalize(self):
        self.equalize = 0

    def on_autocontrast(self, *_):
        self.owner.viewer.edit_image.autocontrast = self.autocontrast

    def update_autocontrast(self, value):
        if value == 'down':
            self.autocontrast = True
        else:
            self.autocontrast = False

    def reset_autocontrast(self):
        self.autocontrast = False

    def on_adaptive(self, *_):
        self.owner.viewer.edit_image.adaptive_clip = self.adaptive

    def reset_adaptive(self):
        self.adaptive = 0

    def on_brightness(self, *_):
        self.owner.viewer.edit_image.brightness = self.brightness

    def reset_brightness(self):
        self.brightness = 0

    def on_shadow(self, *_):
        self.owner.viewer.edit_image.shadow = self.shadow

    def reset_shadow(self):
        self.shadow = 0

    def on_gamma(self, *_):
        self.owner.viewer.edit_image.gamma = self.gamma

    def reset_gamma(self):
        self.gamma = 0

    def on_contrast(self, *_):
        self.owner.viewer.edit_image.contrast = self.contrast

    def reset_contrast(self):
        self.contrast = 0

    def on_saturation(self, *_):
        self.owner.viewer.edit_image.saturation = self.saturation

    def reset_saturation(self):
        self.saturation = 0

    def on_temperature(self, *_):
        self.owner.viewer.edit_image.temperature = self.temperature

    def reset_temperature(self):
        self.temperature = 0

    def reset_all(self):
        """Reset all edit settings on this panel."""

        self.reset_brightness()
        self.reset_shadow()
        self.reset_gamma()
        self.reset_contrast()
        self.reset_saturation()
        self.reset_temperature()
        self.reset_equalize()
        self.reset_autocontrast()
        self.reset_adaptive()


class EditColorImageAdvanced(GridLayout):
    """Panel to expose advanced color editing options."""

    tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    curve = ListProperty([[0, 0], [1, 1]])

    owner = ObjectProperty()
    interpolation_drop_down = ObjectProperty()
    preset_name = StringProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.add_video_preset)
        super(EditColorImageAdvanced, self).__init__(**kwargs)
        #self.interpolation_drop_down = InterpolationDropDown()
        #interpolation_button = self.ids['interpolation']
        #interpolation_button.bind(on_release=self.interpolation_drop_down.open)
        #self.interpolation_drop_down.bind(on_select=self.set_interpolation)

    def add_video_preset(self, *_):
        if not self.owner.view_image:
            video_preset = self.ids['videoPreset']
            video_preset.add_widget(VideoEncodePreset())

    def save_last(self):
        self.owner.edit_advanced = True
        self.owner.tint = self.tint
        curves = self.ids['curves']
        self.curve = curves.points
        self.owner.curve = self.curve

    def load_last(self):
        self.tint = self.owner.tint
        self.curve = self.owner.curve
        curves = self.ids['curves']
        curves.points = self.curve
        curves.refresh()

    def set_interpolation(self, instance, value):
        """Sets the interpolation mode.
        Arguments:
            instance: Widget that called this function.  Not used.
            value: String, new value to set interpolation to.
        """

        del instance
        app = App.get_running_app()
        app.interpolation = value
        curves = self.ids['curves']
        curves.refresh()

    def draw_histogram(self, *_):
        """Draws the histogram image and displays it."""

        histogram_data = self.owner.viewer.edit_image.histogram
        histogram = self.ids['histogram']
        histogram_max = max(histogram_data)
        data_red = histogram_data[0:256]
        data_green = histogram_data[256:512]
        data_blue = histogram_data[512:768]
        multiplier = 256.0/histogram_max

        #Draw red channel
        histogram_red = Image.new(mode='RGB', size=(256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(histogram_red)
        for index in range(256):
            value = int(data_red[index]*multiplier)
            draw.line((index, 256, index, 256-value), fill=(255, 0, 0))

        #Draw green channel
        histogram_green = Image.new(mode='RGB', size=(256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(histogram_green)
        for index in range(256):
            value = int(data_green[index]*multiplier)
            draw.line((index, 256, index, 256-value), fill=(0, 255, 0))

        #Draw blue channel
        histogram_blue = Image.new(mode='RGB', size=(256, 256), color=(0, 0, 0))
        draw = ImageDraw.Draw(histogram_blue)
        for index in range(256):
            value = int(data_blue[index]*multiplier)
            draw.line((index, 256, index, 256-value), fill=(0, 0, 255))

        #Mix channels together
        histogram_red_green = ImageChops.add(histogram_red, histogram_green)
        histogram_image = ImageChops.add(histogram_red_green, histogram_blue)

        #Convert and display image
        image_bytes = BytesIO()
        histogram_image.save(image_bytes, 'jpeg')
        image_bytes.seek(0)
        histogram._coreimage = CoreImage(image_bytes, ext='jpg')
        histogram._on_tex_change()

    def reset_curves(self):
        """Tells the curves widget to reset to its default points."""

        curves = self.ids['curves']
        curves.reset()

    def remove_point(self):
        """Tells the curves widget to remove its last point."""

        curves = self.ids['curves']
        curves.remove_point()

    def on_tint(self, *_):
        self.owner.viewer.edit_image.tint = self.tint

    def reset_tint(self):
        self.tint = [1.0, 1.0, 1.0, 1.0]

    def reset_all(self):
        """Reset all edit settings on this panel."""

        self.reset_curves()
        self.reset_tint()


class EditFilterImage(GridLayout):
    """Panel to expose filter editing options."""

    sharpen = NumericProperty(0)
    vignette_amount = NumericProperty(0)
    vignette_size = NumericProperty(0.5)
    edge_blur_amount = NumericProperty(0)
    edge_blur_size = NumericProperty(0.5)
    edge_blur_intensity = NumericProperty(0.5)
    median = NumericProperty(0)
    bilateral = NumericProperty(0.5)
    bilateral_amount = NumericProperty(0)

    owner = ObjectProperty()
    preset_name = StringProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.add_video_preset)
        super(EditFilterImage, self).__init__(**kwargs)

    def add_video_preset(self, *_):
        if not self.owner.view_image:
            video_preset = self.ids['videoPreset']
            video_preset.add_widget(VideoEncodePreset())

    def save_last(self):
        self.owner.edit_filter = True
        self.owner.sharpen = self.sharpen
        self.owner.vignette_amount = self.vignette_amount
        self.owner.vignette_size = self.vignette_size
        self.owner.edge_blur_amount = self.edge_blur_amount
        self.owner.edge_blur_size = self.edge_blur_size
        self.owner.edge_blur_intensity = self.edge_blur_intensity
        self.owner.bilateral = self.bilateral
        self.owner.bilateral_amount = self.bilateral_amount
        self.owner.median = self.median

    def load_last(self):
        self.sharpen = self.owner.sharpen
        self.vignette_amount = self.owner.vignette_amount
        self.vignette_size = self.owner.vignette_size
        self.edge_blur_amount = self.owner.edge_blur_amount
        self.edge_blur_size = self.owner.edge_blur_size
        self.edge_blur_intensity = self.owner.edge_blur_intensity
        self.bilateral = self.owner.bilateral
        self.bilateral_amount = self.owner.bilateral_amount
        self.median = self.owner.median

    def on_sharpen(self, *_):
        self.owner.viewer.edit_image.sharpen = self.sharpen

    def reset_sharpen(self):
        self.sharpen = 0

    def on_median(self, *_):
        self.owner.viewer.edit_image.median_blur = self.median

    def reset_median(self):
        self.median = 0

    def on_bilateral_amount(self, *_):
        self.owner.viewer.edit_image.bilateral_amount = self.bilateral_amount

    def reset_bilateral_amount(self):
        self.bilateral_amount = 0

    def on_bilateral(self, *_):
        self.owner.viewer.edit_image.bilateral = self.bilateral

    def reset_bilateral(self):
        self.bilateral = 0.5

    def on_vignette_amount(self, *_):
        self.owner.viewer.edit_image.vignette_amount = self.vignette_amount

    def reset_vignette_amount(self):
        self.vignette_amount = 0

    def on_vignette_size(self, *_):
        self.owner.viewer.edit_image.vignette_size = self.vignette_size

    def reset_vignette_size(self):
        self.vignette_size = 0.5

    def on_edge_blur_amount(self, *_):
        self.owner.viewer.edit_image.edge_blur_amount = self.edge_blur_amount

    def reset_edge_blur_amount(self):
        self.edge_blur_amount = 0

    def on_edge_blur_size(self, *_):
        self.owner.viewer.edit_image.edge_blur_size = self.edge_blur_size

    def reset_edge_blur_size(self):
        self.edge_blur_size = 0.5

    def on_edge_blur_intensity(self, *_):
        self.owner.viewer.edit_image.edge_blur_intensity = self.edge_blur_intensity

    def reset_edge_blur_intensity(self):
        self.edge_blur_intensity = 0.5

    def reset_all(self):
        """Reset all edit values to defaults."""

        self.reset_sharpen()
        self.reset_vignette_amount()
        self.reset_vignette_size()
        self.reset_edge_blur_amount()
        self.reset_edge_blur_size()
        self.reset_edge_blur_intensity()
        self.reset_median()
        self.reset_bilateral()
        self.reset_bilateral_amount()


class EditBorderImage(GridLayout):
    """Panel to expose image border overlays."""

    selected = StringProperty()
    border_x_scale = NumericProperty(0)
    border_y_scale = NumericProperty(0)
    border_opacity = NumericProperty(1)
    tint = ListProperty([1.0, 1.0, 1.0, 1.0])

    owner = ObjectProperty()
    borders = ListProperty()
    type = StringProperty()
    preset_name = StringProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.add_video_preset)
        Clock.schedule_once(self.populate_borders)
        super(EditBorderImage, self).__init__(**kwargs)

    def add_video_preset(self, *_):
        if not self.owner.view_image:
            video_preset = self.ids['videoPreset']
            video_preset.add_widget(VideoEncodePreset())

    def save_last(self):
        self.owner.edit_border = True
        self.owner.border_selected = self.selected
        self.owner.border_x_scale = self.border_x_scale
        self.owner.border_y_scale = self.border_y_scale
        self.owner.border_opacity = self.border_opacity
        self.owner.border_tint = self.tint

    def load_last(self):
        self.selected = self.owner.border_selected
        self.border_x_scale = self.owner.border_x_scale
        self.border_y_scale = self.owner.border_y_scale
        self.border_opacity = self.owner.border_opacity
        self.tint = self.owner.border_tint

    def on_selected(self, *_):
        if self.selected:
            border_index = int(self.selected)
        else:
            border_index = 0
        self.reset_border_x_scale()
        self.reset_border_y_scale()
        if border_index == 0:
            self.owner.viewer.edit_image.border_image = []
        else:
            self.owner.viewer.edit_image.border_image = self.borders[border_index]

    def populate_borders(self, *_):
        self.borders = [None]
        for file in os.listdir('borders'):
            if file.endswith('.txt'):
                border_name = os.path.splitext(file)[0]
                border_sizes = []
                border_images = []
                with open(os.path.join('borders', file)) as input_file:
                    for line in input_file:
                        if ':' in line and not line.startswith('#'):
                            size, image = line.split(':')
                            border_sizes.append(float(size))
                            border_images.append(image.strip())
                if border_sizes:
                    self.borders.append([border_name, border_sizes, border_images])

        borders_tree = self.ids['borders']
        nodes = list(borders_tree.iterate_all_nodes())
        for node in nodes:
            borders_tree.remove_node(node)

        for index, border in enumerate(self.borders):
            if border:
                node = TreeViewButton(dragable=False, owner=self, target=str(index), folder_name=border[0])
                borders_tree.add_node(node)
            else:
                node = TreeViewButton(dragable=False, owner=self, target=str(index), folder_name='None')
                borders_tree.add_node(node)
                borders_tree.select_node(node)

    def on_border_x_scale(self, *_):
        self.owner.viewer.edit_image.border_x_scale = self.border_x_scale

    def reset_border_x_scale(self):
        self.border_x_scale = 0

    def on_border_y_scale(self, *_):
        self.owner.viewer.edit_image.border_y_scale = self.border_y_scale

    def reset_border_y_scale(self):
        self.border_y_scale = 0

    def on_border_opacity(self, *_):
        self.owner.viewer.edit_image.border_opacity = self.border_opacity

    def reset_border_opacity(self, *_):
        self.border_opacity = 1

    def on_tint(self, *_):
        self.owner.viewer.edit_image.border_tint = self.tint

    def reset_tint(self):
        self.tint = [1.0, 1.0, 1.0, 1.0]


class EditDenoiseImage(GridLayout):
    """Panel to expose image denoise options."""

    luminance_denoise = StringProperty('10')
    color_denoise = StringProperty('10')
    search_window = StringProperty('15')
    block_size = StringProperty('5')

    owner = ObjectProperty()
    imagefile = StringProperty('')
    image_x = NumericProperty(1)
    image_y = NumericProperty(1)
    full_image = ObjectProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.update_preview)
        super(EditDenoiseImage, self).__init__(**kwargs)

    def save_last(self):
        self.owner.edit_denoise = True
        self.owner.luminance_denoise = self.luminance_denoise
        self.owner.color_denoise = self.color_denoise
        self.owner.search_window = self.search_window
        self.owner.block_size = self.block_size

    def load_last(self):
        self.luminance_denoise = self.owner.luminance_denoise
        self.color_denoise = self.owner.color_denoise
        self.search_window = self.owner.search_window
        self.block_size = self.owner.block_size

    def save_image(self):
        self.owner.viewer.edit_image.denoise = True
        self.owner.save_image()

    def reset_all(self):
        """Reset all edit values to defaults."""
        self.luminance_denoise = '10'
        self.color_denoise = '10'
        self.search_window = '21'
        self.block_size = '7'

    def on_luminance_denoise(self, *_):
        if not self.luminance_denoise:
            luminance_denoise = 0
        else:
            luminance_denoise = int(self.luminance_denoise)
        self.owner.viewer.edit_image.luminance_denoise = luminance_denoise
        self.update_preview()

    def on_color_denoise(self, *_):
        if not self.color_denoise:
            color_denoise = 0
        else:
            color_denoise = int(self.color_denoise)
        self.owner.viewer.edit_image.color_denoise = color_denoise
        self.update_preview()

    def on_search_window(self, *_):
        if not self.search_window:
            search_window = 0
        else:
            search_window = int(self.search_window)
        if (search_window % 2) == 0:
            search_window = search_window + 1
        self.owner.viewer.edit_image.search_window = search_window
        self.update_preview()

    def on_block_size(self, *_):
        if not self.block_size:
            block_size = 0
        else:
            block_size = int(self.block_size)
        if (block_size % 2) == 0:
            block_size = block_size + 1
        self.owner.viewer.edit_image.block_size = block_size
        self.update_preview()

    def update_preview(self, *_):
        scroll_area = self.ids['wrapper']
        width = scroll_area.size[0]
        height = scroll_area.size[1]
        pos_x = int((self.image_x * scroll_area.scroll_x) - (width * scroll_area.scroll_x))
        image_pos_y = self.image_y - int((self.image_y * scroll_area.scroll_y) + (width * (1 - scroll_area.scroll_y)))
        preview = self.owner.viewer.edit_image.denoise_preview(width, height, pos_x, image_pos_y)
        overlay_image = self.ids['denoiseOverlay']
        widget_pos_y = int((self.image_y * scroll_area.scroll_y) - (width * scroll_area.scroll_y))
        overlay_image.pos = [pos_x, widget_pos_y]
        overlay_image._coreimage = CoreImage(preview, ext='jpg')
        overlay_image._on_tex_change()
        overlay_image.opacity = 1

    def denoise(self):
        """Generates a preview using the current denoise settings"""

        self.owner.viewer.edit_image.update_preview(denoise=True)


class EditCropImage(GridLayout):
    """Panel to expose crop editing options."""

    crop_top = NumericProperty(0)
    crop_right = NumericProperty(0)
    crop_bottom = NumericProperty(0)
    crop_left = NumericProperty(0)

    owner = ObjectProperty()
    image_x = NumericProperty(0)
    image_y = NumericProperty(0)
    orientation = StringProperty('horizontal')
    aspect_x = NumericProperty(0)
    aspect_y = NumericProperty(0)
    crop_size = StringProperty('')

    def __init__(self, **kwargs):
        super(EditCropImage, self).__init__(**kwargs)
        self.aspect_dropdown = AspectRatioDropDown()
        self.aspect_dropdown.bind(on_select=lambda instance, x: self.set_aspect_ratio(x))
        self.aspect_x = self.image_x
        self.aspect_y = self.image_y
        if self.image_x >= self.image_y:
            self.orientation = 'horizontal'
            self.ids['horizontalToggle'].state = 'down'
        else:
            self.orientation = 'vertical'
            self.ids['verticalToggle'].state = 'down'

    def update_crop_size_text(self):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.get_crop_size()

    def update_crop(self):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            percents = edit_image.get_crop_percent()
            self.crop_top = percents[0]
            self.crop_right = percents[1]
            self.crop_bottom = percents[2]
            self.crop_left = percents[3]

    def save_last(self):
        self.update_crop()
        self.owner.edit_crop = True
        self.owner.crop_top = self.crop_top
        self.owner.crop_right = self.crop_right
        self.owner.crop_bottom = self.crop_bottom
        self.owner.crop_left = self.crop_left

    def load_last(self):
        self.crop_top = self.owner.crop_top
        self.crop_right = self.owner.crop_right
        self.crop_bottom = self.owner.crop_bottom
        self.crop_left = self.owner.crop_left

    def on_crop_top(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('top', self.crop_top)
            self.update_crop_size_text()

    def on_crop_right(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('right', self.crop_right)
            self.update_crop_size_text()

    def on_crop_bottom(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('bottom', self.crop_bottom)
            self.update_crop_size_text()

    def on_crop_left(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('left', self.crop_left)
            self.update_crop_size_text()

    def recrop(self):
        """tell image to recrop itself based on an aspect ratio"""

        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.set_aspect(self.aspect_x, self.aspect_y)
            self.update_crop()

    def reset_crop(self):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.reset_crop()
            self.update_crop()

    def set_orientation(self, orientation):
        if orientation != self.orientation:
            old_x = self.aspect_x
            old_y = self.aspect_y
            self.aspect_x = old_y
            self.aspect_y = old_x
        self.orientation = orientation

    def set_aspect_ratio(self, method):
        if method == '6x4':
            if self.orientation == 'horizontal':
                self.aspect_x = 6
                self.aspect_y = 4
            else:
                self.aspect_x = 4
                self.aspect_y = 6
        elif method == '7x5':
            if self.orientation == 'horizontal':
                self.aspect_x = 7
                self.aspect_y = 5
            else:
                self.aspect_x = 5
                self.aspect_y = 7
        elif method == '11x8.5':
            if self.orientation == 'horizontal':
                self.aspect_x = 11
                self.aspect_y = 8.5
            else:
                self.aspect_x = 8.5
                self.aspect_y = 11
        elif method == '4x3':
            if self.orientation == 'horizontal':
                self.aspect_x = 4
                self.aspect_y = 3
            else:
                self.aspect_x = 3
                self.aspect_y = 4
        elif method == '16x9':
            if self.orientation == 'horizontal':
                self.aspect_x = 16
                self.aspect_y = 9
            else:
                self.aspect_x = 9
                self.aspect_y = 16
        elif method == '1x1':
            self.aspect_x = 1
            self.aspect_y = 1
        else:
            if self.image_x >= self.image_y:
                width = self.image_x
                height = self.image_y
            else:
                width = self.image_y
                height = self.image_x
            if self.orientation == 'horizontal':
                self.aspect_x = width
                self.aspect_y = height
            else:
                self.aspect_x = height
                self.aspect_y = width
        self.recrop()


class EditRotateImage(GridLayout):
    """Panel to expose rotation editing options."""

    fine_angle = NumericProperty(0)

    owner = ObjectProperty()

    def save_last(self):
        pass

    def load_last(self):
        pass

    def reset_all(self):
        self.update_angle(0)
        self.ids['angles_0'].state = 'down'
        self.ids['angles_90'].state = 'normal'
        self.ids['angles_180'].state = 'normal'
        self.ids['angles_270'].state = 'normal'
        self.fine_angle = 0
        self.ids['fine_angle'].value = 0
        self.update_flip_horizontal(flip='up')
        self.ids['flip_horizontal'].state = 'normal'
        self.update_flip_vertical(flip='up')
        self.ids['flip_vertical'].state = 'normal'

    def update_angle(self, angle):
        self.owner.viewer.edit_image.rotate_angle = angle

    def on_fine_angle(self, *_):
        self.owner.viewer.edit_image.fine_angle = self.fine_angle

    def update_flip_horizontal(self, flip):
        if flip == 'down':
            self.owner.viewer.edit_image.flip_horizontal = True
        else:
            self.owner.viewer.edit_image.flip_horizontal = False

    def update_flip_vertical(self, flip):
        if flip == 'down':
            self.owner.viewer.edit_image.flip_vertical = True
        else:
            self.owner.viewer.edit_image.flip_vertical = False


class EditConvertImage(GridLayout):
    """Currently not supported."""
    owner = ObjectProperty()

    def save_last(self):
        pass

    def load_last(self):
        pass


class EditConvertVideo(GridLayout):
    """Convert a video file to another format using ffmpeg."""

    owner = ObjectProperty()

    #Encoding settings
    video_codec = StringProperty()
    audio_codec = StringProperty()
    video_quality = StringProperty()
    encoding_speed = StringProperty()
    file_format = StringProperty()
    input_file = StringProperty()
    video_bitrate = StringProperty('8000')
    audio_bitrate = StringProperty('192')
    command_line = StringProperty()
    deinterlace = BooleanProperty(False)
    resize = BooleanProperty(False)
    resize_width = StringProperty('1920')
    resize_height = StringProperty('1080')

    #Dropdown menus
    preset_drop = ObjectProperty()
    container_drop = ObjectProperty()
    video_codec_drop = ObjectProperty()
    video_quality_drop = ObjectProperty()
    encoding_speed_drop = ObjectProperty()
    audio_codec_drop = ObjectProperty()

    def __init__(self, **kwargs):
        self.setup_dropdowns()
        app = App.get_running_app()
        encoding_preset = app.config.get('Presets', 'encoding')
        if encoding_preset:
            encoding_settings = encoding_preset.split(',', 10)
            if len(encoding_settings) == 11:
                self.file_format = encoding_settings[0]
                self.video_codec = encoding_settings[1]
                self.audio_codec = encoding_settings[2]
                self.resize = to_bool(encoding_settings[3])
                self.resize_width = encoding_settings[4]
                self.resize_height = encoding_settings[5]
                self.video_bitrate = encoding_settings[6]
                self.audio_bitrate = encoding_settings[7]
                self.encoding_speed = encoding_settings[8]
                self.deinterlace = to_bool(encoding_settings[9])
                self.command_line = encoding_settings[10]
        super(EditConvertVideo, self).__init__(**kwargs)

    def save_last(self):
        pass

    def load_last(self):
        pass

    def store_settings(self):
        encoding_preset = self.file_format+','+self.video_codec+','+self.audio_codec+','+str(self.resize)+','+self.resize_width+','+self.resize_height+','+self.video_bitrate+','+self.audio_bitrate+','+self.encoding_speed+','+str(self.deinterlace)+','+self.command_line
        app = App.get_running_app()
        app.config.set('Presets', 'encoding', encoding_preset)

    def setup_dropdowns(self):
        """Creates and populates the various drop-down menus used by this dialog."""

        self.preset_drop = NormalDropDown()
        app = App.get_running_app()
        for index, preset in enumerate(app.encoding_presets):
            menu_button = MenuButton(text=preset['name'])
            menu_button.bind(on_release=self.set_preset)
            self.preset_drop.add_widget(menu_button)

        self.file_format = containers_friendly[0]
        self.container_drop = NormalDropDown()
        for container in containers_friendly:
            menu_button = MenuButton(text=container)
            menu_button.bind(on_release=self.change_container_to)
            self.container_drop.add_widget(menu_button)

        self.video_codec = video_codecs_friendly[0]
        self.video_codec_drop = NormalDropDown()
        for codec in video_codecs_friendly:
            menu_button = MenuButton(text=codec)
            menu_button.bind(on_release=self.change_video_codec_to)
            self.video_codec_drop.add_widget(menu_button)

        #self.video_quality = 'Constant Bitrate'
        #video_qualities = ['Constant Bitrate', 'High', 'Medium', 'Low', 'Very Low']
        #self.video_quality_drop = NormalDropDown()
        #for quality in video_qualities:
        #    menu_button = MenuButton(text=quality)
        #    menu_button.bind(on_release=self.change_video_quality_to)
        #    self.video_quality_drop.add_widget(menu_button)

        self.encoding_speed = 'Fast'
        encoding_speeds = ['Very Fast', 'Fast', 'Medium', 'Slow', 'Very Slow']
        self.encoding_speed_drop = NormalDropDown()
        for speed in encoding_speeds:
            menu_button = MenuButton(text=speed)
            menu_button.bind(on_release=self.change_encoding_speed_to)
            self.encoding_speed_drop.add_widget(menu_button)

        self.audio_codec = audio_codecs_friendly[0]
        self.audio_codec_drop = NormalDropDown()
        for codec in audio_codecs_friendly:
            menu_button = MenuButton(text=codec)
            menu_button.bind(on_release=self.change_audio_codec_to)
            self.audio_codec_drop.add_widget(menu_button)

    def update_deinterlace(self, state):
        if state == 'down':
            self.deinterlace = True
        else:
            self.deinterlace = False

    def update_resize(self, state):
        if state == 'down':
            self.resize = True
        else:
            self.resize = False

    def set_resize_width(self, instance):
        self.resize_width = instance.text
        self.store_settings()

    def set_resize_height(self, instance):
        self.resize_height = instance.text
        self.store_settings()

    def set_preset(self, instance):
        """Sets the current dialog preset settings to one of the presets stored in the app.
        Argument:
            index: Integer, the index of the preset to set.
        """

        self.preset_drop.dismiss()
        app = App.get_running_app()
        for preset in app.encoding_presets:
            if preset['name'] == instance.text:
                if preset['file_format'] in containers_friendly:
                    self.file_format = preset['file_format']
                else:
                    self.file_format = containers_friendly[0]
                if preset['video_codec'] in video_codecs_friendly:
                    self.video_codec = preset['video_codec']
                else:
                    self.video_codec = video_codecs_friendly[0]
                if preset['audio_codec'] in audio_codecs_friendly:
                    self.audio_codec = preset['audio_codec']
                else:
                    self.audio_codec = audio_codecs_friendly[0]
                self.resize = preset['resize']
                self.resize_width = preset['width']
                self.resize_height = preset['height']
                self.video_bitrate = preset['video_bitrate']
                self.audio_bitrate = preset['audio_bitrate']
                self.encoding_speed = preset['encoding_speed']
                self.deinterlace = preset['deinterlace']
                self.command_line = preset['command_line']
                return
        self.store_settings()

    def on_video_bitrate(self, *_):
        self.store_settings()

    def on_audio_bitrate(self, *_):
        self.store_settings()

    def set_command_line(self, instance):
        self.command_line = instance.text
        self.store_settings()

    def change_video_quality_to(self, instance):
        """Sets the self.video_quality value."""

        self.video_quality_drop.dismiss()
        self.video_quality = instance.text
        self.store_settings()

    def change_encoding_speed_to(self, instance):
        """Sets the self.encoding_speed value."""

        self.encoding_speed_drop.dismiss()
        self.encoding_speed = instance.text
        self.store_settings()

    def change_audio_codec_to(self, instance):
        """Sets the self.audio_codec value."""

        self.audio_codec_drop.dismiss()
        self.audio_codec = instance.text
        self.store_settings()

    def change_video_codec_to(self, instance):
        """Sets the self.video_codec value."""

        self.video_codec_drop.dismiss()
        self.video_codec = instance.text
        self.store_settings()

    def change_container_to(self, instance):
        """Sets the self.file_format value."""

        self.container_drop.dismiss()
        self.file_format = instance.text
        self.store_settings()

    def encode(self):
        """Pass encoding settings to owner album screen and tell it to begin encoding process."""

        #file_format = containers[containers_friendly.index(self.file_format)]
        #video_codec = video_codecs[video_codecs_friendly.index(self.video_codec)]
        #audio_codec = audio_codecs[audio_codecs_friendly.index(self.audio_codec)]
        encoding_settings = {'file_format': self.file_format,
                             'video_codec': self.video_codec,
                             'audio_codec': self.audio_codec,
                             'resize': self.resize,
                             'width': self.resize_width,
                             'height': self.resize_height,
                             'video_bitrate': self.video_bitrate,
                             'audio_bitrate': self.audio_bitrate,
                             'encoding_speed': self.encoding_speed,
                             'deinterlace': self.deinterlace,
                             'command_line': self.command_line}
        self.owner.encoding_settings = encoding_settings
        self.store_settings()
        self.owner.begin_encode()


class PhotoScreen(Screen):
    """Fullscreen photo viewer screen layout."""

    orientation = NumericProperty()
    angle = NumericProperty()
    mirror = BooleanProperty(False)
    popup = None
    viewer = ObjectProperty()
    favorite = BooleanProperty(False)

    def has_popup(self):
        """Detects if the current screen has a popup active.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_extra(self):
        """Dummy function, not valid for this screen, but the app calls it when escape is pressed."""
        return False

    def dismiss_popup(self):
        """Close a currently open popup for this screen."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def key(self, key):
        """Dummy function, not valid for this screen but the app calls it."""

        if not self.popup or (not self.popup.open):
            del key

    def on_enter(self):
        """Called when screen is entered, set up the needed variables and image viewer."""

        app = App.get_running_app()
        container = self.ids['photoViewerContainer']
        container.clear_widgets()
        photoinfo = app.database_exists(app.fullpath)
        if photoinfo:
            self.orientation = photoinfo[13]
        else:
            self.orientation = 1
        if self.orientation == 3 or self.orientation == 4:
            self.angle = 180
        elif self.orientation == 5 or self.orientation == 6:
            self.angle = 270
        elif self.orientation == 7 or self.orientation == 8:
            self.angle = 90
        else:
            self.angle = 0
        if self.orientation in [2, 4, 5, 7]:
            self.mirror = True
        else:
            self.mirror = False
        self.viewer = PhotoViewer(angle=self.angle, mirror=self.mirror, file=app.photo, photoinfo=photoinfo, set_fullscreen=True)
        container.add_widget(self.viewer)


class ImportScreen(Screen):
    """Screen layout for beginning the import photos process.
    Displays import presets and allows the user to pick one.
    """

    popup = None
    selected_import = NumericProperty(-1)

    def dismiss_extra(self):
        """Dummy function, not valid for this screen, but the app calls it when escape is pressed."""
        return False

    def import_preset(self):
        """Activates the import process using the selected import preset."""

        app = App.get_running_app()
        preset = app.imports[self.selected_import]
        if not preset['import_from']:
            app.message("Please Set An Import Directory.")
            return
        good_paths = []
        for path in preset['import_from']:
            if os.path.exists(path):
                good_paths.append(path)
        if not good_paths:
            app.message("No Import From Directories Exist.")
            return
        if not os.path.exists(preset['import_to']):
            app.message("Import To Directory Does Not Exist.")
            return
        database_folders = app.config.get('Database Directories', 'paths')
        database_folders = local_path(database_folders)
        if database_folders.strip(' '):
            databases = database_folders.split(';')
        else:
            databases = []
        if preset['import_to'] not in databases:
            app.message("Please Set A Database To Import To.")
            return
        app.importing_screen.import_to = preset['import_to']
        app.importing_screen.naming_method = preset['naming_method']
        app.importing_screen.delete_originals = preset['delete_originals']
        app.importing_screen.import_from = preset['import_from']
        app.importing_screen.single_folder = preset['single_folder']
        app.show_importing()

    def add_preset(self):
        """Creates a new blank import preset."""

        app = App.get_running_app()
        app.import_preset_new()
        self.selected_import = len(app.imports) - 1
        self.update_treeview()

    def on_leave(self):
        """Called when the screen is left.  Save the import presets."""

        app = App.get_running_app()
        app.import_preset_write()
        presets = self.ids['presets']
        presets.clear_widgets()

    def on_enter(self):
        """Called on entering the screen, updates the treeview and variables."""

        self.selected_import = -1
        self.update_treeview()

    def update_treeview(self):
        """Clears and redraws all the import presets in the treeview."""

        app = App.get_running_app()
        presets = self.ids['presets']

        #Clear old presets
        presets.clear_widgets()

        #Check if database folders are set, cant import without somewhere to import to.
        database_folders = app.config.get('Database Directories', 'paths')
        database_folders = local_path(database_folders)
        if database_folders.strip(' '):
            databases = database_folders.split(';')
        else:
            databases = []
        new_preset_button = self.ids['newPresetButton']
        if databases:
            new_preset_button.disabled = False
            for index, import_preset in enumerate(app.imports):
                preset = ImportPreset(index=index, text=import_preset['title'], owner=self, import_to=import_preset['import_to'])
                preset.data = import_preset
                if index == self.selected_import:
                    preset.expanded = True
                presets.add_widget(preset)
        else:
            new_preset_button.disabled = True
            presets.add_widget(NormalLabel(text="You Must Set Up A Database Before Importing Photos"))

    def has_popup(self):
        """Detects if the current screen has a popup active.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_popup(self, *_):
        """Close a currently open popup for this screen."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def key(self, key):
        """Dummy function, not valid for this screen but the app calls it."""

        if not self.popup or (not self.popup.open):
            pass


class ImportingScreen(Screen):
    """Screen layout for photo importing process.
    Displays photos from directories and lets you select which ones to import.
    """

    type = StringProperty('')
    selected = StringProperty('')
    import_to = StringProperty('')
    naming_method = StringProperty('')
    delete_originals = BooleanProperty(False)
    single_folder = BooleanProperty(False)
    import_from = ListProperty()
    popup = None
    import_photos = []
    duplicates = []
    photos = []
    folders = {}
    unsorted = []
    removed = []
    total_size = 0
    cancel_scanning = BooleanProperty(False)  #The importing process thread checks this and will stop if set to True.
    scanningpopup = None  #Popup dialog showing the importing process progress.
    scanningthread = None  #Importing files thread.
    popup_update_thread = None  #Updates the percentage and time index on scanning popup
    percent_completed = NumericProperty()
    start_time = NumericProperty()
    import_scanning = BooleanProperty(False)

    def get_selected_photos(self, fullpath=False):
        photos = self.ids['photos']
        selected_indexes = photos.selected_nodes
        photos_container = self.ids['photosContainer']
        selected_photos = []
        for selected in selected_indexes:
            if fullpath:
                selected_photos.append(photos_container.data[selected]['fullpath'])
            else:
                selected_photos.append(photos_container.data[selected]['photoinfo'])
        return selected_photos

    def dismiss_extra(self):
        """Cancels the import process if it is running"""

        if self.import_scanning:
            self.cancel_import()
            return True
        else:
            return False

    def date_to_folder(self, date):
        """Generates a string from a date in the format YYYYMMDD."""

        date_info = datetime.datetime.fromtimestamp(date)
        return str(date_info.year)+str(date_info.month).zfill(2)+str(date_info.day).zfill(2)

    def on_enter(self):
        """Called when the screen is entered.  Sets up variables, and scans the import folders."""

        app = App.get_running_app()
        self.ids['leftpanel'].width = app.left_panel_width()
        self.duplicates = []
        self.import_photos = []
        self.folders = {}
        self.unsorted = []
        self.removed = []
        self.total_size = 0
        self.import_scanning = False

        #Display message that folder scanning is in progress
        content = MessagePopup(text='Scanning Import Folders...')
        self.scanningpopup = NormalPopup(title='Scanning Import Folders...', content=content, size_hint=(None, None),
                                         size=(app.popup_x, app.button_scale * 4))
        self.scanningpopup.open()

        Clock.schedule_once(self.scan_folders)

    def scan_folders(self, *_):
        """Function that scans the import folders for valid files to import and populates all dialogs."""

        app = App.get_running_app()
        current_timestamp = time.time()

        #Scan the folders
        for folder in self.import_from:
            if os.path.isdir(folder):
                files = list_files(folder)
                for file_info in files:
                    extension = os.path.splitext(file_info[0])[1].lower()
                    if extension in imagetypes or extension in movietypes:
                        photo_info = get_file_info(file_info, import_mode=True)
                        is_in_database = app.in_database(photo_info)
                        if not is_in_database:
                            is_in_imported = app.in_imported(photo_info)
                            if not is_in_imported:
                                #Non-imported file encountered
                                self.total_size = self.total_size+photo_info[4]
                                self.import_photos.append(photo_info)
                                if self.single_folder:
                                    date = current_timestamp
                                    folderdate = self.date_to_folder(date)
                                else:
                                    date = photo_info[3]
                                    folderdate = self.date_to_folder(date)
                                if folderdate not in self.folders:
                                    date_info = datetime.datetime.fromtimestamp(date)
                                    self.folders[folderdate] = {'naming': True, 'title': '', 'description': '',
                                                                'year': date_info.year, 'month': date_info.month,
                                                                'day': date_info.day, 'photos': [], 'parent': ''}
                                self.folders[folderdate]['photos'].append(photo_info)
                            else:
                                self.unsorted.append(photo_info)
                        else:
                            self.duplicates.append(photo_info)
        self.scanningpopup.dismiss()
        self.scanningpopup = None
        self.update_treeview()
        self.update_photolist()

    def cancel_import(self, unknown=False):
        """Cancel the import process."""
        self.cancel_scanning = True

    def finalize_import(self):
        """Begin the final stage of the import - copying files."""

        app = App.get_running_app()

        #Create popup to show importing progress
        self.cancel_scanning = False
        self.scanningpopup = ScanningPopup(title='Importing Files', auto_dismiss=False, size_hint=(None, None),
                                           size=(app.popup_x, app.button_scale * 4))
        self.scanningpopup.open()
        scanning_button = self.scanningpopup.ids['scanningButton']
        scanning_button.bind(on_press=self.cancel_import)

        #Start importing thread
        self.percent_completed = 0
        self.scanningthread = threading.Thread(target=self.importing_process)
        self.import_scanning = True
        self.scanningthread.start()
        self.start_time = time.time()

    def importing_process(self):
        """Function that actually imports the files."""

        app = App.get_running_app()
        folders = self.folders
        import_to = self.import_to
        total_size = self.total_size
        imported_size = 0
        self.scanningpopup.scanning_text = "Importing "+format_size(total_size)+'  0%'
        imported_folders = []
        imported_files = 0
        failed_files = 0

        print(import_to)
        if disk_usage:
            free_space = disk_usage(import_to)[2]
            if total_size > free_space:
                self.scanningpopup.dismiss()
                self.scanningpopup = None
                app.message("Not enough free drive space! Cancelled import.")
                Clock.schedule_once(lambda *dt: app.show_import())

        #Scan folders
        for folder_name in folders:
            if self.cancel_scanning:
                break
            folder = folders[folder_name]
            if folder['photos']:
                if folder['naming']:
                    folder_name = naming(self.naming_method, title=folder['title'], year=folder['year'],
                                         month=folder['month'], day=folder['day'])
                photos = folder['photos']
                if folder['parent']:
                    path_string = []
                    parent = folder['parent']
                    while parent:
                        newfolder = folders[parent]
                        newfolder_name = parent
                        if newfolder['naming']:
                            newfolder_name = naming(self.naming_method, title=newfolder['title'],
                                                    year=newfolder['year'], month=newfolder['month'],
                                                    day=newfolder['day'])
                        path_string.append(newfolder_name)
                        parent = newfolder['parent']
                    for path in path_string:
                        folder_name = os.path.join(path, folder_name)
                folderinfo = [folder_name, folder['title'], folder['description']]
                path = os.path.join(import_to, folder_name)
                if not os.path.isdir(path):
                    os.makedirs(path)
                if not app.database_folder_exists(folderinfo[0]):
                    app.database_folder_add(folderinfo)
                else:
                    if folderinfo[1]:
                        app.database_folder_update_title(folderinfo[0], folderinfo[1])
                    if folderinfo[2]:
                        app.database_folder_update_description(folderinfo[0], folderinfo[2])

                #Scan and import photos in folder
                for photo in photos:
                    if self.cancel_scanning:
                        break
                    completed = (imported_size/total_size)
                    remaining = 1 - completed
                    self.percent_completed = 100*completed
                    self.scanningpopup.scanning_percentage = self.percent_completed

                    seconds_elapsed = time.time() - self.start_time
                    time_elapsed = '  Time: '+str(datetime.timedelta(seconds=int(seconds_elapsed)))
                    if self.percent_completed > 0:
                        seconds_remain = (seconds_elapsed * remaining) / completed
                        time_remain = '  Remaining: ' + str(datetime.timedelta(seconds=int(seconds_remain)))
                    else:
                        time_remain = ''
                    self.scanningpopup.scanning_text = "Importing "+format_size(total_size)+'  '+str(int(self.percent_completed))+'%  '+time_elapsed+time_remain
                    old_full_filename = os.path.join(photo[2], photo[0])
                    new_photo_fullpath = os.path.join(folder_name, photo[10])
                    new_full_filename = os.path.join(import_to, new_photo_fullpath)
                    thumbnail_data = app.database_thumbnail_get(photo[0], temporary=True)
                    if not app.database_exists(new_photo_fullpath):
                        photo[0] = new_photo_fullpath
                        photo[1] = folder_name
                        photo[2] = import_to
                        photo[6] = int(time.time())

                        try:
                            copy2(old_full_filename, new_full_filename)
                        except:
                            failed_files = failed_files + 1
                            imported_size = imported_size + photo[4]
                        else:
                            if self.delete_originals:
                                if os.path.isfile(new_full_filename):
                                    if os.path.getsize(new_full_filename) == os.path.getsize(old_full_filename):
                                        os.remove(old_full_filename)
                            app.database_add(photo)
                            app.database_imported_add(photo[0], photo[10], photo[3])
                            if thumbnail_data:
                                thumbnail = thumbnail_data[2]
                                app.database_thumbnail_write(photo[0], int(time.time()), thumbnail, photo[13])
                            imported_size = imported_size+photo[4]
                            imported_files = imported_files + 1
                    else:
                        failed_files = failed_files + 1
                        imported_size = imported_size + photo[4]
                imported_folders.append(folder_name)
        app.imported.commit()
        app.photos.commit()
        app.folders.commit()
        app.thumbnails.commit()

        app.update_photoinfo(folders=imported_folders)
        self.scanningpopup.dismiss()
        if failed_files:
            failed = ' Could not import ' + str(failed_files) + ' files.'
        else:
            failed = ''
        if not self.cancel_scanning:
            if imported_files:

                app.message("Finished importing "+str(imported_files)+" files."+failed)
        else:
            if imported_files:
                app.message("Canceled importing, "+str(imported_files)+" files were imported."+failed)
            else:
                app.message("Canceled importing, no files were imported.")
        self.scanningpopup = None
        self.import_scanning = False
        Clock.schedule_once(lambda *dt: app.show_database())

    def set_delete_originals(self, state):
        """Enable the 'Delete Originals' option."""

        if state == 'down':
            self.delete_originals = True
        else:
            self.delete_originals = False

    def previous_album(self):
        """Switch to the previous album in the list."""

        database = self.ids['folders']
        selected_album = database.selected_node
        if selected_album:
            nodes = list(database.iterate_all_nodes())
            index = nodes.index(selected_album)
            if index <= 1:
                index = len(nodes)
            new_selected_album = nodes[index-1]
            database.select_node(new_selected_album)
            new_selected_album.on_press()
            database_container = self.ids['foldersContainer']
            database_container.scroll_to(new_selected_album)

    def next_album(self):
        """Switch to the next item on the list."""

        database = self.ids['folders']
        selected_album = database.selected_node
        if selected_album:
            nodes = list(database.iterate_all_nodes())
            index = nodes.index(selected_album)
            if index >= len(nodes)-1:
                index = 0
            new_selected_album = nodes[index+1]
            database.select_node(new_selected_album)
            new_selected_album.on_press()
            database_container = self.ids['foldersContainer']
            database_container.scroll_to(new_selected_album)

    def delete(self):
        """Remove selected files and place them in the unsorted folder."""

        if self.type == 'folder' or (self.type == 'extra' and self.selected == 'unsorted'):
            selected_files = self.get_selected_photos()
            for photo in selected_files:
                if self.selected != 'unsorted':
                    self.folders[self.selected]['photos'].remove(photo)
                    self.unsorted.append(photo)
            self.update_treeview()
            self.update_photolist()

    def add_folder(self):
        """Begin the add folder process, create an input popup."""

        content = InputPopup(hint='Folder Name', text='Enter A Folder Name:')
        app = App.get_running_app()
        content.bind(on_answer=self.add_folder_answer)
        self.popup = NormalPopup(title='Create Folder', content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 4),
                                 auto_dismiss=False)
        self.popup.open()

    def add_folder_answer(self, instance, answer):
        """Confirm adding the folder.
        Arguments:
            instance: Dialog that called this function.
            answer: String, if set to 'yes', folder is created.
        """

        if answer == 'yes':
            text = instance.ids['input'].text.strip(' ')
            if text:
                if text not in self.folders:
                    self.folders[text] = {'parent': '', 'naming': False, 'title': '', 'description': '',
                                          'year': 0, 'month': 0, 'day': 0, 'photos': []}
        self.dismiss_popup()
        self.update_treeview()

    def delete_folder(self):
        """Delete the selected import folder and move photos to the unsorted folder."""

        if self.type == 'folder' and self.selected:
            folder_info = self.folders[self.selected]
            photos = folder_info['photos']
            for photo in photos:
                self.unsorted.append(photo)
            del self.folders[self.selected]
            self.selected = ''
            self.type = 'None'
            self.update_treeview()
            self.update_photolist()

    def toggle_select(self):
        """Toggles the selection of photos in the current album."""

        photos = self.ids['photos']
        if photos.selected_nodes:
            selected = True
        else:
            selected = False
        photos.clear_selection()
        if not selected:
            photos.select_all()
        self.update_selected()

    def select_none(self):
        """Deselects all photos."""

        photos = self.ids['photos']
        photos.clear_selection()
        self.update_selected()

    def update_treeview(self):
        """Clears and repopulates the left-side folder list."""

        folder_list = self.ids['folders']

        #Clear the treeview list
        nodes = list(folder_list.iterate_all_nodes())
        for node in nodes:
            folder_list.remove_node(node)
        selected_node = None

        #folder_item = TreeViewButton(target='removed', type='extra', owner=self, view_album=False)
        #folder_item.folder_name = 'Removed (Never Scan Again)'
        #total_photos = len(self.removed)
        #folder_item.total_photos_numeric = total_photos
        #if total_photos > 0:
        #    folder_item.total_photos = '('+str(total_photos)+')'
        #folder_list.add_node(folder_item)
        #if self.selected == 'removed' and self.type == 'extra':
        #    selected_node = folder_item

        #Populate the 'Already Imported' folder
        folder_item = TreeViewButton(target='duplicates', type='extra', owner=self, view_album=False)
        folder_item.folder_name = 'Already Imported (Never Import Again)'
        total_photos = len(self.duplicates)
        folder_item.total_photos_numeric = total_photos
        if total_photos > 0:
            folder_item.total_photos = '('+str(total_photos)+')'
        folder_list.add_node(folder_item)
        if self.selected == 'duplicates' and self.type == 'extra':
            selected_node = folder_item

        #Populate the 'Unsorted' folder
        folder_item = TreeViewButton(target='unsorted', type='extra', owner=self, view_album=False)
        folder_item.folder_name = 'Unsorted (Not Imported This Time)'
        total_photos = len(self.unsorted)
        folder_item.total_photos_numeric = total_photos
        if total_photos > 0:
            folder_item.total_photos = '('+str(total_photos)+')'
        folder_list.add_node(folder_item)
        if self.selected == 'unsorted' and self.type == 'extra':
            selected_node = folder_item

        #Populate the importing folders
        sorted_folders = sorted(self.folders)
        self.total_size = 0
        to_parent = []
        added_nodes = {}
        for folder_date in sorted_folders:
            folder_info = self.folders[folder_date]
            target = folder_date
            folder_item = TreeViewButton(is_open=True, fullpath=target, dragable=True, target=target, type='folder',
                                         owner=self, view_album=False)
            if folder_info['naming']:
                folder_item.folder_name = naming(self.naming_method, title=folder_info['title'],
                                                 year=folder_info['year'], month=folder_info['month'],
                                                 day=folder_info['day'])
            else:
                folder_item.folder_name = folder_date
            added_nodes[folder_date] = folder_item
            photos = folder_info['photos']
            for photo in photos:
                self.total_size = self.total_size + photo[4]
            total_photos = len(photos)
            folder_item.total_photos_numeric = total_photos
            if total_photos > 0:
                folder_item.total_photos = '('+str(total_photos)+')'
            if folder_info['parent']:
                to_parent.append([folder_item, folder_info['parent']])
            else:
                folder_list.add_node(folder_item)
            if self.selected == target and self.type == 'folder':
                selected_node = folder_item
        for item in to_parent:
            node = item[0]
            parent_name = item[1]
            if parent_name in added_nodes.keys():
                folder_list.add_node(node, parent=added_nodes[parent_name])
            else:
                folder_list.add_node(node)
        if selected_node:
            folder_list.select_node(selected_node)
        size_display = self.ids['totalSize']
        size_display.text = 'Total Size: '+format_size(self.total_size)

    def on_selected(self, instance, value):
        """Called when a photo is selected.  Activate the delete button, and update photo view."""

        delete_button = self.ids['deleteButton']
        delete_button.disabled = True
        self.update_photolist()

    def new_description(self, description_editor):
        """Called when the description field of the currently selected folder is edited.
        Update internal variables to match.
        Argument:
            description_editor: The input box that has been edited.
        """

        description = description_editor.text
        if self.type == 'folder':
            self.folders[self.selected]['description'] = description

    def new_title(self, title_editor):
        """Called when the title field of the currently selected folder is edited.
        Update internal variables to match.
        Argument:
            title_editor: The input box that has been edited.
        """

        title = title_editor.text
        if self.type == 'folder':
            self.folders[self.selected]['title'] = title
            folder_info = self.folders[self.selected]
            self.update_treeview()
            folder_name = self.ids['folderName']
            folder_name.text = naming(self.naming_method, title=folder_info['title'], year=folder_info['year'],
                                      month=folder_info['month'], day=folder_info['day'])

    def update_photolist(self):
        """Redraw the photo list view for the currently selected folder."""

        folder_name = self.ids['folderName']
        photos = []
        name = ''
        title_editor = self.ids['folderTitle']
        description_editor = self.ids['folderDescription']
        dragable = True

        #Viewing an input folder.
        if self.type == 'folder':
            if self.selected in self.folders:
                folder_info = self.folders[self.selected]
                title_editor.text = folder_info['title']
                title_editor.disabled = False
                description_editor.text = folder_info['description']
                description_editor.disabled = False
                photos = folder_info['photos']
                if folder_info['naming']:
                    name = naming(self.naming_method, title=folder_info['title'], year=folder_info['year'],
                                  month=folder_info['month'], day=folder_info['day'])
                else:
                    name = self.selected

        #Viewing a special sorting folder.
        else:
            title_editor.text = ''
            title_editor.disabled = True
            description_editor.text = ''
            description_editor.disabled = True
            if self.selected == 'unsorted':
                photos = self.unsorted
                name = 'Unsorted (Not Imported This Time)'
            elif self.selected == 'removed':
                photos = self.removed
                name = 'Removed (Never Scanned Again)'
            elif self.selected == 'duplicates':
                dragable = False
                photos = self.duplicates
                name = 'Already Imported (Never Import Again)'

        folder_name.text = name

        #Populate photo view
        photos_container = self.ids['photosContainer']
        datas = []
        for photo in photos:
            full_filename = os.path.join(photo[2], photo[0])
            fullpath = photo[0]
            database_folder = photo[2]
            video = os.path.splitext(full_filename)[1].lower() in movietypes
            data = {
                'fullpath': fullpath,
                'temporary': True,
                'photoinfo': photo,
                'folder': self.selected,
                'database_folder': database_folder,
                'filename': full_filename,
                'target': self.selected,
                'type': self.type,
                'owner': self,
                'video': video,
                'photo_orientation': photo[13],
                'source': full_filename,
                'title': photo[10],
                'selected': False,
                'selectable': True,
                'dragable': dragable
            }
            datas.append(data)
        photos_container.data = datas
        self.select_none()

    def find_photo(self, photo_path, photo_list):
        """Searches through a list of photoinfo objects to find the specified photo.
        Arguments:
            photo_path: The database-relative path to the photo to search for.
            photo_list: The list of photo info objects to look through.
        Returns:
            False if nothing found
            Photo info list if match found.
        """

        for photo in photo_list:
            if photo[0] == photo_path:
                return photo
        return False

    def drop_widget(self, fullpath, position, dropped_type='file'):
        """Called when a widget is dropped after being dragged.
        Determines what to do with the widget based on where it is dropped.
        Arguments:
            fullpath: String, file location of the object being dragged.
            position: List of X,Y window coordinates that the widget is dropped on.
            dropped_type: String, describes the object being dropped.  May be: 'folder' or 'file'
        """

        folder_list = self.ids['folders']
        folder_container = self.ids['foldersContainer']
        if folder_container.collide_point(position[0], position[1]):
            offset_x, offset_y = folder_list.to_widget(position[0], position[1])
            for widget in folder_list.children:
                if widget.collide_point(position[0], offset_y):
                    if widget.type != 'None' and self.type != 'None' and not (widget.target == 'duplicates' and widget.type == 'extra'):

                        #Dropped a folder
                        if dropped_type == 'folder':
                            if widget.fullpath != fullpath:
                                parent = self.folders[widget.fullpath]['parent']
                                while parent:
                                    if parent == fullpath:
                                        return
                                    else:
                                        parent = self.folders[parent]['parent']
                                self.folders[fullpath]['parent'] = widget.fullpath
                                self.update_treeview()
                                self.update_photolist()
                            return

                        #Dropped a file
                        elif dropped_type == 'file':
                            photo_list = self.get_selected_photos(fullpath=True)
                            if fullpath not in photo_list:
                                photo_list.append(fullpath)
                            for photo_path in photo_list:
                                photo_info = False
                                if self.type == 'folder':
                                    photo_info = self.find_photo(photo_path, self.folders[self.selected]['photos'])
                                    if photo_info:
                                        self.folders[self.selected]['photos'].remove(photo_info)
                                else:
                                    if self.selected == 'unsorted':
                                        photo_info = self.find_photo(photo_path, self.unsorted)
                                        if photo_info:
                                            self.unsorted.remove(photo_info)
                                    elif self.selected == 'removed':
                                        photo_info = self.find_photo(photo_path, self.removed)
                                        if photo_info:
                                            self.removed.remove(photo_info)
                                if photo_info:
                                    if widget.type == 'folder':
                                        self.folders[widget.target]['photos'].append(photo_info)
                                    else:
                                        if widget.target == 'unsorted':
                                            self.unsorted.append(photo_info)
                                        elif widget.target == 'removed':
                                            self.removed.append(photo_info)

                            self.type = widget.type
                            self.selected = widget.target
                            self.update_treeview()
                            self.select_none()
                            return

        if dropped_type == 'folder':
            self.folders[fullpath]['parent'] = ''
            self.update_treeview()
            self.update_photolist()

    def update_selected(self):
        """Updates the delete button when files are selected or unselected.  Disables button if nothing is selected."""

        if self.type == 'folder' or (self.type == 'extra' and self.selected == 'unsorted'):
            photos = self.ids['photos']
            if photos.selected_nodes:
                selected = True
            else:
                selected = False
            delete_button = self.ids['deleteButton']
            if self.type != 'extra' and self.selected != 'unsorted':
                delete_button.disabled = not selected

    def has_popup(self):
        """Detects if the current screen has a popup active.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_popup(self):
        """Close a currently open popup for this screen."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def text_input_active(self):
        """Detects if any text input fields are currently active (being typed in).
        Returns: True or False
        """

        input_active = False
        for widget in self.walk(restrict=True):
            if widget.__class__.__name__ == 'NormalInput' or widget.__class__.__name__ == 'FloatInput' or widget.__class__.__name__ == 'IntegerInput':
                if widget.focus:
                    input_active = True
                    break
        return input_active

    def key(self, key):
        """Handles keyboard shortcuts, performs the actions needed.
        Argument:
            key: The name of the key command to perform.
        """

        if self.text_input_active():
            pass
        else:
            if not self.popup or (not self.popup.open):
                if key == 'left' or key == 'up':
                    self.previous_album()
                if key == 'right' or key == 'down':
                    self.next_album()
                if key == 'delete':
                    self.delete()
                if key == 'a':
                    self.toggle_select()
            elif self.popup and self.popup.open:
                if key == 'enter':
                    self.popup.content.dispatch('on_answer', 'yes')


class ExportScreen(Screen):
    popup = None
    sort_dropdown = ObjectProperty()
    sort_method = StringProperty()
    sort_reverse = BooleanProperty(False)
    target = StringProperty()
    type = StringProperty()
    photos_selected = BooleanProperty(False)
    photos = []
    cancel_exporting = BooleanProperty(False)
    total_export_files = NumericProperty(0)
    exported_files = NumericProperty(0)
    total_export = NumericProperty(0)
    exported_size = NumericProperty(0)
    current_upload_blocks = NumericProperty(0)
    exporting = BooleanProperty(False)
    export_start_time = NumericProperty(0)
    scanningthread = None  #Holder for the exporting process thread.
    ftp = None
    sort_reverse_button = StringProperty('normal')
    selected_preset = NumericProperty(-1)

    def get_selected_photos(self, fullpath=False):
        photos = self.ids['photos']
        selected_indexes = photos.selected_nodes
        photos_container = self.ids['photosContainer']
        selected_photos = []
        for selected in selected_indexes:
            if fullpath:
                selected_photos.append(photos_container.data[selected]['fullpath'])
            else:
                selected_photos.append(photos_container.data[selected]['photoinfo'])
        return selected_photos

    def on_sort_reverse(self, *_):
        """Updates the sort reverse button's state variable, since kivy doesnt just use True/False for button states."""

        app = App.get_running_app()
        self.sort_reverse_button = 'down' if to_bool(app.config.get('Sorting', 'album_sort_reverse')) else 'normal'

    def can_export(self):
        return self.photos_selected

    def dismiss_extra(self):
        """Dummy function, not valid for this screen, but the app calls it when escape is pressed."""
        return False

    def resort_method(self, method):
        """Sets the album sort method.
        Argument:
            method: String, the sort method to use
        """

        self.sort_method = method
        app = App.get_running_app()
        app.config.set('Sorting', 'album_sort', method)
        self.update_photolist()

    def resort_reverse(self, reverse):
        """Sets the album sort reverse.
        Argument:
            reverse: String, if 'down', reverse will be enabled, disabled on any other string.
        """

        app = App.get_running_app()
        sort_reverse = True if reverse == 'down' else False
        app.config.set('Sorting', 'album_sort_reverse', sort_reverse)
        self.sort_reverse = sort_reverse
        self.update_photolist()

    def toggle_select(self):
        """Select all files, or unselect all selected files."""

        photos = self.ids['photos']
        if photos.selected_nodes:
            selected = True
        else:
            selected = False
        photos.clear_selection()
        if not selected:
            photos.select_all()
        self.update_selected()

    def update_selected(self):
        """Checks if any viewed photos are selected."""

        photos = self.ids['photos']
        if photos.selected_nodes:
            selected = True
        else:
            selected = False
        self.photos_selected = selected

    def on_enter(self):
        """Called when this screen is entered.  Sets up widgets and gets the photo list."""

        self.selected_preset = -1
        app = App.get_running_app()
        self.exporting = False
        self.sort_dropdown = AlbumSortDropDown()
        self.sort_dropdown.bind(on_select=lambda instance, x: self.resort_method(x))
        self.sort_method = app.config.get('Sorting', 'album_sort')
        self.sort_reverse = to_bool(app.config.get('Sorting', 'album_sort_reverse'))
        self.target = app.export_target
        self.type = app.export_type

        #Get photos
        self.photos = []
        if self.type == 'Album':
            for albuminfo in app.albums:
                if albuminfo['name'] == self.target:
                    photo_paths = albuminfo['photos']
                    for fullpath in photo_paths:
                        photoinfo = app.database_exists(fullpath)
                        if photoinfo:
                            self.photos.append(photoinfo)
        elif self.type == 'Tag':
            self.photos = app.database_get_tag(self.target)
        else:
            self.photos = app.database_get_folder(self.target)

        self.update_treeview()
        self.update_photolist()
        photos = self.ids['photos']
        photos.select_all()
        self.update_selected()

    def update_photolist(self):
        """Clears and refreshes the grid view of photos."""

        #sort photo list
        if self.sort_method == 'Import Date':
            sorted_photos = sorted(self.photos, key=lambda x: x[6], reverse=self.sort_reverse)
        elif self.sort_method == 'Modified Date':
            sorted_photos = sorted(self.photos, key=lambda x: x[7], reverse=self.sort_reverse)
        elif self.sort_method == 'Owner':
            sorted_photos = sorted(self.photos, key=lambda x: x[11], reverse=self.sort_reverse)
        elif self.sort_method == 'File Name':
            sorted_photos = sorted(self.photos, key=lambda x: os.path.basename(x[0]), reverse=self.sort_reverse)
        else:
            sorted_photos = sorted(self.photos, key=lambda x: x[0], reverse=self.sort_reverse)

        #Create photo widgets
        photos_container = self.ids['photosContainer']
        datas = []
        for photo in sorted_photos:
            full_filename = os.path.join(photo[2], photo[0])
            tags = photo[8].split(',')
            favorite = True if 'favorite' in tags else False
            fullpath = photo[0]
            database_folder = photo[2]
            video = os.path.splitext(full_filename)[1].lower() in movietypes
            data = {
                'fullpath': fullpath,
                'photoinfo': photo,
                'folder': self.target,
                'database_folder': database_folder,
                'filename': full_filename,
                'target': self.target,
                'type': self.type,
                'owner': self,
                'favorite': favorite,
                'video': video,
                'photo_orientation': photo[13],
                'source': full_filename,
                'temporary': False,
                'selected': False,
                'selectable': True,
                'dragable': False,
                'view_album': False
            }
            datas.append(data)
        photos_container.data = datas
        self.toggle_select()

    def on_leave(self):
        """Called when the screen is left, write changes to export presets."""

        app = App.get_running_app()
        #app.export_preset_write()
        presets = self.ids['presets']
        presets.clear_widgets()
        photo_container = self.ids['photosContainer']
        photo_container.data = []

    def update_treeview(self):
        """Clears and populates the export presets list on the left side."""

        app = App.get_running_app()
        presets = self.ids['presets']

        #Clear old presets
        presets.clear_widgets()

        #Populate export presets nodes
        for index, export_preset in enumerate(app.exports):
            preset = ExportPreset(index=index, text=export_preset['name'], data=export_preset, owner=self)
            if index == self.selected_preset:
                preset.expanded = True
            presets.add_widget(preset)

    def cancel_export(self, *_):
        """Signal to stop the exporting process.  Will also try to close the ftp connection if it exists."""

        self.cancel_exporting = True
        try:
            self.ftp.close()
        except:
            pass

    def export(self):
        """Begins the export process.  Opens a progress dialog, and starts the export thread."""

        self.ftp = False
        app = App.get_running_app()
        preset = app.exports[self.selected_preset]
        if preset['export'] == 'ftp':
            if not preset['ftp_address']:
                app.message(text="Please Set Export Location")
                return
        else:
            if not preset['export_folder']:
                app.message(text="Please Set Export Location")
                return
        if not self.photos_selected:
            app.message(text="Please Select Photos To Export")
            return
        self.cancel_exporting = False
        self.popup = ScanningPopup(title='Exporting Files', auto_dismiss=False, size_hint=(None, None),
                                   size=(app.popup_x, app.button_scale * 4))
        self.popup.open()
        scanning_button = self.popup.ids['scanningButton']
        scanning_button.bind(on_press=self.cancel_export)
        self.scanningthread = threading.Thread(target=self.exporting_process)
        self.scanningthread.start()

    def update_percentage(self, *_):
        """Updates the exporting process percentage value in the exporting dialog."""

        self.current_upload_blocks = self.current_upload_blocks + 1
        file_completed = (8192*self.current_upload_blocks)
        percent_completed = int(100*((self.exported_size+file_completed)/self.total_export))
        self.popup.scanning_percentage = percent_completed
        time_taken = time.time() - self.export_start_time
        if percent_completed > 0:
            total_time = (100/percent_completed)*time_taken
            time_remaining = total_time - time_taken
            str(datetime.timedelta(seconds=time_remaining))
            remaining = ', '+str(datetime.timedelta(seconds=int(time_remaining)))+' Remaining'
        else:
            remaining = ''
        self.popup.scanning_text = 'Uploading: '+str(self.exported_files)+' out of '+str(self.total_export_files)+' files'+remaining

    def exporting_process(self):
        """Handles exporting the files.  This should be in a different thread so the interface can still respond."""

        self.exporting = True
        app = App.get_running_app()
        preset = app.exports[self.selected_preset]

        #Get photo list
        ignore_tags = preset['ignore_tags']
        exported_photos = 0
        selected_photos = self.get_selected_photos()
        photos = []
        for photo in selected_photos:
            if photo[12] != 0:
                ignore_file = False
                if ignore_tags:
                    for tag in ignore_tags:
                        photo_tags = photo[8].split(',')
                        if tag in photo_tags:
                            ignore_file = True
                if not preset['export_videos']:
                    path, extension = os.path.splitext(photo[0])
                    if extension.lower() in movietypes:
                        ignore_file = True
                if not ignore_file:
                    photos.append(photo)

        #photo_container = self.ids['photos']
        #for widget in photo_container.children:
        #    photoinfo = widget.photoinfo
        #    if photoinfo[12] != 0 and widget.select:
        #        ignore_file = False
        #        if ignore_tags:
        #            for tag in ignore_tags:
        #                if tag in photoinfo[8]:
        #                    ignore_file = True
        #        if not preset['export_videos']:
        #            path, extension = os.path.splitext(photoinfo[0])
        #            if extension.lower() in movietypes:
        #                ignore_file = True
        #        if not ignore_file:
        #            photos.append(photoinfo)
        if not photos:
            return

        #determine export filenames (prevent any duplicate filenames)
        export_photos = []
        for photo in photos:
            photo_filename = os.path.basename(photo[0])
            basename, extension = os.path.splitext(photo_filename)
            test_name = photo_filename
            add_number = 0
            while test_name in export_photos:
                add_number = add_number+1
                test_name = basename+"("+str(add_number)+")"+extension
            export_photos.append(test_name)

        if self.type == 'tag':
            subfolder = 'Photos Tagged As '+self.target.title()
        else:
            subfolder = os.path.split(self.target)[1]

        #ftp export mode
        if preset['export'] == 'ftp':
            subfolder = subfolder.replace("'", "").replace("/", " - ").replace("\\", " - ")
            if '/' in preset['ftp_address']:
                ftp_host, ftp_folder = preset['ftp_address'].split('/', 1)
                ftp_folder = ftp_folder.strip('/')
            else:
                ftp_host = preset['ftp_address']
                ftp_folder = ''
            from ftplib import FTP
            try:
                self.ftp = ftp = FTP()
                self.popup.scanning_text = 'Connecting To FTP...'
                ftp.connect(ftp_host, preset['ftp_port'])
                self.popup.scanning_text = 'Logging In To FTP...'
                ftp.login(preset['ftp_user'], preset['ftp_password'])
                ftp.set_pasv(preset['ftp_passive'])
                self.popup.scanning_text = 'Creating Folders...'
                ftp_filelist = ftp.nlst()

                #set the ftp folder and create if needed
                if ftp_folder:
                    subfolders = ftp_folder.split('/')
                    for folder in subfolders:
                        if folder not in ftp_filelist:
                            ftp.mkd(folder)
                        ftp.cwd(folder)
                        ftp_filelist = ftp.nlst()
                if preset['create_subfolder']:
                    file_list = ftp.nlst()
                    if subfolder not in file_list:
                        ftp.mkd(subfolder)
                    ftp.cwd(subfolder)
                    ftp_filelist = ftp.nlst()

                if preset['export_info']:
                    self.popup.scanning_text = 'Uploading Photo Info...'
                    infofile = os.path.join(".photoinfo.ini")
                    if os.path.exists(infofile):
                        os.remove(infofile)
                    app.save_photoinfo(self.target, '.', '', photos=photos, newnames=export_photos)
                    if '.photoinfo.ini' in ftp_filelist:
                        ftp.delete('.photoinfo.ini')
                    if os.path.exists(infofile):
                        ftp.storbinary("STOR .photoinfo.ini", open(infofile, 'rb'))
                        os.remove(infofile)
                self.total_export = 0
                for photo in photos:
                    photofile = os.path.join(photo[2], photo[0])
                    if os.path.exists(photofile):
                        self.total_export = self.total_export + os.path.getsize(photofile)
                self.popup.scanning_text = 'Uploading '+str(len(photos))+' Files'
                self.exported_size = 0
                self.total_export_files = len(photos)
                self.export_start_time = time.time()
                for index, photo in enumerate(photos):
                    self.exported_files = index+1
                    percent_completed = 100*(self.exported_size/self.total_export)
                    self.popup.scanning_percentage = percent_completed
                    if self.cancel_exporting:
                        self.popup.scanning_text = 'Upload Canceled, '+str(index)+' Files Uploaded'
                        break
                    photofile = os.path.join(photo[2], photo[0])
                    if os.path.exists(photofile):
                        photo_size = os.path.getsize(photofile)
                        extension = os.path.splitext(photofile)[1]
                        photofilename = export_photos[index]
                        #photofilename = os.path.basename(photofile)
                        if photofilename in ftp_filelist:
                            ftp.delete(photofilename)

                        if extension.lower() in imagetypes and (preset['scale_image'] or preset['watermark']):
                            #image needs to be edited in some way
                            imagedata = Image.open(photofile)
                            if imagedata.mode != 'RGB':
                                imagedata = imagedata.convert('RGB')

                            orientation = photo[13]
                            imagedata = app.edit_fix_orientation(imagedata, orientation)

                            if preset['scale_image']:
                                imagedata = app.edit_scale_image(imagedata, preset['scale_size'], preset['scale_size_to'])
                            if preset['watermark']:
                                imagedata = app.edit_add_watermark(imagedata, preset['watermark_image'],
                                                                   preset['watermark_opacity'],
                                                                   preset['watermark_horizontal'],
                                                                   preset['watermark_vertical'], preset['watermark_size'])
                            output = BytesIO()
                            imagedata.save(output, 'JPEG', quality=preset['jpeg_quality'])
                            output.seek(0)
                            self.current_upload_blocks = 0
                            ftp.storbinary("STOR "+photofilename, output, callback=self.update_percentage)
                        else:
                            #image or video should just be uploaded
                            self.current_upload_blocks = 0
                            ftp.storbinary("STOR "+photofilename, open(photofile, 'rb'),
                                           callback=self.update_percentage)
                        exported_photos = exported_photos + 1
                        self.exported_size = self.exported_size+photo_size

                        #check that the file was uploaded
                        ftp_filelist = ftp.nlst()
                        if photofilename not in ftp_filelist:
                            self.cancel_exporting = True
                            self.popup.scanning_text = 'Unable To Upload "'+photo[0]+'".'
                ftp.quit()
                ftp.close()
                self.ftp = False
            except Exception as e:
                if self.cancel_exporting:
                    self.popup.scanning_text = 'Canceled Upload. Partial Files May Be Left On The Server.'
                else:
                    self.cancel_exporting = True
                    self.popup.scanning_text = 'Unable To Upload: '+str(e)

        #local directory export mode
        else:
            if preset['create_subfolder']:
                save_location = os.path.join(preset['export_folder'], subfolder)
            else:
                save_location = preset['export_folder']
            if not os.path.exists(save_location):
                os.makedirs(save_location)
            if preset['export_info']:
                app.save_photoinfo(self.target, save_location, self.type.lower(), photos=photos, newnames=export_photos)
            self.total_export = 0
            for photo in photos:
                photofile = os.path.join(photo[2], photo[0])
                if os.path.exists(photofile):
                    self.total_export = self.total_export + os.path.getsize(photofile)
            self.popup.scanning_text = 'Exporting '+str(len(photos))+' Files'
            self.exported_size = 0
            self.total_export_files = len(photos)
            self.export_start_time = time.time()
            for index, photo in enumerate(photos):
                self.exported_files = index+1
                percent_completed = 100*(self.exported_size/self.total_export)
                self.popup.scanning_percentage = percent_completed
                if self.cancel_exporting:
                    self.popup.scanning_text = 'Export Canceled, '+str(index)+' Files Exported'
                    break
                photofile = os.path.join(photo[2], photo[0])
                if os.path.exists(photofile):
                    photo_size = os.path.getsize(photofile)
                    extension = os.path.splitext(photofile)[1]
                    #photofilename = os.path.basename(photofile)
                    photofilename = export_photos[index]
                    savefile = os.path.join(save_location, photofilename)
                    if os.path.exists(savefile):
                        os.remove(savefile)
                    if extension.lower() in imagetypes and (preset['scale_image'] or preset['watermark']):
                        #image needs to be edited in some way
                        imagedata = Image.open(photofile)
                        if imagedata.mode != 'RGB':
                            imagedata = imagedata.convert('RGB')
                        orientation = photo[13]
                        imagedata = app.edit_fix_orientation(imagedata, orientation)

                        if preset['scale_image']:
                            imagedata = app.edit_scale_image(imagedata, preset['scale_size'], preset['scale_size_to'])
                        if preset['watermark']:
                            imagedata = app.edit_add_watermark(imagedata, preset['watermark_image'],
                                                               preset['watermark_opacity'], preset['watermark_horizontal'],
                                                               preset['watermark_vertical'], preset['watermark_size'])
                        imagedata.save(savefile, 'JPEG', quality=preset['jpeg_quality'])
                    else:
                        #image or video should just be copied
                        copy2(photofile, savefile)
                    exported_photos = exported_photos + 1
                    self.exported_size = self.exported_size+photo_size
            self.exporting = False
        if not self.cancel_exporting:
            app.message('Completed Exporting '+str(len(photos))+' files.')
            Clock.schedule_once(self.finish_export)
        else:
            scanning_button = self.popup.ids['scanningButton']
            scanning_button.text = 'OK'
            scanning_button.bind(on_press=self.finish_export)

    def finish_export(self, *_):
        """Closes the export popup and leaves this screen."""

        self.popup.dismiss()
        app = App.get_running_app()
        app.show_database()

    def add_preset(self):
        """Create a new export preset and refresh the preset list."""

        app = App.get_running_app()
        app.export_preset_new()
        self.selected_preset = len(app.exports) - 1
        self.update_treeview()

    def has_popup(self):
        """Detects if the current screen has a popup active.
        Returns: True or False
        """

        if self.popup:
            if self.popup.open:
                return True
        return False

    def dismiss_popup(self, *_):
        """Close a currently open popup for this screen."""

        if self.exporting:
            self.cancel_export()
        else:
            if self.popup:
                self.popup.dismiss()
                self.popup = None

    def text_input_active(self):
        """Detects if any text input fields are currently active (being typed in).
        Returns: True or False
        """

        input_active = False
        for widget in self.walk(restrict=True):
            if widget.__class__.__name__ == 'NormalInput' or widget.__class__.__name__ == 'FloatInput' or widget.__class__.__name__ == 'IntegerInput':
                if widget.focus:
                    input_active = True
                    break
        return input_active

    def key(self, key):
        """Handles keyboard shortcuts, performs the actions needed.
        Argument:
            key: The name of the key command to perform.
        """

        if self.text_input_active():
            pass
        else:
            if not self.popup or (not self.popup.open):
                if key == 'a':
                    self.toggle_select()


class DatabaseRestoreScreen(Screen):
    popup = None

    def dismiss_extra(self):
        """Dummy function, not valid for this screen, but the app calls it when escape is pressed."""
        return True

    def on_enter(self):
        app = App.get_running_app()
        completed = app.database_restore_process()
        if completed != True:
            app.message("Error: "+completed)
        app.setup_database(restore=True)
        Clock.schedule_once(app.show_database, 1)


class PhotoManager(App):
    """Main class of the app."""

    settings_open = BooleanProperty(False)
    right_panel = BooleanProperty(False)
    last_width = NumericProperty(0)
    #leftpanel_width = NumericProperty()
    #rightpanel_width = NumericProperty()
    button_scale = NumericProperty(40)
    text_scale = NumericProperty(12)
    data_directory = StringProperty('')
    app_location = StringProperty('')
    database_auto_rescanner = ObjectProperty()
    database_auto_rescan_timer = NumericProperty(0)
    database_update_text = StringProperty('')
    showhelp = BooleanProperty(True)
    infotext = StringProperty('')
    infotext_setter = ObjectProperty()
    single_database = BooleanProperty(True)
    simple_interface = BooleanProperty(False)

    #Theming variables
    icon = 'data/icon.png'
    selected_color = (0.5098, 0.8745, 0.6588, .5)
    color_odd = (0, 0, 0, 0)
    color_even = (1, 1, 1, .1)
    padding = 10
    popup_x = 640

    interpolation = StringProperty('Catmull-Rom')  #Interpolation mode of the curves dialog.
    fullpath = StringProperty()
    database_scanning = BooleanProperty(False)
    database_sort = StringProperty('')
    album_sort = StringProperty('')
    database_sort_reverse = BooleanProperty(False)
    album_sort_reverse = BooleanProperty(False)
    thumbsize = 256  #Size in pixels of the long side of any generated thumbnails
    album_directory = 'Albums'  #Directory name to look in for album files
    tag_directory = 'Tags'  #Directory name to look in for tag files
    settings_cls = PhotoManagerSettings
    target = StringProperty()
    type = StringProperty('None')
    photo = StringProperty('')
    imports = []
    exports = []
    albums = []
    tags = []
    programs = []
    shift_pressed = BooleanProperty(False)
    cancel_scanning = BooleanProperty(False)
    export_target = StringProperty()
    export_type = StringProperty()
    encoding_presets = ListProperty()
    selected_encoder_preset = StringProperty()

    #Widget holders
    drag_image = ObjectProperty()
    drag_treenode = ObjectProperty()
    main_layout = ObjectProperty()  #Main layout root widget
    screen_manager = ObjectProperty()
    database_screen = ObjectProperty()
    album_screen = ObjectProperty()
    importing_screen = ObjectProperty()
    database_restore_screen = ObjectProperty()
    scanningthread = None
    scanningpopup = None
    popup = None

    #Databases
    photos = None
    folders = None
    thumbnails = None
    tempthumbnails = None
    imported = None

    about_text = StringProperty()

    def set_single_database(self):
        databases = self.get_database_directories()
        if len(databases) > 1:
            self.single_database = False
        else:
            self.single_database = True

    def message(self, text, timeout=20):
        """Sets the app.infotext variable to a specific message, and clears it after a set amount of time."""

        self.infotext = text
        if self.infotext_setter:
            self.infotext_setter.cancel()
        self.infotext_setter = Clock.schedule_once(self.clear_message, timeout)

    def clear_message(self, *_):
        self.infotext = ''

    def clear_database_update_text(self, *_):
        self.database_update_text = ''

    def refresh_photo(self, fullpath, force=False, no_photoinfo=False, data=False):
        """Checks if a file's modified date has changed, updates photoinfo and thumbnail if it has"""

        if data:
            old_photoinfo = data
        else:
            old_photoinfo = self.database_exists(fullpath)
        if old_photoinfo:
            #Photo is in database, check if it has been modified in any way
            photo_filename = os.path.join(old_photoinfo[2], old_photoinfo[0])
            if os.path.isfile(photo_filename):
                #file still exists
                modified_date = int(os.path.getmtime(photo_filename))
                if modified_date != old_photoinfo[7] or force:
                    #file has been modified somehow, need to update data
                    new_photoinfo = get_file_info([old_photoinfo[0], old_photoinfo[2]], import_mode=True, modified_date=modified_date)
                    photoinfo = list(old_photoinfo)
                    photoinfo[7] = new_photoinfo[7]
                    photoinfo[13] = new_photoinfo[13]
                    self.database_item_update(photoinfo)
                    if not no_photoinfo:
                        self.update_photoinfo(folders=[photoinfo[1]])
                    self.database_thumbnail_update(photoinfo[0], photoinfo[2], photoinfo[7], photoinfo[13], force=True)
                    if self.screen_manager.current == 'album':
                        album_screen = self.screen_manager.get_screen('album')
                        album_screen.clear_cache()
                    return photoinfo
        return False

    def toggle_quicktransfer(self, button):
        if self.config.get("Settings", "quicktransfer") == '0':
            self.config.set("Settings", "quicktransfer", '1')
            button.state = 'normal'
        else:
            self.config.set("Settings", "quicktransfer", '0')
            button.state = 'down'

    def about(self):
        """Creates and opens a dialog telling about this program."""

        title = "About Snu Photo Manager"
        self.popup = AboutPopup(title=title)
        self.popup.open()

    def canprint(self):
        """Check if in desktop mode.
        Returns: Boolean True if in desktop mode, False if not.
        """

        if desktop:
            return True
        else:
            return False

    def print_photo(self):
        """Calls the operating system to print the currently viewed photo."""

        photo_info = self.database_exists(self.fullpath)
        if photo_info:
            photo_file = os.path.abspath(os.path.join(photo_info[2], photo_info[0]))
            self.message("Printing photo...")
            os.startfile(photo_file, "print")

    def program_run(self, index, button):
        """Loads the currently viewed photo in an external program using an external program preset.
        Argument:
            index: Integer, index of the preset to use.
            button: Widget, the button that called this function.
        """

        name, command, argument = self.programs[index]
        if os.path.isfile(command):
            button.disabled = True  # Disable the button so the user knows something is happening
            photo_info = self.database_exists(self.fullpath)
            argument_replace = ''
            if photo_info:
                photo_file = os.path.join(photo_info[2], photo_info[0])
                abs_photo = os.path.abspath(photo_file)
                photo_date = photo_info[7]
                argument_replace = argument.replace('%i', '"'+abs_photo+'"')
                argument_replace = argument_replace.replace('%%', '%')

                run_command = command+' '+argument_replace
                Clock.schedule_once(lambda *dt: self.program_run_finish(run_command, photo_info, button))
        else:
            self.popup_message(text='Not A Valid Program')

    def program_run_finish(self, command, photo_info, button):
        """Finishes the program_run command, must be delayed by a frame to allow the button to be visibly disabled."""

        call(command)
        self.refresh_photo(photo_info[0])
        button.disabled = False

    def program_save(self, index, name, command, argument):
        """Updates an external program preset.
        Arguments:
            index: Integer, index of the preset to run.
            name: Program name
            command: Path to the program executable.
            argument: Extra command arguments
        """

        self.programs[index] = [name, command, argument]
        self.program_export()

    def program_add(self, name, command, argument):
        """Creates a new external program preset.
        Arguments:
            name: Program name
            command: Path to the program executable.
            argument: Extra command arguments
        """

        self.programs.append([name, command, argument])
        self.program_export()

    def program_remove(self, index):
        """Deletes an external program preset.
        Argument:
            index: Integer, preset index to delete.
        """

        del self.programs[index]
        self.program_export()

    def program_export(self):
        """Save current external program presets to the config file."""

        configfile = ConfigParser(interpolation=None)
        for index, preset in enumerate(self.programs):
            name, command, argument = preset
            section = str(index)
            configfile.add_section(section)
            configfile.set(section, 'name', name)
            configfile.set(section, 'command', command)
            configfile.set(section, 'argument', argument)
        with open(self.data_directory+os.path.sep+'programs.ini', 'w') as config:
            configfile.write(config)

    def program_import(self):
        """Import external program presets from the config file."""

        self.programs = []
        filename = self.data_directory+os.path.sep+'programs.ini'
        if os.path.isfile(filename):
            configfile = ConfigParser(interpolation=None)
            configfile.read(filename)
            program_presets = configfile.sections()
            for preset in program_presets:
                program_preset = dict(configfile.items(preset))
                name = program_preset['name']
                command = program_preset['command']
                argument = program_preset['argument']
                self.programs.append([name, command, argument])

    def save_photoinfo(self, target, save_location, container_type='folder', photos=list(), newnames=False):
        """Save relavent photoinfo files for a folder, album, tag, or specified photos.
        Arguments:
            target: String, database identifier for the path where the photos are.
            save_location: String, full absolute path to the folder where the photoinfo file should be saved.
            container_type: String, defaults to 'folder', may be folder, album or tag.
            photos: Optional, List of photoinfo objects to save the photoinfo for.
        """

        description = ''
        title = ''

        #If photos are not provided, find them for the given target.
        if not photos:
            if container_type == 'tag':
                photos = self.database_get_tag(target)
                title = "Photos tagged as '"+target+"'"
            elif container_type == 'album':
                index = self.album_find(target)
                if index >= 0:
                    album_info = self.albums[index]
                    photos = album_info['photos']
                    title = album_info['name']
                    description = album_info['description']
            elif container_type == 'folder':
                folder_info = self.database_folder_exists(target)
                if folder_info:
                    title = folder_info[1]
                    description = folder_info[2]
                photos = self.database_get_folder(target)
            else:
                return

        if photos:
            if newnames:
                if len(newnames) != len(photos):
                    newnames = False
            #Set up config file
            configfile = ConfigParser(interpolation=None)
            config_filename = os.path.join(save_location, '.photoinfo.ini')
            if os.path.exists(config_filename):
                os.remove(config_filename)
            configfile.add_section('Album')
            configfile.set('Album', 'title', title)
            configfile.set('Album', 'description', description)

            #Save photo info
            for index, photo in enumerate(photos):
                if newnames:
                    photo_filename = newnames[index]
                else:
                    photo_filename = os.path.basename(photo[0])
                configfile.add_section(photo_filename)
                configfile.set(photo_filename, 'tags', photo[8])
                configfile.set(photo_filename, 'owner', photo[11])
                configfile.set(photo_filename, 'edited', str(photo[9]))
                configfile.set(photo_filename, 'import_date', str(photo[6]))
                configfile.set(photo_filename, 'rename', photo[5])
                configfile.set(photo_filename, 'export', str(photo[12]))
            try:
                with open(config_filename, 'w') as config:
                    configfile.write(config)
            except:
                pass

    def update_photoinfo(self, folders=list()):
        """Updates the photoinfo files in given folders.
        Arguments:
            folders: List containing Strings for database-relative paths to each folder.
        """

        if self.config.get("Settings", "photoinfo"):
            databases = self.get_database_directories()
            folders = list(set(folders))
            for folder in folders:
                for database in databases:
                    full_path = os.path.join(database, folder)
                    if os.path.isdir(full_path):
                        self.save_photoinfo(target=folder, save_location=full_path)

    def in_database(self, photo_info):
        """Checks the photo database to see if any matches are found for the given file.
        Argument:
            photo_info: List, a photoinfo object.
        Returns: List of photoinfo matches, or False if none found.
        """

        photo_info = agnostic_photoinfo(photo_info)
        original_file = photo_info[10]
        filename_matches = list(self.photos.select('SELECT * FROM photos WHERE OriginalFile = ?', (original_file,)))
        if filename_matches:
            #filename match(es) found
            for filename_match in filename_matches:
                if photo_info[3] == filename_match[3]:
                    #date match found
                    return local_photoinfo(list(filename_match))
        return False

    def in_imported(self, photo_info):
        """Checks the imported database to see if any matches are found for the given file.
        Argument:
            photo_info: List, a photoinfo object.
        Returns: True if matches, or False if none found.
        """

        photo_info = agnostic_photoinfo(photo_info)
        original_file = photo_info[10]
        filename_matches = list(self.imported.select('SELECT * FROM imported WHERE File = ?', (original_file,)))
        if filename_matches:
            #filename match(es) found
            for filename_match in filename_matches:
                if photo_info[3] == filename_match[2]:
                    #date match found
                    return True
        return False

    def on_config_change(self, config, section, key, value):
        self.simple_interface = to_bool(self.config.get("Settings", "simpleinterface"))
        if key == 'buttonsize' or key == 'textsize':
            self.rescale_interface(force=True)
            Clock.schedule_once(self.database_screen.on_enter)

    def build_config(self, config):
        """Setup config file if it is not found."""

        if desktop:
            simple_interface = 0
        else:
            simple_interface = 1
        config.setdefaults(
            'Settings', {
                'photoinfo': 1,
                'buttonsize': 100,
                'textsize': 100,
                'thumbsize': 160,
                'leftpanel': 0.2,
                'rightpanel': 0.2,
                'videoautoplay': 0,
                'precache': 1,
                'rememberview': 1,
                'viewtype': '',
                'viewtarget': '',
                'viewdisplayable': 0,
                'autoscan': 0,
                'quicktransfer': 0,
                'lowmem': 0,
                'simpleinterface': simple_interface,
                'backupdatabase': 1
            })
        config.setdefaults(
            'Database Directories', {
                'paths': '',
                'achive': 0
            })
        config.setdefaults(
            'Sorting', {
                'database_sort': 'Folder Name',
                'database_sort_reverse': 0,
                'album_sort': 'File Name',
                'album_sort_reverse': 0
            })
        config.setdefaults(
            'Presets', {
                'import': 0,
                'export': 0,
                'encoding': ''
            })

    def build_settings(self, settings):
        """Kivy settings dialog panel.
        Settings types: title, bool, numeric, options, string, path
        """

        settingspanel = []
        settingspanel.append({
            "type": "aboutbutton",
            "title": "",
            "section": "Settings",
            "key": "photoinfo"
        })
        settingspanel.append({
            "type": "multidirectory",
            "title": "Database Directories",
            "desc": "Folders For Image Database",
            "section": "Database Directories",
            "key": "paths"
        })
        settingspanel.append({
            "type": "databaseimport",
            "title": "",
            "section": "Database Directories",
            "key": "paths"
        })
        settingspanel.append({
            "type": "databaseclean",
            "title": "",
            "desc": "Remove all missing files in database.  Warning: Make sure all remote directories are accessible",
            "section": "Database Directories",
            "key": "paths"
        })
        settingspanel.append({
            "type": "databasebackup",
            "title": "",
            "desc": "Creates a backup of the current photo databases",
            "section": "Database Directories",
            "key": "paths"
        })
        settingspanel.append({
            "type": "databaserestore",
            "title": "",
            "desc": "Restore and reload database backups from previous run if they exist",
            "section": "Database Directories",
            "key": "paths"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Save .photoinfo.ini Files",
            "desc": "Auto-save .photoinfo.ini files in album folders when photos or albums are changed",
            "section": "Settings",
            "key": "photoinfo"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Button Size Percent",
            "desc": "Scale Percentage Of Interface Buttons",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Text Size Percent",
            "desc": "Scale Percentage Of Interface Text",
            "section": "Settings",
            "key": "textsize"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Thumbnail Size",
            "desc": "Size In Pixels Of Generated Thumbnails",
            "section": "Settings",
            "key": "thumbsize"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Auto-Play Videos On View",
            "desc": "Automatically play videos when they are viewed in album mode",
            "section": "Settings",
            "key": "videoautoplay"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Auto-Cache Images When Browsing",
            "desc": "Automatically cache the next and previous images when browsing an album",
            "section": "Settings",
            "key": "precache"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Remember Last Album View",
            "desc": "Remembers and returns to the last album or folder that was being viewed on last run",
            "section": "Settings",
            "key": "rememberview"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Auto-Rescan Database Interval In Minutes",
            "desc": "Auto-rescan database every number of minutes.  0 will never auto-scan.  Setting this too low will slow the system down",
            "section": "Settings",
            "key": "autoscan"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Simplify Interface For Smaller Screens",
            "desc": "Removes some components of the interface.  Intended for phones or touch screen devices.",
            "section": "Settings",
            "key": "simpleinterface"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Low Memory Mode",
            "desc": "For Older Computers That Show Larger Images As Black, Displays All Images At A Smaller Size.",
            "section": "Settings",
            "key": "lowmem"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Backup Photo Database On Startup",
            "desc": "Automatically make a copy of the photo database on each restart.  Will increase startup time when large databases are loaded.",
            "section": "Settings",
            "key": "backupdatabase"
        })
        settings.add_json_panel('Settings', self.config, data=json.dumps(settingspanel))

    def has_database(self, *_):
        databases = self.get_database_directories()
        if databases:
            return True
        else:
            return False

    def database_auto_rescan(self, *_):
        rescan_time = float(self.config.get("Settings", "autoscan"))
        if rescan_time > 0:
            self.database_auto_rescan_timer = self.database_auto_rescan_timer - 1
            if self.database_auto_rescan_timer < 1:
                self.database_rescan()
                self.database_auto_rescan_timer = rescan_time

    def on_start(self):
        """Function called when the app is first started.
        Add a custom keyboard hook so key buttons can be intercepted.
        """

        #self.rescale_interface(force=True)
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        if not self.has_database():
            self.open_settings()
        self.database_auto_rescan_timer = float(self.config.get("Settings", "autoscan"))
        self.database_auto_rescanner = Clock.schedule_interval(self.database_auto_rescan, 60)
        Window.bind(on_draw=self.rescale_interface)

    def on_pause(self):
        """Function called when the app is paused or suspended on a mobile platform.
        Saves all settings and data.
        """

        self.config.write()
        self.thumbnails.commit()
        self.photos.commit()
        self.folders.commit()
        self.imported.commit()
        return True

    def on_resume(self):
        print('Resuming App...')

    def on_stop(self):
        """Function called just before the app is closed.
        Saves all settings and data.
        """

        if self.database_scanning:
            self.cancel_database_import()
            self.scanningthread.join()
        self.config.write()
        self.tempthumbnails.close()
        self.tempthumbnails.join()
        self.thumbnails.close()
        self.thumbnails.join()
        self.photos.close()
        self.photos.join()
        self.folders.close()
        self.folders.join()
        self.imported.close()
        self.imported.join()

    def open_settings(self, *largs):
        self.settings_open = True
        super().open_settings(*largs)

    def close_settings(self, *largs):
        self.settings_open = False
        super().close_settings(*largs)

    def hook_keyboard(self, window, scancode, *_):
        """This function receives keyboard events"""

        if self.settings_open:
            if scancode == 27:
                self.close_settings()
                return True
        else:
            del window
            current_screen = self.screen_manager.current_screen
            if scancode == 97:
                #a key
                current_screen.key('a')
            if scancode == 276:
                #left key
                current_screen.key('left')
            if scancode == 275:
                #right key
                current_screen.key('right')
            if scancode == 273:
                #up key
                current_screen.key('up')
            if scancode == 274:
                #down key
                current_screen.key('down')
            if scancode == 32:
                #space key
                current_screen.key('space')
            if scancode == 13:
                #enter key
                current_screen.key('enter')
            if scancode == 127 or scancode == 8:
                #delete and backspace key
                current_screen.key('delete')
            if scancode == 9:
                #tab key
                current_screen.key('tab')
            if scancode == 282:
                #f1 key
                current_screen.key('f1')
            if scancode == 283:
                #f2 key
                current_screen.key('f2')
            if scancode == 284:
                #f3 key
                current_screen.key('f3')
            if scancode == 285:
                #f4 key
                current_screen.key('f4')
            if scancode == 27:
                self.clear_drags()
                if Window.keyboard_height > 0:
                    Window.release_all_keyboards()
                    return True
                elif not self.screen_manager.current_screen:
                    return False
                #elif self.database_scanning:
                #    self.cancel_database_import()
                #    return True
                elif self.screen_manager.current_screen.dismiss_extra():
                    return True
                elif self.screen_manager.current_screen.has_popup():
                    self.screen_manager.current_screen.dismiss_popup()
                    return True
                elif self.screen_manager.current != 'database':
                    if self.screen_manager.current == 'photo':
                        self.show_album()
                    else:
                        self.show_database()
                    return True

    def setup_import_presets(self):
        """Reads the import presets from the config file and saves them to the app.imports variable."""

        self.imports = []
        filename = self.data_directory+os.path.sep+'imports.ini'
        if os.path.isfile(filename):
            try:
                configfile = ConfigParser(interpolation=None)
                configfile.read(filename)
                import_presets = configfile.sections()
                for preset in import_presets:
                    try:
                        import_preset = dict(configfile.items(preset))
                        import_title = import_preset['title']
                        import_to = local_path(import_preset['import_to'])
                        naming_method = import_preset['naming_method']
                        if not naming(naming_method, title=''):
                            naming_method = naming_method_default
                        delete_originals = to_bool(import_preset['delete_originals'])
                        single_folder = to_bool(import_preset['single_folder'])
                        if import_preset['import_from']:
                            import_from_folders = local_path(import_preset['import_from'])
                            import_from = import_from_folders.split('|')
                        else:
                            import_from = []
                        self.imports.append({
                            'title': import_title,
                            'import_to': import_to,
                            'naming_method': naming_method,
                            'delete_originals': delete_originals,
                            'single_folder': single_folder,
                            'import_from': import_from})
                    except:
                        pass
            except:
                pass

    def setup_export_presets(self):
        """Reads the export presets from the config file and saves them to the app.exports variable."""

        self.exports = []
        filename = self.data_directory+os.path.sep+'exports.ini'
        if os.path.isfile(filename):
            try:
                configfile = ConfigParser(interpolation=None)
                configfile.read(filename)
                export_presets = configfile.sections()
                for preset in export_presets:
                    try:
                        export_preset = dict(configfile.items(preset))
                        name = export_preset['name']
                        export = export_preset['export']
                        ftp_address = export_preset['ftp_address']
                        ftp_user = export_preset['ftp_user']
                        ftp_password = export_preset['ftp_password']
                        ftp_passive = to_bool(export_preset['ftp_passive'])
                        ftp_port = int(export_preset['ftp_port'])
                        export_folder = local_path(export_preset['export_folder'])
                        create_subfolder = to_bool(export_preset['create_subfolder'])
                        export_info = to_bool(export_preset['export_info'])
                        scale_image = to_bool(export_preset['scale_image'])
                        scale_size = int(export_preset['scale_size'])
                        scale_size_to = export_preset['scale_size_to']
                        jpeg_quality = int(export_preset['jpeg_quality'])
                        watermark = to_bool(export_preset['watermark'])
                        watermark_image = local_path(export_preset['watermark_image'])
                        watermark_opacity = int(export_preset['watermark_opacity'])
                        watermark_horizontal = int(export_preset['watermark_horizontal'])
                        watermark_vertical = int(export_preset['watermark_vertical'])
                        watermark_size = int(export_preset['watermark_size'])
                        if export_preset['ignore_tags']:
                            ignore_tags = export_preset['ignore_tags'].split('|')
                        else:
                            ignore_tags = []
                        export_videos = to_bool(export_preset['export_videos'])
                        self.exports.append({
                            'name': name,
                            'export': export,
                            'ftp_address': ftp_address,
                            'ftp_user': ftp_user,
                            'ftp_password': ftp_password,
                            'ftp_passive': ftp_passive,
                            'ftp_port': ftp_port,
                            'export_folder': export_folder,
                            'create_subfolder': create_subfolder,
                            'export_info': export_info,
                            'scale_image': scale_image,
                            'scale_size': scale_size,
                            'scale_size_to': scale_size_to,
                            'jpeg_quality': jpeg_quality,
                            'watermark': watermark,
                            'watermark_image': watermark_image,
                            'watermark_opacity': watermark_opacity,
                            'watermark_horizontal': watermark_horizontal,
                            'watermark_vertical': watermark_vertical,
                            'watermark_size': watermark_size,
                            'ignore_tags': ignore_tags,
                            'export_videos': export_videos})
                    except:
                        pass
            except:
                pass

    def export_preset_update(self, index, preset):
        """Updates a specific export preset, and saves all presets.
        Arguments:
            index: Index of preset to update.
            preset: Preset data, List containing.
        """

        self.exports[index] = preset
        self.export_preset_write()

    def export_preset_new(self):
        """Create a new blank export preset."""

        preset = {'export': 'folder', 'ftp_address': '', 'ftp_user': '', 'ftp_password': '', 'ftp_passive': True,
                  'ftp_port': 21, 'name': 'Export Preset '+str(len(self.exports)+1), 'export_folder': '',
                  'create_subfolder': True, 'export_info': True, 'scale_image': False, 'scale_size': 1000,
                  'scale_size_to': 'long', 'jpeg_quality': 90, 'watermark_image': '', 'watermark': False,
                  'watermark_opacity': 33, 'watermark_horizontal': 90, 'watermark_vertical': 10, 'watermark_size': 25,
                  'ignore_tags': [], 'export_videos': False}
        self.exports.append(preset)

    def export_preset_write(self):
        """Saves all export presets to the config file."""

        configfile = ConfigParser(interpolation=None)
        for index, preset in enumerate(self.exports):
            section = str(index)
            configfile.add_section(section)
            configfile.set(section, 'name', preset['name'])
            configfile.set(section, 'export', preset['export'])
            configfile.set(section, 'ftp_address', preset['ftp_address'])
            configfile.set(section, 'ftp_user', preset['ftp_user'])
            configfile.set(section, 'ftp_password', preset['ftp_password'])
            configfile.set(section, 'ftp_passive', str(preset['ftp_passive']))
            configfile.set(section, 'ftp_port', str(preset['ftp_port']))
            configfile.set(section, 'export_folder', agnostic_path(preset['export_folder']))
            configfile.set(section, 'create_subfolder', str(preset['create_subfolder']))
            configfile.set(section, 'export_info', str(preset['export_info']))
            configfile.set(section, 'scale_image', str(preset['scale_image']))
            configfile.set(section, 'scale_size', str(preset['scale_size']))
            configfile.set(section, 'scale_size_to', preset['scale_size_to'])
            configfile.set(section, 'jpeg_quality', str(preset['jpeg_quality']))
            configfile.set(section, 'watermark', str(preset['watermark']))
            configfile.set(section, 'watermark_image', agnostic_path(preset['watermark_image']))
            configfile.set(section, 'watermark_opacity', str(preset['watermark_opacity']))
            configfile.set(section, 'watermark_horizontal', str(preset['watermark_horizontal']))
            configfile.set(section, 'watermark_vertical', str(preset['watermark_vertical']))
            configfile.set(section, 'watermark_size', str(preset['watermark_size']))
            configfile.set(section, 'ignore_tags', '|'.join(preset['ignore_tags']))
            configfile.set(section, 'export_videos', str(preset['export_videos']))

        with open(self.data_directory+os.path.sep+'exports.ini', 'w') as config:
            configfile.write(config)

    def export_preset_remove(self, index):
        """Deletes an export preset of a specifc index."""

        try:
            del self.exports[index]
        except:
            return
        self.export_preset_write()

    def import_preset_remove(self, index):
        """Deletes an import preset of a specifc index."""

        try:
            del self.imports[index]
        except:
            return
        self.import_preset_write()

    def import_preset_update(self, index, preset):
        """Overwrite a specific import preset, and save presets.
        Arguments:
            index: Integer, index of the preset to overwrite.
            preset: Dictionary, the new preset settings.
        """

        self.imports[index] = preset
        self.import_preset_write()

    def import_preset_new(self):
        """Create a new import preset with the default settings."""

        preset = {'title': 'Import Preset '+str(len(self.imports)+1), 'import_to': '', 'naming_method': naming_method_default, 'delete_originals': False,
                  'single_folder': False, 'import_from': []}
        self.imports.append(preset)

    def import_preset_write(self):
        """Saves all import presets to the config file."""

        configfile = ConfigParser(interpolation=None)
        for index, preset in enumerate(self.imports):
            section = str(index)
            configfile.add_section(section)
            configfile.set(section, 'title', preset['title'])
            configfile.set(section, 'import_to', agnostic_path(preset['import_to']))
            configfile.set(section, 'naming_method', preset['naming_method'])
            configfile.set(section, 'delete_originals', str(preset['delete_originals']))
            configfile.set(section, 'single_folder', str(preset['single_folder']))
            import_from = agnostic_path('|'.join(preset['import_from']))
            configfile.set(section, 'import_from', import_from)

        with open(self.data_directory+os.path.sep+'imports.ini', 'w') as config:
            configfile.write(config)

    def database_backup(self):
        """Makes a copy of the photos, folders and imported databases to a backup directory"""
        database_directory = self.data_directory + os.path.sep + 'Databases'
        database_backup_dir = os.path.join(database_directory, 'backup')
        if not os.path.exists(database_backup_dir):
            os.makedirs(database_backup_dir)

        photos_db = os.path.join(database_directory, 'photos.db')
        photos_db_backup = os.path.join(database_backup_dir, 'photos.db')
        if os.path.exists(photos_db_backup):
            os.remove(photos_db_backup)
        if os.path.exists(photos_db):
            copyfile(photos_db, photos_db_backup)

        folders_db = os.path.join(database_directory, 'folders.db')
        folders_db_backup = os.path.join(database_backup_dir, 'folders.db')
        if os.path.exists(folders_db_backup):
            os.remove(folders_db_backup)
        if os.path.exists(folders_db):
            copyfile(folders_db, folders_db_backup)

        imported_db = os.path.join(database_directory, 'imported.db')
        imported_db_backup = os.path.join(database_backup_dir, 'imported.db')
        if os.path.exists(imported_db_backup):
            os.remove(imported_db_backup)
        if os.path.exists(imported_db):
            copyfile(imported_db, imported_db_backup)

    def show_database_restore(self):
        """Switch to the database restoring screen layout."""

        self.clear_drags()
        if 'database_restore' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.database_restore_screen)
        self.screen_manager.current = 'database_restore'

    def database_restore(self):
        """Attempts to restore the backup databases"""

        self.close_settings()
        if self.database_scanning:
            self.cancel_database_import()
            self.scanningthread.join()
        self.photos.close()
        self.photos.join()
        self.folders.close()
        self.folders.join()
        self.imported.close()
        self.imported.join()
        self.show_database_restore()

    def database_restore_process(self):
        database_directory = self.data_directory + os.path.sep + 'Databases'
        database_backup_dir = os.path.join(database_directory, 'backup')

        photos_db = os.path.join(database_directory, 'photos.db')
        photos_db_backup = os.path.join(database_backup_dir, 'photos.db')
        folders_db = os.path.join(database_directory, 'folders.db')
        folders_db_backup = os.path.join(database_backup_dir, 'folders.db')
        imported_db = os.path.join(database_directory, 'imported.db')
        imported_db_backup = os.path.join(database_backup_dir, 'imported.db')
        if not os.path.exists(database_backup_dir):
            return "Backup does not exist"
        files = [photos_db_backup, photos_db, folders_db_backup, folders_db, imported_db_backup, imported_db]
        for file in files:
            if not os.path.exists(file):
                return "Backup does not exist"
        try:
            os.remove(photos_db)
            copyfile(photos_db_backup, photos_db)
            os.remove(folders_db)
            copyfile(folders_db_backup, folders_db)
            os.remove(imported_db)
            copyfile(imported_db_backup, imported_db)
        except:
            return "Could not copy backups"
        return True

    def setup_database(self, restore=False):
        """Set up various databases, create if needed."""

        database_directory = self.data_directory+os.path.sep+'Databases'
        if not os.path.exists(database_directory):
            os.makedirs(database_directory)

        photos_db = os.path.join(database_directory, 'photos.db')
        self.photos = MultiThreadOK(photos_db)
        self.photos.execute('''CREATE TABLE IF NOT EXISTS photos(
                            FullPath text PRIMARY KEY,
                            Folder text,
                            DatabaseFolder text,
                            OriginalDate integer,
                            OriginalSize integer,
                            Rename text,
                            ImportDate integer,
                            ModifiedDate integer,
                            Tags text,
                            Edited integer,
                            OriginalFile text,
                            Owner text,
                            Export integer,
                            Orientation integer);''')

        folders_db = os.path.join(database_directory, 'folders.db')
        self.folders = MultiThreadOK(folders_db)
        self.folders.execute('''CREATE TABLE IF NOT EXISTS folders(
                             Path text PRIMARY KEY,
                             Title text,
                             Description text)''')

        if not restore:
            self.thumbnails = MultiThreadOK(os.path.join(database_directory, 'thumbnails.db'))
            self.thumbnails.execute('''CREATE TABLE IF NOT EXISTS thumbnails(
                                    FullPath text PRIMARY KEY,
                                    ModifiedDate integer,
                                    Thumbnail blob,
                                    Orientation integer);''')
            self.tempthumbnails = MultiThreadOK(':memory:')
            self.tempthumbnails.execute('''CREATE TABLE IF NOT EXISTS thumbnails(
                                        FullPath text PRIMARY KEY,
                                        ModifiedDate integer,
                                        Thumbnail blob,
                                        Orientation integer);''')

        imported_db = os.path.join(database_directory, 'imported.db')
        self.imported = MultiThreadOK(imported_db)
        self.imported.execute('''CREATE TABLE IF NOT EXISTS imported(
                              FullPath text PRIMARY KEY,
                              File text,
                              ModifiedDate integer);''')
        if not restore and self.config.getboolean("Settings", "backupdatabase"):
            self.database_backup()

    def album_load_all(self):
        """Scans the album directory, and tries to load all album .ini files into the app.albums variable."""

        self.albums = []
        album_directory = self.album_directory
        if not os.path.exists(album_directory):
            os.makedirs(album_directory)
        album_directory_contents = os.listdir(album_directory)
        for item in album_directory_contents:
            if os.path.splitext(item)[1] == '.ini':
                try:
                    configfile = ConfigParser(interpolation=None)
                    configfile.read(os.path.join(album_directory, item))
                    info = dict(configfile.items('info'))
                    album_name = info['name']
                    album_description = info['description']
                    elements = configfile.items('photos')
                    photos = []
                    for element in elements:
                        photo_path = local_path(element[1])
                        if self.database_exists(photo_path):
                            photos.append(photo_path)
                    self.albums.append({'name': album_name, 'description': album_description, 'file': item,
                                        'photos': photos})
                except:
                    pass

    def tags_load(self):
        """Scans the tags directory and loads saved tags into the app.tags variable."""

        self.tags = []
        tag_directory = self.tag_directory
        if not os.path.exists(tag_directory):
            os.makedirs(tag_directory)
        tag_directory_contents = os.listdir(tag_directory)
        for item in tag_directory_contents:
            filename, extension = os.path.splitext(item)
            if extension == '.tag':
                self.tags.append(filename)

    def tag_make(self, tag_name):
        """Create a new photo tag.
        Argument:
            tag_name: String, name of the tag to create.
        """

        tag_name = tag_name.lower().strip(' ')
        tag_filename = tag_name + '.tag'
        filename = os.path.join(self.tag_directory, tag_filename)
        if not os.path.isfile(filename) and tag_name != 'favorite':
            self.tags.append(tag_name)
            open(filename, 'a').close()

    def album_make(self, album_name, album_description=''):
        """Create a new album file.
        Arguments:
            album_name: String, name of the album.
            album_description: String, description of album, optional.
        """

        exists = False
        for album in self.albums:
            if album['name'].lower() == album_name.lower():
                exists = True
        if not exists:
            album_filename = album_name + '.ini'
            self.albums.append({'name': album_name, 'description': album_description, 'file': album_filename, 'photos': []})
            self.album_save(self.albums[-1])

    def album_delete(self, index):
        """Deletes an album.
        Argument:
            index: Integer, index of album to delete."""

        filename = os.path.join(self.album_directory, self.albums[index]['file'])
        if os.path.isfile(filename):
            os.remove(filename)
        album_name = self.albums[index]['name']
        del self.albums[index]
        self.message("Deleted the album '"+album_name+"'")

    def album_find(self, album_name):
        """Find an album with a given name.
        Argument:
            album_name: Album name to get.
        Returns: Integer, index of album or -1 if not found.
        """

        for index, album in enumerate(self.albums):
            if album['name'] == album_name:
                return index
        return -1

    def album_update_description(self, index, description):
        """Update the description field for a specific album.
        Arguments:
            index: Integer, index of album to update.
            description: String, new description text.
        """

        self.albums[index]['description'] = description
        self.album_save(self.albums[index])

    def album_save(self, album):
        """Saves an album data file.
        Argument:
            album: Dictionary containing album information:
                file: String, filename of the album (with extension)
                name: String, name of the album.
                description: String, description of the album.
                photos: List of Strings, each is a database-relative filepath to a photo in the album.
        """

        configfile = ConfigParser(interpolation=None)
        filename = os.path.join(self.album_directory, album['file'])
        configfile.add_section('info')
        configfile.set('info', 'name', album['name'])
        configfile.set('info', 'description', album['description'])
        configfile.add_section('photos')
        for index, photo in enumerate(album['photos']):
            configfile.set('photos', str(index), agnostic_path(photo))
        with open(filename, 'w') as config:
            configfile.write(config)

    def album_add_photo(self, index, photo):
        """Add a photo to an album.
        Arguments:
            index: Integer, index of the album to update.
            photo: String, database-relative path to the new photo.
        """

        self.albums[index]['photos'].append(photo)
        self.album_save(self.albums[index])

    def album_remove_photo(self, index, fullpath, message=False):
        """Find and remove a photo from an album.
        Arguments:
            index: Integer, index of the album to update.
            fullpath: String, database-relative path to the photo to remove.
        """

        album = self.albums[index]
        photos = album['photos']
        if fullpath in photos:
            photos.remove(fullpath)
            self.album_save(album)
            if message:
                self.message("Removed photo from the album '"+album['name']+"'")

    def left_panel_width(self):
        """Returns the saved width for the left panel.
        Returns: Width of the panel in pixels.
        """

        minpanelsize = (self.button_scale / 2)
        leftpanel = float(self.config.get('Settings', 'leftpanel'))
        leftpanelsize = (leftpanel * Window.width)
        maxwidth = Window.width * 0.4
        if leftpanelsize > minpanelsize and leftpanelsize < maxwidth:
            panelwidth = leftpanelsize
        elif leftpanelsize >= maxwidth:
            panelwidth = maxwidth
        else:
            panelwidth = minpanelsize
        panelwidth = int(panelwidth)
        return panelwidth

    def right_panel_width(self):
        """Returns the saved width for the right panel.
        Returns: Width of the panel in pixels.
        """

        minpanelsize = (self.button_scale / 2)
        rightpanel = float(self.config.get('Settings', 'rightpanel'))
        rightpanelsize = (rightpanel * Window.width)
        maxwidth = Window.width * 0.4
        if rightpanelsize >= minpanelsize and rightpanelsize <= maxwidth:
            return rightpanelsize
        if rightpanelsize >= maxwidth:
            return maxwidth
        else:
            return minpanelsize

    def get_application_config(self, **kwargs):
        if platform == 'win':
            self.data_directory = os.getenv('APPDATA') + os.path.sep + "Snu Photo Manager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'linux':
            self.data_directory = os.path.expanduser('~') + os.path.sep + ".snuphotomanager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'macosx':
            self.data_directory = os.path.expanduser('~') + os.path.sep + ".snuphotomanager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'android':
            self.data_directory = self.user_data_dir
        else:
            self.data_directory = os.path.sep
        self.app_location = os.path.realpath(self.directory)
        # __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        #__location__ = os.path.realpath(sys.path[0])
        #if __location__.endswith('.zip'):
        #    __location__ = os.path.dirname(__location__)
        config_file = os.path.realpath(os.path.join(self.data_directory, "snuphotomanager.ini"))
        print("Config File: "+config_file)
        return config_file

    def load_encoding_presets(self):
        """Loads the video encoding presets from the 'encoding_presets.ini' file."""

        try:
            configfile = ConfigParser(interpolation=None)
            configfile.read(os.path.join(self.app_location, 'data/encoding_presets.ini'))
            preset_names = configfile.sections()
            for preset_name in preset_names:
                try:
                    preset = {'name': preset_name,
                              'file_format': configfile.get(preset_name, 'file_format'),
                              'video_codec': configfile.get(preset_name, 'video_codec'),
                              'audio_codec': configfile.get(preset_name, 'audio_codec'),
                              'resize': to_bool(configfile.get(preset_name, 'resize')),
                              'width': configfile.get(preset_name, 'width'),
                              'height': configfile.get(preset_name, 'height'),
                              'video_bitrate': configfile.get(preset_name, 'video_bitrate'),
                              'audio_bitrate': configfile.get(preset_name, 'audio_bitrate'),
                              'encoding_speed': configfile.get(preset_name, 'encoding_speed'),
                              'deinterlace': to_bool(configfile.get(preset_name, 'deinterlace')),
                              'command_line': configfile.get(preset_name, 'command_line')}
                    self.encoding_presets.append(preset)
                except:
                    pass
        except:
            pass
        try:
            self.selected_encoder_preset = self.config.get("Presets", "selected_preset")
        except:
            self.selected_encoder_preset = self.encoding_presets[0]['name']

    def save_encoding_preset(self):
        self.config.set("Presets", "selected_preset", self.selected_encoder_preset)

    def rescale_interface(self, *_, force=False):
        if self.last_width == 0:
            first_change = True
        else:
            first_change = False
        if Window.width != self.last_width or force:
            self.popup_x = int(Window.width * .75)
            self.last_width = Window.width
            if first_change and desktop:
                return
            if desktop:
                button_multiplier = 1
            else:
                button_multiplier = 2
            self.button_scale = int((Window.height / interface_multiplier) * int(self.config.get("Settings", "buttonsize")) / 100) * button_multiplier
            self.text_scale = int((self.button_scale / 3) * int(self.config.get("Settings", "textsize")) / 100)
            #self.leftpanel_width = self.left_panel_width()
            #self.rightpanel_width = self.right_panel_width()
            Clock.schedule_once(self.show_database)

    def build(self):
        """Called when the app starts.  Load and set up all variables, data, and screens."""

        if int(self.config.get("Settings", "buttonsize")) < 50:
            self.config.set("Settings", "buttonsize", 50)
        if int(self.config.get("Settings", "textsize")) < 50:
            self.config.set("Settings", "textsize", 50)
        if int(self.config.get("Settings", "thumbsize")) < 100:
            self.config.set("Settings", "thumbsize", 100)

        self.simple_interface = to_bool(self.config.get("Settings", "simpleinterface"))
        #Load data
        self.tag_directory = os.path.join(self.data_directory, 'Tags')
        self.album_directory = os.path.join(self.data_directory, 'Albums')
        about_file = open(os.path.join(self.app_location, 'about.txt'), 'r')
        self.about_text = about_file.read()
        about_file.close()
        self.program_import()  #Load external program presets
        self.setup_import_presets()  #Load import presets
        self.setup_export_presets()  #Load export presets
        self.tags_load()  #Load tags
        self.setup_database()  #Import or set up databases
        self.album_load_all()  #Load albums
        self.load_encoding_presets()
        self.set_single_database()

        #Set up widgets
        self.main_layout = FloatLayout()
        self.drag_image = PhotoDrag()
        self.drag_treenode = TreenodeDrag()

        #Set up screens
        self.screen_manager = ScreenManager()
        self.screen_manager.transition = SlideTransition()
        self.main_layout.add_widget(self.screen_manager)
        viewtype = 'None'
        viewtarget = ''
        viewdisplayable = False
        if self.config.getboolean("Settings", "rememberview"):
            config_viewtype = self.config.get("Settings", "viewtype")
            if config_viewtype:
                viewtype = config_viewtype
                viewtarget = self.config.get("Settings", "viewtarget")
                viewdisplayable = to_bool(self.config.get("Settings", "viewdisplayable"))
        self.database_screen = DatabaseScreen(name='database', type=viewtype, selected=viewtarget, displayable=viewdisplayable)
        #self.screen_manager.add_widget(self.database_screen)
        self.importing_screen = ImportingScreen(name='importing')
        #self.screen_manager.add_widget(self.importing_screen)
        self.database_restore_screen = DatabaseRestoreScreen(name='database_restore')

        #Set up keyboard catchers
        Window.bind(on_key_down=self.key_down)
        Window.bind(on_key_up=self.key_up)

        return self.main_layout

    def key_down(self, key, scancode=None, *_):
        """Intercepts various key presses and sends commands to the current screen."""
        del key
        if scancode == 303 or scancode == 304:
            #shift keys
            self.shift_pressed = True

    def key_up(self, key, scancode=None, *_):
        """Checks for the shift key released."""

        del key
        if scancode == 303 or scancode == 304:
            self.shift_pressed = False

    def remove_tag(self, tag):
        """Deletes a tag.
        Argument:
            tag: String, the tag to be deleted."""

        tag = tag.lower()
        tag_file = os.path.join(self.tag_directory, tag+'.tag')
        if os.path.isfile(tag_file):
            os.remove(tag_file)
        if tag in self.tags:
            self.tags.remove(tag)
        self.message("Deleted the tag '"+tag+"'")

    def delete_photo(self, fullpath, filename, message=False):
        """Deletes a photo file, and removes it from the database.
        Arguments:
            fullpath: String, database identifier for the photo to delete.
            filename: Full path to the photo to delete.
        """

        photoinfo = self.database_exists(fullpath)
        if os.path.isfile(filename):
            deleted = self.delete_file(filename)
        else:
            deleted = True
        if deleted:
            if os.path.isfile(photoinfo[10]):
                self.delete_file(photoinfo[10])
            fullpath = agnostic_path(fullpath)
            self.photos.execute('DELETE FROM photos WHERE FullPath = ?', (fullpath,))
            self.thumbnails.execute('DELETE FROM thumbnails WHERE FullPath = ?', (fullpath,))
            if message:
                self.message("Deleted the file '"+filename+"'")
            return True
        else:
            self.popup_message(text='Could not delete file', title='Warning')
            return False

    def delete_photo_original(self, photoinfo):
        """Delete the original edited file.
        Argument:
            photoinfo: List, photoinfo object.
        """

        original_file = local_path(photoinfo[10])
        if os.path.isfile(original_file):
            deleted = self.delete_file(original_file)
            if not deleted:
                self.popup_message(text='Could not delete original file', title='Warning')
        else:
            self.popup_message(text='Could not find original file', title='Warning')

    def delete_file(self, filepath):
        """Attempt to delete a file using send2trash.
        Returns:
            True if file was deleted
            False if file could not be deleted
        """

        try:
            send2trash(filepath)
            #os.remove(filepath)
        except:
            return False
        return True

    def database_remove_tag(self, fullpath, tag, message=False):
        """Remove a tag from a photo.
        Arguments:
            fullpath: String, the database-relative path to the photo.
            tag: String, the tag to remove.
        """

        tag = tag.lower()
        fullpath = agnostic_path(fullpath)
        info = self.photos.select('SELECT * FROM photos WHERE FullPath = ?', (fullpath, ))
        info = list(info)
        if info:
            info = list(info[0])
            current_tags = info[8].split(',')
            if tag in current_tags:
                current_tags.remove(tag)
                new_tags = ",".join(current_tags)
                info[8] = new_tags
                self.database_item_update(info)
                self.update_photoinfo(folders=info[1])
                if message:
                    self.message("Removed tag '"+tag+"' from the photo.")

    def database_toggle_tag(self, fullpath, tag):
        """Toggles a tag on a photo.  Used for enabling/disabling the 'favorite' tag.
        Arguments:
            fullpath: String, the database-relative path to the photo.
            tag: String, the tag to be toggled.
        """

        tag = tag.lower().strip(' ')
        fullpath = agnostic_path(fullpath)
        info = self.photos.select('SELECT * FROM photos WHERE FullPath = ?', (fullpath, ))
        info = list(info)
        if info:
            info = list(info[0])
            tags_unformatted = info[8].strip(' ')
            original_tags = tags_unformatted.split(',')
            if tag in original_tags:
                original_tags.remove(tag)
            else:
                original_tags.append(tag)
            new_tags = ",".join(original_tags)
            info[8] = new_tags
            self.database_item_update(info)
            self.update_photoinfo(folders=info[1])

    def database_add_tag(self, fullpath, tag):
        """Adds a tag to a photo.
        Arguments:
            fullpath: String, the database-relative path to the photo.
            tag: String, the tag to be added.
        """

        tag = tag.lower().strip(' ')
        fullpath = agnostic_path(fullpath)
        info = self.photos.select('SELECT * FROM photos WHERE FullPath = ?', (fullpath, ))
        info = list(info)
        if info:
            info = list(info[0])
            original_tags = info[8].split(',')
            current_tags = []
            update = False
            for original in original_tags:
                if original.strip(' '):
                    current_tags.append(original)
                else:
                    update = True
            if tag not in current_tags:
                current_tags.append(tag)
                update = True
            if update:
                new_tags = ",".join(current_tags)
                info[8] = new_tags
                self.database_item_update(info)
                self.update_photoinfo(folders=info[1])
                return True
        return False

    def database_get_tag(self, tag):
        """Gets all photos that have a tag applied to them.
        Argument:
            tag: String, the tag to search for.
        Returns:
            List of photoinfo Lists.
        """

        tag = tag.lower()
        match = '%'+tag+'%'
        photos = list(self.photos.select('SELECT * FROM photos WHERE Tags LIKE ?', (match, )))
        checked_photos = []
        for photo in photos:
            tags = photo[8].split(',')
            if tag in tags:
                checked_photos.append(photo)
        return local_paths(checked_photos)

    def move_files(self, photo_paths, move_to):
        """Move files from one folder to another.  Will keep files in the same database-relative path as they are in.
        Arguments:
            photo_paths: List of Strings, a database-relative path to each file being moved.
            move_to: String, a database-relative path to the folder the files should be moved to.
        """

        update_folders = []
        moved = 0
        for fullpath in photo_paths:
            photo_info = self.database_exists(fullpath)
            if photo_info:
                new_path = os.path.join(photo_info[2], move_to)
                try:
                    if not os.path.isdir(new_path):
                        os.makedirs(new_path)
                except:
                    self.popup_message(text='Error: Could Not Create Folder', title='Error')
                    break
                photo_path = os.path.join(photo_info[2], photo_info[0])
                current_folder, current_file = os.path.split(photo_path)
                new_photo_path = os.path.join(new_path, current_file)
                new_fullpath = os.path.join(move_to, current_file)
                backup_path = photo_info[10]
                if os.path.exists(backup_path):
                    new_backup_path = os.path.join(new_path, '.originals')
                    new_backup_file = os.path.join(new_backup_path, current_file)
                    try:
                        os.makedirs(new_backup_path)
                        os.rename(backup_path, new_backup_file)
                    except:
                        self.popup_message(text='Error: Could Not Move Backup File', title='Error')
                        break
                    if not os.path.exists(new_backup_file):
                        self.popup_message(text='Error: Could Not Move Backup File', title='Error')
                        break
                    photo_info[10] = new_backup_file
                if os.path.exists(photo_path):
                    try:
                        os.rename(photo_path, new_photo_path)
                    except:
                        self.popup_message(text='Error: Could Not Move File', title='Error')
                        break
                    if not os.path.exists(new_photo_path):
                        self.popup_message(text='Error: Could Not Move File', title='Error')
                        break

                    self.database_item_update(photo_info)
                    self.database_item_rename(fullpath, new_fullpath, move_to)
                    update_folders.append(photo_info[1])
                moved = moved + 1
        if moved:
            self.message("Moved "+str(moved)+" files.")
        update_folders.append(move_to)
        self.update_photoinfo(folders=update_folders)

    def move_folder(self, folder, move_to, rename=False):
        """Move a folder and all files in it to another location.  Also updates database entries.
        Arguments:
            folder: String, the path of the folder to move.
            move_to: String, the path to place the folder inside of.
            rename: Set to a String to rename the folder while it is moved.  Defaults to False.
        """

        error_message = ''
        databases = self.get_database_directories()
        for database in databases:
            move_from_folder = os.path.join(database, folder)
            move_to_folder = os.path.join(database, move_to)
            try:
                if rename:
                    moving_folder = rename
                else:
                    moving_folder = os.path.split(folder)[1]
                if not os.path.isdir(os.path.join(move_to_folder, moving_folder)):
                    if os.path.isdir(move_from_folder):
                        folders = []
                        folders.append('')
                        found_folders = list_folders(move_from_folder)
                        for found_folder in found_folders:
                            folders.append(os.path.join(found_folder))
                        if rename:
                            move(move_from_folder, os.path.join(move_to_folder, rename))
                        else:
                            move(move_from_folder, move_to_folder)
                        #Update database entries of all photos in folder
                        update_folders = []
                        for path in folders:
                            if path:
                                new_folder = os.path.join(os.path.join(move_to, moving_folder), path)
                                photo_path = os.path.join(folder, path)
                            else:
                                new_folder = os.path.join(move_to, moving_folder)
                                photo_path = folder
                            self.database_folder_rename(photo_path, new_folder)
                            photos = self.database_get_folder(photo_path)
                            update_folders.append(photo_path)
                            for photo in photos:
                                if photo[2] == database:
                                    filename = os.path.basename(photo[0])
                                    new_fullpath = os.path.join(new_folder, filename)
                                    self.database_item_rename(photo[0], new_fullpath, new_folder, dontcommit=True)
                        #self.update_photoinfo(folders=update_folders)
                else:
                    raise ValueError
            except Exception as e:
                if rename:
                    error_message = 'Unable To Rename Folder, '+str(e)
                else:
                    error_message = 'Unable To Move Folder, '+str(e)
                self.popup_message(text=error_message, title='Error:')
        if not error_message:
            if rename:
                self.message("Renamed the folder '"+folder+"' to '"+rename+"'")
            else:
                if not move_to:
                    self.message("Moved the folder '" + folder + "' into Root")
                else:
                    self.message("Moved the folder '"+folder+"' into '"+move_to+"'")
        self.photos.commit()
        self.thumbnails.commit()

    def rename_folder(self, old_folder_path, new_name):
        """Rename a folder in place.  Uses the self.move_folder function.
        Arguments:
            old_folder_path: String, path of the folder to rename.
            new_name: String, new name for the folder.
        """

        folder_path, old_name = os.path.split(old_folder_path)
        self.move_folder(old_folder_path, folder_path, rename=new_name)

    def add_folder(self, folder):
        """Attempts to create a new folder in every database directory.
        Argument:
            folder: String, the folder path to create.  Must be database-relative.
        """

        databases = self.get_database_directories()
        created = False
        for database in databases:
            try:
                if not os.path.isdir(os.path.join(database, folder)):
                    os.makedirs(os.path.join(database, folder))
                    created = True
                self.database_folder_add([folder, '', ''])
            except:
                pass
        if created:
            self.message("Created the folder '"+folder+"'")

    def delete_folder(self, folder):
        """Delete a folder and all photos within it.  Removes the contained photos from the database as well.
        Argument:
            folder: String, the folder to be deleted.  Must be a database-relative path.
        """

        folders = []
        update_folders = []
        databases = self.get_database_directories()

        deleted_photos = 0
        deleted_folders = 0

        #Detect all folders to delete
        for database in databases:
            full_folder = os.path.join(database, folder)
            if os.path.isdir(full_folder):
                folders.append([database, folder])
            found_folders = list_folders(full_folder)
            for found_folder in found_folders:
                folders.append([database, os.path.join(folder, found_folder)])

        #Delete photos from folders
        for found_path in folders:
            database, folder_name = found_path
            photos = self.database_get_folder(folder_name)
            if photos:
                update_folders.append(folder_name)
            for photo in photos:
                photo_path = os.path.join(photo[2], photo[0])
                deleted = self.delete_photo(photo[0], photo_path)
                if not deleted:
                    break
                deleted_photos = deleted_photos + 1

        #Delete folders
        for found_path in folders:
            database, folder_name = found_path
            full_found_path = os.path.join(database, folder_name)
            try:
                rmtree(full_found_path)
                deleted_folders = deleted_folders + 1
            except:
                pass
            folder_name = agnostic_path(folder_name)
            self.folders.execute('DELETE FROM folders WHERE Path = ?', (folder_name, ))

        if deleted_photos or deleted_folders:
            self.message("Deleted "+str(deleted_photos)+" photos and "+str(deleted_folders)+" folders.")

        self.folders.commit()
        self.photos.commit()

    def database_folder_rename(self, folder, newfolder):
        """Rename a folder in the folders database.  Does not modify the actual folder.
        Arguments:
            folder: String, path of the folder to rename.
            newfolder: String, path of the new folder name..
        """

        folder = agnostic_path(folder)
        newfolder = agnostic_path(newfolder)
        folders = list(self.folders.select("SELECT * FROM folders WHERE Path = ?", (newfolder, )))
        if folders:
            #renamed folder already exists in database
            self.folders.execute("DELETE FROM folders WHERE Path = ?", (folder, ))
        else:
            self.folders.execute("UPDATE folders SET Path = ? WHERE Path = ?", (newfolder, folder, ))
        self.folders.commit()

    def database_get_folder(self, folder, database=False):
        """Get photos in a folder.
        Argument:
            folder: String, database-relative folder name to get.
        Returns: List of photoinfo Lists.
        """

        folder = agnostic_path(folder)
        if database:
            database = agnostic_path(database)
            photos = list(self.photos.select('SELECT * FROM photos WHERE Folder = ? AND DatabaseFolder = ?', (folder, database, )))
        else:
            photos = list(self.photos.select('SELECT * FROM photos WHERE Folder = ?', (folder, )))
        return local_paths(photos)

    def database_get_folders(self, database_folder=False, quick=False):
        """Get all folders from the photo database.
        Returns: List of folder database-relative paths.
        """

        folders = []
        if database_folder:
            database_folder = agnostic_path(database_folder)
            folder_items = list(self.photos.select('SELECT Folder FROM photos WHERE DatabaseFolder = ? GROUP BY Folder',
                                                   (database_folder, )))
            for item in folder_items:
                folders.append(local_path(item[0]))
        else:
            if quick:
                folder_items = list(self.folders.select('SELECT Path FROM folders'))
                for item in folder_items:
                    folders.append(local_path(item[0]))
            else:
                folder_items = list(self.photos.select('SELECT Folder FROM photos GROUP BY Folder'))
                for item in folder_items:
                    folders.append(local_path(item[0]))

                directories = self.config.get('Database Directories', 'paths')
                directories = local_path(directories)
                databases = directories.split(';')
                real_folders = []
                for database in databases:
                    real_folders = real_folders + list_folders(database)
                for folder in real_folders:
                    if folder not in folders:
                        folders.append(folder)

        return folders

    def database_add(self, fileinfo):
        """Add a new photo to the database.
        Argument:
            fileinfo: List, a photoinfo object.
        """

        fileinfo = agnostic_photoinfo(fileinfo)
        #adds a photo to the photo database
        self.photos.execute("insert into photos values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (fileinfo[0], fileinfo[1], fileinfo[2], fileinfo[3], fileinfo[4], fileinfo[5],
                             fileinfo[6], fileinfo[7], fileinfo[8], fileinfo[9], fileinfo[10], fileinfo[11],
                             fileinfo[12], fileinfo[13]))

    def database_exists(self, fullpath):
        """Get photo data if it is in the photo database.
        Argument:
            fullpath: String, database-relative path to the photo.
        Returns: 
            List of photoinfo if photo found, None if not found.
        """

        fullpath = agnostic_path(fullpath)
        photo = self.photos.select('SELECT * FROM photos WHERE FullPath = ?', (fullpath,))
        photo = list(photo)
        if photo:
            photo = local_photoinfo(list(photo[0]))
        return photo

    def database_imported_exists(self, fullpath):
        """Get photo data if it is in the imported database.
        Argument:
            fullpath: String, database-relative path to the photo.
        Returns: 
            List of photoinfo if photo found, None if not found.
        """

        fullpath = agnostic_path(fullpath)
        photo = self.imported.select('SELECT * FROM imported WHERE FullPath = ?', (fullpath, ))
        photo = list(photo)
        if photo:
            photo = list(photo[0])
            photo[0] = local_path(photo[0])
        return photo

    def database_imported_add(self, fullpath, file_path, modified_date):
        """Add photo info to the imported files database.
        Arguments:
            fullpath: String, the database-relative path to the file.
            file_path: String, the file's absolute path.
            modified_date: Integer, the file's modified date.
        """

        exists = self.database_imported_exists(fullpath)
        if not exists:
            fullpath = agnostic_path(fullpath)
            self.imported.execute("insert into imported values(?, ?, ?)", (fullpath, file_path, modified_date))

    def database_imported_remove(self, fullpath):
        """Removes a photo from the imported database.
        Argument:
            fullpath: String, the database-relative path to the photo.
        """

        fullpath = agnostic_path(fullpath)
        self.imported.execute('DELETE FROM imported WHERE FullPath = ?', (fullpath, ))

    def null_image(self):
        """Returns a minimum photoinfo list pointing to 'null.jpg'.
        Returns: List, a photoinfo object.
        """

        return ['data/null.jpg', '', '', 0, 0, 'data/null.jpg', 0, 0, '', 0, 'data/null.jpg', '', 0, 1]

    def database_clean(self, deep=False):
        """Clean the databases of redundant or missing data.
        Argument:
            deep: Boolean. If True, will remove all files that are currently not found.
        """

        databases = self.get_database_directories()

        #remove referenced files if the database that contained them is no longer loaded
        found_databases = list(self.photos.select('SELECT DatabaseFolder FROM photos GROUP BY DatabaseFolder'))
        for database in found_databases:
            if local_path(database[0]) not in databases:
                self.photos.execute('DELETE FROM photos WHERE DatabaseFolder = ?', (database[0], ))

        #remove references if the photos are not found
        for database in databases:
            if os.path.isdir(database) or deep:
                database_renamed = agnostic_path(database)
                photos = list(self.photos.select('SELECT * FROM photos WHERE DatabaseFolder = ?', (database_renamed, )))
                for photo in photos:
                    photo_file = os.path.join(local_path(photo[2]), local_path(photo[0]))
                    if not isfile2(photo_file):
                        self.database_item_delete(photo[0])

        #remove folder references if the folder is not in any database folder
        folders = list(self.folders.select('SELECT * FROM folders'))
        for folder in folders:
            folder_renamed = local_path(folder[0])
            check = len(databases)
            for database in databases:
                if os.path.isdir(database) or deep:
                    full_folder = os.path.join(database, folder_renamed)
                    if not os.path.isdir(full_folder):
                        check = check - 1
            if check == 0:
                self.folders.execute('DELETE FROM folders WHERE Path = ?', (folder[0], ))

        Clock.schedule_once(lambda *dt: self.screen_manager.current_screen.on_enter())

    def database_item_delete(self, fullpath):
        self.photos.execute('DELETE FROM photos WHERE FullPath = ?', (fullpath,))
        self.thumbnails.execute('DELETE FROM thumbnails WHERE FullPath = ?', (fullpath,))

    def database_rescan(self):
        """Calls database_import and updates the treeview on the database screen."""

        self.database_import()

    def database_thumbnail_get(self, fullpath, temporary=False):
        """Gets a thumbnail image from the thumbnails database.
        Arguments:
            fullpath: String, the database-relative path of the photo to get the thumbnail of.
            temporary: Boolean, set to True to get a thumbnail from the temporary thumbnail database.
        Returns: List containing thumbnail information and data, or None if not found.
        """

        fullpath = agnostic_path(fullpath)
        if temporary:
            thumbnail = self.tempthumbnails.select('SELECT * FROM thumbnails WHERE FullPath = ?', (fullpath,))
        else:
            thumbnail = self.thumbnails.select('SELECT * FROM thumbnails WHERE FullPath = ?', (fullpath,))
        thumbnail = list(thumbnail)
        if thumbnail:
            thumbnail = local_thumbnail(list(thumbnail[0]))
        return thumbnail

    def database_thumbnail_write(self, fullpath, modified_date, thumbnail, orientation, temporary=False):
        """Save or updates a thumbnail to the thumbnail database.
        Arguments:
            fullpath: String, database-relative path to the photo.
            modified_date: Integer, the modified date of the original photo file.
            thumbnail: Thumbnail image data.
            orientation: Integer, EXIF orientation code.
            temporary: Boolean, if True, save to the temporary thumbnails database.
        """

        fullpath = agnostic_path(fullpath)
        if temporary:
            thumbs = self.tempthumbnails
            matches = self.tempthumbnails.select('SELECT * FROM thumbnails WHERE FullPath = ?', (fullpath,))
        else:
            thumbs = self.thumbnails
            matches = self.thumbnails.select('SELECT * FROM thumbnails WHERE FullPath = ?', (fullpath,))

        #Check if thumbnail is already in database.
        matches = list(matches)
        if not matches:
            #No thumbnail, create a new database entry
            thumbs.execute("insert into thumbnails values(?, ?, ?, ?)",
                           (fullpath, modified_date, thumbnail, orientation))
        else:
            #Thumbnail exist already, just update it
            thumbs.execute("UPDATE thumbnails SET ModifiedDate = ?, Thumbnail = ?, Orientation = ? WHERE FullPath = ?",
                           (modified_date, thumbnail, orientation, fullpath, ))

    def database_thumbnail_update(self, fullpath, database, modified_date, orientation, temporary=False, force=False):
        """Check if a thumbnail is already in database, check if out of date, update if needed.
        Arguments:
            fullpath: String, the database-relative path to the photo.
            database: String, database directory the photo is in.
            modified_date: Integer, the modified date of the original photo.
            orientation: Integer, EXIF orientation code.
            temporary: Boolean, if True, uses the temporary thumbnails database.
            force: Boolean, if True, will always update thumbnail, regardless of modified date.
        Returns: Boolean, True if thumbnail updated, False if not.
        """

        #check if thumbnail is already in database, check if out of date, update if needed
        matches = self.database_thumbnail_get(fullpath, temporary=temporary)
        if matches:
            if modified_date <= matches[1] and not force:
                return False
        thumbnail = generate_thumbnail(local_path(fullpath), local_path(database))
        thumbnail = sqlite3.Binary(thumbnail)
        self.database_thumbnail_write(fullpath=fullpath, modified_date=modified_date, thumbnail=thumbnail,
                                      orientation=orientation, temporary=temporary)
        return True

    def database_item_rename(self, fullpath, newname, newfolder, dontcommit=False):
        """Changes the database-relative path of a photo to another path.
        Updates both photos and thumbnails databases.
        Arguments:
            fullpath: String, the original database-relative path.
            newname: String, the new database-relative path.
            newfolder: String, new database-relative containing folder for the file.
        """

        fullpath = agnostic_path(fullpath)
        newname = agnostic_path(newname)
        if self.database_exists(newname):
            self.database_item_delete(newname)
        newfolder_rename = agnostic_path(newfolder)
        self.photos.execute("UPDATE photos SET FullPath = ?, Folder = ? WHERE FullPath = ?",
                            (newname, newfolder_rename, fullpath, ))
        if not dontcommit:
            self.photos.commit()
        self.thumbnails.execute("UPDATE thumbnails SET FullPath = ? WHERE FullPath = ?",
                                (newname, fullpath, ))
        if not dontcommit:
            self.thumbnails.commit()

    def database_item_database_move(self, fileinfo):
        """Updates a photo's database folder.
        Argument:
            fileinfo: list, a photoinfo object.
        """

        fileinfo = agnostic_photoinfo(fileinfo)
        self.photos.execute("UPDATE photos SET DatabaseFolder = ? WHERE FullPath = ?", (fileinfo[2], fileinfo[0]))

    def database_item_update(self, fileinfo):
        """Updates a photo's database entry with new info.
        Argument:
            fileinfo: List, a photoinfo object.
        """

        fileinfo = agnostic_photoinfo(fileinfo)
        self.photos.execute("UPDATE photos SET Rename = ?, ModifiedDate = ?, Tags = ?, Edited = ?, OriginalFile= ?, Owner = ?, Export = ?, Orientation = ? WHERE FullPath = ?",
                            (fileinfo[5], fileinfo[7], fileinfo[8], fileinfo[9], fileinfo[10], fileinfo[11],
                             fileinfo[12], fileinfo[13], fileinfo[0]))
        self.photos.commit()

    def cancel_database_import(self, *_):
        """Signals the database scanning thread to stop."""

        self.cancel_scanning = True

    def database_import(self):
        """Begins the database scanning process.
        Scans the database folders for new files and adds them.
        Open the popup progress dialog, and start the scanning thread.
        """

        if self.database_scanning:
            return
        self.cancel_scanning = False
        self.scanningthread = threading.Thread(target=self.database_import_files)
        self.scanningthread.start()

    def get_database_directories(self):
        """Gets the current database directories.
        Returns: List of Strings of the paths to each database.
        """

        directories = self.config.get('Database Directories', 'paths')
        directories = local_path(directories)
        if directories:
            databases = directories.split(';')
        else:
            databases = []
        databases_cleaned = []
        for database in databases:
            if database:
                databases_cleaned.append(database)
        return databases_cleaned

    def list_files(self, folder):
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
            if self.cancel_scanning:
                return []
            if not firstroot:
                firstroot = root
            filefolder = os.path.relpath(root, firstroot)
            if filefolder == '.':
                filefolder = ''
            for file in files:
                if self.cancel_scanning:
                    return []
                file_list.append([os.path.join(filefolder, file), firstroot])
        return file_list

    def database_import_files(self):
        """Database scanning thread, checks for new files in the database directories and adds them to the database."""

        self.database_scanning = True
        self.database_update_text = 'Rescanning Database, Building Folder List'
        databases = self.get_database_directories()
        update_folders = []

        #Get the file list
        files = []
        for directory in databases:
            if self.cancel_scanning:
                break
            files = files + self.list_files(directory)

        total = len(files)
        self.database_update_text = 'Rescanning Database (5%)'
        #self.scanningpopup.scanning_percentage = 5
        #self.scanningpopup.scanning_text = "Scanning "+str(total)+" Files..."

        #Iterate all files, check if in database, add if needed.
        for index, file_info in enumerate(files):
            if self.cancel_scanning:
                break
            extension = os.path.splitext(file_info[0])[1].lower()
            if extension in imagetypes or extension in movietypes:
                exists = self.database_exists(file_info[0])
                if not exists:
                    #photo not in database, add it
                    fileinfo = get_file_info(file_info)
                    self.database_add(fileinfo)
                    update_folders.append(fileinfo[1])
                else:
                    #photo is already in the database
                    #check modified date to see if it needs to be updated and look for duplicates
                    refreshed = self.refresh_photo(file_info[0], no_photoinfo=True, data=exists)
                    if refreshed:
                        update_folders.append(refreshed[1])

            self.database_update_text = 'Rescanning Database ('+str(int(90*(float(index+1)/float(total))))+'%)'
            #self.scanningpopup.scanning_percentage = int(90*(float(index+1)/float(total)))
        self.photos.commit()

        #Update folders
        #self.scanningpopup.scanning_text = "Updating Folders..."
        folders = self.database_get_folders()
        for folder in folders:
            if self.cancel_scanning:
                break
            exists = self.database_folder_exists(folder)
            if not exists:
                folderinfo = get_folder_info(folder, databases)
                self.database_folder_add(folderinfo)
                update_folders.append(folderinfo[0])
        self.update_photoinfo(folders=folders)
        self.folders.commit()

        #Clean up database
        if not self.cancel_scanning:
            self.database_update_text = 'Cleaning Database...'
            #self.scanningpopup.scanning_text = "Cleaning Database..."
            self.database_clean()
            #self.scanningpopup.dismiss()
            self.database_update_text = "Database scanned "+str(total)+" files"

        self.update_photoinfo(folders=update_folders)
        if self.cancel_scanning:
            self.database_update_text = "Canceled database update."
            #self.scanningpopup.dismiss()
        self.database_scanning = False
        Clock.schedule_once(self.clear_database_update_text, 20)
        if self.screen_manager.current == 'database':
            self.database_screen.update_folders = True
            Clock.schedule_once(self.database_screen.update_treeview)

    def database_folder_exists(self, folder):
        """Get folder info from the folders database if it exists.
        Argument:
            folder: String, the database-relative path to the folder.
        Returns: List, folderinfo if found, None if not found.
        """

        folder = agnostic_path(folder)
        matches = self.folders.select('SELECT * FROM folders WHERE Path = ?', (folder,))
        matches = list(matches)
        if matches:
            matches = list(matches[0])
            matches[0] = local_path(matches[0])
        return matches

    def database_folder_add(self, folderinfo):
        """Adds a folder to the folders database.
        Argument:
            folderinfo: List, folderinfo object containing pth, title and description.
        """

        path, title, description = folderinfo
        renamed_path = agnostic_path(path)
        self.folders.execute("insert into folders values(?, ?, ?)", (renamed_path, title, description))

    def database_folder_update_title(self, path, title):
        """Updates the title of a folder in the folders database.
        Arguments: 
            path: String, database-relative path to the folder.
            title: String, the new folder title.
        """

        path = agnostic_path(path)
        self.folders.execute("UPDATE folders SET Title = ? WHERE Path = ?", (title, path, ))

    def database_folder_update_description(self, path, description):
        """Updates the description of a folder in the folders database.
        Arguments: 
            path: String, database-relative path to the folder.
            description: String, the new folder description.
        """

        path = agnostic_path(path)
        self.folders.execute("UPDATE folders SET Description = ? WHERE Path = ?", (description, path, ))

    def database_folder_update(self, folderinfo):
        """Updates a folder's database entry with new info.
        Argument:
            folderinfo: List, a folderinfo object.
        """

        path, title, description = folderinfo
        renamed_path = agnostic_path(path)
        self.folders.execute("UPDATE folders SET Title = ?, Description = ? WHERE Path = ?",
                             (title, description, renamed_path, ))

    def show_database(self, *_):
        """Switch to the database screen layout."""

        self.clear_drags()
        if 'database' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.database_screen)
        self.screen_manager.current = 'database'

    def show_album(self, button=None):
        """Switch to the album screen layout.
        Argument:
            button: Optional, the widget that called this function. Allows the function to get a specific album to view.
        """

        self.clear_drags()
        if 'album' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(AlbumScreen(name='album'))
        if button:
            if button.type != 'None':
                if not button.folder:
                    self.fullpath = ''
                    self.target = button.target
                    self.photo = ''
                    self.type = button.type
                    self.screen_manager.current = 'album'
                else:
                    self.fullpath = button.fullpath
                    self.target = button.target
                    self.photo = os.path.join(button.database_folder, button.fullpath)
                    self.type = button.type
                    self.screen_manager.current = 'album'
        else:
            self.screen_manager.current = 'album'

    def show_photo(self):
        """Switch to the fullscreen photo view screen layout."""

        self.clear_drags()
        if 'photo' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(PhotoScreen(name='photo'))
        self.screen_manager.current = 'photo'

    def show_import(self):
        """Switch to the import select screen layout."""

        self.clear_drags()
        if 'import' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(ImportScreen(name='import'))
        self.screen_manager.current = 'import'

    def show_importing(self):
        """Switch to the photo import screen layout."""

        self.clear_drags()
        if 'importing' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.importing_screen)
        self.screen_manager.current = 'importing'

    def show_export(self):
        """Switch to the photo export screen layout."""

        self.clear_drags()
        if 'export' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(ExportScreen(name='export'))
        self.screen_manager.current = 'export'

    def show_transfer(self):
        """Switches to the database transfer screen layout"""

        self.clear_drags()
        if 'transfer' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(TransferScreen(name='transfer'))
        self.screen_manager.current = 'transfer'

    def popup_message(self, text, title='Notification'):
        """Creates a simple 'ok' popup dialog.
        Arguments:
            text: String, text that the dialog will display
            title: String, the dialog window title.
        """

        app = App.get_running_app()
        content = MessagePopup(text=text)
        self.popup = NormalPopup(title=title, content=content, size_hint=(None, None),
                                 size=(app.popup_x, app.button_scale * 4))
        self.popup.open()

    def clear_drags(self):
        """Removes the drag-n-drop widgets."""

        self.main_layout.remove_widget(self.drag_treenode)
        self.main_layout.remove_widget(self.drag_image)

    def drag(self, drag_object, mode, position, image=None, offset=list([0, 0]), fullpath=''):
        """Updates the drag-n-drop widget for a standard photo.
        Arguments:
            drag_object: The widget that is being dragged.
            mode: String, what is being done with the drag: 'start', 'end' or 'move'.
            position: The position (x, y) the drag widget should be at in window coordinates.
            image: Needs to be provided if mode is 'start', the image the drag widget should have.
            offset: Needs to be provided if mode is 'start',
                    offset where the drag began, to make the image be placed in the correct location.
            fullpath: Needs to be provided if the mode is 'start',
                      String, the database-relative path of the image being dragged.
        """

        if mode == 'end':
            self.main_layout.remove_widget(self.drag_image)
            self.screen_manager.current_screen.drop_widget(self.drag_image.fullpath, position, dropped_type='file')

        elif mode == 'start':
            orientation = drag_object.photo_orientation
            if orientation == 3 or orientation == 4:
                angle = 180
            elif orientation == 5 or orientation == 6:
                angle = 270
            elif orientation == 7 or orientation == 8:
                angle = 90
            else:
                angle = 0

            self.drag_image.angle = angle
            self.drag_image.offset = offset
            self.main_layout.remove_widget(self.drag_image)
            self.drag_image.pos = (position[0]-offset[0], position[1]-offset[1])
            self.drag_image.texture = image.texture
            self.drag_image.fullpath = fullpath
            self.main_layout.add_widget(self.drag_image)

        else:  #mode == 'move'
            self.drag_image.pos = (position[0]-self.drag_image.offset[0], position[1]-self.drag_image.offset[1])

    def drag_treeview(self, drag_object, mode, position, offset=list([0, 0])):
        """Updates the drag-n-drop widget for a treeview folder.
        Arguments:
            drag_object: The widget that is being dragged.
            mode: String, what is being done with the drag: 'start', 'end' or 'move'.
            position: The position (x, y) the drag widget should be at in window coordinates.
            offset: Needs to be provided if mode is 'start',
                    offset where the drag began, to make the image be placed in the correct location.
        """

        if mode == 'end':
            self.main_layout.remove_widget(self.drag_treenode)
            self.screen_manager.current_screen.drop_widget(drag_object.fullpath, position, dropped_type=drag_object.droptype)

        elif mode == 'start':
            self.drag_treenode.offset = offset
            self.main_layout.remove_widget(self.drag_treenode)
            self.drag_treenode.text = drag_object.folder_name
            if drag_object.subtext:
                self.drag_treenode.height = int(self.button_scale * 1.5)
                self.drag_treenode.subtext = drag_object.subtext
                self.drag_treenode.ids['subtext'].height = int(self.button_scale * 0.5)
            else:
                self.drag_treenode.subtext = ''
                self.drag_treenode.ids['subtext'].height = 0
                self.drag_treenode.height = int(self.button_scale * 1)
            self.drag_treenode.width = drag_object.width
            self.drag_treenode.pos = (position[0]-offset[0], position[1]-offset[1])
            self.main_layout.add_widget(self.drag_treenode)

        else:
            self.drag_treenode.pos = (position[0]-self.drag_treenode.offset[0], position[1]-self.drag_treenode.offset[1])

    def test_description(self, string, *_):
        """Removes unallowed characters from an album/folder description.
        Argument:
            string: String, the description.
        """

        return "".join(i for i in string if i not in "#%&*{}\\/:?<>+|\"=][;")

    def test_album(self, string, *_):
        """Removes unallowed characters from an album name.
        Argument:
            string: String, the album name.
        """

        return "".join(i for i in string if i not in "#%&*{}\\/:?<>+|\"=][;")

    def test_tag(self, string, *_):
        """Checks a tag input string, removes non-allowed characters and sets to lower-case.
        Arguments:
            string: String to replace.
            undo: Not used, sent by the widget.
        Returns: A string.
        """

        return "".join(i for i in string if i not in "#%&*{}\\/:?<>+|\"=][;,").lower()

    def new_description(self, description_editor, root):
        """Update the description of a folder or album.
        Arguments:
            description_editor: Widget, the text input object that was edited.
            root: The screen that owns the text input widget.  Has information about the folder or album being edited.
        """

        if not description_editor.focus:
            folder = root.selected
            description = description_editor.text
            if root.type == 'Folder':
                self.database_folder_update_description(folder, description)
                self.folders.commit()
                self.update_photoinfo(folders=[folder])
            elif root.type == 'Album':
                index = self.album_find(folder)
                if index >= 0:
                    self.album_update_description(index, description)

    def new_title(self, title_editor, root):
        """Update the title of a folder or album.
        Arguments:
            title_editor: Widget, the text input object that was edited.
            root: The screen that owns the text input widget.  Has information about the folder or album being edited.
        """

        if not title_editor.focus:
            folder = root.selected
            title = title_editor.text
            if root.type == 'Folder':
                self.database_folder_update_title(folder, title)
                self.folders.commit()
                self.update_photoinfo(folders=[folder])
                root.update_treeview()

    def edit_add_watermark(self, imagedata, watermark_image, watermark_opacity, watermark_horizontal, watermark_vertical, watermark_size):
        """Adds a watermark overlay to an image

        imagedata - the image to apply the watermark to, a PIL image object
        watermark_image - a string with the watermark filepath
        watermark_opacity - a percentage (0-100) describing how opaque the watermark will be
        watermark_horizontal - a percentage (0-100) describing the horizontal position of the watermark,
            with 0 being all the way on the left side, 100 being all the way on the right side.  
            The watermark will never be partially off of the original image
        watermark_vertical - a percentage (0-100) describing the vertical position of the watermark
        watermark_size - a percentage (0-100) describing the size of the watermark as its horizontal size relates 
            to the original image - 50% will result in a watermark that is half the width of the original image.

        Returns a PIL image object
        """

        image_size = imagedata.size
        watermark = Image.open(watermark_image)
        watermark_size_pixels = watermark.size
        watermark_width, watermark_height = watermark_size_pixels
        watermark_ratio = watermark_width/watermark_height
        new_watermark_width = int(round(image_size[0]*(watermark_size/100)))
        new_watermark_height = int(round(new_watermark_width/watermark_ratio))
        watermark = watermark.resize((new_watermark_width, new_watermark_height), 3)
        watermark_x = int(round((image_size[0]-new_watermark_width)*(watermark_horizontal/100)))
        watermark_y = image_size[1] - new_watermark_height - int(round((image_size[1]-new_watermark_height)*(watermark_vertical/100)))
        if watermark.mode == 'RGBA':
            watermark_alpha = watermark.split()[3]
        else:
            watermark_alpha = watermark.convert('L')
        enhancer = ImageEnhance.Brightness(watermark_alpha)
        watermark_alpha = enhancer.enhance(watermark_opacity/100)
        imagedata.paste(watermark, (watermark_x, watermark_y), watermark_alpha)
        return imagedata

    def edit_fix_orientation(self, imagedata, orientation):
        """Rotates an image to the correct orientation
        
        imagedata - the image to apply the rotation to, a PIL image object
        orientation - jpeg exif orientation value
        
        Returns a PIL image object
        """

        if orientation in [2, 4, 5, 7]:
            mirror = True
        else:
            mirror = False
        if orientation == 3 or orientation == 4:
            angle = 180
            method = 3
        elif orientation == 5 or orientation == 6:
            angle = 270
            method = 4
        elif orientation == 7 or orientation == 8:
            angle = 90
            method = 2
        else:
            angle = 0
            method = False
        if angle:
            #imagedata = imagedata.rotate(angle)
            imagedata = imagedata.transpose(method=method)
        if mirror:
            imagedata = imagedata.transpose(method=0)
        return imagedata

    def edit_scale_image(self, imagedata, scale_size, scale_size_to):
        """Scales an image based on a side length while maintaining aspect ratio.
        
        imagedata - the image to apply the scaling to, a PIL image object
        scale_size - the target edge length in pixels
        scale_size_to - scaling mode, set to one of ('width', 'height', 'short', 'long')
            width - scales the image so the width matches scale_size
            height - scales the image so the height matches scale_size
            short - scales the image so the shorter side matches scale_size
            long - scales the image so the longer side matches scale_size
            
        Returns a PIL image object
        """

        original_size = imagedata.size
        ratio = original_size[0]/original_size[1]
        if scale_size_to == 'width':
            new_size = (scale_size, int(round(scale_size/ratio)))
        elif scale_size_to == 'height':
            new_size = (int(round(scale_size*ratio)), scale_size)
        elif scale_size_to == 'short':
            if original_size[0] > original_size[1]:
                new_size = (int(round(scale_size*ratio)), scale_size)
            else:
                new_size = (scale_size, int(round(scale_size/ratio)))
        else:
            if original_size[0] > original_size[1]:
                new_size = (scale_size, int(round(scale_size/ratio)))
            else:
                new_size = (int(round(scale_size*ratio)), scale_size)
        return imagedata.resize(new_size, 3)


if __name__ == '__main__':
    PhotoManager().run()
