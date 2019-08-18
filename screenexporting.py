import os
from PIL import Image
import datetime
from shutil import copy2
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage
from io import BytesIO
import threading

from generalconstants import *
from generalelements import AlbumSortDropDown, ScanningPopup, NormalDropDown, MenuButton, NormalPopup, ExpandableButton
from generalcommands import to_bool
from filebrowser import FileBrowser

from kivy.lang.builder import Builder
Builder.load_string("""
<ExportScreen>:
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
                on_release: app.show_database()
            MediumBufferX:
            HeaderLabel:
                text: 'Export Photos'
            InfoLabel:
            DatabaseLabel:
            SettingsButton:
        BoxLayout:
            orientation: 'horizontal'
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: .5
                Header:
                    NormalLabel:
                        text: 'Select An Export Preset:'
                    NormalButton:
                        id: newPresetButton
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
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: .5
                Header:
                    MediumBufferX:
                    LeftNormalLabel:
                        text: 'Select Photos To Export: ' + root.target
                    MediumBufferX:
                    ShortLabel:
                        text: 'Sort By:'
                    MenuStarterButton:
                        size_hint_x: 1
                        id: sortButton
                        text: root.sort_method
                        on_release: root.sort_dropdown.open(self)
                    ReverseToggle:
                        id: sortReverseButton
                        state: root.sort_reverse_button
                        on_press: root.resort_reverse(self.state)
                    MediumBufferX:
                    NormalButton:
                        text: 'Toggle Select'
                        on_release: root.toggle_select()
                MainArea:
                    NormalRecycleView:
                        id: photosContainer
                        viewclass: 'PhotoRecycleThumb'
                        SelectableRecycleGrid:
                            id: photos

<ExportPresetArea>:
    cols: 1
    height: self.minimum_height
    size_hint: 1, None
    GridLayout:
        height: app.button_scale
        cols: 3
        size_hint_y: None
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            ShortLabel:
                text: 'Title: '
            NormalInput:
                id: titleEditor
                input_filter: app.test_album
                multiline: False
                text: root.name
                on_focus: root.set_title(self)
        MediumBufferX:
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            ShortLabel:
                text: 'Ignore Tags: '
            NormalInput:
                id: ignoreTags
                input_filter: root.test_tags
                multiline: False
                text: root.ignore_tags
                on_focus: root.set_ignore_tags(self)
    GridLayout:
        cols: 3
        size_hint_y: None
        height: app.button_scale
        NormalToggle:
            size_hint_x: 1
            state: 'down' if root.create_subfolder == True else 'normal'
            text: 'Create Subfolder' if root.create_subfolder == True else "Don't Create Subfolder"
            on_press: root.set_create_subfolder(self.state)
        NormalToggle:
            size_hint_x: 1
            state: 'down' if root.export_info == True else 'normal'
            text: 'Export Photo Info' if root.export_info == True else "Don't Export Info"
            on_press: root.set_export_info(self.state)
        NormalToggle:
            size_hint_x: 1
            state: 'down' if root.export_videos == True else 'normal'
            text: 'Export Videos' if root.export_videos == True else "Don't Export Videos"
            on_press: root.set_export_videos(self.state)
    SmallBufferY:

    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        BoxLayout:
            orientation: 'horizontal'
            size_hint_x: 1
            ShortLabel:
                text: 'Export To: '
            NormalToggle:
                toggle: False
                size_hint_x: 1
                id: toggleFolder
                text: 'Folder'
                group: 'exports'
                on_press: root.toggle_exports(self)
                background_normal: 'data/buttontop.png'
                background_down: 'data/buttontop.png'
            NormalToggle:
                toggle: False
                size_hint_x: 1
                id: toggleFTP
                text: 'FTP'
                group: 'exports'
                on_press: root.toggle_exports(self)
                background_normal: 'data/buttontop.png'
                background_down: 'data/buttontop.png'
        BoxLayout:
            size_hint_x: .33

    GridLayout:
        canvas.before:
            Color:
                rgba: app.theme.button_down
            BorderImage:
                size: self.size
                pos: self.pos
                source: 'data/tabbg.png'
        padding: app.padding
        id: toggleSettings
        cols: 1
        size_hint_y: None
        height: self.minimum_height
    SmallBufferY:

    GridLayout:
        cols: 3
        size_hint_y: None
        height: app.button_scale
        NormalToggle:
            toggle: False
            size_hint_x: .33
            state: 'down' if root.scale_image else 'normal'
            text: 'Scale Photo' if root.scale_image else "Don't Scale Photo"
            on_press: root.set_scale_image(self.state)
            background_normal: 'data/button.png'
            background_down: 'data/buttontop.png'
        BoxLayout:
            size_hint_x: .67
    GridLayout:
        cols: 1
        id: scaleSettings
        height: self.minimum_height
        size_hint_y: None
    SmallBufferY:

    GridLayout:
        cols: 3
        size_hint_y: None
        height: app.button_scale
        NormalToggle:
            toggle: False
            size_hint_x: .33
            state: 'down' if root.watermark else 'normal'
            text: 'Use Watermark' if root.watermark else "Don't Use Watermark"
            on_press: root.set_watermark(self.state)
            background_normal: 'data/button.png'
            background_down: 'data/buttontop.png'
        BoxLayout:
            size_hint_x: .67
    GridLayout:
        cols: 1
        id: watermarkSettings
        height: self.minimum_height
        size_hint_y: None

<ScaleSettings>:
    canvas.before:
        Color:
            rgba: app.theme.button_down
        BorderImage:
            size: self.size
            pos: self.pos
            source: 'data/tabbg.png'
    padding: app.padding
    spacing: app.padding, app.padding
    cols: 1 if app.simple_interface else 2
    height: self.minimum_height
    size_hint_y: None
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: 'Scale To Size:'
        NormalInput:
            input_filter: 'int'
            text: str(root.owner.scale_size)
            on_focus: root.owner.set_scale_size(self)
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: 'Scale Size To:'
        MenuStarterButtonWide:
            id: scaleSizeToButton
            size_hint_x: 1
            text: root.owner.scale_size_to_text
            on_release: root.owner.scale_size_to_dropdown.open(self)
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            id: jpegQualityValue
            text: 'Quality: '+str(root.owner.jpeg_quality)+'%'
        NormalSlider:
            size_hint_x: 1
            min: 1
            max: 100
            value: root.owner.jpeg_quality
            on_value: root.owner.set_jpeg_quality(self)

<WatermarkSettings>:
    canvas.before:
        Color:
            rgba: app.theme.button_down
        BorderImage:
            size: self.size
            pos: self.pos
            source: 'data/tabbg.png'
    padding: app.padding
    spacing: app.padding, 0
    cols: 3
    size_hint_y: None
    height: self.minimum_height
    GridLayout:
        cols: 1
        size_hint_x: None
        size_hint_y: None
        width: self.minimum_width
        height: app.button_scale * 5
        NormalLabel:
            size_hint_x: None
            width: self.texture_size[0]
            text: 'Image: '
        NormalLabel:
            size_hint_x: None
            width: self.texture_size[0]
            id: watermarkOpacityValue
            text: 'Opacity: '
        NormalLabel:
            size_hint_x: None
            width: self.texture_size[0]
            id: watermarkHorizontalValue
            text: 'Horizontal:'
        NormalLabel:
            size_hint_x: None
            width: self.texture_size[0]
            id: watermarkVerticalValue
            text: 'Vertical: '
        NormalLabel:
            size_hint_x: None
            width: self.texture_size[0]
            id: watermarkSizeValue
            text: 'Size: '

    GridLayout:
        cols: 1
        size_hint_y: None
        height: app.button_scale * 5
        NormalButton:
            size_hint_x: 1
            text: root.owner.watermark_image
            on_release: root.owner.select_watermark()
        NormalSlider:
            size_hint_x: .5
            min: 0
            max: 100
            value: root.owner.watermark_opacity
            on_value: root.owner.set_watermark_opacity(self)
        NormalSlider:
            size_hint_x: .5
            min: 0
            max: 100
            value: root.owner.watermark_horizontal
            on_value: root.owner.set_watermark_horizontal(self)
        NormalSlider:
            size_hint_x: .5
            min: 0
            max: 100
            value: root.owner.watermark_vertical
            on_value: root.owner.set_watermark_vertical(self)
        NormalSlider:
            size_hint_x: .5
            min: 1
            max: 100
            value: root.owner.watermark_size
            on_value: root.owner.set_watermark_size(self)

    StackLayout:
        orientation: 'tb-lr'
        size_hint_x: 0.5
        FloatLayout:
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    size: self.size
                    pos: self.pos
                    source: 'data/test.png'
            id: testImage
            size_hint_x: 1
            size_hint_y: None
            height: int(self.width * .75)

<FolderToggleSettings>:
    cols: 2
    size_hint_y: None
    height: self.minimum_height
    NormalInput:
        id: exportTo
        input_filter: root.owner.filename_filter
        multiline: False
        text: root.owner.export_folder
        on_focus: root.owner.set_export_folder(self)
    NormalButton:
        text: ' Browse... '
        on_release: root.owner.select_export()

<FTPToggleSettings>:
    size_hint_y: None
    spacing: app.padding, app.padding
    cols: 1 if app.simple_interface else 2
    height: self.minimum_height
    BoxLayout:
        height: app.button_scale
        size_hint_y: None
        orientation: 'horizontal'
        ShortLabel:
            text: 'Server And Folder: '
        NormalInput:
            multiline: False
            text: root.owner.ftp_address
            input_filter: root.owner.ftp_filter
            on_focus: root.owner.set_ftp_address(self)
    BoxLayout:
        height: app.button_scale
        size_hint_y: None
        orientation: 'horizontal'
        NormalToggle:
            size_hint_x: 1
            text: 'Passive Mode' if root.owner.ftp_passive else 'Active Mode'
            state: 'down' if root.owner.ftp_passive else 'normal'
            on_press: root.owner.set_ftp_passive(self)
        BoxLayout:
            orientation: 'horizontal'
            size_hint_x: 1
            ShortLabel:
                text: 'Port: '
            NormalInput:
                multiline: False
                text: str(root.owner.ftp_port)
                input_filter: 'int'
                on_focus: root.owner.set_ftp_port(self)
    BoxLayout:
        height: app.button_scale
        size_hint_y: None
        orientation: 'horizontal'
        ShortLabel:
            text: 'Login: '
        NormalInput:
            multiline: False
            text: root.owner.ftp_user
            on_focus: root.owner.set_ftp_user(self)
    BoxLayout:
        height: app.button_scale
        size_hint_y: None
        orientation: 'horizontal'
        ShortLabel:
            text: 'Password: '
        NormalInput:
            password: True
            multiline: False
            text: root.owner.ftp_password
            on_focus: root.owner.set_ftp_password(self)
""")


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
        photos.toggle_select()
        self.update_selected()

    def select_all(self):
        photos = self.ids['photos']
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

    def update_photolist(self, select=True):
        """Clears and refreshes the grid view of photos."""

        #sort photo list
        if self.sort_method == 'Imported':
            sorted_photos = sorted(self.photos, key=lambda x: x[6], reverse=self.sort_reverse)
        elif self.sort_method == 'Modified':
            sorted_photos = sorted(self.photos, key=lambda x: x[7], reverse=self.sort_reverse)
        elif self.sort_method == 'Owner':
            sorted_photos = sorted(self.photos, key=lambda x: x[11], reverse=self.sort_reverse)
        elif self.sort_method == 'Name':
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
        if select:
            self.select_all()

    def on_leave(self):
        """Called when the screen is left, clean up data."""

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
        self.popup = ScanningPopup(title='Exporting Files', auto_dismiss=False, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
        self.popup.open()
        scanning_button = self.popup.ids['scanningButton']
        scanning_button.bind(on_release=self.cancel_export)
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
                                imagedata = app.edit_add_watermark(imagedata, preset['watermark_image'], preset['watermark_opacity'], preset['watermark_horizontal'], preset['watermark_vertical'], preset['watermark_size'])
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
                            imagedata = app.edit_add_watermark(imagedata, preset['watermark_image'], preset['watermark_opacity'], preset['watermark_horizontal'], preset['watermark_vertical'], preset['watermark_size'])
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
            scanning_button.bind(on_release=self.finish_export)

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
        self.scale_size_to_dropdown.basic_animation = True
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
        self.owner.owner.popup = filepopup = NormalPopup(title='Select Watermark PNG Image', content=content, size_hint=(0.9, 0.9))
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
        self.update_preset()
        self.update_test_image()

    def set_watermark_horizontal(self, instance):
        self.watermark_horizontal = int(instance.value)
        self.update_preset()
        self.update_test_image()

    def set_watermark_vertical(self, instance):
        self.watermark_vertical = int(instance.value)
        self.update_preset()
        self.update_test_image()

    def set_watermark_size(self, instance):
        self.watermark_size = int(instance.value)
        self.update_preset()
        self.update_test_image()

    def set_jpeg_quality(self, instance):
        self.jpeg_quality = int(instance.value)
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
            self.owner.text = instance.text

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
        self.owner.owner.popup = filepopup = NormalPopup(title='Select An Export Folder', content=content, size_hint=(0.9, 0.9))
        filepopup.open()

    def select_export_confirm(self, *_):
        """Called when the export folder select dialog is closed successfully."""

        self.export_folder = self.owner.owner.popup.content.filename
        self.owner.owner.dismiss_popup()
        self.update_preset()


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
                Clock.schedule_once(self.content.update_test_image)
        super(ExportPreset, self).on_expanded()

    def on_remove(self):
        app = App.get_running_app()
        app.export_preset_remove(self.index)
        self.owner.selected_preset = -1
        self.owner.update_treeview()

    def on_release(self):
        self.owner.selected_preset = self.index
        self.owner.export()


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
