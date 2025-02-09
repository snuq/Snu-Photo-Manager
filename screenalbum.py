import sys
import PIL
from PIL import Image, ImageEnhance, ImageOps, ImageChops, ImageDraw, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
from io import BytesIO
import datetime
from shutil import copy2, copystat
import subprocess
import time
from operator import itemgetter
from functools import partial
import multiprocessing
from configparser import ConfigParser

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
from kivy.config import Config
Config.window_icon = "data/icon.png"
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.animation import Animation
from kivy.graphics.transformation import Matrix
from kivy.uix.behaviors import ButtonBehavior, DragBehavior
from kivy.uix.screenmanager import Screen
from kivy.properties import AliasProperty, ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.treeview import TreeViewNode
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.uix.video import Video
from kivy.uix.videoplayer import VideoPlayer
from kivy.core.image.img_pil import ImageLoaderPIL
from kivy.loader import Loader
Loader.max_upload_per_frame = 16
Loader.num_workers = 2
from kivy.cache import Cache
Cache.register('kv.loader', limit=5)
from kivy.graphics import Rectangle, Color, Line
from resizablebehavior import ResizableBehavior
from colorpickercustom import ColorPickerCustom
from kivy.core.video import Video as KivyCoreVideo
from threading import Thread

from generalcommands import find_dictionary, get_keys_from_list, interpolate, agnostic_path, local_path, time_index, format_size, to_bool, isfile2
from filebrowser import FileBrowser
from generalelements import EncodingSettings, ExpandablePanel, ScrollerContainer, CustomImage, ImageEditor, NormalButton, ExpandableButton, ScanningPopup, NormalPopup, ConfirmPopup, LeftNormalLabel, NormalLabel, ShortLabel, NormalDropDown, AlbumSortDropDown, MenuButton, TreeViewButton, RemoveButton, WideButton, RecycleItem, PhotoRecycleViewButton, AlbumExportDropDown
from generalconstants import *

