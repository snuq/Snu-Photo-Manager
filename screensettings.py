from kivy.app import App
from kivy.clock import Clock
from kivy.uix.settings import SettingsWithNoMenu, SettingItem, SettingTitle, SettingSpacer
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.compat import string_types, text_type

from generalcommands import agnostic_path
from generalelements import NormalPopup, InputPopup, ShortLabel, NormalButton, WideButton, RecycleItem
from filebrowser import FileBrowser

from kivy.lang.builder import Builder
Builder.load_string("""
<-SettingsPanel>:
    spacing: 5
    #padding: 150, 0, 150, 0
    size_hint_y: None
    height: self.minimum_height

<-Settings>:
    canvas.before:
        Color:
            rgba: app.theme.background
        Rectangle:
            size: root.size
            pos: root.pos
        Color:
            rgba: app.theme.main_background
        Rectangle:
            size: root.size
            pos: root.pos
            source: 'data/mainbg.png'
    orientation: 'vertical'
    MainHeader:
        NormalButton:
            text: 'Close Settings'
            on_release: app.close_settings()
        HeaderLabel:
            text: "Settings"
        InfoLabel:
        DatabaseLabel:


<-SettingItem>:
    size_hint: .25, None
    height: labellayout.texture_size[1] + dp(10)
    content: content

    BoxLayout:
        pos: root.pos
        Widget:
            size_hint_x: .2
        BoxLayout:
            canvas:
                Color:
                    rgba: 47 / 255., 167 / 255., 212 / 255., root.selected_alpha
                Rectangle:
                    pos: self.x, self.y + 1
                    size: self.size
                Color:
                    rgb: .2, .2, .2
                Rectangle:
                    pos: self.x, self.y - 2
                    size: self.width, 1
            Label:
                size_hint_x: .66
                id: labellayout
                markup: True
                text: u"{0}\\n[size=13sp]{1}[/size]".format(root.title or "", root.desc or "")
                font_size: '15sp'
                text_size: self.width - 32, None
                color: app.theme.text
            BoxLayout:
                id: content
                size_hint_x: .33
        Widget:
            size_hint_x: .2

<-SettingTitle>:
    size_hint_y: None
    height: max(dp(20), self.texture_size[1] + dp(40))
    color: (.9, .9, .9, 1)
    font_size: '15sp'
    canvas:
        Color:
            rgba: .15, .15, .15, .5
        Rectangle:
            pos: self.x, self.y + 2
            size: self.width, self.height - 2
        Color:
            rgb: .2, .2, .2
        Rectangle:
            pos: self.x, self.y - 2
            size: self.width, 1
    Label:
        size_hint: None, None
        size: root.size
        color: app.theme.text
        text: root.title
        text_size: self.size
        halign: 'left'
        valign: 'bottom'
        pos: root.pos
        font_size: '15sp'

<SettingAboutButton>:
    WideButton:
        text: "About Snu Photo Manager"
        size: root.size
        pos: root.pos
        font_size: '15sp'
        on_release: app.about()

<SettingMultiDirectory>:
    id: multidirectory
    Label:
        color: app.theme.text
        text: root.value or ''
        pos: root.pos
        disabled: app.database_scanning
        font_size: '15sp'

<SettingsThemeButton>:
    WideButton:
        text: 'Theme Settings'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        on_release: root.show_theme()

<SettingDatabaseImport>:
    WideButton:
        text: 'Import/Rescan Database'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: True if app.database_scanning or app.standalone else False
        on_release: root.database_import()

<SettingDatabaseClean>:
    WideButton:
        text: 'Deep Clean Database'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: True if app.database_scanning or app.standalone else False
        on_release: root.database_clean()

<SettingDatabaseRestore>:
    WideButton:
        text: 'Restore Database Backup'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: True if app.database_scanning or app.standalone else False
        on_release: root.database_restore()

<SettingDatabaseBackup>:
    WideButton:
        text: 'Backup Photo Database'
        size: root.size
        pos: root.pos
        font_size: '15sp'
        disabled: True if app.database_scanning or app.standalone else False
        on_release: root.database_backup()

<FolderSettingsItem>:
    deselected_color: 0, 0, 0, 1
    selected_color: 0, 0, 1, 1

<FolderSettingsList>:
    viewclass: 'SimpleRecycleItem'
    SelectableRecycleBoxLayout:

<AboutPopup>:
    canvas.before:
        Color:
            rgba: 0, 0, 0, .75 * self._anim_alpha
        Rectangle:
            size: self._window.size if self._window else (0, 0)
        Color:
            rgba: app.theme.sidebar_background
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/panelbg.png'
    overlay_color: 1, 1, 1, 0
    background_color: 1, 1, 1, 0
    background: 'data/transparent.png'
    separator_color: 1, 1, 1, .25
    title_size: app.text_scale * 1.25
    title_color: app.theme.header_text
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

<SettingString>:
    size_hint_y: None
    Label:
        text: root.value or ''
        pos: root.pos
        font_size: '15sp'
        color: app.theme.text

<SettingBoolean>:
    true_text: 'On'
    false_text: 'Off'
    size_hint_y: None
    NormalToggle:
        size_hint_x: 1
        state: 'normal' if root.value == '0' else 'down'
        on_press: root.value = '0' if self.state == 'normal' else '1'
        text: root.true_text if root.value == '1' else root.false_text
    #Switch:
    #    text: 'Boolean'
    #    pos: root.pos
    #    active: bool(root.values.index(root.value)) if root.value in root.values else False
    #    on_active: root.value = root.values[int(args[1])]
""")


