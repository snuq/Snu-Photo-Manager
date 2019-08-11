"""
Future Todo (lower priority, need to figure out how to do it, or a lot of work):
    Collage editor - add more collage modes (grids)
    Rework cropping editor
    export to facebook - https://github.com/mobolic/facebook-sdk , https://blog.kivy.org/2013/08/using-facebook-sdk-with-python-for-android-kivy/
    RAW import if possible - https://github.com/photoshell/rawkit , need to get libraw working
"""

import time
start = time.perf_counter()

import json
import sys
from PIL import Image, ImageEnhance, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import sqlite3
import os
os.environ['KIVY_VIDEO'] = 'ffpyplayer'
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
from kivy.clock import Clock
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
from generalcommands import list_folders, get_folder_info, local_thumbnail, isfile2, naming, to_bool, local_path, local_paths, agnostic_path, local_photoinfo, agnostic_photoinfo, get_file_info
from generalelements import PhotoDrag, TreenodeDrag, NormalPopup, MessagePopup
from screendatabase import DatabaseScreen, DatabaseRestoreScreen, TransferScreen
from screensettings import PhotoManagerSettings, AboutPopup
print('Startup Time: '+str(time.perf_counter() - start))


version = sys.version_info
kivy.require('1.10.0')
lock = threading.Lock()

if desktop:
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    #Config.set('kivy', 'keyboard_mode', 'system')
    Window.minimum_height = 600
    Window.minimum_width = 800
    Window.maximize()