from kivy.lang.builder import Builder
Builder.load_string("""
#:import os os
#:import SlideTransition kivy.uix.screenmanager.SlideTransition
#:import platform kivy.platform
#:import time_index generalcommands.time_index

<AlbumScreen>:
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
                opacity: 0 if app.standalone else 1
                disabled: True if app.standalone else False
            ShortLabel:
                text: app.standalone_text
            HeaderLabel:
                text: root.folder_title
            InfoLabel:
            DatabaseLabel:
            InfoButton:
            SettingsButton:
        BoxLayout:
            orientation: 'horizontal'
            SplitterPanelLeft:
                id: leftpanel
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_x: .25
                    Header:
                        size_hint_y: None
                        height: app.button_scale
                        ShortLabel:
                            text: 'Sort:'
                        MenuStarterButtonWide:
                            id: sortButton
                            text: root.sort_method
                            on_release: root.sort_dropdown.open(self)
                        ReverseToggle:
                            id: sortReverseButton
                            state: root.sort_reverse_button
                            on_release: root.resort_reverse(self.state)
                    PhotoListRecycleView:
                        size_hint: 1, 1
                        id: albumContainer
                        viewclass: 'PhotoRecycleViewButton'
                        scroll_distance: 10
                        scroll_timeout: 200
                        bar_width: int(app.button_scale * .5)
                        bar_color: app.theme.scroller_selected
                        bar_inactive_color: app.theme.scroller
                        scroll_type: ['bars', 'content']
                        SelectableRecycleBoxLayout:
                            id: album
                            default_size: self.width, (app.button_scale * 2)
                    BoxLayout:
                        size_hint_y: None
                        disabled: app.simple_interface
                        opacity: 0 if app.simple_interface else 1
                        height: 0 if app.simple_interface else app.button_scale
                        orientation: 'horizontal'
                        WideButton:
                            text: 'Previous'
                            on_press: root.previous_photo()
                        WideButton:
                            text: 'Next'
                            on_press: root.next_photo()

            MainArea:
                size_hint_x: .5
                orientation: 'vertical'
                RelativeLayout:
                    id: photoViewerContainer
                Header:
                    height: app.button_scale if root.edit_panel == 'main' else 0
                    disabled: False if root.edit_panel == 'main' else True
                    opacity: 1 if root.edit_panel == 'main' else 0
                    id: buttonsFooter
                    NormalButton:
                        size_hint_y: 1
                        text: 'Full Screen'
                        on_press: root.fullscreen()
                    MenuStarterButton:
                        text: 'Export Album'
                        on_release: root.album_exports.open(self)
                    Label:
                        text: ''
                    NormalToggle:
                        size_hint_y: 1
                        text: '  Favorite  '
                        id: favoriteButton
                        state: 'down' if root.favorite else 'normal'
                        on_press: root.set_favorite()
                        opacity: 0 if (app.standalone and not app.standalone_in_database) else 1
                        disabled: True if app.database_scanning or (app.standalone and not app.standalone_in_database) else False
                    NormalButton:
                        size_hint_y: 1
                        text: 'Share File' if (platform == 'android') else 'Open Folder'
                        disabled: True if (platform == 'android' and not root.view_image) else False
                        on_press: root.open_folder()
                    NormalButton:
                        size_hint_y: 1
                        width: self.texture_size[0] + 20 if root.canprint else 0
                        opacity: 1 if root.canprint else 0
                        disabled: not root.canprint
                        id: printButton
                        text: '  Print  '
                        on_release: app.print_photo()
                    NormalButton:
                        size_hint_y: 1
                        id: deleteButton
                        warn: True
                        text: '  Delete  '
                        on_release: root.delete_selected_confirm()
                        disabled: app.database_scanning
            SplitterPanelRight:
                id: rightpanel
                width: 0
                opacity: 0
                PanelTabs:
                    tab: root.view_panel
                    BoxLayout:
                        tab: 'info'
                        opacity: 0
                        orientation: 'vertical'
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        Scroller:
                            NormalTreeView:
                                id: panelInfo
                        WideButton:
                            text: 'Refresh Photo Info'
                            on_release: root.full_photo_refresh()
                    BoxLayout:
                        tab: 'edit'
                        opacity: 0
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        GridLayout:
                            disabled: app.database_scanning
                            id: panelEdit
                            cols: 1
                            size_hint: 1, 1
                    BoxLayout:
                        tab: 'tags'
                        opacity: 0
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        Scroller:
                            size_hint: 1, 1
                            do_scroll_x: False
                            GridLayout:
                                disabled: app.database_scanning
                                size_hint: 1, None
                                cols: 1
                                height: self.minimum_height
                                GridLayout:
                                    canvas.before:
                                        Color:
                                            rgba: app.theme.area_background
                                        BorderImage:
                                            pos: self.pos
                                            size: self.size
                                            source: 'data/buttonflat.png'
                                    padding: app.padding
                                    id: displayTags
                                    cols: 1
                                    size_hint: 1, None
                                    height: self.minimum_height
                                    NormalLabel:
                                        id: albumLabel
                                        text:"Current Tags:"
                                    GridLayout:
                                        id: panelDisplayTags
                                        size_hint: 1, None
                                        cols: 2
                                        height: self.minimum_height
                                MediumBufferY:
                                GridLayout:
                                    canvas.before:
                                        Color:
                                            rgba: app.theme.area_background
                                        BorderImage:
                                            pos: self.pos
                                            size: self.size
                                            source: 'data/buttonflat.png'
                                    padding: app.padding
                                    id: addToTags
                                    cols: 1
                                    size_hint: 1, None
                                    height: self.minimum_height
                                    NormalLabel:
                                        id: albumLabel
                                        text:"Add Tags:"
                                    GridLayout:
                                        id: panelTags
                                        size_hint: 1, None
                                        cols: 2
                                        height: self.minimum_height
                                MediumBufferY:
                                BoxLayout:
                                    canvas.before:
                                        Color:
                                            rgba: app.theme.area_background
                                        BorderImage:
                                            pos: self.pos
                                            size: self.size
                                            source: 'data/buttonflat.png'
                                    padding: app.padding
                                    orientation: 'vertical'
                                    size_hint: 1, None
                                    height: app.button_scale * 2 + app.padding * 2
                                    NormalLabel:
                                        text: "Create Tags:"
                                    BoxLayout:
                                        orientation: 'horizontal'
                                        size_hint: 1, None
                                        height: app.button_scale
                                        NormalInput:
                                            id: newTag
                                            multiline: True
                                            disable_lines: True
                                            hint_text: 'Tag Name'
                                            input_filter: app.test_tag
                                        NormalButton:
                                            disabled: not root.can_add_tag(newTag.text)
                                            text: 'New'
                                            on_release: root.add_tag()
                                            size_hint_y: None
                                            height: app.button_scale
            StackLayout:
                size_hint_x: None
                width: app.button_scale
                VerticalButton:
                    state: 'down' if root.view_panel == 'info' else 'normal'
                    vertical_text: "Photo Info"
                    on_press: root.show_info_panel()
                VerticalButton:
                    state: 'down' if root.view_panel == 'edit' else 'normal'
                    vertical_text: "Editing"
                    on_press: root.show_edit_panel()
                VerticalButton:
                    state: 'down' if root.view_panel == 'tags' else 'normal'
                    vertical_text: "Tags"
                    on_press: root.show_tags_panel()
                    disabled: True if (app.standalone and not app.standalone_in_database) else False
                    opacity: 0 if (app.standalone and not app.standalone_in_database) else 1

<VideoConverterScreen>:
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
                text: 'Back To Album' if not root.from_database else 'Back To Library'
                on_release: root.back()
            ShortLabel:
                text: app.standalone_text
            HeaderLabel:
                text: "Editing "+root.target
            InfoLabel:
            DatabaseLabel:
            InfoButton:
            SettingsButton:
        BoxLayout:
            orientation: 'horizontal'
            MainArea:
                size_hint_x: .5
                orientation: 'vertical'
                Header:
                    NormalToggle:
                        text: '   Batch Conversion   '
                        state: 'down' if root.use_batch else 'normal'
                        on_release: root.use_batch = not root.use_batch
                    NormalToggle:
                        text: '   Replace/Add Audio   '
                        state: 'down' if root.use_audio else 'normal'
                        on_release: root.use_audio = not root.use_audio
                        disabled: root.use_batch
                    NormalToggle:
                        text: '   Use Custom Command   '
                        state: 'down' if root.use_command else 'normal'
                        on_release: root.use_command = not root.use_command
                    NormalLabel:
                    NormalToggle:
                        text: '   Hide Log   ' if root.show_log else '   Show Log   '
                        state: 'down' if root.show_log else 'normal'
                        on_release: root.show_log = not root.show_log
                    NormalButton:
                        text: 'Browse Export Folder'
                        on_release: root.browse_export_folder()
                        disabled: root.export_folder == ''
                    #NormalButton:
                    #    text: 'Test Conversion Settings'
                    NormalButton:
                        text: 'Convert Videos' if root.use_batch else 'Convert Video'
                        disabled: False if (root.photo or (root.use_batch and root.batch_list)) else True
                        on_release: root.save_edit()
                ExpandablePanel:
                    expanded: not root.use_batch
                    Header:
                        ShortLabel:
                            text: "File: "
                        NormalInput:
                            disabled: True
                            text: root.photo
                        NormalButton:
                            text: 'Load Video...'
                            on_release: root.load_video_begin()
                        NormalButton:
                            text: 'Load Image Sequence...'
                            on_release: root.load_video_begin(image=True)
                Header:
                    ShortLabel:
                        text: "Export To: "
                    NormalInput:
                        id: exportInput
                        hint_text: root.photo if not root.use_batch else ''
                        multiline: False
                        text: root.export_file
                        on_text: root.export_file = self.text
                    NormalButton:
                        text: 'Select File... '
                        on_release: root.browse_export_begin()
                ExpandablePanel:
                    id: addAudioPanel
                    expanded: root.use_audio and not root.use_batch
                    disabled: True
                    Header:
                        ShortLabel:
                            text: "Replace Audio With: "
                        NormalInput:
                            id: audioInput
                            hint_text: "Path\\To\\Audio File.wav"
                            multiline: False
                            text: root.audio_file
                            on_text: root.audio_file = self.text
                        NormalButton:
                            text: 'Select File... '
                            on_release: root.load_audio_begin()
                ExpandablePanel:
                    id: customCommandPanel
                    expanded: root.use_command
                    disabled: True
                    Header:
                        ShortLabel:
                            text: "Manual Command: ffmpeg.exe "
                        NormalInput:
                            id: commandInput
                            hint_text: '-sn %c %v %a %f %p %b %d'
                            multiline: False
                            text: app.encoding_settings.command_line
                            on_text: app.encoding_settings.command_line = self.text
                BoxLayout:
                    orientation: 'horizontal'
                    ScreenManager:
                        transition: SlideTransition(direction='down', duration=app.animation_length)
                        current: root.photo_viewer_current
                        size_hint: 1, 1
                        Screen:
                            name: 'edit'
                            RelativeLayout:
                                size_hint: 1, 1
                                id: photoViewerContainer
                        Screen:
                            name: 'batch'
                            BoxLayout:
                                orientation: 'vertical'
                                Header:
                                    size_hint_y: None
                                    height: app.button_scale
                                    WideButton:
                                        text: 'Add Videos...'
                                        on_release: root.add_batch()
                                    WideButton:
                                        text: 'Remove Selected'
                                        on_release: root.remove_selected_batch()
                                        disabled: not photos.selects
                                    WideButton:
                                        text: 'Remove Completed'
                                        on_release: root.remove_completed_batch()
                                    WideButton:
                                        text: 'Clear All'
                                        on_release: root.clear_batch()
                                        disabled: not root.batch_list
                                PhotoListRecycleView:
                                    canvas.before:
                                        Color:
                                            rgba: app.theme.sidebar_background
                                        Rectangle:
                                            size: self.size
                                            pos: self.pos
                                            source: 'data/panelbg.png'
                                    scroll_distance: 10
                                    scroll_timeout: 200
                                    bar_width: int(app.button_scale * .5)
                                    bar_color: app.theme.scroller_selected
                                    bar_inactive_color: app.theme.scroller
                                    scroll_type: ['bars', 'content']
                                    data: root.batch_list
                                    id: photosContainer
                                    viewclass: 'BatchPhoto'
                                    SelectableRecycleBoxLayout:
                                        default_size: self.width, None
                                        multiselect: True
                                        id: photos
                    BoxLayout:
                        disabled: not root.show_log
                        opacity: 1 if root.show_log else 0
                        size_hint_x: .66 if root.show_log else 0
                        size_hint_y: 1
                        GridLayout:
                            cols: 1
                            size_hint_y: 1
                            id: extra
                            BoxLayout:
                                orientation: 'horizontal'
                                size_hint_y: None
                                height: app.button_scale
                                LeftNormalLabel:
                                    text: 'Conversion Log:'
                                NormalButton:
                                    text: 'Clear Log'
                                    on_release: root.clear_log()
                            NormalRecycleView:
                                id: logviewerscroller
                                size_hint: 1, 1
                                data: root.encode_log
                                viewclass: 'RecycleLabel'
                                RecycleBoxLayout:
                                    default_size: None, app.text_scale
                                    default_size_hint: 1, None
                                    orientation: 'vertical'
                                    size_hint_x: 1
                                    size_hint_y: None
                                    height: self.minimum_height
            SplitterPanelRight:
                id: rightpanel
                width: app.right_panel_width()
                PanelTabs:
                    size_hint_y: 1
                    tab: root.view_panel
                    BoxLayout:
                        tab: 'conversion'
                        opacity: 0
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        EditPanelVideo:
                            size_hint_y: 1
                            owner: root
                            advanced: True
                            name: 'video'
                    BoxLayout:
                        tab: 'info'
                        opacity: 0
                        orientation: 'vertical'
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        Scroller:
                            NormalTreeView:
                                id: panelInfo
                        WideButton:
                            text: 'Refresh Video Info'
                            on_release: root.refresh_photoinfo()
                    BoxLayout:
                        tab: 'edit'
                        opacity: 0
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        GridLayout:
                            id: panelEdit
                            cols: 1
                            size_hint: 1, 1
            StackLayout:
                size_hint_x: None
                width: app.button_scale
                VerticalButton:
                    state: 'down' if root.view_panel == 'conversion' else 'normal'
                    vertical_text: "Conversion"
                    on_press: root.show_conversion_panel()
                VerticalButton:
                    state: 'down' if root.view_panel == 'info' else 'normal'
                    vertical_text: "Video Info"
                    on_press: root.show_info_panel()
                    disabled: root.use_batch
                VerticalButton:
                    state: 'down' if root.view_panel == 'edit' else 'normal'
                    vertical_text: "Editing"
                    on_press: root.show_edit_panel()
                    disabled: not root.photo

<TreeViewInfo>:
    color_selected: app.selected_color
    odd_color: app.list_background_odd
    even_color: app.list_background_even
    size_hint_y: None
    height: app.button_scale
    orientation: 'horizontal'
    LeftNormalLabel:
        text: root.title

<VideoThumbnail>:
    pos_hint: {'x': 0, 'y': 0}
    image_overlay_play: 'atlas://data/images/defaulttheme/player-play-overlay'
    image_loading: 'data/images/image-loading.gif'
    AsyncThumbnail:
        photoinfo: root.photoinfo
        loadfullsize: False
        fit_mode: 'contain'
        mipmap: True
        source: root.source
        color: (.5, .5, .5, 1)
        pos_hint: {'x': 0, 'y': 0}
    Image:
        source: root.image_overlay_play if not root.click_done else root.image_loading
        pos_hint: {'x': 0, 'y': 0}

<PhotoViewer>:
    orientation: 'vertical'
    StencilViewTouch:
        size_hint_y: 1
        canvas.after:
            Color:
                rgba: app.theme.favorite if root.favorite else [0, 0, 0, 0]
            Rectangle:
                source: 'data/star.png'
                pos: self.width - (self.width*.03), 0
                size: (self.width*.03, self.width*.03)
        id: photoStencil
        LimitedScatterLayout:
            bypass: root.bypass
            id: wrapper
            size: photoStencil.size
            size_hint: None, None
            scale_min: 1
            scale_max: root.scale_max
            do_rotation: False
            PhotoShow:
                bypass: root.bypass
                id: photoShow
                pos: photoStencil.pos
                size_hint: 1, 1
                AsyncThumbnail:
                    canvas.before:
                        PushMatrix
                        Scale:
                            x: 1 if (root.angle == 0 or root.angle == 180) or self.width == 0 else ((self.height/self.width) if (self.height/self.width) > .75 else .75)
                            y: 1 if (root.angle == 0 or root.angle == 180) or self.width == 0 else ((self.height/self.width) if (self.height/self.width) > .75 else .75)
                            origin: photoStencil.center
                    canvas.after:
                        PopMatrix
                    photoinfo: root.photoinfo
                    loadanyway: True
                    loadfullsize: True
                    source: root.file
                    mirror: root.mirror
                    fit_mode: 'contain'
                    id: image
                    mipmap: True
    BoxLayout:
        opacity: 0 if root.fullscreen or app.simple_interface or root.edit_mode != 'main' else 1
        disabled: True if root.fullscreen or (root.edit_mode != 'main') or app.simple_interface else False
        orientation: 'horizontal'
        size_hint_y: None
        height: 0 if  root.fullscreen or app.simple_interface or root.edit_mode != 'main' else app.button_scale
        Label:
            size_hint_x: .25
        ShortLabel:
            size_hint_y: None
            height: app.button_scale
            text: "Zoom:"
        NormalSlider:
            size_hint_y: None
            height: app.button_scale
            id: zoomSlider
            min: 0
            max: 1
            value: root.zoom
            on_value: root.zoom = self.value
            reset_value: root.reset_zoom
        Label:
            size_hint_x: .25

<-SpecialVideoPlayer>:
    container: container
    cols: 1
    FloatLayout:
        cols: 1
        id: container
    GridLayout:
        rows: 1
        size_hint_y: None
        height: app.button_scale
        VideoPlayerStop:
            size_hint_x: None
            video: root
            width: '44dp'
            source: root.image_stop
            fit_mode: "contain"
        VideoPlayerPlayPause:
            size_hint_x: None
            video: root
            width: '44dp'
            source: root.image_pause if root.state == 'play' else root.image_play
            fit_mode: "contain"
        VideoPlayerVolume:
            video: root
            size_hint_x: None
            width: '44dp'
            source: root.image_volumehigh if root.volume > 0.8 else (root.image_volumemedium if root.volume > 0.4 else (root.image_volumelow if root.volume > 0 else root.image_volumemuted))
            fit_mode: "contain"
        Widget:
            size_hint_x: None
            width: 5
        VideoPlayerProgressBar:
            video: root
            max: max(root.duration, root.position, 1)
            value: root.position
        Widget:
            size_hint_x: None
            width: 10
        ShortLabel:
            text: time_index(root.position, 2)+'/'+time_index(root.duration, 2)

<VideoViewer>:
    SpecialVideoPlayer:
        canvas.after:
            Color:
                rgba: app.theme.favorite if root.favorite else [0, 0, 0, 0]
            Rectangle:
                source: 'data/star.png'
                pos: self.width - (self.width*.03), 44
                size: (self.width*.03, self.width*.03)
        disabled: True if self.opacity == 0 else False
        pos: root.pos
        size: root.size
        id: player
        favorite: root.favorite
        photoinfo: root.photoinfo
        source: root.file
        options: {'fit_mode': 'contain'}
    BoxLayout:
        orientation: 'vertical'
        opacity: 0
        id: overlay
        pos: root.pos
        size: root.size
        RelativeLayout:
            id: photoShow
            height: root.height - 44 - app.button_scale
            width: root.width
            size_hint: None, None
        BoxLayout:
            size_hint: None, None
            height: app.button_scale
            orientation: 'horizontal'
            width: root.width
            NormalButton:
                text: 'Set Start Point'
                on_release: root.set_start_point()
            NormalButton:
                text: 'Clear Start Point'
                warn: True
                on_release: root.reset_start_point()
            Label:
                size_hint_x: 1
            NormalButton:
                text: 'Clear End Point'
                warn: True
                on_release: root.reset_end_point()
            NormalButton:
                text: 'Set End Point'
                on_release: root.set_end_point()
        FloatLayout:
            width: root.width
            size_hint: None, None
            height: app.button_scale
            HalfSliderLimited:
                size_hint: 1, 1
                pos: self.parent.pos
                disabled: True if self.parent.opacity == 0 else False
                value: root.position
                start: root.start_point
                end: root.end_point
                on_value: root.position = self.value
            ShortLabel:
                text: root.position_time_index
                pos: (self.parent.pos[0] + (self.parent.width * root.position - (self.width * root.position)), self.parent.pos[1])

<ExitFullscreenButton>:
    text: 'Back'

<EditPanelConvert>:
    orientation: 'vertical'
    GridLayout:
        size_hint: 1, None
        cols: 1
        height: self.minimum_height
        WideButton:
            text: "Clear All Edits"
            on_release: root.reset_all()
        BoxLayout:
            canvas.before:
                Color:
                    rgba:0,0,0,1
                Rectangle:
                    size: self.size
                    pos: self.pos
            size_hint_y: None
            height: self.width * .5
            Image:
                id: histogram
                fit_mode: 'fill'
                opacity: 0
        SmallBufferY:
    ScreenManager:
        id: sm
        on_current: root.change_screen(self.current)

<EditPanel>:
    orientation: 'vertical'
    GridLayout:
        size_hint: 1, None
        cols: 1
        height: self.minimum_height
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            WideButton:
                text: 'Confirm Edit'
                on_release: root.confirm_edit()
            WideButton:
                text: 'Cancel Edit'
                warn: True
                on_release: root.cancel_edit()
        WideButton:
            id: loadLast
            disabled: not root.owner.edit_color
            text: "Load Last Settings"
            on_release: root.load_last()
        BoxLayout:
            canvas.before:
                Color:
                    rgba:0,0,0,1
                Rectangle:
                    size: self.size
                    pos: self.pos
            size_hint_y: None
            height: self.width * .5
            Image:
                id: histogram
                fit_mode: 'fill'
                opacity: 0
        SmallBufferY:
    ScreenManager:
        id: sm
        on_current: root.change_screen(self.current)

<EditPanelConversionBase>:
    name: 'edit'
    ScrollerContainer:
        cols: 1
        do_scroll_x: False
        GridLayout:
            size_hint: 1, None
            cols: 1
            height: self.minimum_height
            WideButton:
                text: 'Color Adjustments'
                on_release: root.manager.current = 'color'
            SmallBufferY:
            WideButton:
                text: 'Filters'
                on_release: root.manager.current = 'filter'
            SmallBufferY:
            WideButton:
                text: 'Image Borders'
                on_release: root.manager.current = 'border'
            SmallBufferY:
            WideButton:
                height: app.button_scale if app.opencv else 0
                opacity: 1 if app.opencv else 0
                text: 'Denoise'
                on_release: root.manager.current = 'denoise'
                disabled: not app.opencv
            SmallBufferY:
                height: int(app.button_scale / 4) if app.opencv else 0
            WideButton:
                text: 'Rotate'
                on_release: root.manager.current = 'rotate'
            SmallBufferY:
            WideButton:
                text: 'Crop'
                on_release: root.manager.current = 'crop'

<EditPanelAlbumBase>:
    name: 'edit'
    ScrollerContainer:
        cols: 1
        do_scroll_x: False
        GridLayout:
            size_hint: 1, None
            cols: 1
            height: self.minimum_height
            padding: 0, 0, int(app.button_scale / 2), 0
            WideButton:
                text: 'Advanced Video Editing'
                on_release: app.show_video_converter()
                disabled: root.owner.owner.view_image or not app.ffmpeg
                opacity: 0 if self.disabled else 1
                height: 0 if self.disabled else app.button_scale
            SmallBufferY:
                height: 0 if (root.owner.owner.view_image or not app.ffmpeg) else (app.button_scale / 4)
            WideButton:
                text: 'Video Convert Settings'
                on_release: root.manager.current = 'video'
                disabled: root.owner.owner.view_image or not app.ffmpeg
                height: 0 if (root.owner.owner.view_image or not app.ffmpeg) else app.button_scale
                opacity: 0 if (root.owner.owner.view_image or not app.ffmpeg) else 1
            SmallBufferY:
            WideButton:
                text: 'Color Adjustments'
                on_release: root.manager.current = 'color'
                disabled: not root.owner.owner.view_image and not app.ffmpeg
            SmallBufferY:
            WideButton:
                text: 'Filters'
                on_release: root.manager.current = 'filter'
                disabled: not root.owner.owner.view_image and not app.ffmpeg
            SmallBufferY:
            WideButton:
                text: 'Image Borders'
                on_release: root.manager.current = 'border'
                disabled: not root.owner.owner.view_image and not app.ffmpeg
            SmallBufferY:
            WideButton:
                height: app.button_scale if app.opencv else 0
                opacity: 1 if app.opencv else 0
                text: 'Denoise'
                on_release: root.manager.current = 'denoise'
                disabled: (not root.owner.owner.view_image and not app.ffmpeg) or not app.opencv
            SmallBufferY:
                height: int(app.button_scale / 4) if app.opencv else 0
            WideButton:
                text: 'Rotate'
                on_release: root.manager.current = 'rotate'
                disabled: not root.owner.owner.view_image and not app.ffmpeg
            SmallBufferY:
            WideButton:
                text: 'Crop'
                on_release: root.manager.current = 'crop'
                disabled: not root.owner.owner.view_image and not app.ffmpeg
            MediumBufferY:
            WideButton:
                id: deleteOriginal
                text: 'Delete Unedited Original File'
                disabled: True
                warn: True
                on_release: root.owner.owner.delete_original()
            SmallBufferY:
            WideButton:
                id: deleteOriginalAll
                disabled: True
                text: 'Delete All Originals In Folder'
                warn: True
                on_release: root.owner.owner.delete_original_all()
            SmallBufferY:
            WideButton:
                id: undoEdits
                disabled: True
                text: 'Restore Original Unedited File'
                on_release: root.owner.owner.restore_original()
            MediumBufferY:
            GridLayout:
                cols: 2
                disabled: True if platform == 'android' else False
                size_hint_y: None
                height: 0 if self.disabled else app.button_scale
                opacity: 0 if self.disabled else 1
                LeftNormalLabel:
                    size_hint_x: 1
                    text: 'External Programs:'
                NormalButton:
                    size_hint_x: None
                    text: 'New'
                    on_release: root.add_program()
            GridLayout:
                id: externalPrograms
                height: self.minimum_height
                size_hint_y: None
                cols: 1

<EditPanelColor>:
    name: 'color'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
        SmallBufferY:
        ScrollerContainer:
            cols: 1
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Color Adjustments:'
                    NormalButton:
                        text: 'Reset All'
                        on_release: root.reset()
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale if not self.disabled else 0
                    disabled: root.image.video
                    opacity: 0 if self.disabled else 1
                    NormalToggle:
                        text: "Auto Contrast"
                        id: autocontrastToggle
                        state: 'down' if root.image.autocontrast else 'normal'
                        on_state: root.update_autocontrast(self.state)
                        size_hint_x: 1
                SmallBufferY:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale if app.opencv else 0
                    disabled: not app.opencv
                    opacity: 1 if app.opencv else 0
                    LeftNormalLabel:
                        text: 'Adaptive Histogram Equalize:'
                    NormalButton:
                        text: 'Reset'
                        on_release: root.reset_adaptive()
                HalfSlider:
                    disabled: not app.opencv
                    opacity: 1 if app.opencv else 0
                    height: app.button_scale if app.opencv else 0
                    value: root.image.adaptive_clip
                    on_value: root.image.adaptive_clip = self.value
                    reset_value: root.reset_adaptive
                SmallBufferY:
                    height: int(app.button_scale / 4) if app.opencv else 0
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: "Brightness Addition:"
                    NormalButton:
                        text: "Reset"
                        on_release: root.reset_slide()
                HalfSlider:
                    value: root.image.slide
                    on_value: root.image.slide = self.value
                    reset_value: root.reset_slide
                SmallBufferY:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Highs:'
                    NormalButton:
                        text: 'Reset'
                        on_release: root.reset_brightness()
                NormalSlider:
                    value: root.image.brightness
                    on_value: root.image.brightness = self.value
                    reset_value: root.reset_brightness
                SmallBufferY:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Mids:'
                    NormalButton:
                        text: 'Reset'
                        on_release: root.reset_gamma()
                NormalSlider:
                    value: root.image.gamma
                    on_value: root.image.gamma = self.value
                    reset_value: root.reset_gamma
                SmallBufferY:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Lows:'
                    NormalButton:
                        text: 'Reset'
                        on_release: root.reset_shadow()
                NormalSlider:
                    value: root.image.shadow
                    on_value: root.image.shadow = self.value
                    reset_value: root.reset_shadow
                SmallBufferY:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Color Temperature:'
                    NormalButton:
                        text: 'Reset'
                        on_release: root.reset_temperature()
                NormalSlider:
                    value: root.image.temperature
                    on_value: root.image.temperature = self.value
                    reset_value: root.reset_temperature
                SmallBufferY:
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Saturation:'
                    NormalButton:
                        text: 'Reset'
                        on_release: root.reset_saturation()
                NormalSlider:
                    value: root.image.saturation
                    on_value: root.image.saturation = self.value
                    reset_value: root.reset_saturation
                SmallBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Curves:'
                        NormalButton:
                            text: 'Remove Point'
                            on_release: root.remove_point()
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_curves()
                    BoxLayout:
                        size_hint_y: None
                        height: self.width * .66
                        Curves:
                            owner: root
                            id: curves
                SmallBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Tinting:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_tint()
                    BoxLayout:
                        size_hint_y: None
                        height: sp(33)*10
                        ColorPickerCustom:
                            id: tint
                            color: root.image.tint
                            on_color: root.image.tint = self.color

<EditPanelFilter>:
    name: 'filter'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
        SmallBufferY:
        ScrollerContainer:
            cols: 1
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Filter Image:'
                    NormalButton:
                        text: 'Reset All'
                        on_release: root.reset()
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Soften/Sharpen:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_sharpen()
                    NormalSlider:
                        value: root.image.sharpen
                        on_value: root.image.sharpen = self.value
                        reset_value: root.reset_sharpen
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale if app.opencv else 0
                        opacity: 1 if app.opencv else 0
                        LeftNormalLabel:
                            text: 'Median Blur (Despeckle):'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_median()
                            disabled: not app.opencv
                    HalfSlider:
                        height: app.button_scale if app.opencv else 0
                        opacity: 1 if app.opencv else 0
                        value: root.image.median_blur
                        on_value: root.image.median_blur = self.value
                        disabled: not app.opencv
                        reset_value: root.reset_median
                MediumBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height if app.opencv else 0
                    disabled: not app.opencv
                    opacity: 1 if app.opencv else 0
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Edge-Preserve Blur:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_bilateral_amount()
                    HalfSlider:
                        value: root.image.bilateral_amount
                        on_value: root.image.bilateral_amount = self.value
                        reset_value: root.reset_bilateral_amount
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Blur Size:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_bilateral()
                    HalfSlider:
                        value: root.image.bilateral
                        on_value: root.image.bilateral = self.value
                        reset_value: root.reset_bilateral
                MediumBufferY:
                    height: int(app.button_scale / 2) if app.opencv else 0
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Vignette:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_vignette_amount()
                    HalfSlider:
                        value: root.owner.image.vignette_amount
                        on_value: root.image.vignette_amount = self.value
                        reset_value: root.reset_vignette_amount
                    SmallBufferY:
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Size:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_vignette_size()
                    HalfSlider:
                        value: root.image.vignette_size
                        on_value: root.image.vignette_size = self.value
                        reset_value: root.reset_vignette_size
                MediumBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Edge Blur:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_edge_blur_amount()
                    HalfSlider:
                        value: root.image.edge_blur_amount
                        on_value: root.image.edge_blur_amount = self.value
                        reset_value: root.reset_edge_blur_amount
                    SmallBufferY:
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Size:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_edge_blur_size()
                    HalfSlider:
                        value: root.image.edge_blur_size
                        on_value: root.image.edge_blur_size = self.value
                        reset_value: root.reset_edge_blur_size
                    SmallBufferY:
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Intensity:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_edge_blur_intensity()
                    HalfSlider:
                        value: root.image.edge_blur_intensity
                        on_value: root.image.edge_blur_intensity = self.value
                        reset_value: root.reset_edge_blur_intensity

<EditPanelBorder>:
    name: 'border'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
        SmallBufferY:
        ScrollerContainer:
            cols: 1
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Border Overlays:'
                    NormalButton:
                        text: 'Reset All'
                        on_release: root.reset()
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Border Opacity:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_border_opacity()
                    HalfSlider:
                        value: root.image.border_opacity
                        on_value: root.image.border_opacity = self.value
                        reset_value: root.reset_border_opacity
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'X Size:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_border_x_scale()
                    NormalSlider:
                        value: root.image.border_x_scale
                        on_value: root.image.border_x_scale = self.value
                        reset_value: root.reset_border_x_scale
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Y Size:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_border_y_scale()
                    NormalSlider:
                        value: root.image.border_y_scale
                        on_value: root.image.border_y_scale = self.value
                        reset_value: root.reset_border_y_scale
                    SmallBufferY:
                    LeftNormalLabel:
                        text: 'Select A Border:'
                        height: app.button_scale
                        size_hint_y: None
                    BoxLayout:
                        canvas.before:
                            Color:
                                rgba: app.theme.area_background
                            BorderImage:
                                pos: self.pos
                                size: self.size
                                source: 'data/buttonflat.png'
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: int(app.button_scale * 10)
                        Scroller:
                            id: wrapper
                            NormalTreeView:
                                id: borders
                SmallBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Border Tinting:'
                        NormalButton:
                            text: 'Reset'
                            on_release: root.reset_border_tint()
                    BoxLayout:
                        size_hint_y: None
                        height: sp(33)*10
                        ColorPickerCustom:
                            color: root.image.border_tint
                            on_color: root.image.border_tint = self.color

<EditPanelDenoise>:
    name: 'denoise'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
        SmallBufferY:
        ScrollerContainer:
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Denoise Image:'
                    NormalButton:
                        text: 'Reset All'
                        on_release: root.reset()
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    NormalToggle:
                        text: 'Use Denoise'
                        state: 'down' if root.image.denoise else 'normal'
                        on_state: root.update_denoise(self.state)
                        size_hint_x: 1
                    FloatLayout:
                        canvas.before:
                            Color:
                                rgba:0,0,0,1
                            Rectangle:
                                size: self.size
                                pos: self.pos
                        size_hint_y: None
                        height: self.width
                        ScrollViewCentered:
                            canvas.after:
                                Color:
                                    rgba: self.bar_color[:3] + [self.bar_color[3] * 1 if self.do_scroll_y else 0]
                                Rectangle:
                                    pos: self.right - self.bar_width - self.bar_margin, self.y + self.height * self.vbar[0]
                                    size: self.bar_width, self.height * self.vbar[1]
                                Color:
                                    rgba: self.bar_color[:3] + [self.bar_color[3] * 1 if self.do_scroll_x else 0]
                                Rectangle:
                                    pos: self.x + self.width * self.hbar[0], self.y + self.bar_margin
                                    size: self.width * self.hbar[1], self.bar_width
                            effect_cls: 'ScrollEffect'
                            on_scroll_stop: root.update_preview()
                            pos: self.parent.pos
                            size: self.parent.size
                            scroll_type: ['bars', 'content']
                            id: wrapper
                            size_hint: 1, 1
                            bar_width: int(app.button_scale * .75)
                            bar_color: app.theme.scroller_selected
                            bar_inactive_color: app.theme.scroller
                            RelativeLayout:
                                owner: root
                                size_hint: None, None
                                size: root.image.original_width, root.image.original_height
                                Image:
                                    fit_mode: 'contain'
                                    size: root.image.original_width, root.image.original_height
                                    size_hint: None, None
                                    id: noisePreview
                                    mipmap: True
                                Image:
                                    id: denoiseOverlay
                                    size: self.parent.parent.size
                                    size_hint: None, None
                                    opacity: 0
    
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        NormalLabel:
                            text: 'Luminance: '
                        IntegerInput:
                            text: root.luminance_denoise
                            on_text: root.luminance_denoise = self.text
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        NormalLabel:
                            text: 'Color: '
                        IntegerInput:
                            text: root.color_denoise
                            on_text: root.color_denoise = self.text
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        NormalLabel:
                            text: 'Search Size: '
                        IntegerInput:
                            text: root.search_window
                            on_text: root.search_window = self.text
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        NormalLabel:
                            text: 'Noise Size: '
                        IntegerInput:
                            text: root.block_size
                            on_text: root.block_size = self.text

<EditPanelRotate>:
    name: 'rotate'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
        SmallBufferY:
        ScrollerContainer:
            cols: 1
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Image Rotation:'
                    NormalButton:
                        text: 'Reset All'
                        on_release: root.reset()
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    GridLayout:
                        cols: 4
                        size_hint_y: None
                        size_hint_x: 1
                        height: app.button_scale
                        NormalToggle:
                            id: angles_0
                            size_hint_x: 1
                            state: 'down'
                            text: '0'
                            group: 'angles'
                            on_press: root.update_angle(0)
                        NormalToggle:
                            id: angles_90
                            size_hint_x: 1
                            text: '90'
                            group: 'angles'
                            on_press: root.update_angle(90)
                        NormalToggle:
                            id: angles_180
                            size_hint_x: 1
                            text: '180'
                            group: 'angles'
                            on_press: root.update_angle(180)
                        NormalToggle:
                            id: angles_270
                            size_hint_x: 1
                            text: '270'
                            group: 'angles'
                            on_press: root.update_angle(270)
                    GridLayout:
                        cols: 2
                        size_hint: 1, None
                        height: app.button_scale
                        NormalToggle:
                            text_size: self.size
                            halign: 'center'
                            valign: 'middle'
                            id: flip_horizontal
                            size_hint_x: 1
                            text: 'Horizontal Flip'
                            on_press: root.update_flip_horizontal(self.state)
                        NormalToggle:
                            text_size: self.size
                            halign: 'center'
                            valign: 'middle'
                            id: flip_vertical
                            size_hint_x: 1
                            text: 'Vertical Flip'
                            on_press: root.update_flip_vertical(self.state)
                MediumBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    NormalLabel:
                        text: 'Fine Rotation:'
                    NormalSlider:
                        id: fine_angle
                        value: root.image.fine_angle
                        on_value: root.image.fine_angle = self.value
                        reset_value: root.reset_fine_angle

<EditPanelCrop>:
    name: 'crop'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
        SmallBufferY:
        ScrollerContainer:
            cols: 1
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Cropping:'
                    NormalButton:
                        text: 'Reset All'
                        on_release: root.reset()
                LeftNormalLabel:
                    size_hint_y: None
                    height: app.button_scale
                    text: root.image.crop_text
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Crop Top:'
                        ShortLabel:
                            text: str(round(cropTopSlider.value * 100, 1))+'%'
                    HalfSlider:
                        id: cropTopSlider
                        #value: root.image.crop_top
                        on_value: root.image.crop_top = self.value
                        reset_value: root.reset_crop_top
                    SmallBufferY:
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Crop Right:'
                        ShortLabel:
                            text: str(round(cropRightSlider.value * 100, 1))+'%'
                    HalfSlider:
                        id: cropRightSlider
                        #value: root.image.crop_right
                        on_value: root.image.crop_right = self.value
                        reset_value: root.reset_crop_right
                    SmallBufferY:
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Crop Bottom:'
                        ShortLabel:
                            text: str(round(cropBottomSlider.value * 100, 1))+'%'
                    HalfSlider:
                        id: cropBottomSlider
                        #value: root.image.crop_bottom
                        on_value: root.image.crop_bottom = self.value
                        reset_value: root.reset_crop_bottom
                    SmallBufferY:
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: app.button_scale
                        LeftNormalLabel:
                            text: 'Crop Left:'
                        ShortLabel:
                            text: str(round(cropLeftSlider.value * 100, 1))+'%'
                    HalfSlider:
                        id: cropLeftSlider
                        #value: root.image.crop_left
                        on_value: root.image.crop_left = self.value
                        reset_value: root.reset_crop_left
                SmallBufferY:
                GridLayout:
                    canvas.before:
                        Color:
                            rgba: app.theme.area_background
                        BorderImage:
                            pos: self.pos
                            size: self.size
                            source: 'data/buttonflat.png'
                    padding: app.padding
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    MenuStarterButtonWide:
                        size_hint_x: 1
                        text: 'Set Aspect Ratio...'
                        id: aspectRatios
                        on_release: root.aspect_dropdown.open(self)
                    NormalToggle:
                        text: 'Lock Aspect To ' + root.lock_aspect_name
                        state: 'down' if root.lock_aspect else 'normal'
                        on_state: root.update_lock_aspect(self.state)
                        size_hint_x: 1

<EditPanelVideo>:
    name: 'video'
    BoxLayout:
        orientation: 'vertical'
        WideButton:
            text: 'More Editing'
            on_release: root.manager.current = 'edit'
            disabled: root.advanced
            opacity: 0 if root.advanced else 1
            height: 0 if root.advanced else app.button_scale
        SmallBufferY:
        ScrollerContainer:
            cols: 1
            do_scroll_x: False
            GridLayout:
                padding: 0, 0, int(app.button_scale / 2), 0
                size_hint: 1, None
                cols: 1
                height: self.minimum_height
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: app.button_scale
                    LeftNormalLabel:
                        text: 'Video Convert Settings:'
                BoxLayout:
                    size_hint_y: None
                    orientation: 'horizontal'
                    disabled: not root.advanced
                    opacity: 1 if root.advanced else 0
                    height: app.button_scale if root.advanced else 0
                    NormalInput:
                        text: app.encoding_settings.name
                        on_text: app.encoding_settings.name = self.text
                    NormalButton:
                        text: 'Save'
                        on_release: 
                            app.new_user_encoding_preset()
                            root.setup_presets_menu()
                GridLayout:
                    cols: 1
                    size_hint: 1, None
                    height: self.minimum_height
                    MenuStarterButtonWide:
                        text: 'Presets'
                        size_hint_x: 1
                        on_release: root.preset_drop.open(self)
                    GridLayout:
                        canvas.before:
                            Color:
                                rgba: app.theme.area_background
                            BorderImage:
                                pos: self.pos
                                size: self.size
                                source: 'data/buttonflat.png'
                        padding: app.padding
                        cols: 1
                        size_hint: 1, None
                        height: self.minimum_height
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Container:'
                            MenuStarterButtonWide:
                                size_hint_x: 1
                                text: app.encoding_settings.file_format
                                on_release: root.container_drop.open(self)
                        SmallBufferY:
                        NormalToggle:
                            id: resize
                            size_hint_x: 1
                            state: 'down' if app.encoding_settings.resize else 'normal'
                            text: 'Resize' if self.state == 'down' else 'No Resize'
                            on_release: root.update_resize(self.state)
                        BoxLayout:
                            disabled: not app.encoding_settings.resize
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            ShortLabel:
                                text: 'Size:'
                            NormalInput:
                                id: widthInput
                                hint_text: 'Width'
                                multiline: False
                                text: app.encoding_settings.resize_width
                                on_text: app.encoding_settings.resize_width = self.text
                            ShortLabel:
                                text: 'x'
                            NormalInput:
                                id: heightInput
                                hint_text: 'Height'
                                multiline: False
                                text: app.encoding_settings.resize_height
                                on_text: app.encoding_settings.resize_height = self.text
                            MenuStarterButton:
                                size_hint_x: None
                                width: app.button_scale
                                on_release: root.resolution_presets_drop.open(self)
                        SmallBufferY:
                        NormalToggle:
                            id: deinterlace
                            size_hint_x: 1
                            state: 'down' if app.encoding_settings.deinterlace else 'normal'
                            text: 'Deinterlace' if self.state == 'down' else 'No Deinterlace'
                            on_release: root.update_deinterlace(self.state)
                        SmallBufferY:
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Video Codec:'
                            MenuStarterButtonWide:
                                size_hint_x: 1
                                text: app.encoding_settings.video_codec
                                on_release: root.video_codec_drop.open(self)
                                id: videoCodecDrop
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Encoding Quality:'
                            MenuStarterButtonWide:
                                size_hint_x: 1
                                text: app.encoding_settings.quality
                                on_release: root.quality_drop.open(self)
                                id: qualityDrop
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Encoding Speed:'
                            MenuStarterButtonWide:
                                size_hint_x: 1
                                text: app.encoding_settings.encoding_speed
                                on_release: root.encoding_speed_drop.open(self)
                                id: encodingSpeedDrop
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Color Conversion:'
                            MenuStarterButtonWide:
                                size_hint_x: 1
                                text: app.encoding_settings.encoding_color
                                on_release: root.encoding_color_drop.open(self)
                                id: encodingColorDrop
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Framerate Override:'
                            BoxLayout:
                                FloatInput:
                                    hint_text: "Auto"
                                    id: videoFramerateInput
                                    text: app.encoding_settings.framerate
                                    on_text: app.encoding_settings.framerate = self.text
                                    on_text: root.owner.set_framerate_override(self.text)
                                MenuStarterButton:
                                    size_hint_x: None
                                    width: app.button_scale
                                    on_release: root.framerate_presets_drop.open(self)
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'GOP Size:'
                            FloatInput:
                                hint_text: "Auto"
                                id:videoGOPInput
                                text: app.encoding_settings.gop
                                on_text: app.encoding_settings.gop = self.text
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Video Bitrate:'
                            FloatInput:
                                hint_text: "Auto"
                                id: videoBitrateInput
                                text: app.encoding_settings.video_bitrate
                                on_text: app.encoding_settings.video_bitrate = self.text
                        SmallBufferY:
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Audio Codec:'
                            MenuStarterButtonWide:
                                size_hint_x: 1
                                text: app.encoding_settings.audio_codec
                                on_release: root.audio_codec_drop.open(self)
                                id: audioCodecDrop
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: 'Audio Bitrate:'
                            FloatInput:
                                hint_text: "Auto"
                                id: audioBitrateInput
                                text: app.encoding_settings.audio_bitrate
                                on_text: app.encoding_settings.audio_bitrate = self.text
                        LeftNormalLabel:
                            opacity: 1 if app.encoding_settings.description else 0
                            height: app.button_scale if app.encoding_settings.description else 0
                            text: 'Preset Description:'
                        MultilineLabel:
                            text: app.encoding_settings.description
                    SmallBufferY:
                    GridLayout:
                        canvas.before:
                            Color:
                                rgba: app.theme.area_background
                            BorderImage:
                                pos: self.pos
                                size: self.size
                                source: 'data/buttonflat.png'
                        padding: app.padding
                        cols: 1
                        size_hint: 1, None
                        height: self.minimum_height if root.advanced else 0
                        opacity: 1 if root.advanced else 0
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: "Custom command line settings"
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: "This can override other settings."
                        SmallBufferY:
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: app.button_scale
                            LeftNormalLabel:
                                text: "String Replacements:"
                        GridLayout:
                            cols: 3
                            size_hint: 1, None
                            height: int(app.button_scale * 9)
                            ShortLabel:
                                text: '%i'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Input File (Required)'
                            ShortLabel:
                                text: '%c'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Container Setting'
                            ShortLabel:
                                text: '%v'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Video Codec Setting'
                            ShortLabel:
                                text: '%a'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Audio Codec Setting'
                            ShortLabel:
                                text: '%f'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Framerate Setting'
                            ShortLabel:
                                text: '%p'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Pixel Format (From Original File)'
                            ShortLabel:
                                text: '%b'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Video Bitrate Setting'
                            ShortLabel:
                                text: '%d'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Audio Bitrate Setting'
                            ShortLabel:
                                text: '%%'
                            ShortLabel:
                                text: ' - '
                            LeftNormalLabel:
                                text: 'Single Percent Sign (%)'

<EditMain>:

<AspectRatioDropDown>:
    MenuButton:
        text: 'Original Ratio'
        on_release: root.select('Current')
    MenuButton:
        text: '6 x 4 (Wide)'
        on_release: root.select('6x4')
    MenuButton:
        text: '4 x 6 (Tall)'
        on_release: root.select('4x6')
    MenuButton:
        text: '7 x 5 (Wide)'
        on_release: root.select('7x5')
    MenuButton:
        text: '5 x 7 (Tall)'
        on_release: root.select('5x7')
    MenuButton:
        text: '11 x 8.5 (Wide)'
        on_release: root.select('11x8.5')
    MenuButton:
        text: '8.5 x 11 (Tall)'
        on_release: root.select('8.5x11')
    MenuButton:
        text: '4 x 3 (Wide)'
        on_release: root.select('4x3')
    MenuButton:
        text: '3 x 4 (Tall)'
        on_release: root.select('3x4')
    MenuButton:
        text: '16 x 9 (Wide)'
        on_release: root.select('16x9')
    MenuButton:
        text: '9 x 16 (Tall)'
        on_release: root.select('9x16')
    MenuButton:
        text: '1 x 1'
        on_release: root.select('1x1')

<InterpolationDropDown>:
    MenuButton:
        text: 'Linear'
        on_release: root.select('Linear')
    MenuButton:
        text: 'Cosine'
        on_release: root.select('Cosine')
    MenuButton:
        text: 'Cubic'
        on_release: root.select('Cubic')
    MenuButton:
        text: 'Catmull-Rom'
        on_release: root.select('Catmull-Rom')

<Curves>:

<VGridLine@Widget>:
    canvas.before:
        Color:
            rgba: 1,1,1,.5
        Rectangle:
            pos: self.pos
            size: 1, self.size[1]

<HGridLine@Widget>:
    size_hint: 1, 1
    canvas.before:
        Color:
            rgba: 1,1,1,.5
        Rectangle:
            pos: self.pos
            size: self.size[0], 1

<RotationGrid>:
    RelativeLayout:
        size_hint: 1, 1
        VGridLine:
            pos_hint: {"x": 0.0}
        VGridLine:
            pos_hint: {"x": 0.1}
        VGridLine:
            pos_hint: {"x": 0.2}
        VGridLine:
            pos_hint: {"x": 0.3}
        VGridLine:
            pos_hint: {"x": 0.4}
        VGridLine:
            pos_hint: {"x": 0.5}
        VGridLine:
            pos_hint: {"x": 0.6}
        VGridLine:
            pos_hint: {"x": 0.7}
        VGridLine:
            pos_hint: {"x": 0.8}
        VGridLine:
            pos_hint: {"x": 0.9}
        VGridLine:
            pos_hint: {"x": 1.0}
    RelativeLayout:
        size_hint: 1, 1
        HGridLine:
            pos_hint: {"y": 0.0}
        HGridLine:
            pos_hint: {"y": 0.1}
        HGridLine:
            pos_hint: {"y": 0.2}
        HGridLine:
            pos_hint: {"y": 0.3}
        HGridLine:
            pos_hint: {"y": 0.4}
        HGridLine:
            pos_hint: {"y": 0.5}
        HGridLine:
            pos_hint: {"y": 0.6}
        HGridLine:
            pos_hint: {"y": 0.7}
        HGridLine:
            pos_hint: {"y": 0.8}
        HGridLine:
            pos_hint: {"y": 0.9}
        HGridLine:
            pos_hint: {"y": 1.0}

<CropOverlay>:
    size_hint: None, None
    resizable_left: True
    resizable_right: True
    resizable_up: True
    resizable_down: True
    resize_lock: False
    resizable_border: 40
    resizable_border_offset: 0.5
    RelativeLayout:
        size_hint: 1, 1
        VGridLine:
            pos_hint: {"x": 0.0}
        VGridLine:
            pos_hint: {"x": 0.3333333}
        VGridLine:
            pos_hint: {"x": 0.6666666}
        VGridLine:
            pos_hint: {"x": .999}
    RelativeLayout:
        size_hint: 1, 1
        HGridLine:
            pos_hint: {"y": 0.0}
        HGridLine:
            pos_hint: {"y": 0.3333333}
        HGridLine:
            pos_hint: {"y": 0.6666666}
        HGridLine:
            pos_hint: {"y": .999}
    Image:
        source: 'data/move.png'
        pos_hint: {'center_x': .5, 'center_y': .5}
        height: 100 if root.height > 100 else root.height
        width: 100 if root.width > 100 else root.width
        size_hint: None, None

<ExternalProgramEditor>:
    cols: 1
    height: app.button_scale * 6
    size_hint: 1, None
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: 'Name: '
        NormalInput:
            text: root.name
            multiline: False
            input_filter: app.test_album
            on_focus: root.set_name(self)
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: 'Command: '
        WideButton:
            text: root.command
            text_size: (self.size[0] - app.padding*2, None)
            shorten: True
            on_release: root.select_command()
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: 'Argument: '
        NormalInput:
            text: root.argument
            multiline: False
            input_filter: app.test_album
            on_focus: root.set_argument(self)
    LeftNormalLabel:
        text: 'For The Argument: '
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: '"%i"'
        LeftNormalLabel:
            text: 'Is the image filename'
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        ShortLabel:
            text: '"%%"'
        LeftNormalLabel:
            text: 'Is a single "%"'

<TagSelectButton>:
    size_hint_x: 1

<BatchPhoto>:
    canvas.after:
        Color:
            rgba: 1, 1, 1, (0.5 if root.drag_to else 0)
        Rectangle:
            pos: root.pos[0], (root.pos[1] + root.size[1] - (app.button_scale / 4))
            size: root.size[0], (app.button_scale / 2)
    orientation: 'horizontal'
    size_hint_y: None
    height: app.button_scale * (3 if root.message else 2)
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: None
        width: app.button_scale * 2
        NormalLabel:
            text: str(root.index + 1)
        Widget:
            size_hint_y: None
            height: app.button_scale if root.message else 0
        NormalLabel:
            text: root.encode_state
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            size_hint: 1, 1
            LeftNormalLabel:
                text: os.path.join(root.path, root.file)
            NormalToggle:
                text: '   Apply Edit   '
                state: 'down' if root.edit else 'normal'
                disabled: root.disable_edit
                on_release: root.set_edit()
            NormalButton:
                size_hint_x: None
                width: app.button_scale
                text: 'X'
                warn: True
                on_release: root.remove()
        BoxLayout:
            orientation: 'horizontal'
            size_hint: 1, 1
            ShortLabel:
                text: 'Export To:'
            NormalInput:
                text: root.export_file
                on_focus: root.set_export_file(self.text)
            NormalButton:
                text: 'Browse...'
                on_release: root.select_export()
            MenuStarterButtonWide:
                size_hint_x: 0.34
                text: 'Preset: '+root.preset_name if root.preset_name else 'Select Preset'
                on_release: root.select_preset(self)
        LeftNormalLabel:
            height: app.button_scale if root.message else 0
            text: root.message
    Widget:
        size_hint_x: None
        width: app.button_scale / 2

<RecycleLabel@Label>:
    mipmap: app.mipmap
    color: app.theme.text
    font_size: app.text_scale
    valign: 'top'
    halign: 'left'
    size_hint: 1, None
    text_size: self.width, None
    height: self.texture_size[1] if self.texture_size[1] > app.text_scale else app.text_scale

<VideoProcessingPopup>:
    GridLayout:
        cols: 1
        NormalLabel:
            text: root.overall_process
            text_size: self.size
        NormalRecycleView:
            id: logviewerscroller
            size_hint: 1, 1
            data: root.encode_log
            viewclass: 'RecycleLabel'
            RecycleBoxLayout:
                default_size: None, app.text_scale
                default_size_hint: 1, None
                orientation: 'vertical'
                size_hint_x: 1
                size_hint_y: None
                height: self.minimum_height
        NormalLabel:
            size_hint_y: None
            height: app.button_scale
            id: scanningText
            text: root.scanning_text
            text_size: self.size
        ProgressBar:
            size_hint_y: None
            height: app.button_scale
            id: scanningProgress
            value: root.scanning_percentage
            max: 100
        WideButton:
            size_hint_y: None
            height: app.button_scale
            id: scanningButton
            text: root.button_text

""")


