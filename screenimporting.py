import os
import datetime
from shutil import copy2
import time
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.treeview import TreeViewNode
try:
    from shutil import disk_usage
except:
    disk_usage = None

from generalcommands import local_path, list_files, format_size, naming, get_file_info, offset_file_time
from generalelements import NormalPopup, ScanningPopup, NormalLabel, InputPopup, TreeViewButton, NormalDropDown, MenuButton, ExpandableButton
from filebrowser import FileBrowser
from generalconstants import *

from kivy.lang.builder import Builder
Builder.load_string("""
<ImportScreen>:
    canvas.before:
        Color:
            rgba: app.theme.background
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        MainHeader:
            NormalButton:
                text: 'Back To Library'
                on_release: root.back()
            HeaderLabel:
                text: 'Import Photos'
            InfoLabel:
            DatabaseLabel:
            InfoButton:
            SettingsButton:
        BoxLayout:
            orientation: 'horizontal'
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: .75
                Header:
                    size_hint_y: None
                    height: app.button_scale
                    NormalLabel:
                        text: 'Import From:'
                    NormalButton:
                        id: newPresetButton
                        disabled: True
                        text: 'New Preset'
                        on_release: root.add_preset()
                MainArea:
                    Scroller:
                        id: presetsContainer
                        do_scroll_x: False
                        GridLayout:
                            height: self.minimum_height
                            size_hint_y: None
                            cols: 1
                            id: presets

            LargeBufferX:
            StackLayout:
                size_hint_x: .25 if root.show_naming else 0
                opacity: 1 if root.show_naming else 0
                Scroller:
                    size_hint_y: 1
                    GridLayout:
                        size_hint_y: None
                        height: self.minimum_height
                        cols: 1
                        NormalLabel:
                            text_size: self.width, None
                            height: self.texture_size[1]
                            text: 'Naming Method Details\\n\\nYou may type in an import folder template into this field, the folder names will be generated from the template.  The following characters are not allowed: . \\ / : * ? < > | \\nEncase the title and surrounding characters in < > to hide the surrounding characters if the title is not set.  "Folder< - %t>" would result in "Folder" if Title is not set.\\n\\nThe following keys will be replaced in the input to create a folder name:'
                        GridLayout:
                            cols: 3
                            size_hint_y: None
                            size_hint_y: 1
                            height: (app.button_scale * 11)
                            ShortLabel:
                                text: '%Y'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Full Year (2016)'

                            ShortLabel:
                                text: '%y'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Year Decade Digits (16)'

                            ShortLabel:
                                text: '%B'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Full Month Name (January)'

                            ShortLabel:
                                text: '%b'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Month In 3 Letters (Jan)'

                            ShortLabel:
                                text: '%M'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Month In 2 Digits (01)'

                            ShortLabel:
                                text: '%m'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Month In Digits, No Padding (1)'

                            ShortLabel:
                                text: '%D'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Day Of Month In 2 Digits (04)'

                            ShortLabel:
                                text: '%d'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Day Of Month, No Padding (4)'

                            ShortLabel:
                                text: '%T'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Folder Title (My Pictures)'

                            ShortLabel:
                                text: '%t'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Folder Title With Underscores (My_Pictures)'

                            ShortLabel:
                                text: '%%'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Percent Sign (%)'

<ImportingScreen>:
    canvas.before:
        Color:
            rgba: app.theme.background
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        MainHeader:
            NormalButton:
                text: 'Back To Library'
                on_release: root.back()
            MediumBufferX:
            NormalButton:
                text: 'Import Photos'
                on_release: root.finalize_import()
            MediumBufferX:
            ShortLabel:
                id: totalSize
                text: ''
            MediumBufferX:
            NormalToggle:
                state: 'down' if root.delete_originals == True else 'normal'
                text: 'Delete Original Photos' if root.delete_originals else 'Dont Delete Original Photos'
                on_press: root.set_delete_originals(self.state)
            HeaderLabel:
                text: 'Import Photos'
            InfoLabel:
            DatabaseLabel:
            InfoButton:
            SettingsButton:
        MainArea:
            orientation: 'horizontal'
            SplitterPanelLeft:
                id: leftpanel
                #width: app.leftpanel_width
                BoxLayout:
                    orientation: 'vertical'
                    Header:
                        size_hint_y: None
                        height: app.button_scale
                        NormalLabel:
                            text: 'Folders:'
                        NormalButton:
                            text: 'Delete'
                            on_release: root.delete_folder()
                            warn: True
                        NormalButton:
                            text: 'New'
                            on_release: root.add_folder()
                    BoxLayout:
                        Scroller:
                            id: foldersContainer
                            do_scroll_x: True
                            NormalTreeView:
                                id: folders
                    Header:
                        size_hint_y: None
                        height: app.button_scale
                        NormalLabel:
                            text: 'File Date Offset:'
                        FloatInput:
                            hint_text: "Hours"
                            text: root.timezone_offset
                            on_text: root.timezone_offset = self.text
            BoxLayout:
                orientation: 'vertical'
                Header:
                    ShortLabel:
                        text: 'Current Photos In:'
                    NormalLabel:
                        id: folderName
                        text: ''
                    LargeBufferX:
                    NormalButton:
                        text: 'Toggle Select'
                        on_release: root.toggle_select()
                    NormalButton:
                        id: deleteButton
                        text: 'Remove Selected'
                        disabled: True
                        warn: True
                        on_release: root.delete()
                Header:
                    id: folderDetails
                    BoxLayout:
                        size_hint_x: 0.5
                        ShortLabel:
                            text: 'Title:'
                        NormalInput:
                            disabled: True
                            id: folderTitle
                            input_filter: app.test_album
                            multiline: False
                            text: ''
                            on_text: root.new_title(self)
                    SmallBufferX:
                    BoxLayout:
                        ShortLabel:
                            text: 'Description:'
                        NormalInput:
                            disabled: True
                            id: folderDescription
                            input_filter: app.test_description
                            multiline: True
                            text: ''
                            on_text: root.new_description(self)
                NormalRecycleView:
                    id: photosContainer
                    viewclass: 'PhotoRecycleThumbWide'
                    SelectableRecycleGridWide:
                        id: photos

<ImportPresetArea>:
    cols: 1 if app.simple_interface else 2
    size_hint_y: None
    padding: app.padding
    spacing: app.padding, 0
    height: (app.button_scale * (13 if app.simple_interface else 7))+(app.padding*2)
    GridLayout:
        cols: 2
        spacing: app.padding, 0
        size_hint_y: None
        height: app.button_scale * 6
        GridLayout:
            cols: 1
            size_hint_x: None
            size_hint_y: None
            width: self.minimum_width
            height: app.button_scale * 6
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Preset Name: '
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Folder Name: '
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Naming Method:  '
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Adjust File Date Hours: '
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Delete Originals: '
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Import To: '
            NormalLabel:
                size_hint_x: None
                width: self.texture_size[0]
                text: 'Database: '

        GridLayout:
            cols: 1
            size_hint_y: None
            height: app.button_scale * 6
            NormalInput:
                size_hint_x: 1
                text: root.title
                multiline: False
                input_filter: app.test_album
                on_focus: root.set_title(self)
            NormalLabel:
                text: root.naming_example
            NormalInput:
                size_hint_x: 1
                text: root.naming_method
                multiline: False
                input_filter: root.test_naming_method
                on_focus: root.new_naming_method(self)
            FloatInput:
                size_hint_x: 1
                text: root.timezone_offset
                hint_text: 'Hours'
                multiline: False
                on_focus: root.set_timezone_offset(self)
            NormalToggle:
                size_hint_x: 1
                state: 'down' if root.delete_originals == True else 'normal'
                text: str(root.delete_originals)
                on_press: root.set_delete_originals(self.state)
            MenuStarterButtonWide:
                size_hint_x: 1
                text: root.import_to_folder_friendly[root.single_folder]
                on_release: root.import_to_folder_dropdown.open(self)
            MenuStarterButtonWide:
                id: importToButton
                size_hint_x: 1
                text: root.import_to
                on_release: root.imports_dropdown.open(self)
    BoxLayout:
        size_hint_y: None
        height: app.button_scale * 6
        orientation: 'vertical'
        NormalLabel:
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            text: 'Import From Folders:'
        Scroller:
            size_hint_y: None
            height: app.button_scale * 4
            NormalTreeView:
                size_hint_y: None
                height: app.button_scale * 4
                id: importPresetFolders
                hide_root: True
                root_options: {'text': 'Import From Folders:', 'font_size':app.text_scale}
        WideButton:
            text: 'Add Folder...'
            on_release: root.add_folder()

<ImportPresetFolder>:
    orientation: 'horizontal'
    size_hint_y: None
    height: app.button_scale
    NormalLabel:
        text: root.folder
    RemoveButton:
        id: importPresetFolderRemove
        on_release: root.remove_folder()
""")