else:
    Window.softinput_mode = 'below_target'

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE])


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

    settings_open = BooleanProperty(False)
    right_panel = BooleanProperty(False)
    last_width = NumericProperty(0)
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
    padding = NumericProperty(10)
    popup_x = 640
    animations = True
    animation_length = .2

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

    def generate_thumbnail(self, fullpath, database_folder):
        """Creates a thumbnail image for a photo.

        Arguments:
            fullpath: Path to file, relative to the database folder.
            database_folder: Database root folder where the file is.
        Returns:
            A thumbnail jpeg
        """

        thumbnail = ''
        full_filename = os.path.join(database_folder, fullpath)
        extension = os.path.splitext(fullpath)[1].lower()

        try:
            if extension in imagetypes:
                #This is an image file, use PIL to generate a thumnail
                image = Image.open(full_filename)
                image.thumbnail((self.thumbsize, self.thumbsize), Image.ANTIALIAS)
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

                image.thumbnail((self.thumbsize, self.thumbsize), Image.ANTIALIAS)
                output = BytesIO()
                image.save(output, 'jpeg')
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

    def refresh_photo(self, fullpath, force=False, no_photoinfo=False, data=False, skip_isfile=False):
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
            newnames:
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
                'simpleinterface': simple_interface,
                'backupdatabase': 1,
                'rescanstartup': 0,
                'animations': 1
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
            "type": "bool",
            "title": "Simplify Interface For Smaller Screens",
            "desc": "Removes some components of the interface.  Intended for phones or touch screen devices.",
            "section": "Settings",
            "key": "simpleinterface"
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
            "title": "Low Memory Mode",
            "desc": "For Older Computers That Show Larger Images As Black, Displays All Images At A Smaller Size.",
            "section": "Settings",
            "key": "lowmem"
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

    def on_start(self):
        """Function called when the app is first started.
        Add a custom keyboard hook so key buttons can be intercepted.
        """

        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        if not self.has_database():
            self.open_settings()
        self.database_auto_rescan_timer = float(self.config.get("Settings", "autoscan"))
        self.database_auto_rescanner = Clock.schedule_interval(self.database_auto_rescan, 60)
        self.rescale_interface(force=True)
        Window.bind(on_draw=self.rescale_interface)

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
            if scancode == 27:  #Escape
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

        preset = {'title': 'Import Preset '+str(len(self.imports)+1), 'import_to': '', 'naming_method': naming_method_default, 'delete_originals': False, 'single_folder': False, 'import_from': []}
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
                    self.albums.append({'name': album_name, 'description': album_description, 'file': item, 'photos': photos})
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
            message: Show an app message stating the photo was removed.
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
                if preset_name == 'Automatic':
                    preset = {'name': 'Automatic',
                              'file_format': 'auto',
                              'video_codec': '',
                              'audio_codec': '',
                              'resize': False,
                              'width': '',
                              'height': '',
                              'video_bitrate': '',
                              'audio_bitrate': '',
                              'encoding_speed': '',
                              'deinterlace': False,
                              'command_line': ''}
                    self.encoding_presets.append(preset)
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
                #kivy bugs out on the first refresh on kivy older than 1.11, so skip it if on that version
                if kivy_version_primary <= 1 and kivy_version_secondary < 11:
                    return
            if desktop:
                button_multiplier = 1
            else:
                button_multiplier = 2
            self.button_scale = int((Window.height / interface_multiplier) * int(self.config.get("Settings", "buttonsize")) / 100) * button_multiplier
            self.padding = self.button_scale / 4
            self.text_scale = int((self.button_scale / 3) * int(self.config.get("Settings", "textsize")) / 100)
            Clock.schedule_once(self.show_database)

    def set_transition(self):
        if self.animations:
            self.screen_manager.transition = SlideTransition()
        else:
            self.screen_manager.transition = NoTransition()

    def build(self):
        """Called when the app starts.  Load and set up all variables, data, and screens."""

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
        self.animations = to_bool(self.config.get("Settings", "animations"))
        self.set_transition()
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
        self.database_restore_screen = DatabaseRestoreScreen(name='database_restore')

        #Set up keyboard catchers
        Window.bind(on_key_down=self.key_down)
        Window.bind(on_key_up=self.key_up)
        if self.config.getboolean("Settings", "rescanstartup"):
            self.database_import()
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
            message: Display an app message that the file was deleted.
        """

        photoinfo = self.database_exists(fullpath)
        if os.path.isfile(filename):
            deleted = self.delete_file(filename)
        else:
            deleted = True
        if deleted is True:
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

    def database_get_folders(self, database_folder=False, quick=False):
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
        walk = os.walk
        for root, dirs, files in walk(folder, topdown=True):
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

        #Iterate all files, check if in database, add if needed.
        for index, file_info in enumerate(files):
            if self.cancel_scanning:
                break
            extension = os.path.splitext(file_info[0])[1].lower()
            if extension in imagetypes or extension in movietypes:
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
                    refreshed = self.refresh_photo(file_info[0], no_photoinfo=True, data=exists, skip_isfile=True)
                    if refreshed:
                        update_folders.append(refreshed[1])

            self.database_update_text = 'Rescanning Database ('+str(int(90*(float(index+1)/float(total))))+'%)'
        self.photos.commit()

        #Update folders
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
            self.database_clean()
            self.database_update_text = "Database scanned "+str(total)+" files"

        self.update_photoinfo(folders=update_folders)
        if self.cancel_scanning:
            self.database_update_text = "Canceled database update."
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
        self.folders.execute("UPDATE folders SET Title = ?, Description = ? WHERE Path = ?", (title, description, renamed_path, ))

    def show_database(self, *_):
        """Switch to the database screen layout."""

        self.clear_drags()
        if 'database' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.database_screen)
        if self.animations:
            self.screen_manager.transition.direction = 'right'
        self.screen_manager.current = 'database'

    def show_collage(self):
        """Switch to the create collage screen layout.
        """

        self.clear_drags()
        if 'collage' not in self.screen_manager.screen_names:
            from screencollage import CollageScreen
            self.screen_manager.add_widget(CollageScreen(name='collage'))
        self.type = self.database_screen.type
        self.target = self.database_screen.selected
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'collage'

    def show_album(self, button=None):
        """Switch to the album screen layout.
        Argument:
            button: Optional, the widget that called this function. Allows the function to get a specific album to view.
        """

        self.clear_drags()
        if 'album' not in self.screen_manager.screen_names:
            from screenalbum import AlbumScreen
            self.screen_manager.add_widget(AlbumScreen(name='album'))
        if self.animations:
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

        self.clear_drags()
        if 'import' not in self.screen_manager.screen_names:
            from screenimporting import ImportScreen, ImportingScreen
            self.importing_screen = ImportingScreen(name='importing')
            self.screen_manager.add_widget(ImportScreen(name='import'))
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'import'

    def show_importing(self):
        """Switch to the photo import screen layout."""

        self.clear_drags()
        if 'importing' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(self.importing_screen)
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'importing'

    def show_export(self):
        """Switch to the photo export screen layout."""

        self.clear_drags()
        if 'export' not in self.screen_manager.screen_names:
            from screenexporting import ExportScreen
            self.screen_manager.add_widget(ExportScreen(name='export'))
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'export'

    def show_transfer(self):
        """Switches to the database transfer screen layout"""

        self.clear_drags()
        if 'transfer' not in self.screen_manager.screen_names:
            self.screen_manager.add_widget(TransferScreen(name='transfer'))
        if self.animations:
            self.screen_manager.transition.direction = 'left'
        self.screen_manager.current = 'transfer'

    def popup_message(self, text, title='Notification'):
        """Creates a simple 'ok' popup dialog.
        Arguments:
            text: String, text that the dialog will display
            title: String, the dialog window title.
        """

        app = App.get_running_app()
        content = MessagePopup(text=text)
        self.popup = NormalPopup(title=title, content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
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
            self.screen_manager.current_screen.drop_widget(self.drag_image.fullpath, position, dropped_type='file', aspect=self.drag_image.image_ratio)

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
            self.drag_image.width = drag_object.children[0].width
            self.drag_image.height = drag_object.height
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