class CoreVideo(KivyCoreVideo):
    aspect = NumericProperty(1)
    metadata = None

    def play(self):
        if self._ffplayer and self._state == 'paused':
            self._ffplayer.toggle_pause()
            self._state = 'playing'
            return

        self.load()
        self._out_fmt = 'rgba'
        ff_opts = {
            'paused': True,
            'out_fmt': self._out_fmt,
            'sn': True,
            'volume': self._volume,
        }
        self._ffplayer = MediaPlayer(self._filename, callback=self._player_callback, thread_lib='SDL', loglevel='info', ff_opts=ff_opts)

        #Load aspect ratio
        self.metadata = self._ffplayer.get_metadata()
        aspect_ratio = self.metadata['aspect_ratio']
        try:
            self.aspect = aspect_ratio[1]/aspect_ratio[0]
        except:
            self.aspect = 1

        self._thread = Thread(target=self._next_frame_run, name='Next frame')
        #self._thread.daemon = True
        self._thread.start()

    def _next_frame_run(self):
        ffplayer = self._ffplayer
        sleep = time.sleep
        trigger = self._trigger
        did_dispatch_eof = False
        seek_queue = self._seek_queue

        #Wait for first frame to load before playing so audio doesnt get out of sync too badly
        frame = None
        while frame is None:
            frame, value = ffplayer.get_frame(force_refresh=True)
            sleep(0.1)

        # fast path, if the source video is yuv420p, we'll use a glsl shader
        # for buffer conversion to rgba
        while not self._ffplayer_need_quit:
            src_pix_fmt = ffplayer.get_metadata().get('src_pix_fmt')
            if not src_pix_fmt:
                sleep(0.005)
                continue

            if src_pix_fmt == 'yuv420p':
                self._out_fmt = 'yuv420p'
                ffplayer.set_output_pix_fmt(self._out_fmt)
            self._ffplayer.toggle_pause()
            break

        if self._ffplayer_need_quit:
            return

        # wait until loaded or failed, shouldn't take long, but just to make
        # sure metadata is available.
        s = time.perf_counter()
        while not self._ffplayer_need_quit:
            if ffplayer.get_metadata()['src_vid_size'] != (0, 0):
                break
            # XXX if will fail later then?
            if time.perf_counter() - s > 10.:
                break
            sleep(0.005)

        if self._ffplayer_need_quit:
            return

        # we got all the informations, now, get the frames :)
        self._state = 'playing'

        while not self._ffplayer_need_quit:
            seek_happened = False
            if seek_queue:
                vals = seek_queue[:]
                del seek_queue[:len(vals)]
                percent, precise = vals[-1]
                ffplayer.seek(
                    percent * ffplayer.get_metadata()['duration'],
                    relative=False,
                    accurate=precise
                )
                seek_happened = True
                self._next_frame = None

            # Get next frame if paused:
            if seek_happened and ffplayer.get_pause():
                ffplayer.set_volume(0.0)  # Try to do it silently.
                ffplayer.set_pause(False)
                try:
                    # We don't know concrete number of frames to skip,
                    # this number worked fine on couple of tested videos:
                    to_skip = 6
                    while not self._ffplayer_need_quit:
                        frame, val = ffplayer.get_frame(show=False)
                        # Exit loop on invalid val:
                        if val in ('paused', 'eof'):
                            break
                        # Exit loop on seek_queue updated:
                        if seek_queue:
                            break
                        # Wait for next frame:
                        if frame is None:
                            sleep(0.005)
                            continue
                        # Wait until we skipped enough frames:
                        to_skip -= 1
                        if to_skip == 0:
                            break
                    # Assuming last frame is actual, just get it:
                    frame, val = ffplayer.get_frame(force_refresh=True)
                finally:
                    ffplayer.set_pause(bool(self._state == 'paused'))
                    ffplayer.set_volume(self._volume)
            # Get next frame regular:
            else:
                frame, val = ffplayer.get_frame()

            if val == 'eof':
                self._ffplayer_need_quit = True
                if not did_dispatch_eof:
                    self._do_eos()
                    did_dispatch_eof = True
                
            elif val == 'paused':
                did_dispatch_eof = False
            else:
                did_dispatch_eof = False
                if frame:
                    self._next_frame = frame
                    trigger()
                else:
                    val = val if val else (1 / 30.)
                sleep(val)
        self._ffplayer.set_volume(0.0)
        self._ffplayer.set_pause(True)
        self._ffplayer.seek(0)
        self._ffplayer.close_player()