class ImportScreen(Screen):
    """Screen layout for beginning the import photos process.
    Displays import presets and allows the user to pick one.
    """

    popup = None
    selected_import = NumericProperty(-1)
    show_naming = BooleanProperty(False)

    def back(self, *_):
        app = App.get_running_app()
        app.show_database()
        return True

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
        app.importing_screen.timezone_offset = preset['timezone_offset']
        app.importing_screen.import_index = self.selected_import
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
        app.clear_drags()
        app.import_preset_write()
        presets = self.ids['presets']
        presets.clear_widgets()

    def on_enter(self):
        """Called on entering the screen, updates the treeview and variables."""

        self.show_naming = False
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

    import_index = NumericProperty(0)  #Index of the import preset being used
    type = StringProperty('')
    selected = StringProperty('')
    import_to = StringProperty('')
    naming_method = StringProperty('')
    delete_originals = BooleanProperty(False)
    single_folder = StringProperty('formatted')
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
    timezone_offset = StringProperty('')

    def back(self, *_):
        app = App.get_running_app()
        app.show_database()
        return True

    def rescale_screen(self):
        app = App.get_running_app()
        self.ids['leftpanel'].width = app.left_panel_width()

    def get_selected_photos(self, fullpath=False):
        photos = self.ids['photos']
        photos_container = self.ids['photosContainer']
        selected_indexes = photos.selected_nodes
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

    def date_to_folder(self, date_info):
        """Generates a string from a date in the format YYYYMMDD."""

        folder = str(date_info.year)+str(date_info.month).zfill(2)+str(date_info.day).zfill(2)
        return folder

    def on_leave(self, *_):
        app = App.get_running_app()
        app.clear_drags()
        if app.imports[self.import_index]['timezone_offset'] != self.timezone_offset:
            app.imports[self.import_index]['timezone_offset'] = self.timezone_offset
            app.import_preset_write()

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
        self.cancel_scanning = False
        self.scanningpopup = ScanningPopup(title='Scanning Import Folders...', auto_dismiss=False, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
        self.scanningpopup.open()
        scanning_button = self.scanningpopup.ids['scanningButton']
        scanning_button.bind(on_release=self.cancel_import)

        self.percent_completed = 0
        self.scanningthread = threading.Thread(target=self.scan_folders)
        self.import_scanning = True
        self.scanningthread.start()
        self.start_time = time.time()

    def scan_folders(self, *_):
        """Function that scans the import folders for valid files to import and populates all dialogs."""

        app = App.get_running_app()
        current_timestamp = time.time()

        #Scan the folders
        for folder in self.import_from:
            if os.path.isdir(folder):
                files = list_files(folder)
                for file_info in files:
                    #update popup
                    if self.cancel_scanning:
                        self.scanning_canceled()
                        return
                    self.percent_completed = self.percent_completed + 1
                    if self.percent_completed > 100:
                        self.percent_completed = 0
                    self.scanningpopup.scanning_percentage = self.percent_completed

                    extension = os.path.splitext(file_info[0])[1].lower()
                    if extension in app.imagetypes or extension in app.movietypes:
                        photo_info = get_file_info(file_info, import_mode=True)
                        is_in_database = app.in_database(photo_info)
                        if not is_in_database:
                            is_in_imported = app.in_imported(photo_info)
                            if not is_in_imported:
                                #Non-imported file encountered
                                self.total_size = self.total_size+photo_info[4]
                                self.import_photos.append(photo_info)
                                if self.single_folder == 'single':
                                    date = current_timestamp
                                else:
                                    date = photo_info[3]
                                date_info = datetime.datetime.fromtimestamp(date)
                                foldername = self.date_to_folder(date_info)
                                year = str(date_info.year)
                                month = str(date_info.month).zfill(2)
                                if self.single_folder == 'year':
                                    parent = year
                                    folderdate = os.path.join(parent, foldername)
                                    if year not in self.folders:
                                        self.folders[year] = {'name': year, 'naming': False, 'title': '', 'description': '', 'year': date_info.year, 'month': date_info.month, 'day': date_info.day, 'photos': [], 'parent': ''}
                                elif self.single_folder == 'month':
                                    parent = os.path.join(year, month)
                                    folderdate = os.path.join(parent, foldername)
                                    if year not in self.folders:
                                        self.folders[year] = {'name': year, 'naming': False, 'title': '', 'description': '', 'year': date_info.year, 'month': date_info.month, 'day': date_info.day, 'photos': [], 'parent': ''}
                                    if parent not in self.folders:
                                        self.folders[parent] = {'name': month, 'naming': False, 'title': '', 'description': '', 'year': date_info.year, 'month': date_info.month, 'day': date_info.day, 'photos': [], 'parent': year}
                                else:
                                    folderdate = foldername
                                    parent = ''
                                if folderdate not in self.folders:
                                    self.folders[folderdate] = {'name': foldername, 'naming': True, 'title': '', 'description': '', 'year': date_info.year, 'month': date_info.month, 'day': date_info.day, 'photos': [], 'parent': parent}
                                self.folders[folderdate]['photos'].append(photo_info)
                            else:
                                self.duplicates.append(photo_info)
                        else:
                            self.duplicates.append(photo_info)
        self.scanningpopup.dismiss()
        self.scanningpopup = None
        self.scanningpopup = None
        self.import_scanning = False
        Clock.schedule_once(self.scanning_completed)

    def scanning_completed(self, *_):
        self.update_treeview()
        self.update_photolist()

    def scanning_canceled(self):
        app = App.get_running_app()
        app.message("Canceled import scanning.")
        self.scanningpopup.dismiss()
        self.scanningpopup = None
        self.import_scanning = False
        Clock.schedule_once(lambda *dt: app.show_database())

    def cancel_import(self, unknown=False):
        """Cancel the import process."""
        self.cancel_scanning = True

    def finalize_import(self):
        """Begin the final stage of the import - copying files."""

        app = App.get_running_app()

        #Create popup to show importing progress
        self.cancel_scanning = False
        self.scanningpopup = ScanningPopup(title='Importing Files', auto_dismiss=False, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
        self.scanningpopup.open()
        scanning_button = self.scanningpopup.ids['scanningButton']
        scanning_button.bind(on_release=self.cancel_import)

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

        if disk_usage:
            free_space = disk_usage(import_to)[2]
            if total_size > free_space:
                self.scanningpopup.dismiss()
                self.scanningpopup = None
                app.message("Not enough free drive space! Cancelled import.")
                Clock.schedule_once(lambda *dt: app.show_import())

        #Scan folders
        for folder_path in folders:
            if self.cancel_scanning:
                break
            folder = folders[folder_path]
            folder_name = folder['name']
            if folder['photos']:
                if folder['naming']:
                    folder_name = naming(self.naming_method, title=folder['title'], year=folder['year'], month=folder['month'], day=folder['day'])
                photos = folder['photos']
                parent = folder['parent']
                if parent:
                    path_string = []
                    while parent:
                        newfolder = folders[parent]
                        newfolder_name = newfolder['name']
                        if newfolder['naming']:
                            newfolder_name = naming(self.naming_method, title=newfolder['title'], year=newfolder['year'], month=newfolder['month'], day=newfolder['day'])
                        path_string.append(newfolder_name)
                        parent = newfolder['parent']
                    for path in path_string:
                        folder_name = os.path.join(path, folder_name)
                if '%T' in self.naming_method:
                    title = ''
                else:
                    title = folder['title']
                folderinfo = [folder_name, title, folder['description']]
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
                            try:
                                timezone_offset = float(self.timezone_offset)
                            except:
                                timezone_offset = 0.0
                            if timezone_offset:
                                new_cre, new_mod = offset_file_time(new_full_filename, timezone_offset)
                                photo[3] = new_mod
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
                """
                imported_folders.append(folder_name)
        """
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
        self.popup = NormalPopup(title='Create Folder', content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4), auto_dismiss=False)
        self.popup.open()

    def add_folder_answer(self, instance, answer):
        """Confirm adding the folder.
        Arguments:
            instance: Dialog that called this function.
            answer: String, if set to 'yes', folder is created.
        """

        app = App.get_running_app()
        if answer == 'yes':
            text = instance.ids['input'].text.strip(' ')
            if text:
                if self.type == 'extra':
                    root = ''
                else:
                    root = self.selected
                path = os.path.join(root, text)
                if path not in self.folders:
                    self.folders[path] = {'name': text, 'parent': root, 'naming': False, 'title': '', 'description': '', 'year': 0, 'month': 0, 'day': 0, 'photos': []}
                else:
                    app.message("Folder already exists.")

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
        photos.toggle_select()
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
            folder_item = TreeViewButton(is_open=True, fullpath=target, dragable=True, target=target, type='folder', owner=self, view_album=False)
            if folder_info['naming']:
                folder_item.folder_name = naming(self.naming_method, title=folder_info['title'], year=folder_info['year'], month=folder_info['month'], day=folder_info['day'])
            else:
                folder_item.folder_name = folder_info['name']
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
            folder_name.text = naming(self.naming_method, title=folder_info['title'], year=folder_info['year'], month=folder_info['month'], day=folder_info['day'])

    def update_photolist(self):
        """Redraw the photo list view for the currently selected folder."""

        app = App.get_running_app()
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
                    name = naming(self.naming_method, title=folder_info['title'], year=folder_info['year'], month=folder_info['month'], day=folder_info['day'])
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
            video = os.path.splitext(full_filename)[1].lower() in app.movietypes
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

    def drop_widget(self, fullpath, position, dropped_type='file', aspect=1):
        """Called when a widget is dropped after being dragged.
        Determines what to do with the widget based on where it is dropped.
        Arguments:
            fullpath: String, file location of the object being dragged.
            position: List of X,Y window coordinates that the widget is dropped on.
            dropped_type: String, describes the object being dropped.  May be: 'folder' or 'file'
        """

        app = App.get_running_app()
        folder_list = self.ids['folders']
        folder_container = self.ids['foldersContainer']
        if folder_container.collide_point(position[0], position[1]):
            offset_x, offset_y = folder_list.to_widget(position[0], position[1])
            for widget in folder_list.children:
                if widget.collide_point(position[0], offset_y) and widget.type != 'None' and self.type != 'None' and not (widget.target == 'duplicates' and widget.type == 'extra'):

                    if dropped_type == 'folder':
                        #Dropped a folder
                        dropped_data = self.folders[fullpath]
                        new_path = os.path.join(widget.fullpath, dropped_data['name'])
                        if widget.fullpath != fullpath:
                            #this was actually a drag and not a long click
                            if new_path not in self.folders:
                                #this folder can be dropped here
                                old_parent = fullpath
                                dropped_data['parent'] = widget.fullpath
                                self.folders[new_path] = dropped_data
                                del self.folders[fullpath]

                                new_folders = {}
                                #rename child folders
                                for folder in self.folders:
                                    folder_info = self.folders[folder]
                                    parent = folder_info['parent']
                                    if old_parent and folder.startswith(old_parent):
                                        new_folder_path = new_path + folder[len(old_parent):]
                                        new_parent = new_path + parent[len(old_parent):]
                                        folder_info['parent'] = new_parent
                                        new_folders[new_folder_path] = folder_info
                                    else:
                                        new_folders[folder] = folder_info

                                self.folders = new_folders
                                self.update_treeview()
                                self.update_photolist()
                            else:
                                app.message("Invalid folder location.")
                    elif dropped_type == 'file':
                        #Dropped a file
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
                    break

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

    def dismiss_popup(self, *_):
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


class ImportPresetArea(GridLayout):
    """Widget to display and edit all settings for a particular import preset."""

    title = StringProperty()
    import_to = StringProperty('')
    naming_method = StringProperty('')
    last_naming_method = StringProperty('')
    delete_originals = BooleanProperty(False)
    single_folder = StringProperty('formatted')
    preset_index = NumericProperty()
    naming_example = StringProperty('Naming Example')
    owner = ObjectProperty()
    import_from = ListProperty()
    index = NumericProperty()
    import_to_folder_friendly = {'single': 'All One Folder', 'formatted': 'Date Formatted Subfolders', 'year': 'Yearly Dated Subfolders', 'month': 'Year and Month Subfolders'}
    timezone_offset = StringProperty()

    def __init__(self, **kwargs):
        super(ImportPresetArea, self).__init__(**kwargs)
        app = App.get_running_app()
        self.import_to_folder_dropdown = NormalDropDown()
        self.import_to_folder_dropdown.basic_animation = True
        for import_to_folder in self.import_to_folder_friendly.values():
            menu_button = MenuButton(text=import_to_folder)
            menu_button.bind(on_release=self.change_import_to_folder)
            self.import_to_folder_dropdown.add_widget(menu_button)
        self.imports_dropdown = NormalDropDown()
        self.imports_dropdown.basic_animation = True
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
        Clock.schedule_once(self.update_import_from)

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
        import_preset['timezone_offset'] = self.timezone_offset
        app.imports[self.index] = import_preset
        self.owner.owner.selected_import = self.index

    def set_title(self, instance):
        if not instance.focus:
            self.title = instance.text
            self.update_preset()
            self.owner.data['title'] = instance.text
            self.owner.update_title()

    def set_timezone_offset(self, instance):
        if not instance.focus:
            self.timezone_offset = instance.text
            self.update_preset()
            self.owner.data['timezone_offset'] = instance.text

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
        self.owner.data['import_from'] = self.import_from
        self.owner.update_title()

    def change_import_to_folder(self, instance):
        self.import_to_folder_dropdown.dismiss()
        for setting, value in self.import_to_folder_friendly.items():
            if value == instance.text:
                self.single_folder = setting
                self.update_preset()
                return

    def change_import_to(self, instance):
        self.imports_dropdown.dismiss()
        self.import_to = instance.text
        self.update_preset()

    def add_folder(self):
        app = App.get_running_app()
        content = FileBrowser(ok_text='Add', path=app.last_browse_folder, directory_select=True)
        content.bind(on_cancel=self.owner.owner.dismiss_popup)
        content.bind(on_ok=self.add_folder_confirm)
        self.owner.owner.popup = filepopup = NormalPopup(title='Select A Folder To Import From', content=content, size_hint=(0.9, 0.9))
        filepopup.open()

    def add_folder_confirm(self, *_):
        popup = self.owner.owner.popup
        if popup:
            app = App.get_running_app()
            app.last_browse_folder = popup.content.path
            folder = popup.content.path
            self.import_from.append(folder)
            self.owner.owner.dismiss_popup()
            self.update_preset()
            self.update_import_from()
            self.owner.data['import_from'] = self.import_from
            self.owner.update_title()

    def update_import_from(self, *_):
        preset_folders = self.ids['importPresetFolders']
        nodes = list(preset_folders.iterate_all_nodes())
        for node in nodes:
            preset_folders.remove_node(node)
        for index, folder in enumerate(self.import_from):
            preset_folders.add_node(ImportPresetFolder(folder=folder, owner=self, index=index))
        #self.update_preset()


class ImportPreset(ExpandableButton):
    data = DictProperty()
    owner = ObjectProperty()
    import_to = StringProperty('')

    def on_expanded(self, *_):
        self.owner.show_naming = True
        super().on_expanded()

    def on_data(self, *_):
        import_preset = self.data
        naming_method = import_preset['naming_method']
        self.content = ImportPresetArea(index=self.index, title=import_preset['title'], import_to=import_preset['import_to'], naming_method=naming_method, naming_example=naming(naming_method), last_naming_method=naming_method, single_folder=import_preset['single_folder'], delete_originals=import_preset['delete_originals'], import_from=import_preset['import_from'], timezone_offset=import_preset['timezone_offset'], owner=self)
        self.update_title()

    def update_title(self, *_):
        if self.data['import_from']:
            import_from_text = ' (Import From: ' + ', '.join(self.data['import_from']) + ')'
        else:
            import_from_text = ' (Import From: None)'
        self.text = self.data['title'] + import_from_text

    def on_remove(self):
        app = App.get_running_app()
        app.import_preset_remove(self.index)
        self.owner.selected_import = -1
        self.owner.update_treeview()

    def on_release(self):
        self.owner.selected_import = self.index
        self.owner.import_preset()


class ImportPresetFolder(ButtonBehavior, BoxLayout, TreeViewNode):
    """TreeView widget to display a folder scanned on the import process."""

    folder = StringProperty()
    index = NumericProperty()
    owner = ObjectProperty()

    def remove_folder(self):
        self.owner.remove_folder(self.index)
