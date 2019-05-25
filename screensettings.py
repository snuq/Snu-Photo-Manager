from kivy.app import App
from kivy.clock import Clock
from kivy.uix.settings import Settings, SettingItem
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView

from generalcommands import agnostic_path
from generalelements import NormalPopup, ShortLabel, NormalButton, RecycleItem
from filebrowser import FileBrowser

from kivy.lang.builder import Builder
Builder.load_string("""
<SettingAboutButton>:
    WideButton:
        text: "About Snu Photo Manager"
        size: root.size
        pos: root.pos
        font_size: '15sp'
        on_press: app.about()

<SettingMultiDirectory>:
    id: multidirectory
    Label:
        text: root.value or ''
        pos: root.pos
        disabled: app.database_scanning
        font_size: '15sp'

<SettingDatabaseImport>:
    WideButton:
        text: 'Import/Rescan Database'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: app.database_scanning
        on_press: root.database_import()

<SettingDatabaseClean>:
    WideButton:
        text: 'Deep Clean Database'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: app.database_scanning
        on_press: root.database_clean()

<SettingDatabaseRestore>:
    WideButton:
        text: 'Restore Database Backup'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        on_press: root.database_restore()

<SettingDatabaseBackup>:
    WideButton:
        text: 'Backup Photo Database'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: app.database_scanning
        on_press: root.database_backup()

<FolderSettingsItem>:
    deselected_color: 0, 0, 0, 1
    selected_color: 0, 0, 1, 1

<FolderSettingsList>:
    viewclass: 'SimpleRecycleItem'
    SelectableRecycleBoxLayout:

<AboutPopup>:
    background: 'data/panelbg.png'
    size_hint: .5, None
    height: self.width/2
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            Image:
                source: 'data/icon.png'
                size_hint_x: None
                size_hint_y: 1
                width: self.height
            Scroller:
                do_scroll_x: False
                ShortLabel:
                    size_hint_y: None
                    height: self.texture_size[1] + 20
                    text: app.about_text
        WideButton:
            id: button
            text: root.button_text
            on_release: root.close()

""")


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
        if app.database_scanning:
            return
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
        buttons = BoxLayout(orientation='horizontal', size_hint=(1, None), height=app.button_scale)
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


class FolderSettingsItem(RecycleItem):
    """A Folder item displayed in a folder list popup dialog."""
    pass


class FolderSettingsList(RecycleView):
    pass


class AboutPopup(Popup):
    """Basic popup message with a message and 'ok' button."""

    button_text = StringProperty('OK')

    def close(self, *_):
        app = App.get_running_app()
        app.popup.dismiss()