class ConversionScreen(Screen):
    #Display variables
    selected = StringProperty('')  #The current folder/album/tag being displayed
    type = StringProperty('None')  #'Folder', 'Tag'
    target = StringProperty()  #The identifier of the album/folder/tag that is being viewed
    photos = []  #Photoinfo of all photos in the album
    photoinfo = []  #photoinfo for the currently viewed photo
    photo = StringProperty('')  #The absolute path to the currently visible photo
    fullpath = StringProperty()  #The database-relative path of the current visible photo
    encode_log = ListProperty()
    encoding_start = 0

    viewer = ObjectProperty(allownone=True)  #Holder for the photo viewer widget
    popup = None

    #Video reencode variables
    cancel_encoding = BooleanProperty()
    encoding = BooleanProperty(False)
    encodingthread = ObjectProperty()
    encoding_process_thread = ObjectProperty(allownone=True)
    audio_file = StringProperty()
    use_audio = BooleanProperty(False)
    offset_audio_file = BooleanProperty(False)
    export_file = StringProperty()
    export_folder = StringProperty()
    advanced_encode = BooleanProperty(False)  #Enables 'advanced' features for the encoding command - replace audio, command line override, save to file
    use_batch = BooleanProperty(False)

    #Variables relating to the photo view
    orientation = NumericProperty(1)  #EXIF Orientation of the currently viewed photo
    angle = NumericProperty(0)  #Corrective angle rotation of the currently viewed photo
    mirror = BooleanProperty(False)  #Corrective mirroring of the currently viewed photo
    favorite = BooleanProperty(False)  #True if the currently viewed photo is favorited
    view_image = BooleanProperty(True)  #True if the currently viewed photo is an image, false if it is a video
    image_x = NumericProperty(0)  #Set when the image is loaded, used for orientation of cropping
    image_y = NumericProperty(0)  #Set when the image is loaded, used for orientation of cropping

    #Stored variables for editing
    autocontrast = BooleanProperty(False)
    equalize = NumericProperty(0)
    temperature = NumericProperty(0)
    slide = NumericProperty(0)
    brightness = NumericProperty(0)
    shadow = NumericProperty(0)
    gamma = NumericProperty(0)
    contrast = NumericProperty(0)
    saturation = NumericProperty(0)
    tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    curve = ListProperty([[0, 0], [1, 1]])
    curve_data = ListProperty()
    denoise = BooleanProperty(False)
    luminance_denoise = StringProperty('10')
    color_denoise = StringProperty('10')
    search_window = StringProperty('15')
    block_size = StringProperty('5')
    luminance_denoise_data = NumericProperty(10)
    color_denoise_data = NumericProperty(10)
    search_window_data = NumericProperty(15)
    block_size_data = NumericProperty(5)
    adaptive = NumericProperty(0)  #adaptive_clip
    sharpen = NumericProperty(0)
    median = NumericProperty(0)  #median_blur
    bilateral = NumericProperty(0.5)
    bilateral_amount = NumericProperty(0)
    vignette_amount = NumericProperty(0)
    vignette_size = NumericProperty(0.5)
    edge_blur_amount = NumericProperty(0)
    edge_blur_intensity = NumericProperty(0.5)
    edge_blur_size = NumericProperty(0.5)
    border_selected = StringProperty()
    border_data = ListProperty()  #border_image
    border_x_scale = NumericProperty(0)
    border_y_scale = NumericProperty(0)
    border_tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    border_opacity = NumericProperty(1)
    flip_horizontal = BooleanProperty(False)
    flip_vertical = BooleanProperty(False)
    rotate_angle = NumericProperty(0)
    fine_angle = NumericProperty(0)
    crop_top = NumericProperty(0)
    crop_bottom = NumericProperty(0)
    crop_left = NumericProperty(0)
    crop_right = NumericProperty(0)

    edit_color = BooleanProperty(False)
    edit_advanced = BooleanProperty(False)
    edit_filter = BooleanProperty(False)
    edit_border = BooleanProperty(False)
    edit_denoise = BooleanProperty(False)
    edit_crop = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def back(self, *_):
        app = App.get_running_app()
        app.show_database(scrollto=self.fullpath)
        return True

    def set_framerate_override(self, framerate):
        pass

    def clear_cache(self, *_):
        pass

    def set_photo(self, photo):
        self.photo = photo

    def set_edit_panel(self, *_):
        pass

    def key(self, key):
        pass

    def dismiss_extra(self):
        if self.encoding:
            self.cancel_encode()
            return True
        return False

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

    def dismiss_popup(self, *_):
        """Close a currently open popup for this screen."""

        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def drop_widget(self, fullpath, position, dropped_type='file', aspect=1):
        """Dummy function.  Here because the app can possibly call this function for any screen."""
        pass

    def on_leave(self):
        if self.viewer:
            self.viewer.stop()

        app = App.get_running_app()
        app.clear_drags()

    def on_enter(self):
        #import variables
        app = App.get_running_app()
        self.target = app.target
        self.type = app.type

        self.encoding = False
        self.cancel_encoding = False

    def on_use_audio(self, *_):
        if not self.use_audio:
            self.audio_file = ''

    def update_encoding_settings(self, *_):
        pass

    def cancel_encode(self, *_):
        """Signal to cancel the encodig process."""

        self.cancel_encoding = True
        if self.popup:
            self.popup.scanning_text = "Canceling encoding process, please wait..."

    def get_ffmpeg_audio_command(self, video_input_folder, video_input_filename, audio_input_folder, audio_input_filename, output_file_folder, audio_file_override, offset_audio_file, encoding_settings=None, start=None):
        app = App.get_running_app()
        if not encoding_settings:
            encoding_preset = app.encoding_settings
            encoding_settings = encoding_preset.get_encoding_preset(replace_auto=True)
        container_data = find_dictionary(app.containers, 'name', encoding_settings['file_format'])
        audio_codec_data = find_dictionary(app.audio_codecs, 'name', encoding_settings['audio_codec'])
        file_format = container_data['format']
        audio_codec = audio_codec_data['codec']
        quality = encoding_settings['quality']
        quality_multiplier = encoding_quality[encoding_quality_friendly.index(quality)]

        audio_bitrate = encoding_settings['audio_bitrate']
        if not audio_bitrate:
            audio_bitrate = int(audio_codec_data['bitrate']) * quality_multiplier
            closest_audio_bitrate = min(audio_encode_values, key=lambda x: abs(x-audio_bitrate))
            audio_bitrate = str(closest_audio_bitrate)

        extension = container_data['extension']

        if start is not None:
            seek = ' -ss '+str(start)
        else:
            seek = ''
        video_file = os.path.join(video_input_folder, video_input_filename)
        audio_file = os.path.join(audio_input_folder, audio_input_filename)
        if isfile2(audio_file_override):
            audio_extension = os.path.splitext(audio_file_override)[1].lower()
            if audio_extension in app.movietypes + app.audiotypes:
                audio_file = audio_file_override
                if not offset_audio_file:
                    seek = ''

        output_filename = os.path.splitext(video_input_filename)[0]+'-mux.'+extension
        output_file = os.path.join(output_file_folder, output_filename)
        audio_bitrate_settings = "-b:a " + audio_bitrate + "k"
        audio_codec_settings = "-c:a " + audio_codec + " -strict -2"

        executable = '"'+ffmpeg_command+'"'

        command = executable+' -i "'+video_file+'"'+seek+' -i "'+audio_file+'" -map 0:v -map 1:a -codec copy '+audio_codec_settings+' '+audio_bitrate_settings+' -shortest "'+output_file+'"'
        return [True, command, output_filename]

    def get_ffmpeg_command(self, input_folder, input_filename, output_file_folder, output_filename, input_size, noaudio=False, input_images=False, input_file=None, input_framerate=None, input_pixel_format=None, encoding_settings=None, start=None, duration=None, gpu264=None, gpu265=None):
        threads = multiprocessing.cpu_count() - 2
        if threads > 1:
            threads_command = ' -threads '+str(threads)
        else:
            threads_command = ''
        app = App.get_running_app()
        if not encoding_settings:
            encoding_preset = app.encoding_settings
            encoding_settings = encoding_preset.get_encoding_preset(replace_auto=True)

        container_data = find_dictionary(app.containers, 'name', encoding_settings['file_format'])
        audio_codec_data = find_dictionary(app.audio_codecs, 'name', encoding_settings['audio_codec'])
        video_codec_data = find_dictionary(app.video_codecs, 'name', encoding_settings['video_codec'])
        file_format = container_data['format']
        video_codec = video_codec_data['codec']
        audio_codec = audio_codec_data['codec']
        quality = encoding_settings['quality']
        quality_multiplier = encoding_quality[encoding_quality_friendly.index(quality)]
        encoding_color = encoding_settings['encoding_color']
        encoding_framerate = encoding_settings['framerate']
        gop = encoding_settings['gop']
        if gop:
            gop_setting = " -g "+gop
        else:
            gop_setting = ''

        resize = encoding_settings['resize']
        resize_width = encoding_settings['width']
        resize_height = encoding_settings['height']
        video_bitrate = encoding_settings['video_bitrate']
        if resize:
            pixels_number = int(resize_width) * int(resize_height)
        else:
            pixels_number = input_size[0] * input_size[1]

        if not video_bitrate:
            try:
                codec_divisor = int(video_codec_data['efficiency'])
            except:
                codec_divisor = 100
            if codec_divisor == 0:
                codec_divisor = 100
            video_bitrate = str(int((pixels_number / codec_divisor) * quality_multiplier))
        audio_bitrate = encoding_settings['audio_bitrate']
        if not audio_bitrate:
            audio_bitrate = int(audio_codec_data['bitrate']) * quality_multiplier
            closest_audio_bitrate = min(audio_encode_values, key=lambda x: abs(x-audio_bitrate))
            audio_bitrate = str(closest_audio_bitrate)
        if encoding_settings['encoding_speed'] != 'Auto':
            encoding_speed = encoding_speeds[encoding_speeds_friendly.index(encoding_settings['encoding_speed'])]
            speed_setting = "-preset "+encoding_speed
        else:
            speed_setting = ''

        deinterlace = encoding_settings['deinterlace']
        encoding_command = encoding_settings['command_line']
        extension = container_data['extension']

        if start is not None:
            seek = ' -ss '+str(start)
        else:
            seek = ''
        if duration is not None:
            duration = ' -t '+str(duration)
        else:
            duration = ''
        if not input_file:
            input_file = os.path.join(input_folder, input_filename)
        if input_framerate:
            output_framerate = self.new_framerate(video_codec, input_framerate)
        else:
            output_framerate = False
        if output_framerate:
            framerate_setting = "-r "+str(output_framerate[0] / output_framerate[1])
        else:
            framerate_setting = ""
        if encoding_framerate:
            #output_framerate_setting = "-r "+encoding_framerate
            output_framerate_setting = "-filter:v fps=fps="+encoding_framerate
        else:
            output_framerate_setting = ''
        if input_images:
            input_format_settings = '-f image2pipe -vcodec mjpeg ' + framerate_setting
        else:
            input_format_settings = ''
        if input_pixel_format and encoding_color == 'Copy':
            output_pixel_format = self.new_pixel_format(video_codec, input_pixel_format)
        else:
            if encoding_color == 'Auto':
                output_pixel_format = 'yuv420p'
            elif encoding_color == 'Copy':
                output_pixel_format = ''
            else:
                output_pixel_format = encoding_colors[encoding_colors_friendly.index(encoding_settings['encoding_color'])]
        if output_pixel_format:
            pixel_format_setting = "-pix_fmt "+str(output_pixel_format)
        else:
            pixel_format_setting = ""

        video_bitrate_settings = "-b:v "+video_bitrate+"k"
        #if video_codec == 'mpeg2video':
        #    buffsize = str(int(int(video_bitrate)*0))
        #    video_bitrate_settings = video_bitrate_settings+' -maxrate '+video_bitrate+'k -bufsize '+buffsize+'k'

        if not noaudio:
            audio_bitrate_settings = "-b:a "+audio_bitrate+"k"
            audio_codec_settings = "-c:a " + audio_codec + " -strict -2"
        else:
            audio_bitrate_settings = ''
            audio_codec_settings = ''

        if gpu264 and video_codec == 'libx264':
            video_codec = 'h264_nvenc'
        if gpu265 and video_codec == 'libx265':
            video_codec = 'hevc_nvenc'
        video_codec_settings = "-c:v "+video_codec
        file_format_settings = "-f "+file_format

        if resize and (input_size[0] > int(resize_width) or input_size[1] > int(resize_height)):
            resize_settings = 'scale='+resize_width+":"+resize_height
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
        if video_codec == 'copy':
            input_format_settings = ''
            input_file = os.path.join(input_folder, input_filename)
            video_bitrate_settings = ''
            framerate_setting = ''
            output_framerate_setting = ''
            filter_settings = ''

        executable = '"'+ffmpeg_command+'"'

        if encoding_command and self.advanced_encode:
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
            output_filename = os.path.splitext(output_filename)[0]+'.'+extension
            output_file = os.path.join(output_file_folder, output_filename)
            input_settings = ' -i "'+input_file+'" '
            encoding_command_reformat = encoding_command.replace('%c', file_format_settings).replace('%v', video_codec_settings).replace('%a', audio_codec_settings).replace('%f', output_framerate_setting).replace('%p', pixel_format_setting).replace('%b', video_bitrate_settings).replace('%d', audio_bitrate_settings).replace('%i', input_settings).replace('%%', '%')
            command = executable+seek+' '+input_format_settings+' '+encoding_command_reformat+duration+' "'+output_file+'"'
        else:
            output_filename = os.path.splitext(output_filename)[0]+'.'+extension
            output_file = os.path.join(output_file_folder, output_filename)
            command = executable+threads_command+seek+' '+input_format_settings+' -i "'+input_file+'" '+file_format_settings+' '+filter_settings+' -sn '+speed_setting+' '+video_codec_settings+gop_setting+' '+audio_codec_settings+' '+output_framerate_setting+' '+pixel_format_setting+' '+video_bitrate_settings+' '+audio_bitrate_settings+duration+' "'+output_file+'"'
        return [True, command, output_filename]

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

        try:
            framerates = fftools.get_supported_framerates(codec_name=codec, rate=framerate)
        except:
            return framerate
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

        try:
            available_pixel_formats = fftools.get_supported_pixfmts(codec_name=codec, pix_fmt=pixel_format)
        except:
            return False
        if available_pixel_formats:
            return available_pixel_formats[0]
        else:
            return False

    def save_edit(self):
        if not self.photo:
            return
        if self.view_image:
            self.save_image()
        else:
            self.save_video()

    def save_video(self):
        app = App.get_running_app()
        app.encoding_settings.store_current_encoding_preset()
        self.viewer.stop()

        # Create popup to show progress
        self.cancel_encoding = False
        self.popup = ScanningPopup(title='Processing Video', auto_dismiss=False, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
        self.popup.scanning_text = ''
        self.popup.open()
        encoding_button = self.popup.ids['scanningButton']
        encoding_button.bind(on_press=self.cancel_encode)

        self.clear_log()

        # Start encoding thread
        self.encoding_start = time.perf_counter()
        self.append_log("[INFO] : Beginning encode at "+time.strftime("%H:%M:%S", time.localtime()))
        self.encodingthread = threading.Thread(target=self.save_video_process)
        self.encodingthread.start()

    def end_encode(self, message, end_type=''):
        #self.set_edit_panel('main')
        self.view_panel = ''
        Clock.schedule_once(lambda x: self.set_edit_panel('main'))
        if end_type == 'fail':
            prefix = "[WARNING] : "
        elif end_type == 'info':
            prefix = "[INFO] : "
        else:
            prefix = ''
        self.append_log(prefix+message)
        if self.encoding_start:
            encode_time = int(round(time.perf_counter() - self.encoding_start))
            encode_length_formatted = ".  Encode took: "+time_index(encode_time)
        else:
            encode_length_formatted = ''
        self.append_log("[INFO] : Encoding finished at: "+time.strftime("%H:%M:%S", time.localtime())+encode_length_formatted)
        if not self.use_batch:
            self.encoding = False
            self.cancel_encode()
            self.dismiss_popup()
            self.save_log()
            app = App.get_running_app()
            if end_type == 'fail':
                Clock.schedule_once(lambda x: app.popup_message(text=message, title='Warning'))

    def delete_temp_encode(self, file, folder):
        #Function that will delete the file and the folder if it is empty
        deleted_file = self.delete_output(file)
        if not os.listdir(folder):
            try:
                os.rmdir(folder)
                deleted_folder = True
            except:
                deleted_folder = False
        else:
            deleted_folder = False
        return [deleted_file, deleted_folder]

    def read_stdout_thread(self):
        #Thread that continuously reads the encoding process stdout, so things dont get blocked when lines are blank
        try:
            for line in self.encoding_process_thread.stdout:
                if self.cancel_encoding:
                    return
                if line:
                    self.append_log(line.strip())
        except:
            self.append_log("Encoding process was shut down.")

    def clear_log(self):
        self.encode_log = []

    def append_log(self, text):
        if text.startswith('[mpeg @ ') and ('packet too large' in text or 'buffer underflow' in text):
            return
        if text.startswith('frame='):
            return
        self.encode_log.append({'text': text})

    def save_video_process(self, photo=None, photoinfo=None, export_file=None, encoding_settings=None, audio_file=None, offset_audio_file=None, edit_image=None, start_point=None, end_point=None):
        #Function that applies effects to a video and encodes it

        if photo is None:
            photo = self.photo
        if photoinfo is None:
            photoinfo = self.photoinfo
        if export_file is None:
            export_file = self.export_file
        if encoding_settings is None:
            app = App.get_running_app()
            encoding_settings = app.encoding_settings.get_encoding_preset(replace_auto=True)
        if audio_file is None:
            audio_file = self.audio_file
        if offset_audio_file is None:
            offset_audio_file = self.offset_audio_file
        if edit_image is None:
            edit_image = self.viewer.edit_image
        if start_point is None:
            start_point = self.viewer.start_point
        if end_point is None:
            end_point = self.viewer.end_point

        #get general variables
        self.encoding = True
        app = App.get_running_app()
        start_time = time.time()

        #setup file variables
        self.export_folder = ''
        input_file = os.path.abspath(photo)
        input_file_folder, input_filename = os.path.split(input_file)
        input_basename = os.path.splitext(input_filename)[0]
        output_file_folder = input_file_folder
        output_filename = input_filename

        #Test if given export file is valid
        if self.advanced_encode and export_file:
            export_folder_test, export_file_test = os.path.split(export_file)
            if export_file_test:
                output_filename = export_file_test
            if os.path.isdir(export_folder_test):
                output_file_folder = export_folder_test

        output_file_folder_reencode = os.path.join(output_file_folder, 'reencode')

        #setup encoding settings
        self.append_log("[INFO] : "+'Using FFMPEG from: '+ffmpeg_command)
        self.append_log('')
        if not os.path.isdir(output_file_folder_reencode):
            try:
                os.makedirs(output_file_folder_reencode)
            except:
                message = 'File not encoded, could not create temporary "reencode" folder'
                self.end_encode(message, end_type='fail')
                return ['Error', message]
        pixel_format = edit_image.pixel_format
        input_size = [edit_image.original_width, edit_image.original_height]
        duration = edit_image.length  #total length in seconds
        length = duration * (end_point - start_point)  #converted length in seconds
        edit_image.start_video_convert()
        start_seconds = edit_image.start_seconds  #start offset in seconds
        frame_number = 1
        framerate = edit_image.framerate
        total_frames_duration = (duration * (framerate[0] / framerate[1]))  #estimate of total frames in video
        total_frames = (total_frames_duration * (end_point - start_point))  #estimate of total frames to convert
        start_frame = int(total_frames_duration * start_point)
        gpu264 = app.config.getboolean("Settings", "gpu264")
        gpu265 = app.config.getboolean("Settings", "gpu265")

        #get ready for the encode process
        command_valid, command, output_filename = self.get_ffmpeg_command(input_file_folder, input_filename, output_file_folder_reencode, output_filename, input_size, encoding_settings=encoding_settings, noaudio=True, input_file='-', input_images=True, input_framerate=framerate, input_pixel_format=pixel_format, gpu264=gpu264, gpu265=gpu265)
        output_basename = os.path.splitext(output_filename)[0]
        if not command_valid:
            message = 'Command not valid: '+command
            self.end_encode(message, end_type='fail')
            return ['Error', message]
        output_file = os.path.join(output_file_folder_reencode, output_filename)
        if os.path.isfile(output_file):
            if photoinfo:
                deleted = self.delete_output(output_file)
            else:
                deleted = False
            if not deleted:
                message = 'File not encoded, temporary file already exists, could not delete'
                self.end_encode(message, end_type='fail')
                return ["Error", message]

        self.append_log("[INFO] : "+"Encoding video using the command:")
        self.append_log(command)
        self.append_log('')
        if hasattr(subprocess, 'NORMAL_PRIORITY_CLASS'):
            if app.config.getboolean("Settings", "highencodingpriority"):
                creationflags = subprocess.NORMAL_PRIORITY_CLASS
            else:
                creationflags = subprocess.IDLE_PRIORITY_CLASS
        else:
            creationflags = 0
        video_codec_data = find_dictionary(app.video_codecs, 'name', encoding_settings['video_codec'])
        video_codec = video_codec_data['codec']

        if video_codec == 'copy':
            #Copy video only, no processing to do
            try:
                self.encoding_process_thread = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, shell=True)
            except Exception as e:
                message = "Video encode failed: "+str(e)
                self.end_encode(message, end_type='fail')
                self.kill_encoding_process_thread()
                self.delete_temp_encode(output_file, output_file_folder_reencode)
                return ["Error", message]

            while True:
                if self.cancel_encoding:
                    self.kill_encoding_process_thread()
                    self.delete_temp_encode(output_file, output_file_folder_reencode)
                    self.end_encode("Canceled video processing", end_type='info')
                    return ["Canceled", "Encoding canceled by user"]

                nextline = self.encoding_process_thread.stdout.readline()
                self.append_log(nextline.strip())
                if nextline == '' and self.encoding_process_thread.poll() is not None:
                    break
                if nextline.startswith('frame= '):
                    current_frame = int(nextline.split('frame=')[1].split('fps=')[0].strip())
                    scanning_percentage = 95 + ((current_frame - start_frame) / total_frames * 5)
                    self.popup.scanning_percentage = scanning_percentage
                    elapsed_time = time.time() - start_time

                    try:
                        time_done = time_index(elapsed_time)
                        time_text = "  Time: " + time_done
                    except:
                        time_text = ""
                    self.popup.scanning_text = str(int(scanning_percentage)) + "%" + time_text

            output = self.encoding_process_thread.communicate()[0]
            if output:
                self.append_log(output.strip())
        else:
            #Process video frame-by-frame and encode
            try:
                self.encoding_process_thread = subprocess.Popen(command, creationflags=creationflags, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                read_stdout = threading.Thread(target=self.read_stdout_thread)
                read_stdout.start()
            except Exception as e:
                message = "Video encode failed: "+str(e)
                self.end_encode(message, end_type='fail')
                self.kill_encoding_process_thread()
                self.delete_temp_encode(output_file, output_file_folder_reencode)
                return ["Error", message]

            #Poll process for new output until finished
            while True:
                if self.cancel_encoding:
                    self.kill_encoding_process_thread()
                    self.delete_temp_encode(output_file, output_file_folder_reencode)
                    self.end_encode("Canceled video processing", end_type='info')
                    return ["Canceled", "Encoding canceled by user"]
                frameinfo = edit_image.get_converted_frame()
                if frameinfo is None:
                    #finished encoding
                    break

                frame, pts = frameinfo
                if frame is None:
                    #there was an error with creating the frame, error is in the pts variable
                    message = "First encode failed on frame "+str(frame_number)+": "+str(pts)
                    self.end_encode(message, end_type='fail')
                    self.kill_encoding_process_thread()
                    self.delete_temp_encode(output_file, output_file_folder_reencode)
                    return ["Error", message]
                try:
                    frame.save(self.encoding_process_thread.stdin, 'JPEG')
                    frame = None
                except:
                    if not self.cancel_encoding:
                        self.delete_temp_encode(output_file, output_file_folder_reencode)
                        message = 'Ffmpeg shut down, failed encoding on frame: '+str(frame_number)
                        self.end_encode(message, end_type='fail')
                        self.kill_encoding_process_thread()
                        return ["Error", message]
                frame_number = frame_number+1
                scanning_percentage = ((pts - start_seconds)/length) * 95
                self.popup.scanning_percentage = scanning_percentage
                elapsed_time = time.time() - start_time

                try:
                    percentage_remaining = 95 - scanning_percentage
                    seconds_left = (elapsed_time * percentage_remaining) / scanning_percentage
                    if seconds_left < 0:
                        seconds_left = 0
                    time_done = time_index(elapsed_time)
                    time_remaining = time_index(seconds_left)
                    time_text = "  Time: " + time_done + "  Remaining: " + time_remaining
                except:
                    time_text = ""
                if not self.cancel_encoding:
                    self.popup.scanning_text = str(int(scanning_percentage))+"%"+time_text

            outs, errors = self.encoding_process_thread.communicate()
            read_stdout.join()
            self.encoding_process_thread.stdin.close()
            self.encoding_process_thread.wait()

        exit_code = self.encoding_process_thread.returncode
        self.append_log("[INFO] : "+"Video encode process ended with exit code "+str(exit_code))
        self.append_log('')
        self.append_log('')

        if self.encoding_process_thread:
            try:
                self.encoding_process_thread.kill()
                self.encoding_process_thread.terminate()
                outs, errs = self.encoding_process_thread.communicate()
            except:
                pass

        if exit_code == 0:
            #encoding first file completed
            if app.encoding_settings.audio_codec == 'None/Remove':
                #User has indicated to skip adding audio track
                output_temp_file = output_file
                no_audio = False
            else:
                #Add audio track
                command_valid, command, output_temp_filename = self.get_ffmpeg_audio_command(output_file_folder_reencode, output_filename, input_file_folder, input_filename, output_file_folder_reencode, audio_file, offset_audio_file, encoding_settings=encoding_settings, start=start_seconds)
                output_temp_file = os.path.join(output_file_folder_reencode, output_temp_filename)

                self.append_log("[INFO] : "+"Encoding audio using the command:")
                self.append_log(command)
                self.append_log('')
                deleted = self.delete_output(output_temp_file)
                if not deleted:
                    message = 'File not encoded, temporary file already existed and could not be replaced'
                    self.end_encode(message, end_type='fail')
                    return ["Error", message]

                #Poll process for new output until finished
                try:
                    self.encoding_process_thread = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, shell=True)
                except Exception as e:
                    self.encoding_process_thread = None
                    self.append_log("[WARNING] : "+"Audio encode process failed: "+str(e))
                    exit_code = -1

                while self.encoding_process_thread:
                    if self.cancel_encoding:
                        self.kill_encoding_process_thread()
                        self.delete_temp_encode(output_file, output_file_folder_reencode)
                        deleted = self.delete_output(output_temp_file)
                        self.end_encode("Canceled video processing", end_type='info')
                        return ["Canceled", "Encoding canceled by user"]

                    nextline = self.encoding_process_thread.stdout.readline()
                    self.append_log(nextline.strip())
                    if nextline == '' and self.encoding_process_thread.poll() is not None:
                        break
                    if nextline.startswith('frame= '):
                        current_frame = int(nextline.split('frame=')[1].split('fps=')[0].strip())
                        scanning_percentage = 95 + ((current_frame - start_frame) / total_frames * 5)
                        self.popup.scanning_percentage = scanning_percentage
                        elapsed_time = time.time() - start_time

                        try:
                            time_done = time_index(elapsed_time)
                            time_text = "  Time: " + time_done
                        except:
                            time_text = ""
                        self.popup.scanning_text = str(int(scanning_percentage)) + "%" + time_text

                if self.encoding_process_thread:
                    output = self.encoding_process_thread.communicate()[0]
                    if output:
                        self.append_log(output.strip())
                    exit_code = self.encoding_process_thread.returncode
                    self.encoding_process_thread.wait()
                    self.append_log("[INFO] : "+"Audio encode process ended with exit code: "+str(exit_code))
                    self.append_log('')

                if exit_code != 0:
                    #Could not encode audio element, video file may not include audio, warn the user and continue
                    deleted = self.delete_output(output_temp_file)  #Attempt to delete any incomplete encode
                    no_audio = True
                    output_temp_file = output_file
                else:
                    #Audio track was encoded properly, delete the first encoded file
                    deleted = self.delete_output(output_file)
                    no_audio = False

                if self.encoding_process_thread:
                    self.kill_encoding_process_thread()

            #encoding completed
            new_photoinfo = list(photoinfo)

            #Deal with original file if needed
            if not self.advanced_encode or (photoinfo and (not export_file or (output_file_folder == input_file_folder and output_basename == input_basename))):
                #File is in database, not being exported to a different file
                edit_image.close_video()
                new_original_file = os.path.join(input_file_folder, '.originals', input_filename)
                new_original_file_relative = os.path.join('.originals', input_filename)
                if not os.path.isdir(os.path.join(input_file_folder, '.originals')):
                    os.makedirs(os.path.join(input_file_folder, '.originals'))
                new_encoded_file = os.path.join(input_file_folder, output_filename)

                #check if original file has been backed up already
                if not os.path.isfile(new_original_file):
                    try:
                        os.rename(input_file, new_original_file)
                    except:
                        self.export_folder = output_file_folder_reencode
                        message = 'Could not replace video, converted video left in "reencode" subfolder'
                        self.end_encode(message, end_type='fail')
                        return ["Error", message]
                    if new_photoinfo:
                        new_photoinfo[10] = new_original_file_relative
                else:
                    deleted = self.delete_output(input_file)
                    if not deleted:
                        self.export_folder = output_file_folder_reencode
                        message = 'Could not replace video, converted video left in "reencode" subfolder'
                        self.end_encode(message, end_type='fail')
                        return ["Error", message]
                try:
                    os.rename(output_temp_file, new_encoded_file)
                except:
                    self.export_folder = output_file_folder_reencode
                    message = 'Could not replace video, original file may be deleted, converted video left in "reencode" subfolder'
                    self.end_encode(message, end_type='fail')
                    return ["Error", message]

                if not os.listdir(output_file_folder_reencode):
                    os.rmdir(output_file_folder_reencode)

                #update database
                if new_photoinfo:
                    extension = os.path.splitext(new_encoded_file)[1]
                    new_photoinfo[0] = os.path.splitext(photoinfo[0])[0]+extension  #fix extension
                    new_photoinfo[7] = int(os.path.getmtime(new_encoded_file))  #update modified date
                    new_photoinfo[9] = 1  #set edited

                #update database and variables
                if photoinfo:
                    if photoinfo[0] != new_photoinfo[0]:
                        app.database_item_rename(photoinfo[0], new_photoinfo[0], new_photoinfo[1])
                    app.database_item_update(new_photoinfo)
                    photoinfo = new_photoinfo
                    app.thumbnail_cache.remove_cache(input_file)
                    app.database_thumbnail_update(photoinfo[0], photoinfo[2], photoinfo[7], photoinfo[13], force=True)
                    self.fullpath = local_path(new_photoinfo[0])
                self.export_folder = output_file_folder

            else:
                #File is not in database, or being exported to a different folder
                #output_temp_file : finished encodeded temp file, in the output_file_folder_reencode folder
                #check if output exists, rename if needed
                new_original_file = input_file
                new_encoded_file = os.path.join(output_file_folder, output_filename)
                new_encoded_basefile, new_encoded_extension = os.path.splitext(new_encoded_file)
                index = 1
                while os.path.isfile(new_encoded_file):
                    new_encoded_file = new_encoded_basefile+'_'+str(index)+new_encoded_extension
                    index = index + 1

                try:
                    os.rename(output_temp_file, new_encoded_file)
                except:
                    self.export_folder = output_file_folder_reencode
                    message = 'Could not rename video, converted video left in "reencode" subfolder'
                    self.end_encode(message, end_type='fail')
                    return ["Error", message]

                if not os.listdir(output_file_folder_reencode):
                    os.rmdir(output_file_folder_reencode)
                self.export_folder = output_file_folder

            #Notify user of success
            if no_audio:
                Clock.schedule_once(lambda x: app.message("Completed encoding file, could not find audio track."))
            else:
                Clock.schedule_once(lambda x: app.message("Completed encoding file '"+new_encoded_file+"'"))
            #reload video in ui
            if new_photoinfo:
                #self.set_photo(os.path.join(local_path(new_photoinfo[2]), local_path(new_photoinfo[0])))
                Clock.schedule_once(lambda *dt: self.set_photo(os.path.join(local_path(new_photoinfo[2]), local_path(new_photoinfo[0]))))
            #else:
            #    Clock.schedule_once(lambda *dt: self.set_photo(new_encoded_file))
            Clock.schedule_once(self.clear_cache)

        else:
            #failed first encode, clean up
            message = 'First file not encoded, FFMPEG gave exit code '+str(exit_code)
            self.end_encode(message, end_type='fail')
            self.delete_temp_encode(output_file, output_file_folder_reencode)
            return ["Error", message]
        if no_audio:
            self.append_log("[WARNING] : Could not encode audio element, file may not have audio.")
        copystat(new_original_file, new_encoded_file)
        return_prefix = "Complete"
        return_text = "Completed encoding file to: "+new_encoded_file
        self.end_encode(return_text, end_type='info')
        return [return_prefix, return_text]

    def kill_encoding_process_thread(self):
        try:
            self.encoding_process_thread.kill()
            self.encoding_process_thread.terminate()
            outs, errs = self.encoding_process_thread.communicate()
        except:
            pass

    def save_image(self):
        """Saves any temporary edits on the currently viewed image."""

        app = App.get_running_app()
        error = ''

        #generate full quality image
        try:
            edit_image = self.viewer.edit_image.get_full_quality()
        except MemoryError as e:
            error = 'Could not generate image: out of memory error, please try again.'
            app.popup_message(text=error, title='Warning')
            return
        try:
            exif = self.viewer.edit_image.original_image.getexif()
            exif[274] = 1  #Reset rotation
        except:
            exif = self.viewer.edit_image.exif
        self.viewer.stop()

        #back up old image and save new edit
        photo_file_original = os.path.abspath(self.photo)
        backup_directory = os.path.join(local_path(self.photoinfo[2]), local_path(self.photoinfo[1]), '.originals')
        if not os.path.exists(backup_directory):
            os.mkdir(backup_directory)
        if not os.path.exists(backup_directory):
            app.popup_message(text='Could not create backup directory', title='Warning')
            return
        backup_photo_file = os.path.join(backup_directory, os.path.basename(self.photo))
        backup_photo_file_relative = os.path.join('.originals', os.path.basename(self.photo))
        if not os.path.isfile(photo_file_original):
            app.popup_message(text='Photo file no longer exists', title='Warning')
            return
        if not os.path.isfile(backup_photo_file):
            try:
                os.rename(photo_file_original, backup_photo_file)
            except Exception as e:
                error = str(e)
        if not os.path.isfile(backup_photo_file):
            app.popup_message(text='Could not create backup photo', title='Warning')
            return
        if os.path.isfile(photo_file_original):
            error = app.delete_file(photo_file_original)
            #os.remove(photo_file_original)
        if os.path.isfile(photo_file_original):
            app.popup_message(text='Could not save edited photo', title='Warning')
            return
        photo_file = os.path.splitext(photo_file_original)[0]+'.jpg'
        try:
            edit_image.save(photo_file, "JPEG", quality=95, exif=exif)
        except Exception as e:
            error = str(e)
            print(error)
            if os.path.isfile(photo_file):
                os.remove(photo_file)
        if not os.path.isfile(photo_file):
            if os.path.isfile(backup_photo_file):
                copy2(backup_photo_file, photo_file)
                if os.path.isfile(photo_file):
                    os.remove(backup_photo_file)
                    app.popup_message(text='Could not save edited photo, resored backup', title='Warning')
                else:
                    app.popup_message(text='Could not save edited photo, backup left in .originals folder', title='Warning')
            else:
                app.popup_message(text='Could not save edited photo', title='Warning')
            return

        #update photo info
        new_fullpath = os.path.splitext(self.photoinfo[0])[0]+'.jpg'
        update_photoinfo = list(self.photoinfo)
        update_photoinfo[13] = 1  #reset rotation
        update_photoinfo[10] = agnostic_path(backup_photo_file_relative)
        update_photoinfo[0] = agnostic_path(new_fullpath)
        update_photoinfo[1] = agnostic_path(update_photoinfo[1])
        update_photoinfo[2] = agnostic_path(update_photoinfo[2])
        update_photoinfo[9] = 1
        #update_photoinfo[7] = int(os.path.getmtime(photo_file))
        if self.photoinfo[0] != new_fullpath:
            app.database_item_rename(self.photoinfo[0], update_photoinfo[0], update_photoinfo[1])
        app.database_item_update(update_photoinfo)
        app.save_photoinfo(target=update_photoinfo[1], save_location=os.path.join(update_photoinfo[2], update_photoinfo[1]))
        copystat(backup_photo_file, photo_file)

        #regenerate thumbnail
        app.thumbnail_cache.remove_cache(photo_file)
        app.database_thumbnail_update(update_photoinfo[0], update_photoinfo[2], update_photoinfo[7], update_photoinfo[13], force=True)

        self.set_edit_panel('main')

        #reload photo image in ui
        self.clear_cache()

        #update interface and switch active photo in photo list back to image
        self.photoinfo = update_photoinfo
        self.fullpath = local_path(update_photoinfo[0])
        self.set_photo(os.path.join(local_path(update_photoinfo[2]), local_path(update_photoinfo[0])))
        #Clock.schedule_once(lambda *dt: self.set_photo(os.path.join(local_path(update_photoinfo[2]), local_path(update_photoinfo[0]))))
        self.on_photo()

        app.message("Saved edits to image")

    def save_log(self):
        app = App.get_running_app()
        app.save_log(self.encode_log, 'encode')


