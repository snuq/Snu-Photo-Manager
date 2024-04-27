"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
Todo before 1.0:
    Update readme - add some gifs/screenshots
    Video editor:
        add ability to play back video with audio for easier selecting the in/out
    Need to think of a way to divide up years abstractly
        Maybe manually added 'markers' that can be jumped to
        Maybe add 'pages' somehow
            maybe button at bottom that shows 'More albums (number)'
            maybe buttons next to database scroller that show starting/ending folder names - clicking them reloads scroller with that group

Bugs:
    seems that hd mpeg2 videos do not respect given bitrate settings... might be a buffer problem? causes 'buffer underflow' errors
    editing rotated photos may not rotate them back when editing

Todo Possible Future:
    Export to facebook - https://github.com/mobolic/facebook-sdk , https://blog.kivy.org/2013/08/using-facebook-sdk-with-python-for-android-kivy/
    RAW import - https://github.com/photoshell/rawkit , need to get libraw working

"""
import time
start = time.perf_counter()

import datetime
import json
import sys
from PIL import Image, ImageEnhance, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import sqlite3
import os
os.environ['KIVY_VIDEO'] = 'ffpyplayer'
try:
    from os.path import sep
except:
    from os import sep
from configparser import ConfigParser
from io import BytesIO
from shutil import copyfile
from shutil import rmtree
from shutil import move
from subprocess import call
import threading

#all these are needed to get ffpyplayer working on linux
import ffpyplayer.threading
import ffpyplayer.player.queue
import ffpyplayer.player.frame_queue
import ffpyplayer.player.decoder
import ffpyplayer.player.clock
import ffpyplayer.player.core
from ffpyplayer.player import MediaPlayer
from ffpyplayer.pic import SWScale

from kivy.config import Config
Config.window_icon = "data/icon.png"
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock, mainthread
from kivy.base import EventLoop
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import SlideTransition, NoTransition
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from send2trash import send2trash
from queue import Queue
try:
    import win32timezone
except:
    pass

from generalconstants import *
from generalcommands import get_crashlog, save_crashlog, list_folders, get_folder_info, local_thumbnail, isfile2, naming, to_bool, local_path, local_paths, agnostic_path, local_photoinfo, agnostic_photoinfo, get_file_info
from generalelements import ClickFade, EncodingSettings, PhotoDrag, TreenodeDrag, NormalPopup, MessagePopup, InputMenu
from screendatabase import DatabaseScreen, DatabaseRestoreScreen, TransferScreen
from screensettings import PhotoManagerSettings, AboutPopup


version = sys.version_info
kivy.require('1.10.0')
lock = threading.Lock()

if desktop:
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    #Config.set('kivy', 'keyboard_mode', 'system')
    Window.minimum_height = 600
    Window.minimum_width = 1024
    Window.maximize()
else:
    Window.softinput_mode = 'below_target'

if platform == 'win':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE])


class MainWindow(FloatLayout):
    pass


class Theme(Widget):
    colors = ['button_down', 'button_up', 'button_text', 'button_warn_down', 'button_warn_up', 'button_toggle_true', 'button_toggle_false', 'button_menu_up', 'button_menu_down', 'button_disabled', 'button_disabled_text', 'header_background', 'header_main_background', 'header_text', 'info_text', 'info_background', 'input_background', 'scroller', 'scroller_selected', 'sidebar_background', 'sidebar_resizer', 'slider_grabber', 'slider_background', 'main_background', 'menu_background', 'area_background', 'background', 'text', 'disabled_text', 'selected', 'missing', 'favorite']

    button_down = ListProperty()
    button_up = ListProperty()
    button_text = ListProperty()
    button_warn_down = ListProperty()
    button_warn_up = ListProperty()
    button_toggle_true = ListProperty()
    button_toggle_false = ListProperty()
    button_menu_up = ListProperty()
    button_menu_down = ListProperty()
    button_disabled = ListProperty()
    button_disabled_text = ListProperty()

    header_background = ListProperty()
    header_main_background = ListProperty()
    header_text = ListProperty()

    info_text = ListProperty()
    info_background = ListProperty()

    input_background = ListProperty()

    scroller = ListProperty()
    scroller_selected = ListProperty()

    sidebar_background = ListProperty()
    sidebar_resizer = ListProperty()

    slider_grabber = ListProperty()
    slider_background = ListProperty()

    main_background = ListProperty()
    menu_background = ListProperty()
    area_background = ListProperty()

    background = ListProperty()
    text = ListProperty()
    disabled_text = ListProperty()
    selected = ListProperty()
    missing = ListProperty()
    favorite = ListProperty()


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


class PhotoManager(App):
    """Main class of the app."""

    #Global variables
    ffmpeg = BooleanProperty(False)
    opencv = BooleanProperty(False)
    containers = ListProperty()
    video_codecs = ListProperty()
    audio_codecs = ListProperty()
    imagetypes = ListProperty()
    movietypes = ListProperty()
    audiotypes = ListProperty()
    has_crashlog = BooleanProperty(False)
    crashlog_date = StringProperty('')

    #Display variables
    photosinfo = ListProperty()  #List of all photoinfo from currently displayed photos
    photoinfo = ListProperty()  #Photoinfo list for the currently selected/viewed photo
    folder_path = StringProperty('')  #The current folder/tag being displayed
    folder_name = StringProperty()  #The identifier of the folder/tag that is being viewed

    mipmap = BooleanProperty(False)
    app_directory = ''
    last_browse_folder = ''

    first_rescale = True
    standalone = False
    standalone_file = ''
    standalone_in_database = False
    standalone_database = ''
    standalone_text = ''
    timer_value = 0
    button_update = BooleanProperty(False)
    settings_open = BooleanProperty(False)
    right_panel = BooleanProperty(False)
    last_width = NumericProperty(0)
    display_border = NumericProperty(16)
    button_scale = NumericProperty(40)
    text_scale = NumericProperty(12)
    data_directory = StringProperty('')
    database_auto_rescanner = ObjectProperty()
    database_auto_rescan_timer = NumericProperty(0)
    database_update_text = StringProperty('')
    showhelp = BooleanProperty(True)
    infotext = StringProperty('')
    infotext_history = ListProperty()
    infotext_setter = ObjectProperty()
    single_database = BooleanProperty(True)
    simple_interface = BooleanProperty(False)
    can_export = BooleanProperty(True)  #Controls if the export button in the album view area is enabled

    #Theming variables
    icon = 'data/icon.png'
    theme = ObjectProperty()
    selected_color = (0.5098, 0.8745, 0.6588, .5)
    list_background_odd = (0, 0, 0, 0)
    list_background_even = (0, 0, 0, .1)
    padding = NumericProperty(10)
    popup_x = 640
    animations = True
    animation_length = .2

    interpolation = StringProperty('Catmull-Rom')  #Interpolation mode of the curves dialog.
    fullpath = StringProperty()
    database_scanning = BooleanProperty(False)
    thumbsize = 256  #Size in pixels of the long side of any generated thumbnails
    tag_directory = 'Tags'  #Directory name to look in for tag files
    settings_cls = PhotoManagerSettings
    target = StringProperty()
    type = StringProperty('None')
    photo = StringProperty('')
    imports = []
    exports = []
    tags = []
    programs = []
    shift_pressed = BooleanProperty(False)
    cancel_scanning = BooleanProperty(False)
    export_target = StringProperty()
    export_type = StringProperty()
    encoding_settings = ObjectProperty()
    encoding_presets = ListProperty()
    encoding_presets_extra = ListProperty()
    encoding_presets_user = ListProperty()

    #Widget holders
    drag_image = ObjectProperty()
    drag_treenode = ObjectProperty()
    main_layout = ObjectProperty()  #Main layout root widget
    screen_manager = ObjectProperty()
    database_screen = ObjectProperty()
    album_screen = ObjectProperty()
    video_converter_screen = ObjectProperty()
    importing_screen = ObjectProperty()
    collage_screen = ObjectProperty()
    export_screen = ObjectProperty()
    database_restore_screen = ObjectProperty()
    scanningthread = None
    scanningpopup = None
    popup = None
    bubble = None
    clickfade_object = ObjectProperty(allownone=True)

    #Databases
    photos_name = 'photos.db'
    folders_name = 'folders.db'
    thumbnails_name = 'thumbnails.db'
    imported_name = 'imported.db'
    photos = None
    folders = None
    thumbnails = None
    tempthumbnails = None
    imported = None

    about_text = StringProperty()

    def build(self):
        """Called when the app starts.  Load and set up all variables, data, and screens."""

        crashlog = get_crashlog()
        if os.path.isfile(crashlog):
            self.has_crashlog = True
            crashlog_timestamp = os.path.getmtime(crashlog)
            self.crashlog_date = datetime.datetime.fromtimestamp(crashlog_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            self.has_crashlog = False

        self.ffmpeg = ffmpeg
        self.opencv = opencv

        self.encoding_settings = EncodingSettings()
        self.encoding_settings.load_current_encoding_preset()

        self.load_formats()

        self.theme = Theme()
        self.theme_default()
        themefile = os.path.realpath(os.path.join(self.data_directory, "theme.txt"))
        if themefile and os.path.exists(themefile):
            Logger.info('Loading theme file...')
            loaded, data = self.load_theme_data(themefile)
            if loaded:
                self.data_to_theme(data)
        Window.clearcolor = list(self.theme.background)
        if int(self.config.get("Settings", "buttonsize")) < 50:
            self.config.set("Settings", "buttonsize", 50)
        if int(self.config.get("Settings", "textsize")) < 50:
            self.config.set("Settings", "textsize", 50)
        if int(self.config.get("Settings", "thumbsize")) < 100:
            self.config.set("Settings", "thumbsize", 100)

        self.thumbsize = int(self.config.get("Settings", "thumbsize"))
        self.simple_interface = to_bool(self.config.get("Settings", "simpleinterface"))
        #Load data
        self.tag_directory = os.path.join(self.data_directory, 'Tags')
        about_file = open(kivy.resources.resource_find('about.txt'), 'r')
        self.about_text = about_file.read()
        about_file.close()
        self.program_import()  #Load external program presets
        self.setup_import_presets()  #Load import presets
        self.setup_export_presets()  #Load export presets
        self.tags_load()  #Load tags
        self.load_encoding_presets()

        database_directory = self.data_directory+sep+'Databases'
        if not os.path.exists(database_directory):
            os.makedirs(database_directory)
        self.photos_name = os.path.join(database_directory, 'photos.db')
        self.folders_name = os.path.join(database_directory, 'folders.db')
        self.thumbnails_name = os.path.join(database_directory, 'thumbnails.db')
        self.imported_name = os.path.join(database_directory, 'imported.db')
        self.setup_database()  #Import or set up databases

        #Parse open with commands and see if file is valid
        for possible_photo in sys.argv:
            if '.' in possible_photo:
                extension = '.' + possible_photo.lower().split('.')[-1]
                if extension in self.imagetypes or extension in self.movietypes:
                    if os.path.isfile(possible_photo):
                        Logger.info('Loading file: ' + possible_photo)
                        self.standalone_file = possible_photo
                        self.standalone = True
                        break

        #check if standalone file is in database
        if self.standalone:
            abspath = os.path.abspath(self.standalone_file)
            photoinfo = self.file_in_database(self.standalone_file)
            if photoinfo:
                self.standalone_in_database = True
                self.photo = abspath
                self.fullpath = photoinfo[0]
                self.target = photoinfo[1]
                self.type = 'Folder'
                self.standalone_text = 'Stand-Alone Mode, Using Database'
            else:
                self.standalone_in_database = False

            if not self.standalone_in_database:
                #File/folder is not in database, use temp databases
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

                self.photos_name = ':memory:'
                self.folders_name = ':memory:'
                self.thumbnails_name = ':memory:'
                self.imported_name = ':memory:'
                self.setup_database()

                #determine temp folder and database from passed in file
                full_folder, file = os.path.split(abspath)
                database_path, folder = os.path.split(full_folder)
                self.standalone_database = database_path
                self.photo = abspath
                self.fullpath = os.path.relpath(abspath, database_path)
                self.target = folder
                self.type = 'Folder'
                self.scan_folder(self.standalone_database, self.target)
                self.standalone_text = 'Stand-Alone Mode, Not Using Database'

        else:
            #Not standalone mode, setup default settings
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
            self.database_restore_screen = DatabaseRestoreScreen(name='database_restore')
            if self.config.getboolean("Settings", "rescanstartup"):
                self.database_import()
        self.set_single_database()

        #Set up widgets
        self.main_layout = MainWindow()
        self.drag_image = PhotoDrag()
        self.drag_treenode = TreenodeDrag()
        self.clickfade_object = ClickFade()

        #Set up screens
        self.screen_manager = ScreenManager()
        self.animations = to_bool(self.config.get("Settings", "animations"))
        self.set_transition()
        self.main_layout.add_widget(self.screen_manager)

        #Set up keyboard catchers
        Window.bind(on_key_down=self.key_down)
        Window.bind(on_key_up=self.key_up)
        Window.bind(on_dropfile=self.drop_file)
        return self.main_layout

    def on_start(self):
        """Function called when the app is first started.
        Add a custom keyboard hook so key buttons can be intercepted.
        """

        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        if not self.has_database():
            self.open_settings()
        self.database_auto_rescan_timer = float(self.config.get("Settings", "autoscan"))
        self.database_auto_rescanner = Clock.schedule_interval(self.database_auto_rescan, 60)
        Window.bind(on_draw=self.rescale_interface)
        startup_message = 'Startup Time: '+str(time.perf_counter() - start)
        Logger.info(startup_message)

    def on_pause(self):
        """Function called when the app is paused or suspended on a mobile platform.
        Saves all settings and data.
        """

        if self.main_layout:
            self.config.write()
            self.thumbnails.commit()
            self.photos.commit()
            self.folders.commit()
            self.imported.commit()
        return True

    def on_resume(self):
        Logger.info('Resuming App...')

    def on_stop(self):
        """Function called just before the app is closed.
        Saves all settings and data.
        """

        self.screen_manager.current_screen.on_leave()
        if self.database_scanning:
            self.cancel_database_import()
            self.scanningthread.join()
        self.encoding_settings.store_current_encoding_preset()
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

    def drop_file(self, window, filepath):
        current_screen = self.screen_manager.current_screen
        pos = Window.mouse_pos
        if type(filepath) == bytes:
            filepath = filepath.decode("utf-8")
        if hasattr(current_screen, 'drop_file'):
            current_screen.drop_file(filepath, pos)

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

    def hook_keyboard(self, window, scancode, *_):
        """This function receives keyboard events"""

        #print(scancode)
        self.close_bubble()

        if self.settings_open:
            if scancode == 27:
                if self.popup:
                    self.popup.dismiss()
                    self.popup = None
                    return True
                else:
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
            if scancode == 278:
                #Home key
                current_screen.key('home')
            if scancode == 279:
                #End key
                current_screen.key('end')
            if scancode == 280:
                #PgUp key
                current_screen.key('pgup')
            if scancode == 281:
                #PgDn key
                current_screen.key('pgdn')
            if scancode == 27:  #Escape
                self.clear_drags()
                if self.standalone:
                    match_screen = 'album'
                else:
                    match_screen = 'database'
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
                elif self.screen_manager.current != match_screen:
                    self.screen_manager.current_screen.back()
                    return True

    def load_formats(self):
        self.containers = self.parse_preset_config_file(os.path.join('data', 'containers.ini'), keys=['format', 'extension'], section_key='name')
        self.video_codecs = self.parse_preset_config_file(os.path.join('data', 'video_codecs.ini'), keys=['codec', 'efficiency'], section_key='name')
        self.video_codecs.append({'name': 'Copy Video', 'codec': 'copy', 'efficiency': '0'})
        self.audio_codecs = self.parse_preset_config_file(os.path.join('data', 'audio_codecs.ini'), keys=['codec', 'bitrate'], section_key='name')
        self.audio_codecs.append({'name': 'None/Remove', 'codec': '', 'bitrate': '0'})
        self.audio_codecs.append({'name': 'Copy Audio', 'codec': 'copy', 'bitrate': '0'})
        self.imagetypes = self.parse_list_file(os.path.join('data', 'imagetypes.txt'))
        self.movietypes = self.parse_list_file(os.path.join('data', 'movietypes.txt'))
        self.audiotypes = self.parse_list_file(os.path.join('data', 'audiotypes.txt'))

    def parse_list_file(self, filename):
        """Function that parses lines of a text file into a list, strips the lines and skips empty lines.
        Returns an empty list if file is not found or if empty."""

        elements = []
        filepath = kivy.resources.resource_find(filename)
        try:
            with open(filepath) as list_file:
                for line in list_file:
                    line = line.strip()
                    if line:
                        elements.append(line)
        except:
            pass
        return elements

    def parse_preset_config_file(self, preset_file, keys, ignore_sections=[], section_key=''):
        """Function that returns a list of presets loaded from a .ini file.
        keys: list of required keys for each preset to have, preset will not be returned if it does not have all of these
        ignore_sections: list of section names to ignore (optional)
        section_key: string, name of the dictionary key to store the section in.  if blank, will not be stored.

        Returns a list of dictionaries, each with the required keys.  Returns an empty list if none are found, or if file cannot be loaded."""

        try:
            presets = []
            configfile = ConfigParser(interpolation=None)
            config_filename = kivy.resources.resource_find(preset_file)
            configfile.read(config_filename)
            sections = configfile.sections()
        except:
            return []

        for section in sections:
            if section not in ignore_sections:
                valid = True
                preset = {}
                if section_key:
                    preset[section_key] = section
                for key in keys:
                    try:
                        preset[key] = configfile.get(section, key)
                    except:
                        valid = False
                if valid:
                    presets.append(preset)

        return presets

    def clickfade(self, widget, mode='opacity'):
        try:
            self.main_layout.remove_widget(self.clickfade_object)
        except:
            pass
        self.clickfade_object.size = widget.size
        self.clickfade_object.pos = widget.to_window(*widget.pos)
        self.clickfade_object.begin(mode)
        self.main_layout.add_widget(self.clickfade_object)

    def save_log(self, log, log_name):
        logfile_name = os.path.realpath(os.path.join(self.data_directory, log_name+".txt"))
        if os.path.isfile(logfile_name):
            os.remove(logfile_name)
        logfile = open(logfile_name, 'w')
        log_text = ''
        for line in log:
            log_text = log_text+line['text']+'\n'
        logfile.write(log_text)
        logfile.close()

    def timer(self, *_):
        start_time = time.perf_counter()
        timed = start_time - self.timer_value
        self.timer_value = start_time
        return timed

    def popup_bubble(self, text_input, pos, edit=True):
        self.close_bubble()
        text_input.unfocus_on_touch = False
        self.bubble = InputMenu(owner=text_input, edit=edit)
        window = self.root_window
        window.add_widget(self.bubble)
        posx = pos[0]
        posy = pos[1]
        #check position to ensure its not off screen
        if posx + self.bubble.width > window.width:
            posx = window.width - self.bubble.width
        if posy + self.bubble.height > window.height:
            posy = window.height - self.bubble.height
        self.bubble.pos = [posx, posy]

    def close_bubble(self, *_):
        if self.bubble:
            self.bubble.owner.unfocus_on_touch = True
            window = self.root_window
            window.remove_widget(self.bubble)
            self.bubble = None

    def save_current_theme(self):
        data = self.theme_to_data(self.theme)
        themefile = os.path.realpath(os.path.join(self.data_directory, "theme.txt"))
        self.save_theme_data(themefile, data)
        self.message('Saved Current Theme Settings')

    def theme_default(self):
        data = themes[0]
        self.data_to_theme(data)

    def theme_to_data(self, theme):
        data = {}
        for color in theme.colors:
            data[color] = list(eval('theme.'+color))
        return data

    def data_to_theme(self, data):
        theme = self.theme
        for color in theme.colors:
            try:
                new_color = data[color]
                r = float(new_color[0])
                g = float(new_color[1])
                b = float(new_color[2])
                a = float(new_color[3])
                new_color = [r, g, b, a]
                setattr(theme, color, new_color)
            except:
                pass
        self.button_update = not self.button_update

    def save_theme_data(self, theme_file, data):
        try:
            json.dump(data, open(theme_file, 'w'))
            return True
        except Exception as e:
            return e

    def load_theme_data(self, theme_file):
        try:
            data = json.load(open(theme_file))
            return [True, data]
        except Exception as e:
            return [False, e]

    def generate_thumbnail(self, fullpath, database_folder):
        """Creates a thumbnail image for a photo.

        Arguments:
            fullpath: Path to file, relative to the database folder.
            database_folder: Database root folder where the file is.
        Returns:
            A thumbnail jpeg
        """

        thumbnail = None
        full_filename = os.path.join(database_folder, fullpath)
        extension = os.path.splitext(fullpath)[1].lower()

        try:
            if extension in self.imagetypes:
                #This is an image file, use PIL to generate a thumnail
                image = Image.open(full_filename)
                image.thumbnail((self.thumbsize, self.thumbsize), Image.Resampling.LANCZOS)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                output = BytesIO()
                image.save(output, 'jpeg')
                image = None
                thumbnail = output.getvalue()

            elif extension in self.movietypes:
                #This is a video file, use ffpyplayer to generate a thumbnail
                player = MediaPlayer(full_filename, ff_opts={'paused': True, 'ss': 1.0, 'an': True, 'lowres': 2})
                frame = None
                frame_load_tries = 0
                while not frame:
                    if frame_load_tries > 100:
                        player.close_player()
                        player = None
                        # thumbnail has been trying to load for 10 seconds, give up
                        return None
                    frame, value = player.get_frame(force_refresh=True)
                    if not frame:
                        frame_load_tries += 1
                        time.sleep(0.1)
                metadata = player.get_metadata()
                aspect_ratio = metadata['aspect_ratio']
                aspect = aspect_ratio[1]/aspect_ratio[0]
                player.close_player()
                player = None
                frame = frame[0]
                frame_size = frame.get_size()
                current_pixel_format = frame.get_pixel_format()
                if current_pixel_format != 'rgb24':
                    frame_converter = SWScale(frame_size[0], frame_size[1], current_pixel_format, ofmt='rgb24')
                    frame = frame_converter.scale(frame)
                image_data = bytes(frame.to_bytearray()[0])

                image = Image.frombuffer(mode='RGB', size=(frame_size[0], frame_size[1]), data=image_data, decoder_name='raw')
                #image = image.transpose(1)
                if aspect != 1:
                    image = image.resize(size=(frame_size[0], int(frame_size[1] * aspect)))

                image.thumbnail((self.thumbsize, self.thumbsize), Image.Resampling.LANCZOS)

                output = BytesIO()
                image.save(output, 'jpeg')
                image = None
                thumbnail = output.getvalue()
            return thumbnail
        except:
            return None

    def set_single_database(self):
        databases = self.get_database_directories()
        if len(databases) > 1:
            self.single_database = False
        else:
            self.single_database = True

    @mainthread
    def message(self, text, timeout=20):
        """Sets the app.infotext variable to a specific message, and clears it after a set amount of time."""

        time_index = datetime.datetime.now().strftime('%I:%M%p')
        self.infotext_history.append([time_index, text])
        self.infotext_history = self.infotext_history[-10:]
        self.infotext = text
        if self.infotext_setter:
            self.infotext_setter.cancel()
        self.infotext_setter = Clock.schedule_once(self.clear_message, timeout)

    def clear_message(self, *_):
        self.infotext = ''

    def clear_database_update_text(self, *_):
        self.database_update_text = ''

    def refresh_photo(self, fullpath, force=False, no_photoinfo=False, data=False, skip_isfile=False, modified_date=None):
        """Checks if a file's modified date has changed, updates photoinfo and thumbnail if it has"""

        if data:
            old_photoinfo = data
        else:
            old_photoinfo = self.database_exists(fullpath)
        if old_photoinfo:
            #Photo is in database, check if it has been modified in any way
            photo_filename = os.path.join(old_photoinfo[2], old_photoinfo[0])
            if skip_isfile or os.path.isfile(photo_filename):
                #file still exists
                if modified_date is None:
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
            if photo_info:
                photo_file = os.path.join(photo_info[2], photo_info[0])
                abs_photo = os.path.abspath(photo_file)
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
        with open(self.data_directory+sep+'programs.ini', 'w') as config:
            configfile.write(config)

    def program_import(self):
        """Import external program presets from the config file."""

        self.programs = []
        filename = self.data_directory+sep+'programs.ini'
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
        """Save relavent photoinfo files for a folder, tag, or specified photos.
        Arguments:
            target: String, database identifier for the path where the photos are.
            save_location: String, full absolute path to the folder where the photoinfo file should be saved.
            container_type: String, defaults to 'folder', may be folder or tag.
            photos: Optional, List of photoinfo objects to save the photoinfo for.
            newnames:
        """

        if not self.config.get("Settings", "photoinfo") or (self.standalone and not self.standalone_in_database):
            return
        description = ''
        title = ''

        #If photos are not provided, find them for the given target.
        if not photos:
            if container_type == 'tag':
                photos = self.database_get_tag(target)
                title = "Photos tagged as '"+target+"'"
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

        join = os.path.join
        isdir = os.path.isdir
        if self.config.get("Settings", "photoinfo"):
            databases = self.get_database_directories()
            folders = list(set(folders))
            for folder in folders:
                for database in databases:
                    full_path = join(database, folder)
                    if isdir(full_path):
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
        self.mipmap = to_bool(self.config.get("Settings", "mipmap"))
        self.animations = to_bool(self.config.get("Settings", "animations"))
        self.set_transition()
        self.simple_interface = to_bool(self.config.get("Settings", "simpleinterface"))
        self.thumbsize = int(self.config.get("Settings", "thumbsize"))
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
                'thumbsize': 256,
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
                'mipmap': 1,
                'simpleinterface': simple_interface,
                'backupdatabase': 1,
                'rescanstartup': 0,
                'animations': 1,
                'databasescale': 1,
                'editvideo': 0,
                'highencodingpriority': 0,
                'gpu264': 0,
                'gpu265': 0
            })
        config.setdefaults(
            'Database Directories', {
                'paths': '',
                'achive': 0
            })
        config.setdefaults(
            'Sorting', {
                'database_sort': 'Name',
                'database_sort_reverse': 0,
                'album_sort': 'Name',
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
            "type": "savecrashlog",
            "title": "",
            "section": "Settings",
            "key": "photoinfo"
        })

        #Database settings
        settingspanel.append({
            "type": "label",
            "title": "        Database Settings"
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
            "type": "numeric",
            "title": "Auto-Rescan Database Interval In Minutes",
            "desc": "Auto-rescan database every number of minutes.  0 will never auto-scan.  Setting this too low will slow the system down.",
            "section": "Settings",
            "key": "autoscan"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Rescan Photo Database On Startup",
            "desc": "Automatically scan and update the photo database on each restart.  Prevents editing functions from being done until finished.",
            "section": "Settings",
            "key": "rescanstartup"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Backup Photo Database On Startup",
            "desc": "Automatically make a copy of the photo database on each restart.  Will increase startup time when large databases are loaded.",
            "section": "Settings",
            "key": "backupdatabase"
        })

        #Visual Settings
        settingspanel.append({
            "type": "label",
            "title": "        Visual Settings"
        })
        settingspanel.append({
            "type": "themescreen",
            "title": "",
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
            "desc": "Scale percentage of interface text",
            "section": "Settings",
            "key": "textsize"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Thumbnail Size",
            "desc": "Size in pixels of generated thumbnails",
            "section": "Settings",
            "key": "thumbsize"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Database Thumbs Scale",
            "desc": "Default pecentage scale for thumbnails in the database screen",
            "section": "Settings",
            "key": "databasescale"
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
            "title": "Use Mipmaps On Buttons And Labels",
            "desc": "Smooths interface a bit, but may cause blurry text.",
            "section": "Settings",
            "key": "mipmap"
        })

        #Browsing settings
        settingspanel.append({
            "type": "label",
            "title": "        Browsing Settings"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Save .photoinfo.ini Files",
            "desc": "Auto-save .photoinfo.ini files in album folders when photos or albums are changed",
            "section": "Settings",
            "key": "photoinfo"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Auto-Edit Video Files",
            "desc": "Go to video editng screen when loading a video file from the OS",
            "section": "Settings",
            "key": "editvideo"
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
            "title": "Remember Last Album View",
            "desc": "Remembers and returns to the last album or folder that was being viewed on last run",
            "section": "Settings",
            "key": "rememberview"
        })

        #Performance settings
        settingspanel.append({
            "type": "label",
            "title": "        Performance Settings"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Animate Interface",
            "desc": "Animate various elements of the interface.  Disable this on slow computers.",
            "section": "Settings",
            "key": "animations"
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
            "title": "Low Memory Mode",
            "desc": "For older computers that show larger images as black, display all images at a smaller size",
            "section": "Settings",
            "key": "lowmem"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Higher Video Encoding Priority",
            "desc": "Raise the priority of the video encoding thread.  WARNING: this can temporarily freeze the interface!",
            "section": "Settings",
            "key": "highencodingpriority"
        })
        settingspanel.append({
            "type": "bool",
            "title": "NVIDIA GPU H.264 Encoding",
            "desc": "Enable GPU encoding options for encoding H.264 videos.  WARNING: only enable this if you have an NVIDIA graphic card that supports this!",
            "section": "Settings",
            "key": "gpu264"
        })
        settingspanel.append({
            "type": "bool",
            "title": "NVIDIA GPU H.265 Encoding",
            "desc": "Enable GPU encoding options for encoding H.265 videos.  WARNING: only enable this if you have an NVIDIA graphic card that supports this!",
            "section": "Settings",
            "key": "gpu265"
        })
        settings.add_json_panel('App', self.config, data=json.dumps(settingspanel))

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

    def start_screen_layout(self, *_):
        #Show correct screen layout:
        if ffmpeg:
            if self.config.getboolean("Settings", "editvideo"):
                if self.photo:
                    extension = os.path.splitext(self.photo)[1].lower()
                    if extension in self.movietypes:
                        Clock.schedule_once(self.show_video_converter)
                        return
        Clock.schedule_once(self.show_database)

    def open_settings(self, *largs):
        self.clear_drags()
        self.settings_open = True
        super().open_settings(*largs)

    def close_settings(self, *largs):
        self.settings_open = False
        super().close_settings(*largs)

    def setup_import_presets(self):
        """Reads the import presets from the config file and saves them to the app.imports variable."""

        self.imports = []
        filename = self.data_directory+sep+'imports.ini'
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
                        single_folder = import_preset['single_folder'].lower()
                        if single_folder not in ['single', 'formatted', 'year', 'month']:
                            is_single = to_bool(single_folder)
                            if is_single:
                                single_folder = 'single'
                            else:
                                single_folder = 'formatted'
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
        filename = self.data_directory+sep+'exports.ini'
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

        preset = {'export': 'folder',
                  'ftp_address': '',
                  'ftp_user': '',
                  'ftp_password': '',
                  'ftp_passive': True,
                  'ftp_port': 21,
                  'name': 'Export Preset '+str(len(self.exports)+1),
                  'export_folder': '',
                  'create_subfolder': True,
                  'export_info': True,
                  'scale_image': False,
                  'scale_size': 1000,
                  'scale_size_to': 'long',
                  'jpeg_quality': 90,
                  'watermark_image': '',
                  'watermark': False,
                  'watermark_opacity': 33,
                  'watermark_horizontal': 90,
                  'watermark_vertical': 10,
                  'watermark_size': 25,
                  'ignore_tags': [],
                  'export_videos': False}
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

        with open(self.data_directory+sep+'exports.ini', 'w') as config:
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

        databases = self.get_database_directories()
        if databases:
            import_to = databases[0]
        else:
            import_to = ''
        preset = {'title': 'Import Preset '+str(len(self.imports)+1), 'import_to': import_to, 'naming_method': naming_method_default, 'delete_originals': False, 'single_folder': 'formatted', 'import_from': []}
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

        with open(self.data_directory+sep+'imports.ini', 'w') as config:
            configfile.write(config)

    def database_backup(self):
        """Makes a copy of the photos, folders and imported databases to a backup directory"""
        database_directory = self.data_directory+sep+'Databases'
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
        self.message('Backed up databases')

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
        database_directory = self.data_directory+sep+'Databases'
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

        self.photos = MultiThreadOK(self.photos_name)
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

        self.folders = MultiThreadOK(self.folders_name)
        self.folders.execute('''CREATE TABLE IF NOT EXISTS folders(
                             Path text PRIMARY KEY,
                             Title text,
                             Description text)''')

        if not restore:
            self.thumbnails = MultiThreadOK(self.thumbnails_name)
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

        self.imported = MultiThreadOK(self.imported_name)
        self.imported.execute('''CREATE TABLE IF NOT EXISTS imported(
                              FullPath text PRIMARY KEY,
                              File text,
                              ModifiedDate integer);''')
        if not restore and self.config.getboolean("Settings", "backupdatabase"):
            self.database_backup()

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

        tag_name = tag_name.strip(' ')
        tag_filename = tag_name + '.tag'
        filename = os.path.join(self.tag_directory, tag_filename)
        if not os.path.isfile(filename) and tag_name.lower() != 'favorite':
            self.tags.append(tag_name)
            open(filename, 'a').close()

    def tag_load_description(self, tag_name):
        tag_filename = tag_name + '.tag'
        filename = os.path.join(self.tag_directory, tag_filename)
        try:
            tag_file = open(filename, "r")
            tag_data = tag_file.read()
            tag_file.close()
            return tag_data
        except:
            return ''

    def tag_save_description(self, tag_name, description):
        tag_filename = tag_name + '.tag'
        filename = os.path.join(self.tag_directory, tag_filename)
        try:
            tag_file = open(filename, "w")
            tag_file.write(description)
            tag_file.close()
            return True
        except:
            return False

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
        self.app_directory = app_directory
        Logger.info('App Folder: '+self.app_directory)
        if platform == 'win':
            self.data_directory = os.getenv('APPDATA')+sep+"Snu Photo Manager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'linux':
            self.data_directory = os.path.expanduser('~')+sep+".snuphotomanager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'macosx':
            self.data_directory = os.path.expanduser('~')+sep+".snuphotomanager"
            if not os.path.isdir(self.data_directory):
                os.makedirs(self.data_directory)
        elif platform == 'android':
            self.data_directory = self.user_data_dir
        else:
            self.data_directory = sep
        # __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        #__location__ = os.path.realpath(sys.path[0])
        #if __location__.endswith('.zip'):
        #    __location__ = os.path.dirname(__location__)
        config_file = os.path.realpath(os.path.join(self.data_directory, "snuphotomanager.ini"))
        Logger.info("Config File: "+config_file)
        return config_file

    def load_encoding_presets(self):
        """Loads the video encoding presets from the 'encoding_presets.ini' file."""

        presets = self.parse_encoding_presets_file('data/encoding_presets.ini')
        self.encoding_presets = [EncodingSettings(name='Automatic')] + presets
        self.encoding_presets_extra = self.parse_encoding_presets_file('data/encoding_presets_extra.ini')
        self.encoding_presets_user = self.parse_encoding_presets_file(self.data_directory+sep+'encoding_presets_user.ini')

    def new_user_encoding_preset(self):
        current_preset = self.encoding_settings
        if not current_preset.name:
            current_preset.name = 'User Preset'
        for preset in self.encoding_presets_user:
            if preset.name == current_preset.name:
                preset.copy_from(current_preset)
                self.save_user_encoding_presets()
                return
        self.encoding_presets_user.append(current_preset)
        self.save_user_encoding_presets()
        self.message('Saved encoding preset: '+current_preset.name)

    def remove_user_encoding_preset(self, preset):
        try:
            self.encoding_presets_user.remove(preset)
            self.save_user_encoding_presets()
            self.message('Deleted encoding preset: '+preset.name)
        except:
            pass

    def save_user_encoding_presets(self):
        user_preset_file = self.data_directory+sep+'encoding_presets_user.ini'
        configfile = ConfigParser(interpolation=None)
        for index, preset in enumerate(self.encoding_presets_user):
            section = preset.name
            configfile.add_section(section)
            configfile.set(section, 'file_format', preset.file_format)
            configfile.set(section, 'video_codec', preset.video_codec)
            configfile.set(section, 'audio_codec', preset.audio_codec)
            configfile.set(section, 'resize', str(preset.resize))
            configfile.set(section, 'resize_width', preset.resize_width)
            configfile.set(section, 'resize_height', preset.resize_height)
            configfile.set(section, 'video_bitrate', preset.video_bitrate)
            configfile.set(section, 'audio_bitrate', preset.audio_bitrate)
            configfile.set(section, 'encoding_speed', preset.encoding_speed)
            configfile.set(section, 'deinterlace', str(preset.deinterlace))
            configfile.set(section, 'command_line', preset.command_line)
            configfile.set(section, 'quality', preset.quality)
            configfile.set(section, 'gop', preset.gop)
            configfile.set(section, 'description', preset.description)

        with open(user_preset_file, 'w') as config:
            configfile.write(config)

    def parse_encoding_presets_file(self, preset_file):
        try:
            presets = []
            configfile = ConfigParser(interpolation=None)
            configfile.read(kivy.resources.resource_find(preset_file))
            preset_names = configfile.sections()
        except:
            return []

        for preset_name in preset_names:
            preset = EncodingSettings()
            preset.name = preset_name
            try:
                preset.file_format = configfile.get(preset_name, 'file_format')
            except:
                pass
            try:
                preset.video_codec = configfile.get(preset_name, 'video_codec')
            except:
                pass
            try:
                preset.audio_codec = configfile.get(preset_name, 'audio_codec')
            except:
                pass
            try:
                preset.resize = to_bool(configfile.get(preset_name, 'resize'))
            except:
                pass
            try:
                preset.resize_width = configfile.get(preset_name, 'width')
            except:
                pass
            try:
                preset.resize_height = configfile.get(preset_name, 'height')
            except:
                pass
            try:
                preset.video_bitrate = configfile.get(preset_name, 'video_bitrate')
            except:
                pass
            try:
                preset.audio_bitrate = configfile.get(preset_name, 'audio_bitrate')
            except:
                pass
            try:
                preset.encoding_speed = configfile.get(preset_name, 'encoding_speed')
            except:
                pass
            try:
                preset.deinterlace = to_bool(configfile.get(preset_name, 'deinterlace'))
            except:
                pass
            try:
                preset.command_line = configfile.get(preset_name, 'command_line')
            except:
                pass
            try:
                preset.quality = configfile.get(preset_name, 'quality')
            except:
                pass
            try:
                preset.gop = configfile.get(preset_name, 'gop')
            except:
                pass
            try:
                preset.description = configfile.get(preset_name, 'description')
            except:
                pass
            presets.append(preset)
        return presets

    def rescale_interface(self, *_, force=False):
        if self.last_width == 0:
            first_change = True
        else:
            first_change = False
        if Window.width != self.last_width or force:
            self.popup_x = int(Window.width * .75)
            self.last_width = Window.width
            if first_change:
                Clock.schedule_once(lambda x: self.rescale_interface(force=True))
                return
            if desktop:
                button_multiplier = 1
            else:
                button_multiplier = 1.5
            buttonsize = int(self.config.get("Settings", "buttonsize"))
            if buttonsize < 50:
                buttonsize = 50
            button_scale = int((max(Window.height, 600) / interface_multiplier) * buttonsize / 100) * button_multiplier
            if self.button_scale < 10:
                button_scale = 10
            self.button_scale = button_scale
            self.display_border = button_scale / 3
            self.padding = self.button_scale / 4

            textsize = int(self.config.get("Settings", "textsize"))
            if textsize < 50:
                textsize = 50
            self.text_scale = int((self.button_scale / 3) * textsize / 100)
            if self.first_rescale:
                self.first_rescale = False
                self.start_screen_layout()
            try:
                self.screen_manager.current_screen.rescale_screen()
            except:
                pass

    def set_transition(self):
        if self.animations:
            self.screen_manager.transition = SlideTransition()
        else:
            self.screen_manager.transition = NoTransition()

    def scan_folder(self, database_folder, folder):
        #Full scan of files in the folder, used when in standalone mode

        files = []
        full_folder = os.path.join(database_folder, folder)
        for (dirpath, dirnames, filenames) in os.walk(full_folder):
            files.extend(filenames)
            break

        for index, file in enumerate(files):
            extension = os.path.splitext(file)[1].lower()
            if extension in self.imagetypes or extension in self.movietypes:
                file_info = [os.path.join(folder, file), database_folder]
                file_info = get_file_info(file_info)
                self.database_add(file_info)

        self.photos.commit()

    def file_in_database(self, file):
        """Checks if the given file is in the database, returns the photoinfo if it is"""

        databases = self.get_database_directories(real=True)
        abspath = os.path.abspath(file)

        #Check if path begins with any of the databases
        for database_path in databases:
            if abspath.startswith(database_path):
                fullpath = os.path.relpath(abspath, database_path)
                photoinfo = self.database_exists(fullpath)
                if photoinfo:
                    #File is in database, use current database
                    return photoinfo
        return None

    def remove_tag(self, tag):
        """Deletes a tag.
        Argument:
            tag: String, the tag to be deleted."""

        tag = tag
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
            message: Display an app message that the file was deleted.
        """

        photoinfo = self.database_exists(fullpath)
        if os.path.isfile(filename):
            deleted = self.delete_file(filename)
        else:
            deleted = True
        if deleted is True:
            if photoinfo:  #this should not be none... but apparently it happens sometimes
                if os.path.isfile(photoinfo[10]):
                    self.delete_file(photoinfo[10])
            fullpath = agnostic_path(fullpath)
            self.photos.execute('DELETE FROM photos WHERE FullPath = ?', (fullpath,))
            self.thumbnails.execute('DELETE FROM thumbnails WHERE FullPath = ?', (fullpath,))
            if message:
                self.message("Deleted the file '"+filename+"'")
            return True
        else:
            if message:
                self.popup_message(text='Could not delete file', title='Warning')
            return deleted

    def delete_folder_original(self, folder):
        """Delete all original unedited files in a given folder"""

        photos = self.database_get_folder(folder)
        deleted_photos = []
        for photoinfo in photos:
            deleted, message = self.delete_photo_original(photoinfo)
            if deleted is True:
                deleted_photos.append(photoinfo)
        return deleted_photos

    def delete_photo_original(self, photoinfo):
        """Delete the original unedited file.
        Argument:
            photoinfo: List, photoinfo object.
        """

        if not photoinfo[10]:
            return False, 'Could not find original file'
        original_file = os.path.abspath(local_path(photoinfo[2])+sep+local_path(photoinfo[1])+sep+local_path(photoinfo[10]))
        current_file = os.path.abspath(os.path.join(local_path(photoinfo[2]), local_path(photoinfo[0])))
        if os.path.isfile(original_file) and original_file != current_file:
            deleted = self.delete_file(original_file)
            if deleted is not True:
                return False, 'Could not delete original file: '+str(deleted)
        else:
            return False, 'Could not find original file'
        return True, "Deleted original file"

    def delete_file(self, filepath):
        """Attempt to delete a file using send2trash.
        Returns:
            True if file was deleted
            False if file could not be deleted
        """

        try:
            if platform != 'android':
                send2trash(filepath)
            else:
                os.remove(filepath)
        except Exception as ex:
            return ex
        return True

    def database_remove_tag(self, fullpath, tag, message=False):
        """Remove a tag from a photo.
        Arguments:
            fullpath: String, the database-relative path to the photo.
            tag: String, the tag to remove.
            message: Display an app message stating that the tag was removed.
        """

        tag = tag.lower()
        fullpath = agnostic_path(fullpath)
        info = self.photos.select('SELECT * FROM photos WHERE FullPath = ?', (fullpath, ))
        info = list(info)
        if info:
            info = list(info[0])
            current_tags = info[8].lower().split(',')
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
            tags_unformatted = info[8].lower().strip(' ')
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
                    current_tags.append(original.lower())
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
        return os.path.join(folder_path, new_name)

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
        self.folders.execute('DELETE FROM folders WHERE Path = ?', (agnostic_path(folder), ))
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

    def database_get_all_folder_info(self):
        folders = []
        folder_items = list(self.folders.select('SELECT * FROM folders'))
        for item in folder_items:
            folders.append([local_path(item[0]), item[1], item[2]])
        return folders

    def database_get_folders(self, database_folder=False, quick=False, real_folders=None):
        """Get all folders from the photo database.
        Returns: List of folder database-relative paths.
        """

        folders = []
        if database_folder:
            database_folder = agnostic_path(database_folder)
            folder_items = list(self.photos.select('SELECT Folder FROM photos WHERE DatabaseFolder = ? GROUP BY Folder', (database_folder, )))
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
                if real_folders is None:
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
        self.photos.execute("insert into photos values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (fileinfo[0], fileinfo[1], fileinfo[2], fileinfo[3], fileinfo[4], fileinfo[5], fileinfo[6], fileinfo[7], fileinfo[8], fileinfo[9], fileinfo[10], fileinfo[11], fileinfo[12], fileinfo[13]))

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

    def database_clean(self, deep=False, photo_filenames=[]):
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
                    if photo_file not in photo_filenames:
                        if not isfile2(photo_file):  #Takes a lot of time
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
        """Calls database_import."""

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
            thumbs.execute("insert into thumbnails values(?, ?, ?, ?)", (fullpath, modified_date, thumbnail, orientation))
        else:
            #Thumbnail exist already, just update it
            thumbs.execute("UPDATE thumbnails SET ModifiedDate = ?, Thumbnail = ?, Orientation = ? WHERE FullPath = ?", (modified_date, thumbnail, orientation, fullpath, ))

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
        thumbnail = self.generate_thumbnail(local_path(fullpath), local_path(database))
        if thumbnail is None:
            return False
        thumbnail = sqlite3.Binary(thumbnail)
        self.database_thumbnail_write(fullpath=fullpath, modified_date=modified_date, thumbnail=thumbnail, orientation=orientation, temporary=temporary)
        return True

    def database_item_rename(self, fullpath, newname, newfolder, dontcommit=False):
        """Changes the database-relative path of a photo to another path.
        Updates both photos and thumbnails databases.
        Arguments:
            fullpath: String, the original database-relative path.
            newname: String, the new database-relative path.
            newfolder: String, new database-relative containing folder for the file.
            dontcommit: Dont write to the database when finished.
        """

        fullpath = agnostic_path(fullpath)
        newname = agnostic_path(newname)
        if self.database_exists(newname):
            self.database_item_delete(newname)
        newfolder_rename = agnostic_path(newfolder)
        self.photos.execute("UPDATE photos SET FullPath = ?, Folder = ? WHERE FullPath = ?", (newname, newfolder_rename, fullpath, ))
        if not dontcommit:
            self.photos.commit()
        self.thumbnails.execute("UPDATE thumbnails SET FullPath = ? WHERE FullPath = ?", (newname, fullpath, ))
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
        self.photos.execute("UPDATE photos SET Rename = ?, ModifiedDate = ?, Tags = ?, Edited = ?, OriginalFile= ?, Owner = ?, Export = ?, Orientation = ? WHERE FullPath = ?", (fileinfo[5], fileinfo[7], fileinfo[8], fileinfo[9], fileinfo[10], fileinfo[11], fileinfo[12], fileinfo[13], fileinfo[0]))
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

    def get_database_directories(self, real=False):
        """Gets the current database directories.
        Returns: List of Strings of the paths to each database.
        """

        if not real and (self.standalone and not self.standalone_in_database):
            #if real is not passed in, and a standalone database is set, use that
            return [self.standalone_database]
        else:
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

    def list_files_folders(self, folder):
        """Function that returns a list of every nested file within a folder.
        Argument:
            folder: The folder name to look in
        Returns: A list of file lists, each list containing:
            Full path to the file, relative to the root directory.
            Root directory for all files.
        """
        join = os.path.join
        getmtime = os.path.getmtime
        relpath = os.path.relpath
        walk = os.walk
        file_list = []
        filenames = []
        folder_list = []
        firstroot = False
        for root, dirs, files in walk(folder, topdown=True):
            dir_files = []
            if self.cancel_scanning:
                return [[], [], []]
            if not firstroot:
                firstroot = root
            filefolder = relpath(root, firstroot)
            if filefolder == '.':
                filefolder = ''
            for file in files:
                if file == '.nomedia':
                    dirs.clear()
                    dir_files = []
                    break
                if self.cancel_scanning:
                    return [[], [], []]
                fullpath = join(filefolder, file)
                full_filename = join(folder, fullpath)
                filenames.append(full_filename)
                modified_date = int(getmtime(full_filename))
                dir_files.append([fullpath, firstroot, modified_date])
            for directory in dirs:
                folder_list.append(join(filefolder, directory))
            file_list.extend(dir_files)
        return [file_list, folder_list, filenames]

    def database_find_file(self, file_info):
        #search the database for a file that has been moved to a new directory, returns the updated info or None if not found.
        filepath, filename = os.path.split(file_info[0])
        old_photos = self.photos.select('SELECT * FROM photos WHERE FullPath LIKE ?', ('%'+filename+'%',))
        if old_photos:
            possible_matches = []
            old_photos = list(old_photos)
            for photo in old_photos:
                #check if photo still exists, ignore if it does
                photo_path = os.path.join(local_path(photo[2]), local_path(photo[0]))
                if not os.path.exists(photo_path):
                    possible_matches.append(photo)
            #return first match
            if possible_matches:
                return possible_matches[0]
        return None

    @mainthread
    def enable_database_scanning(self, *_):
        self.database_scanning = True

    @mainthread
    def disable_database_scanning(self, *_):
        self.database_scanning = False

    def database_import_files(self):
        """Database scanning thread, checks for new files in the database directories and adds them to the database."""

        self.enable_database_scanning()
        self.database_update_text = 'Rescanning Database, Building Folder List'
        databases = self.get_database_directories()
        update_folders = []

        #Get the file list
        files = []
        real_folders = []
        filenames = []
        for directory in databases:
            if self.cancel_scanning:
                break
            database_files, database_folders, database_filenames = self.list_files_folders(directory)
            files = files + database_files
            real_folders = real_folders + database_folders
            filenames = filenames + database_filenames

        total = len(files)
        self.database_update_text = 'Rescanning Database (5%)'

        #Iterate all files, check if in database, add if needed.
        for index, file_info in enumerate(files):
            if self.cancel_scanning:
                break
            extension = os.path.splitext(file_info[0])[1].lower()
            if extension in self.imagetypes or extension in self.movietypes:
                exists = self.database_exists(file_info[0])
                if not exists:
                    #photo not in database, add it or ceck if moved
                    file_info = get_file_info(file_info)
                    found_file = self.database_find_file(file_info)
                    if found_file:
                        found_file = agnostic_photoinfo(list(found_file))
                        self.database_item_rename(found_file[0], file_info[0], file_info[1], dontcommit=True)
                        update_folders.append(found_file[1])
                        update_folders.append(file_info[1])
                    else:
                        self.database_add(file_info)
                        update_folders.append(file_info[1])
                else:
                    #photo is already in the database
                    #check modified date to see if it needs to be updated and look for duplicates
                    refreshed = self.refresh_photo(file_info[0], no_photoinfo=True, data=exists, skip_isfile=True, modified_date=file_info[2])
                    if refreshed:
                        update_folders.append(refreshed[1])

            self.database_update_text = 'Rescanning Database ('+str(int(90*(float(index+1)/float(total))))+'%)'
        self.photos.commit()
        #Update folders
        folders = self.database_get_folders(real_folders=real_folders)
        for folder in folders:
            if self.cancel_scanning:
                break
            exists = self.database_folder_exists(folder)
            if not exists:
                folderinfo = get_folder_info(folder, databases)
                self.database_folder_add(folderinfo)
                update_folders.append(folderinfo[0])
        update_folders = list(set(update_folders))
        #self.update_photoinfo(folders=folders)  #Doesnt need to run on all folders
        self.folders.commit()
        #Clean up database
        if not self.cancel_scanning:
            self.database_update_text = 'Cleaning Database...'
            self.database_clean(photo_filenames=filenames)
            self.database_update_text = "Database scanned "+str(total)+" files"

        self.update_photoinfo(folders=update_folders)
        if self.cancel_scanning:
            self.database_update_text = "Canceled database update."
        self.disable_database_scanning()
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
        self.folders.execute("UPDATE folders SET Title = ?, Description = ? WHERE Path = ?", (title, description, renamed_path, ))

    def show_database(self, *_, scrollto=''):
        """Switch to the database screen layout."""

        if self.standalone:
            self.show_album()
        else:
            if 'database' not in self.screen_manager.screen_names:
                self.screen_manager.add_widget(self.database_screen)
            if self.animations:
                self.screen_manager.transition.direction = 'right'
            self.database_screen.scrollto = scrollto
            self.screen_manager.current = 'database'

    def show_database_restore(self):
        """Switch to the database restoring screen layout."""

        if 'database_restore' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.database_restore_screen)
        self.screen_manager.current = 'database_restore'

    def show_theme(self):
        """Switch to the theme editor screen layout."""

        if 'theme' not in self.screen_manager.screen_names:
            from screentheme import ThemeScreen
            self.screen_manager.add_widget(ThemeScreen(name='theme'))
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'theme'

    def show_collage(self, from_database=False):
        """Switch to the create collage screen layout.
        """

        if 'collage' not in self.screen_manager.screen_names:
            from screencollage import CollageScreen
            self.collage_screen = CollageScreen(name='collage')
            self.screen_manager.add_widget(self.collage_screen)
        #self.type = self.database_screen.type
        #self.target = self.database_screen.selected
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.collage_screen.from_database = from_database
        self.screen_manager.current = 'collage'

    def show_video_converter(self, from_database=False):
        if 'video' not in self.screen_manager.screen_names:
            from screenalbum import VideoConverterScreen
            self.video_converter_screen = VideoConverterScreen(name='video')
            self.screen_manager.add_widget(self.video_converter_screen)
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.video_converter_screen.from_database = from_database
        self.screen_manager.current = 'video'

    def show_album(self, button=None, back=False):
        """Switch to the album screen layout.
        Argument:
            button: Optional, the widget that called this function. Allows the function to get a specific album to view.
        """

        if 'album' not in self.screen_manager.screen_names:
            from screenalbum import AlbumScreen
            self.album_screen = AlbumScreen(name='album')
            self.screen_manager.add_widget(self.album_screen)
        if self.animations:
            if back:
                self.screen_manager.transition.direction = 'right'
            else:
                self.screen_manager.transition.direction = 'left'

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

    def show_import(self):
        """Switch to the import select screen layout."""

        if 'import' not in self.screen_manager.screen_names:
            from screenimporting import ImportScreen, ImportingScreen
            self.importing_screen = ImportingScreen(name='importing')
            self.screen_manager.add_widget(ImportScreen(name='import'))
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'import'

    def show_importing(self):
        """Switch to the photo import screen layout."""

        if 'importing' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.importing_screen)
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'importing'

    def show_export(self, from_database=False):
        """Switch to the photo export screen layout."""

        if 'export' not in self.screen_manager.screen_names:
            from screenexporting import ExportScreen
            self.export_screen = ExportScreen(name='export')
            self.screen_manager.add_widget(self.export_screen)
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.export_screen.from_database = from_database
        self.screen_manager.current = 'export'

    def show_transfer(self):
        """Switches to the database transfer screen layout"""

        if 'transfer' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(TransferScreen(name='transfer'))
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'transfer'

    def dismiss_popup(self, *_):
        #Close the app's open popup if it has one

        if self.popup:
            self.popup.dismiss()
            self.popup = None
            return True
        return False

    def popup_message(self, text, title='Notification'):
        """Creates a simple 'ok' popup dialog.
        Arguments:
            text: String, text that the dialog will display
            title: String, the dialog window title.
        """

        self.dismiss_popup()
        content = MessagePopup(text=text)
        self.popup = NormalPopup(title=title, content=content, size_hint=(None, None), size=(self.popup_x, self.button_scale * 4))
        self.popup.open()

    def clear_drags(self):
        """Removes the drag-n-drop widgets and copy popups."""

        self.close_bubble()
        self.main_layout.remove_widget(self.drag_treenode)
        self.main_layout.remove_widget(self.drag_image)

    def drag(self, drag_object, mode, position, image=None, offset=list([0, 0]), fullpath='', photos=0):
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
            photos: Number of dragged photos
        """

        if mode == 'end':
            self.main_layout.remove_widget(self.drag_image)
            self.screen_manager.current_screen.drop_widget(self.drag_image.fullpath, position, dropped_type='file', aspect=self.drag_image.ids['image'].image_ratio)

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
            if photos > 1:
                self.drag_image.total_drags = str(photos) + ' Photos'
            else:
                self.drag_image.total_drags = ''
            self.drag_image.width = drag_object.children[0].width
            self.drag_image.height = drag_object.height
            self.drag_image.angle = angle
            self.drag_image.offset = offset
            self.main_layout.remove_widget(self.drag_image)
            self.drag_image.pos = (position[0]-offset[0], position[1]-offset[1])
            self.drag_image.ids['image'].texture = image.texture
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
            self.screen_manager.current_screen.drop_widget(drag_object.fullpath, position, dropped_type=drag_object.droptype, aspect=1)

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
        Returns: A string.
        """

        return "".join(i for i in string if i not in "#%&*{}\\/:?<>+|\"=][;,")

    def new_description(self, description_editor, root, folder, title_type):
        """Update the description of a folder.
        Arguments:
            description_editor: Widget, the text input object that was edited.
            root: The screen that owns the text input widget.  Has information about the folder or album being edited.
        """

        if not description_editor.focus:
            description = description_editor.text
            if title_type == 'Folder':
                self.database_folder_update_description(folder, description)
                self.folders.commit()
                self.update_photoinfo(folders=[folder])
            elif title_type == 'Tag':
                saved = self.tag_save_description(folder, description)
                if not saved:
                    self.message("Unable to save tag description")

    def new_title(self, title_editor, root, folder, title_type):
        """Update the title of a folder or album.
        Arguments:
            title_editor: Widget, the text input object that was edited.
            root: The screen that owns the text input widget.  Has information about the folder or album being edited.
        """

        if not title_editor.focus:
            title = title_editor.text
            if title_type == 'Folder':
                self.database_folder_update_title(folder, title)
                self.folders.commit()
                self.update_photoinfo(folders=[folder])
                root.update_folders = True
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
        image_size_min = min(*image_size)
        try:
            watermark = Image.open(watermark_image)
        except:
            self.message('Watermark image not found')
            return imagedata
        watermark_size_pixels = watermark.size
        watermark_width, watermark_height = watermark_size_pixels
        watermark_ratio = watermark_width/watermark_height
        new_watermark_width = int(round(image_size_min*(watermark_size/100)))
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
    try:
        PhotoManager().run()
    except Exception as e:
        try:
            save_crashlog()
        except:
            pass
        os._exit(-1)