class SettingString(SettingItem):
    popup = ObjectProperty(None, allownone=True)
    textinput = ObjectProperty(None)

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

    def dismiss(self, *largs):
        if self.popup:
            self.popup.dismiss()
        app = App.get_running_app()
        if app.popup:
            app.popup = None
        self.popup = None

    def _validate(self, instance, answer):
        value = self.popup.content.ids['input'].text.strip()
        self.dismiss()
        if answer == 'yes':
            self.value = value

    def _create_popup(self, instance):
        content = InputPopup(text='', input_text=self.value)
        app = App.get_running_app()
        content.bind(on_answer=self._validate)
        self.popup = NormalPopup(title=self.title, content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 5), auto_dismiss=True)
        app = App.get_running_app()
        app.popup = self.popup
        self.popup.open()


class SettingNumeric(SettingString):
    def _validate(self, instance, answer):
        # we know the type just by checking if there is a '.' in the original value
        is_float = '.' in str(self.value)
        value = self.popup.content.ids['input'].text
        self.dismiss()
        if answer == 'yes':
            try:
                if is_float:
                    self.value = text_type(float(value))
                else:
                    self.value = text_type(int(value))
            except ValueError:
                return


class PhotoManagerSettings(SettingsWithNoMenu):
    """Expanded settings class to add new settings buttons and types."""

    def __init__(self, **kwargs):
        super(PhotoManagerSettings, self).__init__(**kwargs)
        self.register_type('string', SettingString)
        self.register_type('numeric', SettingNumeric)
        self.register_type('multidirectory', SettingMultiDirectory)
        self.register_type('themescreen', SettingsThemeButton)
        self.register_type('databaseimport', SettingDatabaseImport)
        self.register_type('databaseclean', SettingDatabaseClean)
        self.register_type('aboutbutton', SettingAboutButton)
        self.register_type('databaserestore', SettingDatabaseRestore)
        self.register_type('databasebackup', SettingDatabaseBackup)
        self.register_type('label', SettingTitle)


class SettingAboutButton(SettingItem):
    """Widget that opens an about dialog."""
    pass


class SettingsThemeButton(SettingItem):
    """Widget that opens the theme screen"""
    def show_theme(self):
        app = App.get_running_app()
        app.close_settings()
        app.show_theme()


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
            self.folderlist = folderlist = FolderSettingsList(size_hint=(1, .8))
            folderlist.data = folderdata
            content.add_widget(folderlist)
        buttons = BoxLayout(orientation='horizontal', size_hint=(1, None), height=app.button_scale)
        addbutton = NormalButton(text='+')
        addbutton.bind(on_release=self.add_path)
        removebutton = NormalButton(text='-')
        removebutton.bind(on_release=self.remove_path)
        okbutton = WideButton(text='OK')
        okbutton.bind(on_release=self._dismiss)
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
        app = App.get_running_app()
        content = FileBrowser(ok_text='Add', path=app.last_browse_folder, directory_select=True)
        content.bind(on_cancel=self.filepopup_dismiss)
        content.bind(on_ok=self.add_directory)
        self.filepopup = filepopup = NormalPopup(title=self.title, content=content, size_hint=(0.9, 0.9))
        filepopup.open()

    def filepopup_dismiss(self, *_):
        if self.filepopup:
            self.filepopup.dismiss()
        self.filepopup = None

    def add_directory(self, *_):
        if self.filepopup:
            app = App.get_running_app()
            app.last_browse_folder = self.filepopup.content.path
            self.modified = True
            all_folders = self.value.split(';')
            all_folders.append(agnostic_path(self.filepopup.content.path))
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