class VideoConverterScreen(ConversionScreen):
    from_database = BooleanProperty(False)  #indicates if the database screen switched to this screen
    edit_panel_object = ObjectProperty(allownone=True)
    folder = StringProperty('')
    view_panel = StringProperty('')
    use_command = BooleanProperty(False)
    show_extra = BooleanProperty(False)
    batch_list = ListProperty()
    photo_viewer_current = StringProperty('')
    show_log = BooleanProperty(False)
    apply_edit = BooleanProperty(False)  #Determines if the edit will be applied to batch conversions
    drag_image = ObjectProperty(allownone=True)
    drag_offset = ListProperty()
    sequence = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.advanced_encode = True

    def set_framerate_override(self, framerate):
        if self.viewer:
            try:
                self.viewer.framerate_override = float(framerate)
            except:
                self.viewer.framerate_override = 0

    def drop_file(self, filepath, pos):
        if os.path.isdir(filepath):
            path = filepath
            file = ''
        else:
            path, file = os.path.split(filepath)
        drop_widget = None
        if pos[0] != 0 or pos[1] != 0:
            for child in self.walk(restrict=True):
                point = child.to_parent(*pos)
                if child.collide_point(*point):
                    drop_widget = child

        audio_input = self.ids['audioInput']
        export_to = self.ids['exportInput']
        if drop_widget == audio_input:
            self.load_audio_check(path, file)
        elif drop_widget == export_to:
            self.browse_export_check(path, file)
        else:
            if self.use_batch:
                #import code; vars = globals().copy(); vars.update(locals()); shell = code.InteractiveConsole(vars); shell.interact()

                #add file to batch list
                if os.path.isdir(filepath):
                    #Add all files in folder to batch
                    files = os.listdir(filepath)
                    filepaths = []
                    for file in files:
                        filename = os.path.join(filepath, file)
                        if os.path.isfile(filename):
                            filepaths.append(filename)
                    if filepaths:
                        self.add_files_to_batch(filepaths)
                else:
                    self.add_files_to_batch([filepath])
            else:
                #set file as current
                self.load_video_check(path, file)

    def drag(self, widget, mode, touch_pos, offset=None):
        if mode == 'start':
            self.drag_offset = offset
            self.drag_image = BatchPhoto()
            self.drag_image.size_hint_x = None
            self.drag_image.width = widget.width
            self.drag_image.file = widget.file
            self.drag_image.path = widget.path
            self.drag_image.preset_name = widget.preset_name
            self.drag_image.export_file = widget.export_file
            self.drag_image.edit = widget.edit
            self.drag_image.disable_edit = widget.disable_edit
            self.drag_image.opacity = 0
            app = App.get_running_app()
            app.main_layout.add_widget(self.drag_image)
            self.drag_image.pos = (touch_pos[0] - self.drag_offset[0], touch_pos[1] - self.drag_offset[1])

        if mode == 'move':
            if self.drag_image:
                self.drag_image.pos = (touch_pos[0] - self.drag_offset[0], touch_pos[1] - self.drag_offset[1])
                batch_container = self.ids['photos']
                local_coords = batch_container.to_widget(*touch_pos)
                self.drag_image.opacity = 0
                for child in batch_container.children:
                    if child != widget:
                        if child.collide_point(*local_coords):
                            child.drag_to = True
                            self.drag_image.opacity = 0.5
                            for index, batch in enumerate(self.batch_list):
                                if index == widget.index:
                                    batch['selected'] = True
                                else:
                                    batch['selected'] = False
                            batch_list = self.ids['photosContainer']
                            batch_list.refresh_from_data()
                        else:
                            child.drag_to = False

        if mode == 'end':
            if self.drag_image:
                app = App.get_running_app()
                app.main_layout.remove_widget(self.drag_image)
                self.drag_image = None
                batch_container = self.ids['photos']
                local_coords = batch_container.to_widget(*touch_pos)
                for child in batch_container.children:
                    child.drag_to = False
                    if child != widget:
                        if child.collide_point(*local_coords):
                            pop_index = widget.index
                            insert_index = child.index
                            if insert_index > pop_index:
                                insert_index = insert_index - 1
                            widget_data = self.batch_list.pop(pop_index)
                            self.batch_list.insert(insert_index, widget_data)
                            batch_list = self.ids['photosContainer']
                            batch_list.refresh_from_data()

    def save_batch(self):
        app = App.get_running_app()
        encoding_preset = app.encoding_settings.store_current_encoding_preset(store_app=False)

        configfile = ConfigParser(interpolation=None)
        configfile.add_section('batch')
        configfile.set('batch', 'export_file', self.export_file)
        configfile.set('batch', 'encoding_preset', encoding_preset)

        for index, batch in enumerate(self.batch_list):
            section = str(index)
            configfile.add_section(section)
            configfile.set(section, 'file', batch['file'])
            configfile.set(section, 'path', batch['path'])
            configfile.set(section, 'preset', batch['preset_name'])
            configfile.set(section, 'export_file', batch['export_file'])
            configfile.set(section, 'encode_state', batch['encode_state'])
            configfile.set(section, 'edit', str(batch['edit']))

        with open(os.path.join(app.data_directory, 'batch.ini'), 'w') as config:
            configfile.write(config)

    def load_batch(self):
        app = App.get_running_app()

        filename = os.path.join(app.data_directory, 'batch.ini')
        if os.path.isfile(filename):
            configfile = ConfigParser(interpolation=None)
            configfile.read(filename)
            batch_list = []
            screen_export_file = configfile.get('batch', 'export_file', fallback='')
            encoding_preset = configfile.get('batch', 'encoding_preset', fallback='')
            sections = configfile.sections()
            index = '0'
            all_encoding_presets = app.encoding_presets + app.encoding_presets_extra + app.encoding_presets_user

            while index in sections:
                data = configfile[index]
                file = data.get('file', '')
                path = data.get('path', '')
                preset_name = data.get('preset', '')
                preset = None
                export_file = data.get('export_file', '')
                encode_state = data.get('encode_state', 'Ready')
                edit = to_bool(data.get('edit', 'True'))
                index = str(int(index) + 1)
                full_path = os.path.join(path, file)
                if os.path.isfile(full_path):
                    for check_preset in all_encoding_presets:
                        if check_preset.name == preset_name:
                            preset_name = check_preset.name
                            preset = check_preset
                            break
                    batch = {
                        'file': file,
                        'path': path,
                        'owner': self,
                        'preset': preset,
                        'preset_name': preset_name,
                        'export_file': export_file,
                        'edit': edit,
                        'disable_edit': not self.photo,
                        'encode_state': encode_state,
                        'message': '',
                        'selected': False,
                        'selectable': True
                    }
                    batch_list.append(batch)
            if batch_list:
                self.batch_list = batch_list
                if encoding_preset:
                    app.encoding_settings.load_current_encoding_preset(load_from=encoding_preset)
                self.export_file = screen_export_file

    def image_preset(self, image, to_image):
        preset = self
        if to_image:
            #Store current preset to a CustomImage
            save = image
            load = preset
            save.curve_points = load.curve
            save.curve = load.curve_data
            save.adaptive_clip = load.adaptive
            save.median_blur = load.median
            save.border_image = load.border_data
            save.luminance_denoise = load.luminance_denoise_data
            save.color_denoise = load.color_denoise_data
            save.search_window = load.search_window_data
            save.block_size = load.block_size_data

        else:
            #Store CoreImage edit settings to preset settings
            save = preset
            load = image
            save.curve_data = load.curve
            save.curve = load.curve_points
            save.adaptive = load.adaptive_clip
            save.median = load.median_blur
            save.border_data = load.border_image
            save.luminance_denoise_data = load.luminance_denoise
            save.color_denoise_data = load.color_denoise
            save.search_window_data = load.search_window
            save.block_size_data = load.block_size

        save.autocontrast = load.autocontrast
        save.equalize = load.equalize
        save.temperature = load.temperature
        save.slide = load.slide
        save.brightness = load.brightness
        save.shadow = load.shadow
        save.gamma = load.gamma
        save.contrast = load.contrast
        save.saturation = load.saturation
        save.tint = load.tint
        save.denoise = load.denoise
        save.sharpen = load.sharpen
        save.bilateral = load.bilateral
        save.bilateral_amount = load.bilateral_amount
        save.vignette_amount = load.vignette_amount
        save.vignette_size = load.vignette_size
        save.edge_blur_amount = load.edge_blur_amount
        save.edge_blur_intensity = load.edge_blur_intensity
        save.edge_blur_size = load.edge_blur_size
        save.border_x_scale = load.border_x_scale
        save.border_y_scale = load.border_y_scale
        save.border_tint = load.border_tint
        save.border_opacity = load.border_opacity
        save.flip_horizontal = load.flip_horizontal
        save.flip_vertical = load.flip_vertical
        save.rotate_angle = load.rotate_angle
        save.fine_angle = load.fine_angle
        save.crop_top = load.crop_top
        save.crop_bottom = load.crop_bottom
        save.crop_left = load.crop_left
        save.crop_right = load.crop_right

    def rescale_screen(self):
        app = App.get_running_app()
        #self.ids['leftpanel'].width = app.left_panel_width()
        self.ids['rightpanel'].width = app.right_panel_width()

    def key(self, key):
        if key == 'a':
            if self.popup:
                self.popup.content.toggle_select()

    def on_use_batch(self, *_):
        if self.use_batch:
            self.photo_viewer_current = 'batch'
            #self.show_conversion_panel(ensure=True)
        else:
            self.photo_viewer_current = 'edit'
        self.update_disable_edit()

    def remove_batch(self, index):
        self.batch_list.remove(self.batch_list[index])

    def set_batch_export_file(self, index, text):
        self.batch_list[index]['export_file'] = text
        batch_list = self.ids['photosContainer']
        batch_list.refresh_from_data()

    def select_batch_export(self, index):
        batch = self.batch_list[index]
        browse_folder, file = os.path.split(batch['export_file'])
        if not browse_folder:
            browse_folder = batch['path']
        if not file:
            file = batch['file']
        content = FileBrowser(ok_text='Select', path=browse_folder, file=file, file_editable=True, export_mode=True)
        content.remember = index
        content.bind(on_cancel=self.dismiss_popup)
        content.bind(on_ok=self.browse_preset_export_check)
        self.popup = NormalPopup(title="Select Export Folder", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def clear_batch_export(self, index):
        self.batch_list[index]['export_file'] = ''
        batch_list = self.ids['photosContainer']
        batch_list.refresh_from_data()

    def set_batch_edit(self, index):
        self.batch_list[index]['edit'] = not self.batch_list[index]['edit']
        batch_list = self.ids['photosContainer']
        batch_list.refresh_from_data()

    def browse_preset_export_check(self, *_):
        popup = self.popup
        if popup:
            path = popup.content.path
            file = popup.content.file
            index = popup.content.remember
            self.dismiss_popup()
            self.batch_list[index]['export_file'] = os.path.join(path, file)
            batch_list = self.ids['photosContainer']
            batch_list.refresh_from_data()

    def set_preset(self, index, preset):
        self.batch_list[index]['preset'] = preset
        if preset:
            self.batch_list[index]['preset_name'] = preset.name
        else:
            self.batch_list[index]['preset_name'] = ''
        batch_list = self.ids['photosContainer']
        batch_list.refresh_from_data()

    def add_batch(self):
        app = App.get_running_app()
        if app.last_browse_folder:
            browse_folder = app.last_browse_folder
        else:
            browse_folder = self.folder
        video_filter = []
        for movietype in app.movietypes:
            video_filter.append('*'+movietype)
        content = FileBrowser(ok_text='Add', path=browse_folder, filters=video_filter, multiselect=True, file_editable=False, export_mode=False)
        content.bind(on_cancel=self.dismiss_popup)
        content.bind(on_ok=self.add_batch_check)
        self.popup = NormalPopup(title="Select Videos To Add", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def add_batch_check(self, *_):
        popup = self.popup
        if popup:
            app = App.get_running_app()
            path = popup.content.path
            app.last_browse_folder = path
            files = popup.content.files
            full_files = []
            for file in files:
                full_files.append(os.path.join(path, file))
            self.dismiss_popup()
            self.add_files_to_batch(full_files)

    def add_files_to_batch(self, files):
        files = sorted(files)
        app = App.get_running_app()
        for filepath in files:
            path, file = os.path.split(filepath)
            extension = os.path.splitext(filepath)[1].lower()
            disable_edit = not self.photo
            if extension in app.movietypes:
                self.batch_list.append({
                    'file': file,
                    'path': path,
                    'owner': self,
                    'preset': None,
                    'preset_name': '',
                    'export_file': '',
                    'edit': True,
                    'disable_edit': disable_edit,
                    'encode_state': 'Ready',
                    'message': '',
                    'selected': False,
                    'selectable': True
                })

    def update_disable_edit(self):
        disable_edit = not self.photo
        for batch in self.batch_list:
            batch['disable_edit'] = disable_edit
        batch_list = self.ids['photosContainer']
        batch_list.refresh_from_data()

    def remove_completed_batch(self):
        for file in reversed(self.batch_list):
            if file['encode_state'] == 'Complete':
                self.batch_list.remove(file)
        files_area = self.ids['photos']
        files_area.clear_selects()

    def remove_selected_batch(self):
        for file in reversed(self.batch_list):
            if file['selected']:
                self.batch_list.remove(file)
        files_area = self.ids['photos']
        files_area.clear_selects()

    def clear_batch(self):
        self.batch_list = []
        files_area = self.ids['photos']
        files_area.clear_selects()

    def back(self, *_):
        app = App.get_running_app()
        if self.from_database:
            app.show_database()
        else:
            app.show_album(back=True)

    def dismiss_extra(self):
        if self.encoding:
            self.cancel_encode()
            return True
        elif self.from_database:
            app = App.get_running_app()
            app.show_database()
            return True
        return False

    def browse_export_folder(self):
        try:
            if self.export_folder:
                import webbrowser
                webbrowser.open(self.export_folder)
        except:
            pass

    def on_use_command(self, *_):
        if not self.use_command:
            app = App.get_running_app()
            app.encoding_settings.command_line = ''

    def update_encoding_settings(self, *_):
        app = App.get_running_app()
        if app.encoding_settings.command_line:
            self.use_command = True
        else:
            self.use_command = False

    def show_conversion_panel(self, ensure=False):
        self.show_panel('conversion', ensure)

    def show_info_panel(self):
        self.show_panel('info')

    def show_edit_panel(self):
        self.show_panel('edit')

    def show_panel(self, panel_name, ensure=False):
        right_panel = self.ids['rightpanel']
        if self.view_panel == panel_name and not ensure:
            right_panel.hidden = True
            self.view_panel = ''
        else:
            self.view_panel = panel_name
            right_panel.hidden = False

    def on_leave(self):
        super().on_leave()
        self.save_batch()
        self.clear_edit()
        try:
            app = App.get_running_app()
            batch_container = self.ids['photos']
            for child in batch_container.children:
                child.drag_to = False
            app.main_layout.remove_widget(self.drag_image)
            self.drag_image = None
        except:
            pass

    def clear_edit(self):
        if self.viewer:
            self.viewer.stop()  #Ensure that an old video is no longer playing.
            self.viewer.close()
            self.viewer.end_edit_mode()
            self.viewer = None

        container = self.ids['photoViewerContainer']
        container.clear_widgets()
        edit_panel_container = self.ids['panelEdit']
        edit_panel_container.clear_widgets()
        self.edit_panel_object = None

    def browse_export_begin(self):
        app = App.get_running_app()
        if app.last_browse_folder:
            browse_folder = app.last_browse_folder
        else:
            browse_folder = self.folder
        if not self.use_batch:
            file = self.target
        else:
            file = ''
        content = FileBrowser(ok_text='Select', path=browse_folder, file=file, export_mode=True, allow_no_file=True, file_editable=True)
        content.bind(on_cancel=self.dismiss_popup)
        content.bind(on_ok=self.browse_export_finish)
        self.popup = NormalPopup(title="Select Export Folder", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def browse_export_finish(self, *_):
        popup = self.popup
        if popup:
            app = App.get_running_app()
            path = popup.content.path
            app.last_browse_folder = path
            file = popup.content.file
            self.dismiss_popup()
            self.browse_export_check(path, file)

    def browse_export_check(self, path, file):
        app = App.get_running_app()
        self.export_file = os.path.join(path, file)
        app.message('Export to: '+self.export_file)

    def load_audio_begin(self):
        app = App.get_running_app()
        if app.last_browse_folder:
            browse_folder = app.last_browse_folder
        else:
            browse_folder = self.folder
        audio_filter = []
        for audiotype in app.audiotypes:
            audio_filter.append('*'+audiotype)
        content = FileBrowser(ok_text='Load', path=browse_folder, filters=audio_filter, file_editable=True, export_mode=False, file=self.target)
        content.bind(on_cancel=self.dismiss_popup)
        content.bind(on_ok=self.load_audio_finish)
        self.popup = NormalPopup(title="Select An Audio File", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def load_audio_finish(self, *_):
        popup = self.popup
        if popup:
            app = App.get_running_app()
            path = popup.content.path
            app.last_browse_folder = path
            file = popup.content.file
            self.dismiss_popup()
            self.load_audio_check(path, file)

    def load_audio_check(self, path, file):
        app = App.get_running_app()
        extension = os.path.splitext(file)[1].lower()
        if extension in app.movietypes + app.audiotypes:
            self.audio_file = os.path.join(path, file)
            app.message('Selected file: '+file)
            return
        app.message('Warning: File type not supported')

    def load_video_begin(self, image=False):
        app = App.get_running_app()
        if app.last_browse_folder:
            browse_folder = app.last_browse_folder
        else:
            browse_folder = self.folder
        if image:
            image_filter = []
            for imagetype in app.imagetypes:
                image_filter.append('*'+imagetype)
            content = FileBrowser(ok_text='Load', path=browse_folder, filters=image_filter, export_mode=False, directory_select=True)
            content.bind(on_cancel=self.dismiss_popup)
            content.bind(on_ok=self.load_image_sequence_finish)
            self.popup = NormalPopup(title="Select Image Sequence Folder", content=content, size_hint=(0.9, 0.9))
        else:
            video_filter = []
            for movietype in app.movietypes:
                video_filter.append('*'+movietype)
            content = FileBrowser(ok_text='Load', path=browse_folder, filters=video_filter, file_editable=True, export_mode=False, file=self.target)
            content.bind(on_cancel=self.dismiss_popup)
            content.bind(on_ok=self.load_video_finish)
            self.popup = NormalPopup(title="Select A Video File", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def load_image_sequence_finish(self, *_):
        popup = self.popup
        if popup:
            app = App.get_running_app()
            path = popup.content.path
            app.last_browse_folder = path

            files = popup.content.folder_files
            from filebrowser import sort_nicely
            import fnmatch
            image_filter = []
            for imagetype in app.imagetypes:
                image_filter.append('*'+imagetype)
            filtered_files = []
            for item in image_filter:
                filtered_files += fnmatch.filter(files, item)
            files = filtered_files
            files = sort_nicely(files)

            self.sequence = files
            self.folder = path
            self.target = files[0]
            self.photo = os.path.join(path, files[0])
            app.message('Loaded image sequence from: '+path)

            self.dismiss_popup()

    def load_video_finish(self, *_):
        popup = self.popup
        if popup:
            app = App.get_running_app()
            path = popup.content.path
            app.last_browse_folder = path
            file = popup.content.file
            self.dismiss_popup()
            self.load_video_check(path, file)

    def load_video_check(self, path, file):
        app = App.get_running_app()
        extension = os.path.splitext(file)[1].lower()
        if extension in app.movietypes:
            self.sequence = []
            self.folder = path
            self.target = file
            self.photo = os.path.join(path, file)
            app.message('Loaded file: '+file)
            return
        app.message('Warning: File type not supported')

    def on_enter(self):
        super().on_enter()
        self.show_log = False
        self.show_extra = False
        self.use_batch = False
        self.sequence = []
        self.photo_viewer_current = 'edit'
        self.update_encoding_settings()
        self.show_panel('conversion', ensure=True)
        self.photo = ''
        self.load_batch()
        Clock.schedule_once(self.load_app_photo)  #Delay this to give the previous screen a chance to clear out memory if needed

    def load_app_photo(self, *_):
        app = App.get_running_app()
        if app.photo:
            self.photo = app.photo

    def on_photo(self, *_):
        app = App.get_running_app()
        self.use_audio = False
        self.audio_file = ''
        if self.photo:
            extension = os.path.splitext(self.photo)[1].lower()
            if extension not in app.movietypes:
                if self.sequence:
                    self.photoinfo = []
                    self.fullpath = ''
                    self.export_file = ''
                    self.export_folder = ''
                    self.edit_video()
                    self.refresh_photoinfo()
                    return
                else:
                    self.photo = ''
                    self.folder = ''
                    self.target = ''
                    self.export_file = ''
                    self.export_folder = ''
                    self.photoinfo = []
                    self.edit_video()
                    return
        self.folder, self.target = os.path.split(self.photo)
        photoinfo = app.file_in_database(self.photo)
        if photoinfo:
            self.photoinfo = photoinfo
            self.fullpath = photoinfo[0]
        else:
            self.photoinfo = []
            self.fullpath = ''

        self.export_file = ''
        self.export_folder = ''
        self.edit_video()
        self.refresh_photoinfo()

    def edit_video(self, *_):
        #Start the video editor functionality
        if isfile2(self.photo):
            app = App.get_running_app()
            if self.viewer:
                self.viewer.stop()  #Ensure that an old video is no longer playing.
                self.viewer.close()  #Ensure old video is no longer loaded

            #Set up photo viewer
            container = self.ids['photoViewerContainer']
            container.clear_widgets()
            self.photoinfo = app.database_exists(self.fullpath)
            if self.photoinfo:
                self.orientation = self.photoinfo[13]
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
            self.view_image = False
            self.viewer = VideoViewer(favorite=self.favorite, angle=self.angle, mirror=self.mirror, file=self.photo, photoinfo=self.photoinfo, sequence=self.sequence)
            try:
                self.viewer.framerate_override = float(app.encoding_settings.framerate)
            except:
                self.viewer.framerate_override = 0
            container.add_widget(self.viewer)

            edit_panel = 'edit'
            edit_panel_container = self.ids['panelEdit']
            edit_panel_container.clear_widgets()
            #Start edit mode
            self.viewer.edit_mode = edit_panel
            self.viewer.init_edit_mode()
            self.viewer.bypass = True
            self.edit_panel_object = EditPanelConvert(owner=self, viewer=self.viewer, image=self.viewer.edit_image)
            self.viewer.edit_image.bind(histogram=self.edit_panel_object.draw_histogram)

            edit_panel_container.add_widget(self.edit_panel_object)
        else:
            self.clear_edit()

    def refresh_photoinfo(self):
        """Displays the basic info for the current photo in the photo info right tab."""

        #Clear old info
        info_panel = self.ids['panelInfo']
        nodes = list(info_panel.iterate_all_nodes())
        for node in nodes:
            info_panel.remove_node(node)

        if isfile2(self.photo):
            #Add basic info
            filename = self.target
            info_panel.add_node(TreeViewInfo(title='Filename: ' + filename))
            path = self.folder
            info_panel.add_node(TreeViewInfo(title='Path: ' + path))
            if self.photoinfo:
                database_folder = self.photoinfo[2]
                info_panel.add_node(TreeViewInfo(title='Database: ' + database_folder))
                import_date = datetime.datetime.fromtimestamp(self.photoinfo[6]).strftime('%Y-%m-%d, %I:%M%p')
                info_panel.add_node(TreeViewInfo(title='Import Date: ' + import_date))
            modified_date = datetime.datetime.fromtimestamp(int(os.path.getmtime(self.photo))).strftime('%Y-%m-%d, %I:%M%p')
            info_panel.add_node(TreeViewInfo(title='Modified Date: ' + modified_date))
            file_size = format_size(int(os.path.getsize(self.photo)))
            info_panel.add_node(TreeViewInfo(title='File Size: ' + file_size))

            video = self.viewer.edit_image
            length = time_index(video.length)
            info_panel.add_node(TreeViewInfo(title='Duration: ' + length))
            image_x = video.original_width
            image_y = video.original_height
            resolution = str(image_x) + ' * ' + str(image_y)
            megapixels = round(((image_x * image_y) / 1000000), 2)
            info_panel.add_node(TreeViewInfo(title='Resolution: ' + str(megapixels) + 'MP (' + resolution + ')'))

    def save_log(self):
        app = App.get_running_app()
        app.save_log(self.encode_log, 'encode')
        self.show_extra = True

    def on_encode_log(self, *_):
        if self.popup:
            if hasattr(self.popup, 'encode_log'):
                self.popup.encode_log = self.encode_log

    def save_edit(self):
        app = App.get_running_app()
        self.apply_edit = False
        if self.use_batch:
            if self.viewer:
                if self.photo and self.viewer.edit_image:
                    #save current image settings to local preset
                    self.image_preset(self.viewer.edit_image, to_image=False)
                    self.apply_edit = True
                self.viewer.stop()
            self.clear_edit()
            app.encoding_settings.store_current_encoding_preset()
            self.cancel_encoding = False
            #Create popup to show progress
            self.popup = VideoProcessingPopup(title='Processing Videos', auto_dismiss=False, size_hint=(0.9, 0.9))
            self.popup.scanning_text = ''
            self.popup.open()
            encoding_button = self.popup.ids['scanningButton']
            encoding_button.bind(on_press=self.cancel_encode)

            #Start batch encoding thread
            save_batch_thread = threading.Thread(target=self.save_video_batch)
            save_batch_thread.start()
        else:
            if not self.photo:
                return
            self.apply_edit = True
            app.encoding_settings.store_current_encoding_preset()
            self.viewer.stop()

            #Create popup to show progress
            self.cancel_encoding = False
            self.popup = VideoProcessingPopup(title='Processing Video', auto_dismiss=False, size_hint=(0.9, 0.9))
            self.popup.scanning_text = ''
            self.popup.open()
            encoding_button = self.popup.ids['scanningButton']
            encoding_button.bind(on_press=self.cancel_encode)

            self.clear_log()
            self.encoding_start = time.perf_counter()
            self.append_log("[INFO] : Beginning encode at "+time.strftime("%H:%M:%S", time.localtime()))

            #Start encoding thread
            self.encodingthread = threading.Thread(target=self.save_video_process)
            self.encodingthread.start()

    def save_video_batch(self):
        app = App.get_running_app()
        self.clear_log()
        self.save_batch()

        self.append_log("[INFO] : Beginning encode at "+time.strftime("%H:%M:%S", time.localtime()))

        #Iterate through batches and encode each
        for index, file in enumerate(self.batch_list):
            photo = os.path.join(file['path'], file['file'])
            status_text = 'Encoding file '+str(index + 1)+' of '+str(len(self.batch_list))+': '+photo
            self.popup.overall_process = status_text
            self.append_log('[INFO] : '+status_text)
            self.append_log('')
            if isfile2(photo):
                photoinfo = []
                if file['export_file']:
                    export_file = file['export_file']
                elif self.export_file:
                    export_file = self.export_file
                else:
                    export_file = os.path.join(file['path'], file['file'])
                if file['preset'] is not None:
                    encoding_settings = file['preset'].get_encoding_preset(replace_auto=True)
                else:
                    encoding_settings = app.encoding_settings.get_encoding_preset(replace_auto=True)
                audio_file = ''
                offset_audio_file = False

                #edit_image = CustomImage(photoinfo=photoinfo, source=photo)
                edit_image = ImageEditor(photoinfo=photoinfo, source=photo)

                if self.apply_edit and file['edit']:
                    self.image_preset(edit_image, to_image=True)

                self.encoding_start = time.perf_counter()

                result, reason = self.save_video_process(photo=photo, photoinfo=photoinfo, export_file=export_file, encoding_settings=encoding_settings, audio_file=audio_file, offset_audio_file=offset_audio_file, edit_image=edit_image, start_point=0, end_point=1)

                file['encode_state'] = result
                file['message'] = reason
                edit_image.close_video()
                edit_image.clear_image()
                edit_image = None

                self.append_log('')
                self.append_log('')
            else:
                file['encode_state'] = 'Error'
                file['message'] = "File not found"
                self.append_log("[WARNING] : File not found: "+photo)
                self.append_log('')
                self.append_log('')

            self.save_batch()

            if self.cancel_encoding:
                break

        self.encoding = False
        self.save_log()
        self.dismiss_popup()
        Clock.schedule_once(self.edit_video)
        batch_list = self.ids['photosContainer']
        batch_list.refresh_from_data()


class AlbumScreen(ConversionScreen):
    """Screen layout of the album viewer."""

    folder_title = StringProperty('Album Viewer')
    view_panel = StringProperty('')
    sort_reverse_button = StringProperty('normal')
    canprint = BooleanProperty(True)

    #Widget holder variables
    sort_dropdown = ObjectProperty()  #Holder for the sort method dropdown menu
    edit_panel = StringProperty('')  #The type of edit panel currently loaded
    edit_panel_object = ObjectProperty(allownone=True)  #Holder for the edit panel widget
    album_exports = ObjectProperty()

    #Variables relating to the photo list view on the left
    sort_method = StringProperty('Name')  #Current album sort method
    sort_reverse = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.advanced_encode = False

    def rescale_screen(self):
        app = App.get_running_app()
        self.ids['leftpanel'].width = app.left_panel_width()
        self.ids['rightpanel'].width = app.right_panel_width()

    def export_screen(self):
        """Switches the app to export mode with the current selected album."""

        app = App.get_running_app()
        app.export_target = self.target
        app.export_type = self.type
        app.show_export()

    def collage_screen(self):
        """Switches the app to the collage mode with the current selected album."""

        app = App.get_running_app()
        app.export_target = self.target
        app.export_type = self.type
        app.show_collage()

    def show_panel(self, panel_name):
        right_panel = self.ids['rightpanel']
        if self.view_panel == panel_name:
            self.set_edit_panel('main')
            right_panel.hidden = True
            self.view_panel = ''
            self.show_left_panel()
        else:
            if panel_name == 'edit':
                self.set_edit_panel('edit')
            else:
                self.set_edit_panel('main')
            self.view_panel = panel_name
            right_panel.hidden = False
            app = App.get_running_app()
            if app.simple_interface:
                self.hide_left_panel()

    def show_tags_panel(self, *_):
        self.show_panel('tags')

    def show_info_panel(self, *_):
        self.show_panel('info')

    def show_edit_panel(self, *_):
        self.show_panel('edit')

    def show_left_panel(self, *_):
        left_panel = self.ids['leftpanel']
        left_panel.hidden = False

    def hide_left_panel(self, *_):
        left_panel = self.ids['leftpanel']
        left_panel.hidden = True

    def open_folder(self):
        import os
        if platform == 'android':
            photofile = self.photo

            from jnius import cast
            from jnius import autoclass
            StrictMode = autoclass('android.os.StrictMode')
            StrictMode.disableDeathOnFileUriExposure()

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            #PythonActivity = autoclass('org.renpy.android.PythonActivity')  # Non-sdl2
            Intent = autoclass('android.content.Intent')
            String = autoclass('java.lang.String')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')

            shareIntent = Intent(Intent.ACTION_SEND)
            shareIntent.setType('"image/*"')
            imageFile = File(photofile)

            uri = Uri.fromFile(imageFile)
            parcelable = cast('android.os.Parcelable', uri)
            shareIntent.putExtra(Intent.EXTRA_STREAM, parcelable)

            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(shareIntent)
        else:
            try:
                import webbrowser
                folder = os.path.split(self.photo)[0]
                webbrowser.open(folder)
            except:
                pass

    def set_photo(self, photo):
        self.photo = photo
        Clock.schedule_once(self.refresh_all)

    def on_sort_reverse(self, *_):
        """Updates the sort reverse button's state variable, since kivy doesnt just use True/False for button states."""

        app = App.get_running_app()
        self.sort_reverse_button = 'down' if to_bool(app.config.get('Sorting', 'album_sort_reverse')) else 'normal'

    def delete_original(self):
        """Tries to delete the original version of an edited photo."""

        app = App.get_running_app()
        deleted, message = app.delete_photo_original(self.photoinfo)
        if deleted:
            self.set_edit_panel('edit')
        app.message(message)

    def delete_original_all(self):
        folder = self.photoinfo[1]
        app = App.get_running_app()
        deleted_photos = app.delete_folder_original(folder)
        if len(deleted_photos) > 0:
            app.message('Deleted '+str(len(deleted_photos))+' original files')
            self.set_edit_panel('edit')
        else:
            app.message('Could not delete any original files')

    def restore_original(self):
        """Tries to restore the original version of an edited photo."""

        self.set_edit_panel('main')
        self.viewer.stop()
        app = App.get_running_app()
        edited_file = self.photo
        original_file = os.path.abspath(os.path.join(local_path(self.photoinfo[2]), local_path(self.photoinfo[1]), local_path(self.photoinfo[10])))
        original_filename = os.path.split(original_file)[1]
        edited_filename = os.path.split(edited_file)[1]
        new_original_file = os.path.join(os.path.split(edited_file)[0], original_filename)
        if original_file == new_original_file:
            app.popup_message(text='Could not restore original file, original does not exist', title='Warning')
            return
        if os.path.isfile(original_file):
            if os.path.isfile(edited_file):
                try:
                    os.remove(edited_file)
                except:
                    pass
            if os.path.isfile(edited_file):
                app.popup_message(text='Could not restore original file, error deleting edited file', title='Warning')
                return
            try:
                os.rename(original_file, new_original_file)
            except Exception as e:
                pass
            if os.path.isfile(original_file) or not os.path.isfile(new_original_file):
                app.popup_message(text='Could not restore original file, unable to move original file', title='Warning')
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
            app.save_photoinfo(target=self.photoinfo[1], save_location=os.path.join(self.photoinfo[2], self.photoinfo[1]))

            #regenerate thumbnail
            app.thumbnail_cache.remove_cache(edited_file)
            app.database_thumbnail_update(self.photoinfo[0], self.photoinfo[2], self.photoinfo[7], self.photoinfo[13], force=True)

            #reload photo image in ui
            self.fullpath = self.photoinfo[0]
            self.photo = new_original_file
            app.message("Restored original file.")
            self.clear_cache()
            self.on_photo()
            self.refresh_all()

            #switch active photo in photo list back to image
            self.show_selected()
        else:
            app.popup_message(text='Could not find original file', title='Warning')

    def set_edit_panel(self, panelname):
        """Switches the current edit panel to another."""

        if self.edit_panel_object:
            self.edit_panel_object.save_last()
        edit_panel_container = self.ids['panelEdit']
        edit_panel_container.clear_widgets()
        self.edit_panel_object = None
        self.edit_panel = panelname
        if self.viewer:
            if panelname != 'main' and isfile2(self.photo):
                #Start edit mode
                self.viewer.stop()
                self.viewer.edit_mode = self.edit_panel
                self.viewer.init_edit_mode()
                self.viewer.bypass = True
                self.edit_panel_object = EditPanel(owner=self, viewer=self.viewer, image=self.viewer.edit_image)
                self.viewer.edit_image.bind(histogram=self.edit_panel_object.draw_histogram)
                edit_panel_container.add_widget(self.edit_panel_object)
            else:
                #Close edit mode
                #self.edit_panel_object = EditMain(owner=self)
                self.viewer.edit_mode = 'main'
                self.viewer.bypass = False
                right_panel = self.ids['rightpanel']
                right_panel.hidden = True
                self.view_panel = ''
                self.show_left_panel()

    def export(self):
        """Switches to export screen."""

        if self.photos:
            app = App.get_running_app()
            app.export_target = self.target
            app.export_type = self.type
            app.show_export()

    def dismiss_extra(self):
        """Deactivates fullscreen mode on the video viewer if applicable.
        Returns: True if it was deactivated, False if not.
        """

        dismissed = super().dismiss_extra()
        if dismissed:
            return True
        if self.edit_panel != 'main':
            self.set_edit_panel('main')
            return True
        if self.viewer.fullscreen:
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
                    if self.viewer:
                        self.viewer.fullscreen = not self.viewer.fullscreen
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
                if key == 'end':
                    self.photo_index(-1)
                if key == 'home':
                    self.photo_index(0)
                if key == 'pgup':
                    self.previous_photo(page=True)
                if key == 'pgdn':
                    self.next_photo(page=True)
            elif self.popup and self.popup.open:
                if key == 'enter':
                    self.popup.content.dispatch('on_answer', 'yes')

    def photo_index(self, index, wrap=True):
        photos_length = len(self.photos)
        if index < 0:
            if wrap:
                index = photos_length - 1
            else:
                index = 0
        elif index >= photos_length:
            if wrap:
                index = 0
            else:
                index = photos_length - 1
        new_photo = self.photos[index]
        self.fullpath = new_photo[0]
        self.photo = os.path.join(new_photo[2], new_photo[0])
        self.scroll_photolist()

    def next_photo(self, page=False):
        """Changes the viewed photo to the next photo in the album index."""

        current_photo_index = self.current_photo_index()
        album = self.ids['album']
        album_length = len(album.children) - 1
        if page:
            self.photo_index(current_photo_index + album_length, wrap=False)
        else:
            self.photo_index(current_photo_index + 1)

    def previous_photo(self, page=False):
        """Changes the viewed photo to the previous photo in the album index."""

        current_photo_index = self.current_photo_index()
        album = self.ids['album']
        album_length = len(album.children) - 1
        if page:
            self.photo_index(current_photo_index - album_length, wrap=False)
        else:
            self.photo_index(current_photo_index - 1)

    def update_photoinfo_from_database(self):
        """Reloads the database info and updates the self.photoinfo and self.photos data"""

        app = App.get_running_app()
        self.photoinfo = app.database_exists(self.fullpath)
        self.photos[self.current_photo_index()] = self.photoinfo

    def set_favorite(self):
        """Toggles the currently viewed photo as favorite."""

        app = App.get_running_app()
        if not app.database_scanning:
            if self.target != 'Favorite':
                app.database_toggle_tag(self.fullpath, 'favorite')
                self.update_photoinfo_from_database()
                self.update_tags()
                self.refresh_photolist()
                self.viewer.favorite = self.favorite

    def delete(self):
        """Begins the delete process.  Just calls 'delete_selected_confirm'.
        Not really necessary, but is here to mirror the database screen delete function.
        """

        self.delete_selected_confirm()

    def delete_selected_confirm(self):
        """Creates a delete confirmation popup and opens it."""

        if self.type == 'Tag':
            action_text = 'Remove The Tag "'+self.target+'" From Selected Photo?'
            content = ConfirmPopup(text='The photo will remain in the database and on the disk.', yes_text='Remove', no_text="Don't Remove", warn_yes=True)
        else:
            action_text = 'Delete The Selected File?'
            content = ConfirmPopup(text='The file will be removed from the database and from the disk.', yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        app = App.get_running_app()
        content.bind(on_answer=self.delete_selected_answer)
        self.popup = NormalPopup(title=action_text, content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4), auto_dismiss=False)
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
            self.viewer.stop()
            fullpath = self.fullpath
            filename = self.photo
            if self.type == 'Tag':
                app.database_remove_tag(fullpath, self.target, message=True)
                deleted = True
            else:
                photo_info = app.database_exists(fullpath)
                deleted = app.delete_photo(fullpath, filename, message=True)
                if deleted:
                    if photo_info:
                        app.update_photoinfo(folders=photo_info[1])
            if deleted:
                app.photos.commit()
                if len(self.photos) == 1:
                    app.show_database()
                else:
                    Clock.schedule_once(self.post_delete_update)
        self.dismiss_popup()

    def post_delete_update(self, *_):
        #Cache.remove('kv.loader')
        #Cache.remove('kv.image')
        #Cache.remove('kv.texture')
        self.next_photo()
        self.update_tags()
        Clock.schedule_once(self.update_treeview)

    def current_photo_index(self):
        """Determines the index of the currently viewed photo in the album photos.
        Returns: Integer index value.
        """

        for index, photo in enumerate(self.photos):
            if photo[0] == self.fullpath:
                return index
        return 0

    def remove_from_tag(self, remove_from, tag_name):
        app = App.get_running_app()
        app.database_remove_tag(remove_from, tag_name, message=True)
        self.update_photoinfo_from_database()
        self.update_tags()
        if tag_name.lower() == 'favorite':
            self.update_treeview()

    def add_to_tag(self, tag_name):
        """Adds a tag to the currently viewed photo.
        Arguments:
            tag_name: Tag to add to current photo.
        """

        tag_name = tag_name.strip(' ')
        if tag_name:
            app = App.get_running_app()
            app.database_add_tag(self.fullpath, tag_name)
            self.update_photoinfo_from_database()
            self.update_tags()
            if tag_name.lower() == 'favorite':
                self.update_treeview()

    def can_add_tag(self, tag_name):
        """Checks if a new tag can be created.
        Argument:
            tag_name: The tag name to check.
        Returns: True or False.
        """

        app = App.get_running_app()
        tags = [tag.lower() for tag in app.tags]
        tag_name = tag_name.lower().strip(' ')
        if tag_name and (tag_name not in tags) and (tag_name != 'favorite'):
            return True
        else:
            return False

    def add_tag(self):
        """Adds the current input tag to the app tags."""

        app = App.get_running_app()
        tag_input = self.ids['newTag']
        tag_name = tag_input.text
        tag_name = tag_name.strip(' ')
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
            self.viewer.fullscreen = True

    def on_photo(self, *_):
        """Called when a new photo is viewed.
        Sets up the photo viewer widget and updates all necessary settings."""

        if self.viewer:
            self.viewer.stop()  #Ensure that an old video is no longer playing.
            self.viewer.close()
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
        if os.path.splitext(self.photo)[1].lower() in app.imagetypes:
            #a photo is selected
            self.view_image = True
            if app.canprint():
                print_button = self.ids['printButton']
                print_button.disabled = False
            if not self.photo:
                self.photo = 'data/null.jpg'
            self.viewer = PhotoViewer(favorite=self.favorite, angle=self.angle, mirror=self.mirror, file=self.photo, photoinfo=self.photoinfo)
            container.add_widget(self.viewer)
            self.refresh_photoinfo_simple()
            self.refresh_photoinfo_full()
        else:
            #a video is selected
            self.view_image = False
            if app.canprint():
                print_button = self.ids['printButton']
                print_button.disabled = True
            if not self.photo:
                self.photo = 'data/null.jpg'
            self.viewer = VideoViewer(favorite=self.favorite, angle=self.angle, mirror=self.mirror, file=self.photo, photoinfo=self.photoinfo)
            container.add_widget(self.viewer)
            self.refresh_photoinfo_simple()

        app.refresh_photo(self.fullpath)
        if app.config.getboolean("Settings", "precache"):
            self.cache_nearby_images()
        if self.view_panel == 'edit':
            self.set_edit_panel('edit')
            if self.edit_panel_object:
                self.edit_panel_object.load_last()
        #self.ids['album'].selected = self.fullpath

    def cache_nearby_images(self, *_):
        """Determines the next and previous images in the list, and caches them to speed up browsing."""

        app = App.get_running_app()
        current_photo_index = self.current_photo_index()
        if current_photo_index == len(self.photos) - 1:
            next_photo_index = 0
        else:
            next_photo_index = current_photo_index + 1
        next_photo_info = self.photos[next_photo_index]
        prev_photo_info = self.photos[current_photo_index-1]
        next_photo_filename = os.path.join(next_photo_info[2], next_photo_info[0])
        prev_photo_filename = os.path.join(prev_photo_info[2], prev_photo_info[0])
        if next_photo_filename != self.photo and os.path.splitext(next_photo_filename)[1].lower() in app.imagetypes:
            try:
                if os.path.splitext(next_photo_filename)[1].lower() == '.bmp':
                    next_photo = ImageLoaderPIL(next_photo_filename)
                else:
                    next_photo = Loader.image(next_photo_filename)
            except:
                pass
        if prev_photo_filename != self.photo and os.path.splitext(prev_photo_filename)[1].lower() in app.imagetypes:
            try:
                if os.path.splitext(prev_photo_filename)[1].lower() == '.bmp':
                    prev_photo = ImageLoaderPIL(prev_photo_filename)
                else:
                    prev_photo = Loader.image(prev_photo_filename)
            except:
                pass

    def show_selected(self, *_):
        album_container = self.ids['albumContainer']
        album = self.ids['album']
        selected = self.fullpath
        data = album_container.data
        selected_album = {}
        for i, node in enumerate(data):
            if node['fullpath'] == selected:
                node['selected'] = True
                selected_album = node
            else:
                node['selected'] = False
        album.selected = selected_album
        album_container.scroll_to_selected()
        Clock.schedule_once(album_container.update_selected)
        #album_container.refresh_from_data()

    def scroll_photolist(self, *_):
        """Scroll the right-side photo list to the current active photo."""

        self.show_selected()

    def refresh_all(self, *_):
        self.refresh_photolist()

    def refresh_photolist(self, *_):
        """Reloads and sorts the photo list"""

        app = App.get_running_app()

        #Get photo list
        self.photos = []
        if self.type == 'Tag':
            self.folder_title = 'Tagged As: "'+self.target+'"'
            self.photos = app.database_get_tag(self.target)
        else:
            self.folder_title = 'Folder: "'+self.target+'"'
            self.photos = app.database_get_folder(self.target)

        #Sort photos
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
        self.photos = sorted_photos
        Clock.schedule_once(self.refresh_photoview)

    def refresh_photoview(self, *_):
        #refresh recycleview

        app = App.get_running_app()
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
            photodata['video'] = os.path.splitext(source)[1].lower() in app.movietypes
            photodata['selectable'] = True
            if self.fullpath == photo[0]:
                photodata['selected'] = True
            else:
                photodata['selected'] = False
            photodatas.append(photodata)
        photolist.data = photodatas

    def full_photo_refresh(self):
        app = App.get_running_app()
        app.refresh_photo(self.fullpath, force=True)
        self.on_photo()

    def refresh_photoinfo_simple(self):
        """Displays the basic info for the current photo in the photo info right tab."""

        app = App.get_running_app()

        #Clear old info
        info_panel = self.ids['panelInfo']
        nodes = list(info_panel.iterate_all_nodes())
        for node in nodes:
            info_panel.remove_node(node)

        #Add basic info
        photoinfo = app.database_exists(self.fullpath)
        if not photoinfo:
            return
        full_filename = os.path.join(photoinfo[2], photoinfo[0])
        filename = os.path.basename(photoinfo[0])
        info_panel.add_node(TreeViewInfo(title='Filename: ' + filename))
        path = os.path.join(photoinfo[2], photoinfo[1])
        info_panel.add_node(TreeViewInfo(title='Path: ' + path))
        database_folder = photoinfo[2]
        info_panel.add_node(TreeViewInfo(title='Database: ' + database_folder))
        import_date = datetime.datetime.fromtimestamp(photoinfo[6]).strftime('%Y-%m-%d, %I:%M%p')
        info_panel.add_node(TreeViewInfo(title='Import Date: ' + import_date))
        modified_date = datetime.datetime.fromtimestamp(photoinfo[7]).strftime('%Y-%m-%d, %I:%M%p')
        info_panel.add_node(TreeViewInfo(title='Modified Date: ' + modified_date))
        if os.path.exists(full_filename):
            file_size = format_size(int(os.path.getsize(full_filename)))
        else:
            file_size = format_size(photoinfo[4])
        info_panel.add_node(TreeViewInfo(title='File Size: ' + file_size))
        orientation = photoinfo[13]
        orientation_text = 'No Rotation'
        if orientation == 3 or orientation == 4:
            orientation_text = "Rotate 180 Degrees"
        elif orientation == 5 or orientation == 6:
            orientation_text = "Rotate 90 Degrees"
        elif orientation == 7 or orientation == 8:
            orientation_text = "Rotate 270 Degrees"
        if orientation in [2, 4, 5, 7]:
            orientation_text = orientation_text + ', Flipped'
        info_panel.add_node(TreeViewInfo(title="Orientation: "+orientation_text))

    def refresh_photoinfo_full(self, video=None):
        """Displays all the info for the current photo in the photo info right tab."""

        info_panel = self.ids['panelInfo']
        app = App.get_running_app()
        container = self.ids['photoViewerContainer']

        if not self.view_image:
            if video:
                length = time_index(video.duration)
                info_panel.add_node(TreeViewInfo(title='Duration: ' + length))
                self.image_x, self.image_y = video.texture.size
                resolution = str(self.image_x) + ' * ' + str(self.image_y)
                megapixels = round(((self.image_x * self.image_y) / 1000000), 2)
                info_panel.add_node(TreeViewInfo(title='Resolution: ' + str(megapixels) + 'MP (' + resolution + ')'))
                if 'frame_rate' in video.metadata:
                    framerate = video.metadata['frame_rate']
                    framerate_string = str(framerate[0] / framerate[1])
                    info_panel.add_node(TreeViewInfo(title='Frame Rate: ' + framerate_string))
                if 'src_pix_fmt' in video.metadata:
                    pixel_format = video.metadata['src_pix_fmt']
                    info_panel.add_node(TreeViewInfo(title='Color Format: ' + pixel_format.decode("utf-8")))
        else:
            #Add resolution info
            try:
                pil_image = Image.open(self.photo)
            except:
                pil_image = False
            try:
                exif = pil_image._getexif()
            except:
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
                info_panel.add_node(TreeViewInfo(title='Resolution: ' + str(megapixels) + 'MP (' + resolution + ')'))
            else:
                self.viewer.scale_max = 2
                self.image_x = 0
                self.image_y = 0

            #Add exif info
            if exif:
                if 271 in exif:
                    try:
                        camera_type = exif[271]+' '+exif[272]
                        info_panel.add_node(TreeViewInfo(title='Camera: ' + camera_type))
                    except:
                        pass
                if 33432 in exif:
                    try:
                        copyright = exif[33432]
                        info_panel.add_node(TreeViewInfo(title='Copyright: ' + copyright))
                    except:
                        pass
                if 36867 in exif:
                    try:
                        camera_date = exif[36867]
                        info_panel.add_node(TreeViewInfo(title='Date Taken: ' + camera_date))
                    except:
                        pass
                if 33434 in exif:
                    try:
                        exposure = exif[33434]
                        try:
                            camera_exposure = str(exposure[0]/exposure[1])+'seconds'
                        except:
                            camera_exposure = str(exposure)+'seconds'
                        info_panel.add_node(TreeViewInfo(title='Exposure Time: ' + camera_exposure))
                    except:
                        pass
                if 37377 in exif:
                    try:
                        camera_shutter_speed = str(exif[37377][0]/exif[37377][1])
                        info_panel.add_node(TreeViewInfo(title='Shutter Speed: ' + camera_shutter_speed))
                    except:
                        pass
                if 33437 in exif:
                    try:
                        f_stop = exif[33437]
                        camera_f = str(f_stop[0]/f_stop[1])
                        info_panel.add_node(TreeViewInfo(title='F Stop: ' + camera_f))
                    except:
                        pass
                if 37378 in exif:
                    try:
                        camera_aperture = str(exif[37378][0]/exif[37378][0])
                        info_panel.add_node(TreeViewInfo(title='Aperture: ' + camera_aperture))
                    except:
                        pass
                if 34855 in exif:
                    try:
                        camera_iso = str(exif[34855])
                        info_panel.add_node(TreeViewInfo(title='ISO Level: ' + camera_iso))
                    except:
                        pass
                if 37385 in exif:
                    try:
                        flash = bin(exif[37385])[2:].zfill(8)
                        camera_flash = 'Not Used' if flash[1] == '0' else 'Used'
                        info_panel.add_node(TreeViewInfo(title='Flash: ' + str(camera_flash)))
                    except:
                        pass
                if 37386 in exif:
                    try:
                        focal_length_data = exif[37386]
                        try:
                            focal_length = str(focal_length_data[0]/focal_length_data[1])+'mm'
                        except:
                            focal_length = str(focal_length_data)+'mm'
                        if 41989 in exif:
                            film_focal = exif[41989]
                            if film_focal != 0:
                                focal_length = focal_length+' ('+str(film_focal)+' 35mm equiv.)'
                        info_panel.add_node(TreeViewInfo(title='Focal Length: ' + focal_length))
                    except:
                        pass
                if 41988 in exif:
                    try:
                        digital_zoom_data = exif[41988]
                        if digital_zoom_data:
                            if type(digital_zoom_data) in [list, tuple]:
                                digital_zoom_amount = str(round(digital_zoom_data[0]/digital_zoom_data[1], 2))+'X'
                            else:
                                digital_zoom_amount = str(round(digital_zoom_data, 2))+'X'
                            info_panel.add_node(TreeViewInfo(title='Digital Zoom: ' + digital_zoom_amount))
                    except:
                        pass
                if 34850 in exif:
                    try:
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
                            info_panel.add_node(TreeViewInfo(title='Exposure Mode: ' + program_name))
                    except:
                        pass

    def resort_method(self, method):
        """Sets the album sort method.
        Argument:
            method: String, the sort method to use
        """

        self.sort_method = method
        app = App.get_running_app()
        app.config.set('Sorting', 'album_sort', method)
        self.refresh_all()
        Clock.schedule_once(self.scroll_photolist)

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
        Clock.schedule_once(self.scroll_photolist)

    def on_leave(self):
        """Called when the screen is left.  Clean up some things."""

        super().on_leave()
        self.set_edit_panel('main')
        if self.viewer:
            self.viewer.stop()  #Ensure that an old video is no longer playing.
            self.viewer.end_edit_mode()

        right_panel = self.ids['rightpanel']
        #right_panel.width = app.right_panel_width()
        right_panel.hidden = True
        self.view_panel = ''
        self.show_left_panel()

    def clear_cache(self, *_):
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
        #self.on_photo()
        self.update_tags()
        self.refresh_all()

    def update_treeview(self, *_):
        """Called by delete buttons."""

        self.on_enter()
        self.on_photo()

    def on_enter(self):
        """Called when the screen is entered.  Set up variables and widgets, and prepare to view images."""

        super().on_enter()
        self.use_audio = False
        self.audio_file = ''
        app = App.get_running_app()
        self.ids['leftpanel'].width = app.left_panel_width()
        right_panel = self.ids['rightpanel']
        right_panel.hidden = True
        self.view_panel = ''
        self.show_left_panel()
        self.album_exports = AlbumExportDropDown()

        #set up printing button
        if not app.canprint():
            self.canprint = False
        else:
            self.canprint = True

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
            Clock.schedule_once(self.scroll_photolist)

        #reset edit panel
        self.edit_panel = 'main'


class VideoProcessingPopup(NormalPopup):
    encode_log = ListProperty()
    overall_process = StringProperty()
    button_text = StringProperty('Cancel')
    scanning_percentage = NumericProperty(0)
    scanning_text = StringProperty('')

    def on_open(self, *_):
        Clock.schedule_once(self.scroll_to_bottom)

    def scroll_to_bottom(self, *_):
        logviewerscroller = self.ids['logviewerscroller']
        logviewerscroller.scroll_y = 0


class BatchPhoto(DragBehavior, RecycleItem):
    file = StringProperty('')
    path = StringProperty('')
    preset = ObjectProperty(allownone=True)
    preset_name = StringProperty('')
    export_file = StringProperty('')
    disable_edit = BooleanProperty(False)
    edit = BooleanProperty(False)
    encode_state = StringProperty('Ready')
    owner = ObjectProperty()
    preset_drop = ObjectProperty(allownone=True)
    message = StringProperty('')
    drag = BooleanProperty(False)
    drag_to = BooleanProperty(False)

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.drag = True
            touch.grab(self, exclusive=True)
            window_coords = self.to_window(*touch.pos)
            widget_coords = (touch.pos[0] - self.pos[0], touch.pos[1] - self.pos[1])
            self.owner.drag(self, 'start', window_coords, offset=widget_coords)

    def on_touch_move(self, touch):
        #super().on_touch_move(touch)
        if self.drag:
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            self.owner.drag(self, 'move', window_coords)

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        if self.drag:
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            self.owner.drag(self, 'end', window_coords)
            self.drag = False

    def add_presets_to_menu(self, preset_drop, presets):
        for index, preset in enumerate(presets):
            menu_button = MenuButton(text=preset.name)
            menu_button.remember = preset
            menu_button.bind(on_release=self.set_preset)
            preset_drop.add_widget(menu_button)

    def setup_presets_menu(self):
        app = App.get_running_app()
        self.preset_drop = NormalDropDown()
        menu_button = MenuButton(text='None')
        menu_button.remember = None
        menu_button.bind(on_release=self.set_preset)
        self.preset_drop.add_widget(menu_button)
        self.preset_drop.add_widget(NormalLabel(text='Standard Presets'))
        self.add_presets_to_menu(self.preset_drop, app.encoding_presets)
        self.preset_drop.add_widget(NormalLabel(text='Extra Presets'))
        self.add_presets_to_menu(self.preset_drop, app.encoding_presets_extra)
        if app.encoding_presets_user:
            self.preset_drop.add_widget(NormalLabel(text='User Presets'))
            self.add_presets_to_menu(self.preset_drop, app.encoding_presets_user)

    def select_preset(self, button):
        self.setup_presets_menu()
        self.preset_drop.open(button)

    def remove(self, *_):
        app = App.get_running_app()
        app.clickfade(self, mode='height')
        self.owner.remove_batch(self.index)

    def set_preset(self, instance):
        """Sets the current dialog preset settings to one of the presets stored in the app.
        Argument:
            index: Integer, the index of the preset to set.
        """

        self.preset_drop.dismiss()
        preset = instance.remember
        self.owner.set_preset(self.index, preset)

    def set_export_file(self, text):
        self.owner.set_batch_export_file(self.index, text)

    def select_export(self):
        self.owner.select_batch_export(self.index)

    def clear_export(self):
        self.owner.clear_batch_export(self.index)

    def set_edit(self):
        self.owner.set_batch_edit(self.index)


class EditPanelBase(Screen):
    owner = ObjectProperty()
    image = ObjectProperty()  #Image object that all effects are applied to
    viewer = ObjectProperty()  #Image viewer, used to display the edit modes


class EditPanelAlbumBase(EditPanelBase):
    owner = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_programs()
        self.refresh_buttons()

    def save_last(self):
        pass

    def load_last(self):
        pass

    def refresh_buttons(self):
        self.update_undo()
        self.update_delete_original()
        self.update_delete_original_all()

    def update_delete_original(self):
        """Checks if the current viewed photo has an original file, enables the 'Delete Original' button if so."""

        delete_original_button = self.ids['deleteOriginal']
        photoinfo = self.owner.owner.photoinfo
        if photoinfo[9] == 1 and os.path.isfile(os.path.join(photoinfo[2], photoinfo[1], photoinfo[10])):
            delete_original_button.disabled = False
        else:
            delete_original_button.disabled = True

    def update_delete_original_all(self):
        """Checks if currently viewing a folder, enables 'Delete All Originals' button if so."""

        delete_original_all_button = self.ids['deleteOriginalAll']
        if self.owner.owner.type == 'Folder':
            delete_original_all_button.disabled = False
        else:
            delete_original_all_button.disabled = True

    def update_undo(self):
        """Checks if the current viewed photo has an original file, enables the 'Restore Original' button if so."""

        undo_button = self.ids['undoEdits']
        photoinfo = self.owner.owner.photoinfo
        if photoinfo[9] == 1 and os.path.isfile(os.path.join(photoinfo[2], photoinfo[1], photoinfo[10])):
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
        #self.update_programs(expand=True, expand_index=index)

    def add_program(self):
        """Add a new external program to the programs panel."""

        app = App.get_running_app()
        app.program_add('Program Name', 'command', '%i')
        self.update_programs(expand=True)

    def remove_program(self, index):
        """Removes a program from the external programs list.
        Argument:
            index: Index of the program to remove in the external program list.
        """

        app = App.get_running_app()
        app.program_remove(index)
        self.update_programs()

    def program_run(self, index, button):
        app = App.get_running_app()
        self.owner.owner.set_edit_panel('main')
        app.program_run(index, button)

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
            program_button.bind(on_release=lambda button: self.program_run(button.index, button))
            program_button.bind(on_remove=lambda button: self.remove_program(button.index))
            program_button.content = ExternalProgramEditor(index=index, name=name, command=command, argument=argument, owner=self)
            external_programs.add_widget(program_button)
            if index == expand_index and expand:
                program_button.expanded = True


class EditPanelConversionBase(EditPanelBase):
    pass


class EditPanelColor(EditPanelBase):
    def reset(self, *_):
        self.reset_slide()
        self.reset_brightness()
        self.reset_shadow()
        self.reset_gamma()
        self.reset_saturation()
        self.reset_temperature()
        self.reset_equalize()
        self.reset_autocontrast()
        self.reset_adaptive()
        self.reset_curves()
        self.reset_tint()

    def save(self, preset):
        preset.equalize = self.image.equalize
        preset.autocontrast = self.image.autocontrast
        preset.adaptive = self.image.adaptive_clip
        preset.slide = self.image.slide
        preset.brightness = self.image.brightness
        preset.gamma = self.image.gamma
        preset.saturation = self.image.saturation
        preset.temperature = self.image.temperature
        preset.shadow = self.image.shadow
        preset.tint = self.image.tint
        curves = self.ids['curves']
        preset.curve = curves.points

    def load(self, preset):
        self.image.equalize = preset.equalize
        self.image.autocontrast = preset.autocontrast
        self.image.adaptive_clip = preset.adaptive
        self.image.slide = preset.slide
        self.image.brightness = preset.brightness
        self.image.gamma = preset.gamma
        self.image.saturation = preset.saturation
        self.image.temperature = preset.temperature
        self.image.shadow = preset.shadow
        self.image.tint = preset.tint
        curves = self.ids['curves']
        curves.points = preset.curve
        curves.refresh()

    def update_autocontrast(self, state):
        if state == 'down':
            self.image.autocontrast = True
        else:
            self.image.autocontrast = False

    def reset_autocontrast(self, *_):
        self.image.autocontrast = CustomImage().autocontrast

    def reset_equalize(self, *_):
        self.image.equalize = CustomImage().equalize

    def reset_adaptive(self, *_):
        self.image.adaptive_clip = CustomImage().adaptive_clip

    def reset_slide(self, *_):
        self.image.slide = CustomImage().slide

    def reset_brightness(self, *_):
        self.image.brightness = CustomImage().brightness

    def reset_gamma(self, *_):
        self.image.gamma = CustomImage().gamma

    def reset_shadow(self, *_):
        self.image.shadow = CustomImage().shadow

    def reset_temperature(self, *_):
        self.image.temperature = CustomImage().temperature

    def reset_saturation(self, *_):
        self.image.saturation = CustomImage().saturation

    def remove_point(self, *_):
        """Tells the curves widget to remove its last point."""

        curves = self.ids['curves']
        curves.remove_point()

    def reset_curves(self, *_):
        """Tells the curves widget to reset to its default points."""

        curves = self.ids['curves']
        curves.reset()

    def reset_tint(self, *_):
        self.image.tint = CustomImage().tint


class EditPanelFilter(EditPanelBase):
    def reset(self, *_):
        self.reset_sharpen()
        self.reset_median()
        self.reset_bilateral_amount()
        self.reset_bilateral()
        self.reset_vignette_amount()
        self.reset_vignette_size()
        self.reset_edge_blur_amount()
        self.reset_edge_blur_size()
        self.reset_edge_blur_intensity()

    def save(self, preset):
        preset.sharpen = self.image.sharpen
        preset.median = self.image.median_blur
        preset.bilateral_amount = self.image.bilateral_amount
        preset.bilateral = self.image.bilateral
        preset.vignette_amount = self.image.vignette_amount
        preset.vignette_size = self.image.vignette_size
        preset.edge_blur_amount = self.image.edge_blur_amount
        preset.edge_blur_size = self.image.edge_blur_size
        preset.edge_blur_intensity = self.image.edge_blur_intensity

    def load(self, preset):
        self.image.sharpen = preset.sharpen
        self.image.median_blur = preset.median
        self.image.bilateral_amount = preset.bilateral_amount
        self.image.bilateral = preset.bilateral
        self.image.vignette_amount = preset.vignette_amount
        self.image.vignette_size = preset.vignette_size
        self.image.edge_blur_amount = preset.edge_blur_amount
        self.image.edge_blur_size = preset.edge_blur_size
        self.image.edge_blur_intensity = preset.edge_blur_intensity

    def reset_sharpen(self, *_):
        self.image.sharpen = CustomImage().sharpen

    def reset_median(self, *_):
        self.image.median_blur = CustomImage().median_blur

    def reset_bilateral_amount(self, *_):
        self.image.bilateral_amount = CustomImage().bilateral_amount

    def reset_bilateral(self, *_):
        self.image.bilateral = CustomImage().bilateral

    def reset_vignette_amount(self, *_):
        self.image.vignette_amount = CustomImage().vignette_amount

    def reset_vignette_size(self, *_):
        self.image.vignette_size = CustomImage().vignette_size

    def reset_edge_blur_amount(self, *_):
        self.image.edge_blur_amount = CustomImage().edge_blur_amount

    def reset_edge_blur_size(self, *_):
        self.image.edge_blur_size = CustomImage().edge_blur_size

    def reset_edge_blur_intensity(self, *_):
        self.image.edge_blur_intensity = CustomImage().edge_blur_intensity


class EditPanelBorder(EditPanelBase):
    selected = StringProperty()
    borders = ListProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.populate_borders)
        super(EditPanelBorder, self).__init__(**kwargs)

    def reset(self, *_):
        self.selected = ''
        self.reset_border_x_scale()
        self.reset_border_y_scale()
        self.reset_border_opacity()
        self.reset_border_tint()

    def save(self, preset):
        preset.border_selected = self.selected
        preset.border_x_scale = self.image.border_x_scale
        preset.border_y_scale = self.image.border_y_scale
        preset.border_opacity = self.image.border_opacity
        preset.border_tint = self.image.border_tint

    def load(self, preset):
        self.selected = preset.border_selected
        self.image.border_x_scale = preset.border_x_scale
        self.image.border_y_scale = preset.border_y_scale
        self.image.border_opacity = preset.border_opacity
        self.image.border_tint = preset.border_tint
        self.select_border()

    def populate_borders(self, *_):
        self.borders = [None]
        borders_dir = os.path.join(app_directory, 'borders')
        if os.path.isdir(borders_dir):
            for file in os.listdir(borders_dir):
                if file.endswith('.txt'):
                    border_name = os.path.splitext(file)[0]
                    border_sizes = []
                    border_images = []
                    with open(os.path.join(borders_dir, file)) as input_file:
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

    def select_border(self):
        borders_tree = self.ids['borders']
        nodes = list(borders_tree.iterate_all_nodes())
        if self.selected:
            border_name = self.borders[int(self.selected)][0]
        else:
            border_name = 'None'
        for node in nodes:
            if hasattr(node, 'folder_name'):
                if node.folder_name == border_name:
                    borders_tree.select_node(node)
                    break

    def on_selected(self, *_):
        if self.selected:
            border_index = int(self.selected)
        else:
            border_index = 0
        self.reset_border_x_scale()
        self.reset_border_y_scale()
        if border_index == 0:
            self.image.border_image = []
        else:
            self.image.border_image = self.borders[border_index]

    def reset_border_x_scale(self, *_):
        self.image.border_x_scale = CustomImage().border_x_scale

    def reset_border_y_scale(self, *_):
        self.image.border_y_scale = CustomImage().border_y_scale

    def reset_border_opacity(self, *_):
        self.image.border_opacity = CustomImage().border_opacity

    def reset_border_tint(self, *_):
        self.image.border_tint = CustomImage().border_tint


class EditPanelDenoise(EditPanelBase):
    luminance_denoise = StringProperty('10')
    color_denoise = StringProperty('10')
    search_window = StringProperty('15')
    block_size = StringProperty('5')

    def __init__(self, **kwargs):
        Clock.schedule_once(self.setup_denoise_preview)
        Clock.schedule_once(self.update_preview)
        super(EditPanelDenoise, self).__init__(**kwargs)

    def reset(self, *_):
        self.image.denoise = False
        self.luminance_denoise = '10'
        self.color_denoise = '10'
        self.search_window = '21'
        self.block_size = '7'

    def save(self, preset):
        preset.denoise = self.image.denoise
        preset.luminance_denoise = self.luminance_denoise
        preset.color_denoise = self.color_denoise
        preset.search_window = self.search_window
        preset.block_size = self.block_size

    def load(self, preset):
        self.image.denoise = preset.denoise
        self.luminance_denoise = preset.luminance_denoise
        self.color_denoise = preset.color_denoise
        self.search_window = preset.search_window
        self.block_size = preset.block_size

    def update_denoise(self, state):
        if state == 'down':
            self.image.denoise = True
        else:
            self.image.denoise = False

    def on_luminance_denoise(self, *_):
        if not self.luminance_denoise:
            luminance_denoise = 0
        else:
            luminance_denoise = int(self.luminance_denoise)
        self.image.luminance_denoise = luminance_denoise
        self.update_preview()

    def on_color_denoise(self, *_):
        if not self.color_denoise:
            color_denoise = 0
        else:
            color_denoise = int(self.color_denoise)
        self.image.color_denoise = color_denoise
        self.update_preview()

    def on_search_window(self, *_):
        if not self.search_window:
            search_window = 0
        else:
            search_window = int(self.search_window)
        if (search_window % 2) == 0:
            search_window = search_window + 1
        self.image.search_window = search_window
        self.update_preview()

    def on_block_size(self, *_):
        if not self.block_size:
            block_size = 0
        else:
            block_size = int(self.block_size)
        if (block_size % 2) == 0:
            block_size = block_size + 1
        self.image.block_size = block_size
        self.update_preview()

    def setup_denoise_preview(self, *_):
        #convert pil image to bytes and display background image

        if not self.image:
            return
        app = App.get_running_app()
        if to_bool(app.config.get("Settings", "lowmem")):
            image = self.image.edit_image
        else:
            image = self.image.get_original_image()
        if not image:
            return
        noise_preview = self.ids['noisePreview']
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_bytes = BytesIO()
        image.save(image_bytes, 'jpeg')
        image_bytes.seek(0)
        noise_preview._coreimage = CoreImage(image_bytes, ext='jpg')
        noise_preview._on_tex_change()

    def update_preview(self, *_):
        #Gets the denoised preview image and updates it in the ui

        if not self.image:
            return

        #Update background image if video
        if self.image.video:
            self.setup_denoise_preview()

        #update overlay image
        scroll_area = self.ids['wrapper']
        width = scroll_area.size[0]
        height = scroll_area.size[1]
        pos_x = int((self.image.original_width * scroll_area.scroll_x) - (width * scroll_area.scroll_x))
        image_pos_y = self.image.original_height - int((self.image.original_height * scroll_area.scroll_y) + (width * (1 - scroll_area.scroll_y)))
        preview = self.image.denoise_preview(width, height, pos_x, image_pos_y)
        if preview is None:
            return
        overlay_image = self.ids['denoiseOverlay']
        widget_pos_y = int((self.image.original_height * scroll_area.scroll_y) - (width * scroll_area.scroll_y))
        overlay_image.pos = [pos_x, widget_pos_y]
        overlay_image._coreimage = CoreImage(preview, ext='jpg')
        overlay_image._on_tex_change()
        overlay_image.opacity = 1


class EditPanelRotate(EditPanelBase):
    def reset(self, *_):
        self.update_angle(0)
        self.ids['angles_0'].state = 'down'
        self.ids['angles_90'].state = 'normal'
        self.ids['angles_180'].state = 'normal'
        self.ids['angles_270'].state = 'normal'
        self.update_flip_horizontal(flip='up')
        self.ids['flip_horizontal'].state = 'normal'
        self.update_flip_vertical(flip='up')
        self.ids['flip_vertical'].state = 'normal'
        self.reset_fine_angle()

    def update_angle(self, angle):
        self.image.rotate_angle = angle

    def update_flip_horizontal(self, flip):
        if flip == 'down':
            self.image.flip_horizontal = True
        else:
            self.image.flip_horizontal = False

    def update_flip_vertical(self, flip):
        if flip == 'down':
            self.image.flip_vertical = True
        else:
            self.image.flip_vertical = False

    def reset_fine_angle(self, *_):
        self.image.fine_angle = CustomImage().fine_angle


class EditPanelCrop(EditPanelBase):
    lock_aspect = BooleanProperty(False)
    lock_aspect_name = StringProperty('Current')
    aspect_dropdown = ObjectProperty()

    def __init__(self, **kwargs):
        self.aspect_dropdown = AspectRatioDropDown()
        self.aspect_dropdown.bind(on_select=lambda instance, x: self.set_aspect_ratio(x))
        Clock.schedule_once(self.setup_crop)
        super(EditPanelCrop, self).__init__(**kwargs)

    def reset(self, *_):
        if self.image:
            self.image.reset_crop()

    def setup_crop(self, *_):
        self.image.crop_controls = self
        self.set_aspect_ratio('Current')
        self.reset()
        self.update_crop_sliders()

    def update_lock_aspect(self, value):
        if value == 'down':
            self.lock_aspect = True
        else:
            self.lock_aspect = False

    def on_lock_aspect(self, *_):
        if self.image:
            self.image.lock_aspect = self.lock_aspect
            if self.lock_aspect:
                self.image.set_aspect()

    def reset_crop_top(self, *_):
        self.image.crop_top = CustomImage().crop_top

    def reset_crop_right(self, *_):
        self.image.crop_right = CustomImage().crop_right

    def reset_crop_bottom(self, *_):
        self.image.crop_bottom = CustomImage().crop_bottom

    def reset_crop_left(self, *_):
        self.image.crop_left = CustomImage().crop_left

    def update_crop_sliders(self, *_):
        self.ids['cropTopSlider'].value = self.image.crop_top
        self.ids['cropRightSlider'].value = self.image.crop_right
        self.ids['cropBottomSlider'].value = self.image.crop_bottom
        self.ids['cropLeftSlider'].value = self.image.crop_left

    def set_aspect_ratio(self, method):
        self.lock_aspect_name = method
        if method == '6x4':
            aspect_x = 6
            aspect_y = 4
        elif method == '4x6':
            aspect_x = 4
            aspect_y = 6
        elif method == '7x5':
            aspect_x = 7
            aspect_y = 5
        elif method == '5x7':
            aspect_x = 5
            aspect_y = 7
        elif method == '11x8.5':
            aspect_x = 11
            aspect_y = 8.5
        elif method == '8.5x11':
            aspect_x = 8.5
            aspect_y = 11
        elif method == '4x3':
            aspect_x = 4
            aspect_y = 3
        elif method == '3x4':
            aspect_x = 3
            aspect_y = 4
        elif method == '16x9':
            aspect_x = 16
            aspect_y = 9
        elif method == '9x16':
            aspect_x = 9
            aspect_y = 16
        elif method == '1x1':
            aspect_x = 1
            aspect_y = 1
        else:
            aspect_x = self.image.original_width
            aspect_y = self.image.original_height
        self.image.set_aspect(aspect_x, aspect_y)


class EditPanelVideo(EditPanelBase):
    #Video encoding dropdown menus
    preset_drop = ObjectProperty()
    container_drop = ObjectProperty()
    video_codec_drop = ObjectProperty()
    quality_drop = ObjectProperty()
    encoding_speed_drop = ObjectProperty()
    encoding_color_drop = ObjectProperty()
    framerate_presets_drop = ObjectProperty()
    resolution_presets_drop = ObjectProperty()
    audio_codec_drop = ObjectProperty()
    advanced = BooleanProperty(False)

    def __init__(self, **kwargs):
        Clock.schedule_once(self.setup_video)
        super(EditPanelVideo, self).__init__(**kwargs)

    def remove_preset(self, preset, instance):
        app = App.get_running_app()
        app.remove_user_encoding_preset(preset)
        self.preset_drop.dismiss()
        self.setup_presets_menu()

    def add_presets_to_menu(self, preset_drop, presets, user=False):
        app = App.get_running_app()
        for index, preset in enumerate(presets):
            menu_button = MenuButton(text=preset.name)
            menu_button.remember = preset
            menu_button.bind(on_release=self.set_preset)
            if user:
                menu_holder = BoxLayout(orientation='horizontal', size_hint_y=None, height=app.button_scale)
                menu_holder.add_widget(menu_button)
                remove_button = NormalButton(warn=True, text="X")
                remove_button.bind(on_release=partial(self.remove_preset, preset))
                menu_holder.add_widget(remove_button)
                preset_drop.add_widget(menu_holder)
            else:
                preset_drop.add_widget(menu_button)

    def setup_presets_menu(self):
        app = App.get_running_app()
        self.preset_drop = NormalDropDown()
        self.add_presets_to_menu(self.preset_drop, app.encoding_presets)
        if self.advanced:
            self.preset_drop.add_widget(NormalLabel(text='Extra Presets'))
            self.add_presets_to_menu(self.preset_drop, app.encoding_presets_extra)
            if app.encoding_presets_user:
                self.preset_drop.add_widget(NormalLabel(text='User Presets'))
                self.add_presets_to_menu(self.preset_drop, app.encoding_presets_user, user=True)

    def setup_video(self, *_):
        app = App.get_running_app()
        self.setup_presets_menu()
        containers_friendly = get_keys_from_list(app.containers)
        video_codecs_friendly = get_keys_from_list(app.video_codecs)
        audio_codecs_friendly = get_keys_from_list(app.audio_codecs)

        all_containers = ['Auto'] + containers_friendly
        self.container_drop = NormalDropDown()
        for container in all_containers:
            menu_button = MenuButton(text=container)
            menu_button.bind(on_release=self.change_container_to)
            self.container_drop.add_widget(menu_button)

        all_video_codecs = ['Auto'] + video_codecs_friendly
        self.video_codec_drop = NormalDropDown()
        for codec in all_video_codecs:
            menu_button = MenuButton(text=codec)
            menu_button.bind(on_release=self.change_video_codec_to)
            self.video_codec_drop.add_widget(menu_button)

        qualities = ['Auto']+encoding_quality_friendly
        self.quality_drop = NormalDropDown()
        for quality in qualities:
            menu_button = MenuButton(text=quality)
            menu_button.bind(on_release=self.change_quality_to)
            self.quality_drop.add_widget(menu_button)

        all_encoding_speeds = ['Auto'] + encoding_speeds_friendly
        self.encoding_speed_drop = NormalDropDown()
        for speed in all_encoding_speeds:
            menu_button = MenuButton(text=speed)
            menu_button.bind(on_release=self.change_encoding_speed_to)
            self.encoding_speed_drop.add_widget(menu_button)

        all_encoding_colors = ['Auto'] + encoding_colors_friendly
        self.encoding_color_drop = NormalDropDown()
        for color in all_encoding_colors:
            menu_button = MenuButton(text=color)
            menu_button.bind(on_release=self.change_encoding_color_to)
            self.encoding_color_drop.add_widget(menu_button)

        all_audio_codecs = ['Auto'] + audio_codecs_friendly
        self.audio_codec_drop = NormalDropDown()
        for codec in all_audio_codecs:
            menu_button = MenuButton(text=codec)
            menu_button.bind(on_release=self.change_audio_codec_to)
            self.audio_codec_drop.add_widget(menu_button)

        self.framerate_presets_drop = NormalDropDown()
        self.framerate_presets_drop.auto_width = False
        for framerate in framerate_presets:
            menu_button = MenuButton(text=framerate)
            menu_button.bind(on_release=self.change_framerate_to)
            self.framerate_presets_drop.add_widget(menu_button)

        self.resolution_presets_drop = NormalDropDown()
        self.resolution_presets_drop.auto_width = False
        for resolution in resolution_presets:
            menu_button = MenuButton(text=resolution)
            menu_button.bind(on_release=self.change_resolution_to)
            self.resolution_presets_drop.add_widget(menu_button)

    def set_preset(self, instance):
        """Sets the current dialog preset settings to one of the presets stored in the app.
        Argument:
            index: Integer, the index of the preset to set.
        """

        self.preset_drop.dismiss()
        app = App.get_running_app()
        app.encoding_settings.copy_from(instance.remember)
        self.owner.update_encoding_settings()

    def change_framerate_to(self, instance):
        app = App.get_running_app()
        self.framerate_presets_drop.dismiss()
        app.encoding_settings.framerate = instance.text

    def change_resolution_to(self, instance):
        app = App.get_running_app()
        res_x, res_y = instance.text.split('x')
        self.resolution_presets_drop.dismiss()
        app.encoding_settings.resize_width = res_x
        app.encoding_settings.resize_height = res_y

    def change_container_to(self, instance):
        """Sets the self.file_format value."""

        app = App.get_running_app()
        self.container_drop.dismiss()
        app.encoding_settings.file_format = instance.text

    def change_video_codec_to(self, instance):
        """Sets the self.video_codec value."""

        app = App.get_running_app()
        self.video_codec_drop.dismiss()
        app.encoding_settings.video_codec = instance.text

    def change_audio_codec_to(self, instance):
        """Sets the self.audio_codec value."""

        app = App.get_running_app()
        self.audio_codec_drop.dismiss()
        app.encoding_settings.audio_codec = instance.text

    def update_resize(self, state):
        app = App.get_running_app()
        if state == 'down':
            app.encoding_settings.resize = True
        else:
            app.encoding_settings.resize = False

    def change_encoding_speed_to(self, instance):
        """Sets the self.encoding_speed value."""

        app = App.get_running_app()
        self.encoding_speed_drop.dismiss()
        app.encoding_settings.encoding_speed = instance.text

    def change_encoding_color_to(self, instance):
        app = App.get_running_app()
        self.encoding_color_drop.dismiss()
        app.encoding_settings.encoding_color = instance.text

    def update_deinterlace(self, state):
        app = App.get_running_app()
        if state == 'down':
            app.encoding_settings.deinterlace = True
        else:
            app.encoding_settings.deinterlace = False

    def change_quality_to(self, instance):
        """Sets the quality value."""

        app = App.get_running_app()
        self.quality_drop.dismiss()
        app.encoding_settings.quality = instance.text


class EditPanelConvert(BoxLayout):
    image = ObjectProperty()  #Image object that all effects are applied to
    viewer = ObjectProperty()  #Image viewer, used to display the edit modes
    owner = ObjectProperty()  #Panel holder

    edit_panel_base = ObjectProperty()
    edit_panel_color = ObjectProperty()
    edit_panel_filter = ObjectProperty()
    edit_panel_border = ObjectProperty()
    edit_panel_denoise = ObjectProperty()
    edit_panel_rotate = ObjectProperty()
    edit_panel_crop = ObjectProperty()
    edit_panel_video = ObjectProperty()

    def __init__(self, **kwargs):
        Clock.schedule_once(self.setup_screen_manager)
        super(EditPanelConvert, self).__init__(**kwargs)

    def setup_screen_manager(self, *_):
        screen_manager = self.ids['sm']
        self.edit_panel_base = EditPanelConversionBase(name='edit', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_color = EditPanelColor(name='color', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_filter = EditPanelFilter(name='filter', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_border = EditPanelBorder(name='border', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_denoise = EditPanelDenoise(name='denoise', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_rotate = EditPanelRotate(name='rotate', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_crop = EditPanelCrop(name='crop', owner=self, image=self.image, viewer=self.viewer)
        screen_manager.add_widget(self.edit_panel_base)
        screen_manager.add_widget(self.edit_panel_color)
        screen_manager.add_widget(self.edit_panel_filter)
        screen_manager.add_widget(self.edit_panel_border)
        screen_manager.add_widget(self.edit_panel_denoise)
        screen_manager.add_widget(self.edit_panel_rotate)
        screen_manager.add_widget(self.edit_panel_crop)

    def change_screen(self, current):
        #Called when edit screen changes, sets the image to the right edit type
        self.viewer.edit_mode = current

    def confirm_edit(self, *_):
        self.owner.save_edit()

    def draw_histogram(self, *_):
        """Draws the histogram image and displays it."""

        if self.image is None:
            return
        size = 256  #Determines histogram resolution
        size_multiplier = int(256/size)
        histogram_data = self.image.histogram
        if len(histogram_data) == 768:
            histogram = self.ids['histogram']
            histogram.opacity = 1
            histogram_max = max(histogram_data)
            data_red = histogram_data[0:256]
            data_green = histogram_data[256:512]
            data_blue = histogram_data[512:768]
            multiplier = 256.0/histogram_max/size_multiplier

            #Draw red channel
            histogram_red = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
            draw = ImageDraw.Draw(histogram_red)
            for index in range(size):
                value = int(data_red[index*size_multiplier]*multiplier)
                draw.line((index, size, index, size-value), fill=(255, 0, 0))

            #Draw green channel
            histogram_green = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
            draw = ImageDraw.Draw(histogram_green)
            for index in range(size):
                value = int(data_green[index*size_multiplier]*multiplier)
                draw.line((index, size, index, size-value), fill=(0, 255, 0))

            #Draw blue channel
            histogram_blue = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
            draw = ImageDraw.Draw(histogram_blue)
            for index in range(size):
                value = int(data_blue[index*size_multiplier]*multiplier)
                draw.line((index, size, index, size-value), fill=(0, 0, 255))

            #Mix channels together
            histogram_red_green = ImageChops.add(histogram_red, histogram_green)
            histogram_image = ImageChops.add(histogram_red_green, histogram_blue)

            #Convert and display image
            image_bytes = BytesIO()
            histogram_image.save(image_bytes, 'jpeg')
            image_bytes.seek(0)
            histogram._coreimage = CoreImage(image_bytes, ext='jpg')
            histogram._on_tex_change()

    def save_last(self, *_):
        pass

    def reset_all(self, *_):
        self.edit_panel_color.reset()
        self.edit_panel_filter.reset()
        self.edit_panel_border.reset()
        self.edit_panel_denoise.reset()
        self.edit_panel_rotate.reset()
        self.edit_panel_crop.reset()


class EditPanel(BoxLayout):
    image = ObjectProperty()  #Image object that all effects are applied to
    viewer = ObjectProperty()  #Image viewer, used to display the edit modes
    owner = ObjectProperty()  #Panel holder

    edit_panel_base = ObjectProperty()
    edit_panel_color = ObjectProperty()
    edit_panel_filter = ObjectProperty()
    edit_panel_border = ObjectProperty()
    edit_panel_denoise = ObjectProperty()
    edit_panel_rotate = ObjectProperty()
    edit_panel_crop = ObjectProperty()
    edit_panel_video = ObjectProperty()

    def __init__(self, **kwargs):
        super(EditPanel, self).__init__(**kwargs)
        self.setup_screens()
        Clock.schedule_once(self.setup_screen_manager)

    def setup_screens(self):
        self.edit_panel_base = EditPanelAlbumBase(name='edit', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_color = EditPanelColor(name='color', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_filter = EditPanelFilter(name='filter', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_border = EditPanelBorder(name='border', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_denoise = EditPanelDenoise(name='denoise', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_rotate = EditPanelRotate(name='rotate', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_crop = EditPanelCrop(name='crop', owner=self, image=self.image, viewer=self.viewer)
        self.edit_panel_video = EditPanelVideo(name='video', owner=self.owner, image=self.image, viewer=self.viewer)

    def setup_screen_manager(self, *_):
        screen_manager = self.ids['sm']
        screen_manager.add_widget(self.edit_panel_base)
        screen_manager.add_widget(self.edit_panel_color)
        screen_manager.add_widget(self.edit_panel_filter)
        screen_manager.add_widget(self.edit_panel_border)
        screen_manager.add_widget(self.edit_panel_denoise)
        screen_manager.add_widget(self.edit_panel_rotate)
        screen_manager.add_widget(self.edit_panel_crop)
        screen_manager.add_widget(self.edit_panel_video)

    def change_screen(self, current):
        #Called when edit screen changes, sets the image to the right edit type
        self.viewer.edit_mode = current

    def confirm_edit(self, *_):
        self.owner.save_edit()

    def cancel_edit(self, *_):
        self.owner.set_edit_panel('main')

    def draw_histogram(self, *_):
        """Draws the histogram image and displays it."""

        if self.image is None:
            return
        size = 256  #Determines histogram resolution
        size_multiplier = int(256/size)
        histogram_data = self.image.histogram
        if len(histogram_data) == 768:
            histogram = self.ids['histogram']
            histogram.opacity = 1
            histogram_max = max(histogram_data)
            data_red = histogram_data[0:256]
            data_green = histogram_data[256:512]
            data_blue = histogram_data[512:768]
            multiplier = 256.0/histogram_max/size_multiplier

            #Draw red channel
            histogram_red = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
            draw = ImageDraw.Draw(histogram_red)
            for index in range(size):
                value = int(data_red[index*size_multiplier]*multiplier)
                draw.line((index, size, index, size-value), fill=(255, 0, 0))

            #Draw green channel
            histogram_green = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
            draw = ImageDraw.Draw(histogram_green)
            for index in range(size):
                value = int(data_green[index*size_multiplier]*multiplier)
                draw.line((index, size, index, size-value), fill=(0, 255, 0))

            #Draw blue channel
            histogram_blue = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
            draw = ImageDraw.Draw(histogram_blue)
            for index in range(size):
                value = int(data_blue[index*size_multiplier]*multiplier)
                draw.line((index, size, index, size-value), fill=(0, 0, 255))

            #Mix channels together
            histogram_red_green = ImageChops.add(histogram_red, histogram_green)
            histogram_image = ImageChops.add(histogram_red_green, histogram_blue)

            #Convert and display image
            image_bytes = BytesIO()
            histogram_image.save(image_bytes, 'jpeg')
            image_bytes.seek(0)
            histogram._coreimage = CoreImage(image_bytes, ext='jpg')
            histogram._on_tex_change()

    def save_last(self, *_):
        self.owner.edit_color = True
        self.edit_panel_color.save(self.owner)
        self.edit_panel_filter.save(self.owner)
        self.edit_panel_border.save(self.owner)
        self.edit_panel_denoise.save(self.owner)

    def load_last(self, *_):
        self.edit_panel_color.load(self.owner)
        self.edit_panel_filter.load(self.owner)
        self.edit_panel_border.load(self.owner)
        self.edit_panel_denoise.load(self.owner)

    def reset_all(self, *_):
        self.edit_panel_color.reset()
        self.edit_panel_filter.reset()
        self.edit_panel_border.reset()
        self.edit_panel_denoise.reset()
        self.edit_panel_rotate.reset()
        self.edit_panel_crop.reset()


class PanelTabs(FloatLayout):
    tab = StringProperty('')
    animate_in = None
    animate_out = None

    def disable_tab(self, tab, *_):
        tab.disabled = True
        tab.size_hint_x = 0

    def on_tab(self, *_):
        app = App.get_running_app()
        animate_in = Animation(opacity=1, duration=app.animation_length)
        animate_out = Animation(opacity=0, duration=app.animation_length)
        for child in self.children:
            if self.animate_in:
                self.animate_in.cancel(child)
            if self.animate_out:
                self.animate_out.cancel(child)
            if child.tab == self.tab:
                child.size_hint_x = 1
                child.disabled = False
                if app.animations:
                    animate_in.start(child)
                else:
                    child.opacity = 1
            else:
                if app.animations:
                    animate_out.start(child)
                    animate_out.bind(on_complete=partial(self.disable_tab, child))
                else:
                    child.opacity = 0
                    child.disabled = True
                    child.size_hint_x = 0
        self.animate_in = animate_in
        self.animate_out = animate_out


class TreeViewInfo(BoxLayout, TreeViewNode):
    """Simple treeview node to display a line of text.
    Has two elements, they will be shown as: 'title: content'"""

    title = StringProperty()


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


class ExitFullscreenButton(NormalButton):
    owner = ObjectProperty()

    def on_press(self):
        self.owner.fullscreen = False


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
                    photocontainer.on_zoom()  #Need to call this manually because sometimes it doesnt get called...?
                else:
                    zoompos = self.to_local(touch.pos[0], touch.pos[1])
                    photocontainer.zoompos = zoompos
                    photocontainer.zoom = 1

        else:
            super(PhotoShow, self).on_touch_down(touch)


class PhotoViewer(BoxLayout):
    """Holds the fullsized photo image in album view mode."""

    photoinfo = ListProperty()
    favorite = BooleanProperty(False)
    angle = NumericProperty(0)
    mirror = BooleanProperty(False)
    file = StringProperty()
    scale_max = NumericProperty(1)
    edit_mode = StringProperty('main')
    edit_image = ObjectProperty(allownone=True)
    overlay = ObjectProperty(allownone=True)
    bypass = BooleanProperty(False)
    zoom = NumericProperty(0)
    zoompos = ListProperty([0, 0])
    fullscreen = BooleanProperty(False)
    _fullscreen_state = None
    exit_button = ObjectProperty()

    def on_height(self, *_):
        self.reset_zoompos()

    def reset_zoompos(self):
        self.zoompos = [self.width / 2, self.height / 2]

    def reset_zoom(self, *_):
        self.zoom = 0

    def on_zoom(self, *_):
        if self.zoom == 0:
            self.reset_zoompos()
        scale_max = self.scale_max
        scale_size = 1 + ((scale_max - 1) * self.zoom)
        scale = Matrix().scale(scale_size, scale_size, scale_size)
        #wrapper = LimitedScatterLayout()
        wrapper = self.ids['wrapper']
        wrapper.transform = Matrix()
        zoompos = self.zoompos
        wrapper.apply_transform(scale, anchor=zoompos)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                if self.edit_mode != 'main' and self.edit_image.cropping:
                    self.edit_image.reset_crop()
                    return True
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

    def refresh(self):
        """Updates the image subwidget's source file."""

        image = self.ids['image']
        image.source = self.file

    def init_edit_mode(self, *_):
        if not self.edit_image:
            self.edit_image = CustomImage(mirror=self.mirror, angle=self.angle, photoinfo=self.photoinfo, source=self.file)
            viewer = self.ids['photoShow']
            viewer.add_widget(self.edit_image)

    def on_edit_mode(self, *_):
        """Called when the user enters or exits edit mode.
        Adds the edit image widget, and overlay if need be, and sets them up."""

        image = self.ids['image']
        self.init_edit_mode()
        viewer = self.ids['photoShow']
        if self.overlay:
            viewer.remove_widget(self.overlay)
            self.overlay = None
        if self.edit_mode == 'main':
            image.opacity = 1
            self.end_edit_mode()
        else:
            Clock.schedule_once(self.start_edit_mode)  #Need to delay this because if i add it right away it will show a non-rotated version for some reason

    def end_edit_mode(self, *_):
        if self.edit_image:
            viewer = self.ids['photoShow']
            viewer.remove_widget(self.edit_image)
            self.edit_image.clear_image()
            self.edit_image = None

    def start_edit_mode(self, *_):
        if self.edit_image is None:
            return
        image = self.ids['image']
        image.opacity = 0
        viewer = self.ids['photoShow']

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
        elif self.edit_image.crop_top != 0 or self.edit_image.crop_bottom != 0 or self.edit_image.crop_left != 0 or self.edit_image.crop_right != 0:
            #not currently cropping, need to display crop blackout
            self.edit_image.update_preview()

    def stop(self):
        self.fullscreen = False
        if self.edit_image:
            self.edit_image.close_image()

    def close(self):
        self.end_edit_mode()

    def on_fullscreen(self, instance, value):
        window = self.get_parent_window()
        if value:
            self._fullscreen_state = state = {
                'parent': self.parent,
                'pos': self.pos,
                'size': self.size,
                'pos_hint': self.pos_hint,
                'size_hint': self.size_hint,
                'window_children': window.children[:]}

            #remove all window children
            for child in window.children[:]:
                window.remove_widget(child)

            #put the video in fullscreen
            if state['parent'] is not window:
                state['parent'].remove_widget(self)
            window.add_widget(self)

            #ensure the widget is in 0, 0, and the size will be readjusted
            self.pos = (0, 0)
            self.size = (100, 100)
            self.pos_hint = {}
            self.size_hint = (1, 1)
            self.exit_button = ExitFullscreenButton(owner=self)
            window.add_widget(self.exit_button)

        else:
            state = self._fullscreen_state
            window.remove_widget(self)
            window.remove_widget(self.exit_button)
            for child in state['window_children']:
                window.add_widget(child)
            self.pos_hint = state['pos_hint']
            self.size_hint = state['size_hint']
            self.pos = state['pos']
            self.size = state['size']
            if state['parent'] is not window:
                state['parent'].add_widget(self)


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
    position = NumericProperty(0.0)
    position_time_index = StringProperty()
    start_point = NumericProperty(0.0)
    end_point = NumericProperty(1.0)
    fullscreen = BooleanProperty(False)
    overlay = ObjectProperty(allownone=True)
    sequence = ListProperty()
    framerate_override = NumericProperty(0)

    def on_framerate_override(self, *_):
        if self.edit_image:
            self.edit_image.framerate_override = self.framerate_override

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                if self.edit_mode != 'main' and self.edit_image.cropping:
                    self.edit_image.reset_crop()
                    return True
            return super(VideoViewer, self).on_touch_down(touch)

    def reset_start_point(self, *_):
        self.start_point = 0.0

    def reset_end_point(self, *_):
        self.end_point = 1.0

    def set_start_point(self, *_):
        if self.position < 1.0:
            self.start_point = self.position
            if self.end_point <= self.start_point:
                self.reset_end_point()

    def set_end_point(self, *_):
        if self.position > 0.0:
            self.end_point = self.position
            if self.start_point >= self.end_point:
                self.reset_start_point()

    def on_position(self, *_):
        if self.edit_image:
            self.edit_image.position = self.position
            position_seconds = self.edit_image.length * self.position
            minutes, seconds = divmod(position_seconds, 60)
            self.position_time_index = str(int(minutes))+':'+format(round(seconds, 2), '.2f').zfill(5)
        else:
            self.position_time_index = ''

    def on_start_point(self, *_):
        if self.edit_image:
            self.edit_image.start_point = self.start_point

    def on_end_point(self, *_):
        if self.edit_image:
            self.edit_image.end_point = self.end_point

    def init_edit_mode(self, *_):
        if not self.edit_image:
            self.edit_image = CustomImage(sequence=self.sequence, mirror=self.mirror, angle=self.angle, photoinfo=self.photoinfo, source=self.file)
            self.edit_image.framerate_override = self.framerate_override
            viewer = self.ids['photoShow']
            viewer.add_widget(self.edit_image)
            self.position = 0

    def on_edit_mode(self, *_):
        """Called when the user enters or exits edit mode.
        Adds the edit image widget, and overlay if need be, and sets them up."""

        self.init_edit_mode()
        overlay_container = self.ids['overlay']
        player = self.ids['player']
        viewer = self.ids['photoShow']
        if self.overlay:
            viewer.remove_widget(self.overlay)
            self.overlay = None
        if self.edit_mode == 'main':
            self.reset_start_point()
            self.reset_end_point()
            player.opacity = 1
            overlay_container.opacity = 0
            self.end_edit_mode()
        else:
            overlay_container.opacity = 1
            player.opacity = 0
            viewer = self.ids['photoShow']
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

    def end_edit_mode(self, *_):
        if self.edit_image:
            viewer = self.ids['photoShow']
            viewer.remove_widget(self.edit_image)
            self.edit_image.close_video()
            self.edit_image.clear_image()
            self.edit_image = None

    def on_fullscreen(self, instance, value):
        player = self.ids['player']
        player.fullscreen = self.fullscreen

    def close(self):
        player = self.ids['player']
        player.close()
        self.end_edit_mode()

    def stop(self):
        """Stops the video playback."""

        player = self.ids['player']
        self.fullscreen = False
        player.state = 'stop'


class SpecialVideoPlayer(VideoPlayer):
    """Custom VideoPlayer class that replaces the default video widget with the 'PauseableVideo' widget."""

    photoinfo = ListProperty()
    mirror = BooleanProperty(False)
    favorite = BooleanProperty(False)
    exit_button = ObjectProperty()
    owner = ObjectProperty()

    def close(self):
        if self._video is not None:
            self._video.unload()
            self._video = None
        self._image = None
        self.container.clear_widgets()

    def _try_load_default_thumbnail(self, *_):
        self._load_thumbnail()

    def _load_thumbnail(self, *_):
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
            self.owner = self.parent
        if self.owner.fullscreen != self.fullscreen:
            self.owner.fullscreen = self.fullscreen
        super(SpecialVideoPlayer, self).on_fullscreen(instance, value)
        window = self.get_parent_window()
        if self.fullscreen:
            self.exit_button = ExitFullscreenButton(owner=self)
            window.add_widget(self.exit_button)
            self.exit_button.pos[1] = 45
        else:
            window.remove_widget(self.exit_button)

    def _do_video_load(self, *largs):
        """this function has been changed to replace the Video object with the special PauseableVideo object.
        Also, checks if auto-play videos are enabled in the settings.
        """

        if isfile2(self.source):
            self._video = PauseableVideo(source=self.source, state=self.state, volume=self.volume, pos_hint={'x': 0, 'y': 0}, **self.options)
            self._video.bind(texture=self._play_started, duration=self.setter('duration'), position=self.setter('position'), volume=self.setter('volume'), state=self._set_state)
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


class PauseableVideo(Video):
    """modified Video class to allow clicking anywhere to pause/resume."""

    first_load = True
    aspect = NumericProperty(1)

    def get_norm_image_size(self):
        if not self.texture:
            return list(self.size)

        ratio = self.image_ratio / self.aspect  #changed from original code to allow non-square pixels in videos
        w, h = self.size
        tw, th = self.texture.size

        if self.fit_mode == "cover":
            widget_ratio = w / max(1, h)
            if widget_ratio > ratio:
                return [w, (w * th) / tw]
            else:
                return [(h * tw) / th, h]
        elif self.fit_mode == "fill":
            return [w, h]
        elif self.fit_mode == "contain":
            iw = w
        else:
            iw = min(w, tw)

        # calculate the appropriate height
        ih = iw / ratio
        # if the height is too higher, take the height of the container
        # and calculate appropriate width. no need to test further. :)
        if ih > h:
            if self.fit_mode == "contain":
                ih = h
            else:
                ih = min(h, th)
            iw = ih * ratio
        return [iw, ih]

    norm_image_size = AliasProperty(get_norm_image_size, bind=('texture', 'size', 'image_ratio', 'fit_mode',), cache=True,)

    def _do_video_load(self, *largs):
        if CoreVideo is None:
            return
        self.unload()
        if not self.source:
            self._video = None
            self.texture = None
        else:
            filename = self.source
            # Check if filename is not url
            if '://' not in filename:
                filename = kivy.resources.resource_find(filename)
            self._video = CoreVideo(filename=filename, **self.options)
            if self._video:
                self._video.volume = self.volume
                self._video.bind(on_load=self._on_load, on_frame=self._on_video_frame, on_eos=self._on_eos)
                if self.state == 'play' or self.play:
                    self._video.play()
            self.duration = 1.
            self.position = 0.

    def on_texture(self, *kwargs):
        super(PauseableVideo, self).on_texture(*kwargs)
        if self._video:
            if self.first_load:
                app = App.get_running_app()
                if app.album_screen:
                    app.album_screen.refresh_photoinfo_full(video=self._video)
                self.aspect = self._video.aspect
            self.first_load = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.state == 'play':
                self.state = 'pause'
            else:
                self.state = 'play'
            return True


class EditMain(GridLayout):
    """Main menu edit panel, contains buttons to activate the other edit panels."""

    owner = ObjectProperty()

    def save_last(self):
        pass

    def load_last(self):
        pass


class DenoisePreview(RelativeLayout):
    finished = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_finished')
        super(DenoisePreview, self).__init__(**kwargs)

    def on_finished(self, *_):
        self.root.update_preview()


class AspectRatioDropDown(NormalDropDown):
    """Drop-down menu for sorting aspect ratio presets"""
    pass


class InterpolationDropDown(NormalDropDown):
    """Drop-down menu for curves interpolation options"""
    pass


class Curves(FloatLayout):
    """Widget for viewing and generating color curves information."""

    owner = ObjectProperty()
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

    def on_size(self, *_):
        self.refresh()

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
        canvas.before.clear()
        canvas.before.add(Color(0, 0, 0))
        canvas.before.add(Rectangle(size=self.size, pos=self.pos))
        self.generate_curve()
        self.draw_line(canvas)

        for point in self.points:
            self.draw_point(canvas, point)

        if self.owner:
            image = self.owner.image
            if image:
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
        app = App.get_running_app()
        if point == self.current_point:
            color = app.theme.selected
        else:
            color = (1, 1, 1, 1)
        source = 'data/curve_point.png'
        canvas.add(Color(rgba=color))
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
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, before=previous_y, before_distance=previous_distance, after=next_y, after_distance=next_distance, mode='catmull', rounding=True)
            elif interpolation == 'Cubic':
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, before=previous_y, before_distance=previous_distance, after=next_y, after_distance=next_distance, mode='cubic', rounding=True)
            elif interpolation == 'Cosine':
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, mode='cosine', rounding=True)
            else:
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, rounding=True)
            self.curve = self.curve + ys
            x = stop_x
            index = index + 1
            previous_point = start_point
            start_point = stop_point
        self.curve.append(round(self.points[-1][1] * total_bytes))

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

    def find_parent_scroller(self):
        parent = self.parent
        while parent:
            if isinstance(parent, ScrollerContainer):
                return parent
            parent = parent.parent
        return None

    def on_touch_down(self, touch):
        """Intercept touches and begin moving points.
        Will also modify scrolling in the parent scroller widget to improve usability.
        """

        edit_scroller = self.find_parent_scroller()
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

        edit_scroller = self.find_parent_scroller()
        edit_scroller.scroll_timeout = self.scroll_timeout  #Reset parent scroller object to normal operation
        self.moving = False
        if self.collide_point(*touch.pos):
            return True


class RotationGrid(FloatLayout):
    """A grid display overlay used for alignment when an image is being rotated."""
    pass


class CropOverlay(ResizableBehavior, RelativeLayout):
    """Overlay widget for showing cropping area."""

    owner = ObjectProperty()
    drag_mode = BooleanProperty(False)
    recrop_mode = BooleanProperty(False)
    start_x = NumericProperty(0)
    moved_x = NumericProperty(0)
    start_y = NumericProperty(0)
    moved_y = NumericProperty(0)
    start_width = NumericProperty(1)
    start_height = NumericProperty(1)

    def __init__(self, **kwargs):
        super(CropOverlay, self).__init__(**kwargs)
        self._drag_touch = None

    def on_size(self, instance, size):
        self.owner.set_crop(self.pos[0], self.pos[1], size[0], size[1])

    def on_pos(self, instance, pos):
        self.owner.set_crop(pos[0], pos[1], self.size[0], self.size[1])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            #adjust crop mode
            #if touch.button == 'left':
            if self.check_resizable_side(*touch.pos):
                self.drag_mode = False
                super(CropOverlay, self).on_touch_down(touch)
            else:
                self.start_x = self.pos[0]
                self.start_y = self.pos[1]
                self.moved_x = 0
                self.moved_y = 0
                self.start_width = self.width
                self.start_height = self.height
                self.drag_mode = True
            return True
        elif self.owner.collide_point(*touch.pos):
            #recrop mode
            self.recrop_mode = True
            self.start_x = touch.pos[0]
            self.start_y = touch.pos[1]
            return True

    def on_touch_move(self, touch):
        if self.drag_mode:
            self.moved_x += touch.dx
            self.moved_y += touch.dy
            x1 = self.start_x + self.moved_x
            y1 = self.start_y + self.moved_y
            x2 = x1 + self.start_width
            y2 = y1 + self.start_height
            self.set_cropper(x1, y1, x2, y2)
        elif self.recrop_mode:
            x2 = touch.pos[0]
            y2 = touch.pos[1]
            self.set_cropper(self.start_x, self.start_y, x2, y2)
        else:
            super(CropOverlay, self).on_touch_move(touch)
        if self.owner.lock_aspect:
            if (self.resizing_up or self.resizing_down) and not (self.resizing_left or self.resizing_right):
                force_dir = 'h'
            else:
                force_dir = 'v'
            self.owner.set_aspect(force=force_dir)

    def set_cropper(self, x1, y1, x2, y2):
        #takes 4 points and sets the cropper based on them, ensures that they are only inside the texture
        xs = [x1, x2]
        ys = [y1, y2]
        min_x = min(xs)
        min_y = min(ys)
        max_x = max(xs)
        max_y = max(ys)

        texture_top, texture_right, texture_bottom, texture_left = self.owner.get_texture_size()
        if min_x < texture_left:
            min_x = texture_left
        if min_y < texture_bottom:
            min_y = texture_bottom
        if max_x > texture_right:
            max_x = texture_right
        if max_y > texture_top:
            max_y = texture_top

        width = max_x - min_x
        height = max_y - min_y

        self.pos = (min_x, min_y)
        self.size = (width, height)

    def on_touch_up(self, touch):
        if self.drag_mode:
            self.drag_mode = False
        elif self.recrop_mode:
            self.recrop_mode = False
        else:
            super(CropOverlay, self).on_touch_up(touch)

    def on_resizing(self, instance, resizing):
        pass


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
            self.parent.parent.text = instance.text

    def set_argument(self, instance):
        if not instance.focus:
            self.argument = instance.text
            self.save_program()

    def select_command(self):
        """Opens a popup filebrowser to select a program to run."""

        app = App.get_running_app()
        content = FileBrowser(ok_text='Select', path=app.last_browse_folder, filters=['*'])
        content.bind(on_cancel=lambda x: self.owner.owner.owner.dismiss_popup())
        content.bind(on_ok=self.select_command_confirm)
        self.owner.owner.owner.popup = filepopup = NormalPopup(title='Select A Program', content=content, size_hint=(0.9, 0.9))
        filepopup.open()

    def select_command_confirm(self, *_):
        """Called when the filebrowser dialog is successfully closed."""

        popup = self.owner.owner.owner.popup
        if popup:
            self.command = popup.content.filename
            path = popup.content.path
            app = App.get_running_app()
            app.last_browse_folder = path
            self.owner.owner.owner.dismiss_popup()
            self.save_program()


class TagSelectButton(WideButton):
    """Tag display button - used for adding a tag to a photo"""

    remove = False
    target = StringProperty()
    type = StringProperty('None')
    owner = ObjectProperty()

    def on_press(self):
        self.owner.add_to_tag(self.target)


class RemoveFromTagButton(RemoveButton):
    """Button to remove a tag from the current photo."""

    def on_release(self):
        self.owner.remove_from_tag(self.remove_from, self.to_remove)


class RemoveTagButton(RemoveButton):
    """Button to remove a tag from the tags list.  Will popup a confirm dialog before removing."""

    def on_release(self):
        app = App.get_running_app()
        content = ConfirmPopup(text='Delete The Tag "'+self.to_remove+'"?', yes_text='Delete', no_text="Don't Delete", warn_yes=True)
        content.bind(on_answer=self.on_answer)
        self.owner.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4), auto_dismiss=False)
        self.owner.popup.open()

    def on_answer(self, instance, answer):
        del instance
        if answer == 'yes':
            app = App.get_running_app()
            app.remove_tag(self.to_remove)
            self.owner.update_treeview()
        self.owner.dismiss_popup()
