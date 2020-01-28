try:
    import numpy
    import cv2
    opencv = True
except:
    opencv = False
import sys
import PIL
from PIL import Image, ImageEnhance, ImageOps, ImageChops, ImageDraw, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
from io import BytesIO
import datetime
from shutil import copy2
import subprocess
import time
from operator import itemgetter
from functools import partial

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
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics.transformation import Matrix
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.treeview import TreeViewNode
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.uix.video import Video
from kivy.uix.videoplayer import VideoPlayer
from kivy.core.image.img_pil import ImageLoaderPIL
from kivy.loader import Loader
Loader.max_upload_per_frame = 4
Loader.num_workers = 2
from kivy.cache import Cache
Cache.register('kv.loader', limit=5)
from kivy.graphics import Rectangle, Color, Line
from resizablebehavior import ResizableBehavior
from colorpickercustom import ColorPickerCustom

from generalcommands import interpolate, agnostic_path, local_path, time_index, format_size, to_bool, isfile2
from filebrowser import FileBrowser
from generalelements import CustomImage, NormalButton, ExpandableButton, ScanningPopup, NormalPopup, ConfirmPopup, NormalLabel, ShortLabel, NormalDropDown, AlbumSortDropDown, MenuButton, TreeViewButton, RemoveButton, WideButton, RecycleItem, PhotoRecycleViewButton, AlbumExportDropDown
from generalconstants import *

from kivy.lang.builder import Builder
Builder.load_string("""
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
                on_release: app.show_database()
                opacity: 0 if app.standalone else 1
                disabled: True if app.standalone else False
            ShortLabel:
                text: app.standalone_text
            HeaderLabel:
                text: root.folder_title
            InfoLabel:
            DatabaseLabel:
            SettingsButton:
        BoxLayout:
            orientation: 'horizontal'
            SplitterPanelLeft:
                id: leftpanel
                #width: app.leftpanel_width
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
                        id: editPanelContainer
                        pos: self.parent.pos
                        size: self.parent.size
                        padding: app.padding
                        ScrollerContainer:
                            cols: 1
                            id: editScroller
                            do_scroll_x: False
                            EditPanelContainer:
                                disabled: app.database_scanning
                                id: panelEdit
                                cols: 1
                                size_hint: 1, None
                                height: self.minimum_height
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
                                            multiline: False
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
        allow_stretch: True
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
                            x: 1 if root.angle == 0 or self.width == 0 else ((self.height/self.width) if (self.height/self.width) > .75 else .75)
                            y: 1 if root.angle == 0 or self.width == 0 else ((self.height/self.width) if (self.height/self.width) > .75 else .75)
                            origin: photoStencil.center
                    canvas.after:
                        PopMatrix
                    photoinfo: root.photoinfo
                    loadanyway: True
                    loadfullsize: True
                    source: root.file
                    mirror: root.mirror
                    allow_stretch: True
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
        options: {'allow_stretch': True}
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
        HalfSliderLimited:
            disabled: True if self.parent.opacity == 0 else False
            size_hint_y: None
            width: root.width
            value: root.position
            start: root.start_point
            end: root.end_point
            on_value: root.position = self.value
            height: app.button_scale

<ExitFullscreenButton>:
    text: 'Back'

<EditNone>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    size_hint: 1, None
    height: self.minimum_height

<EditMain>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    size_hint: 1, None
    height: self.minimum_height
    WideButton:
        text: 'Basic Color Adjustments'
        on_release: root.owner.set_edit_panel('color')
        disabled: not root.owner.view_image and not root.owner.ffmpeg
    SmallBufferY:
    WideButton:
        text: 'Advanced Color Adjustments'
        on_release: root.owner.set_edit_panel('advanced')
        disabled: not root.owner.view_image and not root.owner.ffmpeg
    SmallBufferY:
    WideButton:
        text: 'Filters'
        on_release: root.owner.set_edit_panel('filter')
        disabled: not root.owner.view_image and not root.owner.ffmpeg
    SmallBufferY:
    WideButton:
        text: 'Image Borders'
        on_release: root.owner.set_edit_panel('border')
        disabled: not root.owner.view_image and not root.owner.ffmpeg
    SmallBufferY:
    WideButton:
        height: app.button_scale if root.owner.opencv else 0
        opacity: 1 if root.owner.opencv else 0
        text: 'Denoise'
        on_release: root.owner.set_edit_panel('denoise')
        disabled: (not root.owner.view_image and not root.owner.ffmpeg) or not root.owner.opencv
    SmallBufferY:
        height: int(app.button_scale / 4) if root.owner.opencv else 0
    WideButton:
        text: 'Rotate'
        on_release: root.owner.set_edit_panel('rotate')
        disabled: (not root.owner.view_image and not root.owner.ffmpeg) or not root.owner.opencv
    SmallBufferY:
    WideButton:
        text: 'Crop'
        on_release: root.owner.set_edit_panel('crop')
        disabled: (not root.owner.view_image and not root.owner.ffmpeg) or not root.owner.opencv
    SmallBufferY:
    WideButton:
        text: 'Convert'
        on_release: root.owner.set_edit_panel('convert')
        disabled: root.owner.view_image or not root.owner.ffmpeg
    LargeBufferY:
    WideButton:
        id: deleteOriginal
        text: 'Delete Unedited Original File'
        warn: True
        on_release: root.owner.delete_original()
    SmallBufferY:
    WideButton:
        id: deleteOriginalAll
        text: 'Delete All Originals In Folder'
        warn: True
        on_release: root.owner.delete_original_all()
    SmallBufferY:
    WideButton:
        id: undoEdits
        text: 'Restore Original Unedited File'
        on_release: root.owner.restore_original()
    LargeBufferY:
    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            size_hint_x: 1
            text: 'External Programs:'
        NormalButton:
            size_hint_x: None
            text: 'New'
            on_release: root.owner.add_program()
    GridLayout:
        id: externalPrograms
        height: self.minimum_height
        size_hint_y: None
        cols: 1

<EditColorImage>:
    padding: 0, 0, int(app.button_scale / 2), 0
    id: editColor
    size_hint: 1, None
    cols: 1
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.owner.save_edit()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    WideButton:
        id: loadLast
        disabled: not root.owner.edit_color
        text: "Load Last Settings"
        on_release: root.load_last()
    MediumBufferY:
    GridLayout:
        id: videoPreset
        cols: 1
        height: self.minimum_height
        size_hint_y: None
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Color Adjustments:'
        NormalButton:
            text: 'Reset All'
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
            allow_stretch: True
            keep_ratio: False
    SmallBufferY:
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        NormalToggle:
            text: "Auto Contrast"
            id: autocontrastToggle
            state: 'down' if root.autocontrast else 'normal'
            on_state: root.update_autocontrast(self.state)
            size_hint_x: 1
    SmallBufferY:
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Equalize Histogram:'
        NormalButton:
            text: 'Reset'
            on_release: root.reset_equalize()
    HalfSlider:
        id: equalizeSlider
        on_value: root.equalize = self.value
        reset_value: root.reset_equalize
    SmallBufferY:
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale if root.owner.opencv else 0
        disabled: not root.owner.opencv
        opacity: 1 if root.owner.opencv else 0
        LeftNormalLabel:
            text: 'Adaptive Histogram Equalize:'
        NormalButton:
            text: 'Reset'
            on_release: root.reset_adaptive()
    HalfSlider:
        disabled: not root.owner.opencv
        opacity: 1 if root.owner.opencv else 0
        height: app.button_scale if root.owner.opencv else 0
        id: adaptiveSlider
        on_value: root.adaptive = self.value
        reset_value: root.reset_adaptive
    SmallBufferY:
        height: int(app.button_scale / 4) if root.owner.opencv else 0
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
        id: brightnessSlider
        on_value: root.brightness = self.value
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
        id: gammaSlider
        on_value: root.gamma = self.value
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
        id: shadowSlider
        on_value: root.shadow = self.value
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
        id: temperatureSlider
        on_value: root.temperature = self.value
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
        id: saturationSlider
        on_value: root.saturation = self.value
        reset_value: root.reset_saturation

<EditColorImageAdvanced>:
    padding: 0, 0, int(app.button_scale / 2), 0
    id: editColor
    size_hint: 1, None
    cols: 1
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.owner.save_edit()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    WideButton:
        id: loadLast
        disabled: not root.owner.edit_advanced
        text: "Load Last Settings"
        on_release: root.load_last()
    MediumBufferY:
    GridLayout:
        id: videoPreset
        cols: 1
        height: self.minimum_height
        size_hint_y: None
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Color Adjustments:'
        NormalButton:
            text: 'Reset All'
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
            allow_stretch: True
            keep_ratio: False
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
                id: curves
        #BoxLayout:
        #    orientation: 'horizontal'
        #    size_hint_y: None
        #    height: app.button_scale
        #    LeftNormalLabel:
        #        text: 'Interpolation Mode:'
        #    MenuStarterButton:
        #        size_hint_x: 1
        #        id: interpolation
        #        text: app.interpolation
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
                color: root.tint
                on_color: root.tint = self.color

<EditFilterImage>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    size_hint: 1, None
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.owner.save_edit()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    WideButton:
        id: loadLast
        disabled: not root.owner.edit_filter
        text: "Load Last Settings"
        on_release: root.load_last()
    MediumBufferY:
    GridLayout:
        id: videoPreset
        cols: 1
        height: self.minimum_height
        size_hint_y: None
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Filter Image:'
        NormalButton:
            text: 'Reset All'
            on_release: root.reset_all()
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
            id: sharpenSlider
            on_value: root.sharpen = self.value
            reset_value: root.reset_sharpen
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale if root.owner.opencv else 0
            opacity: 1 if root.owner.opencv else 0
            LeftNormalLabel:
                text: 'Median Blur (Despeckle):'
            NormalButton:
                text: 'Reset'
                on_release: root.reset_median()
                disabled: not root.owner.opencv
        HalfSlider:
            height: app.button_scale if root.owner.opencv else 0
            opacity: 1 if root.owner.opencv else 0
            id: medianSlider
            on_value: root.median = self.value
            disabled: not root.owner.opencv
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
        height: self.minimum_height if root.owner.opencv else 0
        disabled: not root.owner.opencv
        opacity: 1 if root.owner.opencv else 0
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
            id: bilateralAmountSlider
            on_value: root.bilateral_amount = self.value
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
            id: bilateralSlider
            on_value: root.bilateral = self.value
            reset_value: root.reset_bilateral
    MediumBufferY:
        height: int(app.button_scale / 2) if root.owner.opencv else 0
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
            id: vignetteAmountSlider
            on_value: root.vignette_amount = self.value
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
            value: .5
            id: vignetteSizeSlider
            on_value: root.vignette_size = self.value
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
            id: edgeBlurAmountSlider
            on_value: root.edge_blur_amount = self.value
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
            value: .5
            id: edgeBlurSizeSlider
            on_value: root.edge_blur_size = self.value
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
            value: .5
            id: edgeBlurIntensitySlider
            on_value: root.edge_blur_intensity = self.value
            reset_value: root.reset_edge_blur_intensity

<EditBorderImage>:
    padding: 0, 0, int(app.button_scale / 2), 0
    id: editBorder
    size_hint: 1, None
    cols: 1
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.owner.save_edit()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    WideButton:
        id: loadLast
        disabled: not root.owner.edit_border
        text: "Load Last Settings"
        on_release: root.load_last()
    MediumBufferY:
    GridLayout:
        id: videoPreset
        cols: 1
        height: self.minimum_height
        size_hint_y: None
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Border Overlays:'
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
            id: opacitySlider
            on_value: root.border_opacity = self.value
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
            id: borderXScale
            on_value: root.border_x_scale = self.value
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
            id: borderYScale
            on_value: root.border_y_scale = self.value
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
                on_release: root.reset_tint()
        BoxLayout:
            size_hint_y: None
            height: sp(33)*10
            ColorPickerCustom:
                id: tint
                color: root.tint
                on_color: root.tint = self.color

<EditDenoiseImage>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    size_hint: 1, None
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.save_image()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    WideButton:
        id: loadLast
        disabled: not root.owner.edit_denoise
        text: "Load Last Settings"
        on_release: root.load_last()
    MediumBufferY:
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Denoise Image:'
        NormalButton:
            text: 'Reset All'
            on_release: root.reset_all()
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
        #NormalButton:
        #    size_hint_x: 1
        #    text: 'Generate Full Preview'
        #    on_release: root.denoise()
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
                    size: root.image_x, root.image_y
                    Image:
                        allow_stretch: True
                        size: root.image_x, root.image_y
                        size_hint: None, None
                        id: noisePreview
                        mipmap: True
                        #source: root.imagefile
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

<EditCropImage>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.save_image()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    WideButton:
        id: loadLast
        disabled: not root.owner.edit_crop
        text: "Load Last Settings"
        on_release: root.load_last()
    MediumBufferY:
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Image Cropping:'
        NormalButton:
            text: 'Reset All'
            on_release: root.reset_crop()
    LeftNormalLabel:
        size_hint_y: None
        height: app.button_scale
        text: root.crop_size
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
            on_value: root.crop_top = self.value
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
            on_value: root.crop_right = self.value
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
            on_value: root.crop_bottom = self.value
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
            on_value: root.crop_left = self.value
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
        GridLayout:
            cols: 2
            size_hint: 1, None
            height: app.button_scale
            NormalToggle:
                id: horizontalToggle
                size_hint_x: 1
                text: 'Horizontal'
                state: 'down' if root.orientation == 'horizontal' else 'normal'
                group: 'orientation'
                on_press: root.set_orientation('horizontal')
            NormalToggle:
                id: verticalToggle
                size_hint_x: 1
                text: 'Vertical'
                state: 'down' if root.orientation == 'vertical' else 'normal'
                group: 'orientation'
                on_press: root.set_orientation('vertical')

<EditRotateImage>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    size_hint_y: None
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Confirm Edit'
            on_release: root.save_image()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    MediumBufferY:
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        LeftNormalLabel:
            text: 'Image Rotation:'
        NormalButton:
            text: 'Reset All'
            on_release: root.reset_all()
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
            orientation: 'horizontal'
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
            on_value: root.fine_angle = self.value
            reset_value: root.reset_fine_angle

<EditConvertImage>:
    cols: 1
    size_hint: 1, None
    height: self.minimum_height
    WideButton:
        text: 'Cancel Edit'
        on_release: root.owner.set_edit_panel('main')
    MediumBufferY:
    NormalLabel:
        text: 'Convert Is Not Available For Images'

<EditConvertVideo>:
    padding: 0, 0, int(app.button_scale / 2), 0
    cols: 1
    size_hint: 1, None
    height: self.minimum_height
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: 'Convert'
            on_release: root.encode()
        WideButton:
            text: 'Cancel Edit'
            warn: True
            on_release: root.owner.set_edit_panel('main')
    MediumBufferY:
    NormalLabel:
        text: 'Convert Video:'
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
                text: root.file_format
                on_release: root.container_drop.open(self)
        SmallBufferY:
        NormalToggle:
            id: resize
            size_hint_x: 1
            state: 'down' if root.resize else 'normal'
            text: 'Resize' if self.state == 'down' else 'No Resize'
            on_release: root.update_resize(self.state)
        BoxLayout:
            disabled: not root.resize
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            ShortLabel:
                text: 'Size:'
            NormalInput:
                id: widthInput
                hint_text: '1920'
                multiline: False
                text: root.resize_width
                on_text: root.set_resize_width(self)
            ShortLabel:
                text: 'x'
            NormalInput:
                id: heightInput
                hint_text: '1080'
                multiline: False
                text: root.resize_height
                on_text: root.set_resize_height(self)
        SmallBufferY:
        NormalToggle:
            id: deinterlace
            size_hint_x: 1
            state: 'down' if root.deinterlace else 'normal'
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
                text: root.video_codec
                on_release: root.video_codec_drop.open(self)
                id: videoCodecDrop
        #BoxLayout:
        #    orientation: 'horizontal'
        #    size_hint_y: None
        #    height: app.button_scale
        #    LeftNormalLabel:
        #        text: 'Video Quality:'
        #    MenuStarterButtonWide:
        #        size_hint_x: 1
        #        text: root.video_quality
        #        on_release: root.video_quality_drop.open(self)
        #        id: videoQualityDrop
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            LeftNormalLabel:
                text: 'Encoding Speed:'
            MenuStarterButtonWide:
                size_hint_x: 1
                text: root.encoding_speed
                on_release: root.encoding_speed_drop.open(self)
                id: encodingSpeedDrop
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            LeftNormalLabel:
                text: 'Video Bitrate:'
            FloatInput:
                id: videoBitrateInput
                text: root.video_bitrate

        SmallBufferY:
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            LeftNormalLabel:
                text: 'Audio Codec:'
            MenuStarterButtonWide:
                size_hint_x: 1
                text: root.audio_codec
                on_release: root.audio_codec_drop.open(self)
                id: audioCodecDrop
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            LeftNormalLabel:
                text: 'Audio Bitrate:'
            FloatInput:
                id: audioBitrateInput
                text: root.audio_bitrate
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
                text: "Manual command line:"
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            LeftNormalLabel:
                text: "This will override all other settings."
        SmallBufferY:
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: app.button_scale
            ShortLabel:
                text: 'ffmpeg.exe '
            NormalInput:
                id: commandInput
                hint_text: '-sn %c %v %a %f %p %b %d'
                multiline: False
                text: root.command_line
                on_text: root.set_command_line(self)
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
                text: 'Framerate (From Original File)'

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

<AspectRatioDropDown>:
    MenuButton:
        text: 'Current Ratio'
        on_release: root.select('current')
    MenuButton:
        text: '6 x 4'
        on_release: root.select('6x4')
    MenuButton:
        text: '7 x 5'
        on_release: root.select('7x5')
    MenuButton:
        text: '11 x 8.5'
        on_release: root.select('11x8.5')
    MenuButton:
        text: '4 x 3'
        on_release: root.select('4x3')
    MenuButton:
        text: '16 x 9'
        on_release: root.select('16x9')
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

<VideoEncodePreset>:
    orientation: 'vertical'
    size_hint_y: None
    height: int(app.button_scale * 2.5)
    BoxLayout:
        orientation: 'vertical'
        LeftNormalLabel:
            text: 'Video Encode:'
        MenuStarterButton:
            text: root.preset_name
            size_hint_x: 1
            on_release: root.preset_drop.open(self)
    MediumBufferY:

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
    mipmap: True
    size_hint_x: 1

<AlbumSelectButton>:
    mipmap: True
    size_hint_x: 1

""")


class AlbumScreen(Screen):
    """Screen layout of the album viewer."""

    #Display variables
    selected = StringProperty('')  #The current folder/album/tag being displayed
    type = StringProperty('None')  #'Folder', 'Album', 'Tag'
    target = StringProperty()  #The identifier of the album/folder/tag that is being viewed
    photos = []  #Photoinfo of all photos in the album
    photoinfo = []  #photoinfo for the currently viewed photo
    photo = StringProperty('')  #The absolute path to the currently visible photo
    fullpath = StringProperty()  #The database-relative path of the current visible photo

    folder_title = StringProperty('Album Viewer')
    view_panel = StringProperty('')
    sort_reverse_button = StringProperty('normal')
    opencv = BooleanProperty()
    canprint = BooleanProperty(True)
    ffmpeg = BooleanProperty(False)

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
    edit_panel = StringProperty('')  #The type of edit panel currently loaded
    edit_panel_object = ObjectProperty(allownone=True)  #Holder for the edit panel widget
    viewer = ObjectProperty()  #Holder for the photo viewer widget
    album_exports = ObjectProperty()

    #Variables relating to the photo list view on the left
    sort_method = StringProperty('Name')  #Current album sort method
    sort_reverse = BooleanProperty(False)

    #Variables relating to the photo view
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

    def cancel_encode(self, *_):
        """Signal to cancel the encodig process."""

        self.cancel_encoding = True

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
            self.popup = ScanningPopup(title='Converting Video', auto_dismiss=False, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
            self.popup.scanning_text = ''
            self.popup.open()
            encoding_button = self.popup.ids['scanningButton']
            encoding_button.bind(on_press=self.cancel_encode)

            # Start encoding thread
            self.encodingthread = threading.Thread(target=self.encode_process)
            self.encodingthread.start()

    def get_ffmpeg_audio_command(self, video_input_folder, video_input_filename, audio_input_folder, audio_input_filename, output_file_folder, encoding_settings=None, start=None):
        if not encoding_settings:
            encoding_settings = self.encoding_settings
        if encoding_settings['file_format'].lower() == 'auto':
            audio_codec = 'aac'
            audio_bitrate = '192'
            extension = 'mp4'
        else:
            file_format = containers[containers_friendly.index(encoding_settings['file_format'])]
            audio_codec = audio_codecs[audio_codecs_friendly.index(encoding_settings['audio_codec'])]
            audio_bitrate = encoding_settings['audio_bitrate']
            extension = containers_extensions[containers.index(file_format)]

        if start is not None:
            seek = ' -ss '+str(start)
        else:
            seek = ''
        video_file = video_input_folder+os.path.sep+video_input_filename
        audio_file = audio_input_folder+os.path.sep+audio_input_filename
        output_filename = os.path.splitext(video_input_filename)[0]+'-mux.'+extension
        output_file = output_file_folder+os.path.sep+output_filename
        audio_bitrate_settings = "-b:a " + audio_bitrate + "k"
        audio_codec_settings = "-c:a " + audio_codec + " -strict -2"

        command = 'ffmpeg -i "'+video_file+'"'+seek+' -i "'+audio_file+'" -map 0:v -map 1:a -codec copy '+audio_codec_settings+' '+audio_bitrate_settings+' -shortest "'+output_file+'"'
        return [True, command, output_filename]

    def get_ffmpeg_command(self, input_folder, input_filename, output_file_folder, input_size, noaudio=False, input_images=False, input_file=None, input_framerate=None, input_pixel_format=None, encoding_settings=None, start=None, duration=None):
        if not encoding_settings:
            encoding_settings = self.encoding_settings
        if encoding_settings['file_format'].lower() == 'auto':
            file_format = 'MP4'
            pixels_number = input_size[0] * input_size[1]
            video_bitrate = str(pixels_number / 250)
            video_codec = 'libx264'
            audio_codec = 'aac'
            audio_bitrate = '192'
            encoding_speed = 'fast'
            deinterlace = False
            resize = False
            resize_width = input_size[0]
            resize_height = input_size[1]
            encoding_command = ''
            extension = 'mp4'
        else:
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

        if start is not None:
            seek = ' -ss '+str(start)
        else:
            seek = ''
        if duration is not None:
            duration = ' -t '+str(duration)
        else:
            duration = ''
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
            command = 'ffmpeg'+seek+' '+input_format_settings+encoding_command_reformat+duration+' "'+output_file+'"'
        else:
            output_filename = os.path.splitext(input_filename)[0]+'.'+extension
            output_file = output_file_folder+os.path.sep+output_filename
            #command = 'ffmpeg '+file_format_settings+' -i "'+input_file+'"'+filter_settings+' -sn '+speed_setting+' '+video_codec_settings+' '+audio_codec_settings+' '+framerate_setting+' '+pixel_format_setting+' '+video_bitrate_settings+' '+audio_bitrate_settings+' "'+output_file+'"'
            command = 'ffmpeg'+seek+' '+input_format_settings+' -i "'+input_file+'" '+file_format_settings+' '+filter_settings+' -sn '+speed_setting+' '+video_codec_settings+' '+audio_codec_settings+' '+framerate_setting+' '+pixel_format_setting+' '+video_bitrate_settings+' '+audio_bitrate_settings+duration+' "'+output_file+'"'
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

        start_time = time.time()
        start_point = self.viewer.start_point
        end_point = self.viewer.end_point
        framerate = input_metadata['frame_rate']
        duration = input_metadata['duration']
        self.total_frames = (duration * (end_point - start_point)) * (framerate[0] / framerate[1])
        start_seconds = start_point * duration
        duration_seconds = (end_point * duration) - start_seconds

        pixel_format = input_metadata['src_pix_fmt']
        input_size = input_metadata['src_vid_size']
        input_file_folder, input_filename = os.path.split(input_file)
        output_file_folder = input_file_folder+os.path.sep+'reencode'
        command_valid, command, output_filename = self.get_ffmpeg_command(input_file_folder, input_filename, output_file_folder, input_size, input_framerate=framerate, input_pixel_format=pixel_format, start=start_seconds, duration=duration_seconds)
        if not command_valid:
            self.cancel_encode()
            self.dismiss_popup()
            app.popup_message(text="Invalid FFMPEG command: " + command, title='Warning')
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

        self.encoding_process_thread = subprocess.Popen(command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

        # Poll process for new output until finished
        progress = []
        while True:
            if self.cancel_encoding:
                try:
                    self.encoding_process_thread.terminate()
                    self.encoding_process_thread.kill()
                    outs, errs = self.encoding_process_thread.communicate()
                except:
                    pass
                if os.path.isfile(output_file):
                    self.delete_output(output_file)
                if not os.listdir(output_file_folder):
                    os.rmdir(output_file_folder)
                self.dismiss_popup()
                self.encoding = False
                app.message("Canceled video processing.")
                return
            nextline = self.encoding_process_thread.stdout.readline()
            if nextline == '' and self.encoding_process_thread.poll() is not None:
                break
            if nextline.startswith('frame= '):
                self.current_frame = int(nextline.split('frame=')[1].split('fps=')[0].strip())
                scanning_percentage = self.current_frame / self.total_frames * 100
                self.popup.scanning_percentage = scanning_percentage
                #time_done = nextline.split('time=')[1].split('bitrate=')[0].strip()
                elapsed_time = time.time() - start_time
                time_done = time_index(elapsed_time)
                remaining_frames = self.total_frames - self.current_frame
                try:
                    fps = float(nextline.split('fps=')[1].split('q=')[0].strip())
                    seconds_left = remaining_frames / fps
                    time_remaining = time_index(seconds_left)
                    time_text = "  Time: "+time_done+"  Remaining: "+time_remaining
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
                    if self.encoding_settings['width'] and self.encoding_settings['height']:
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
                    if self.photoinfo[0] != new_photoinfo[0]:
                        app.database_item_rename(self.photoinfo[0], new_photoinfo[0], new_photoinfo[1])
                    app.database_item_update(new_photoinfo)

                    # reload video in ui
                    self.fullpath = local_path(new_photoinfo[0])
                    newpath = os.path.join(local_path(new_photoinfo[2]), local_path(new_photoinfo[0]))
                    Clock.schedule_once(lambda x: self.set_photo(newpath))

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

    def set_photo(self, photo):
        self.photo = photo
        Clock.schedule_once(lambda *dt: self.refresh_all())
        Clock.schedule_once(self.show_selected)

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
        deleted, message = app.delete_photo_original(self.photoinfo)
        if deleted:
            self.set_edit_panel('main')
        app.message(message)

    def delete_original_all(self):
        folder = self.photoinfo[1]
        app = App.get_running_app()
        deleted_photos = app.delete_folder_original(folder)
        if len(deleted_photos) > 0:
            app.message('Deleted '+str(len(deleted_photos))+' original files')
        else:
            app.message('Could not delete any original files')

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
            app.save_photoinfo(target=self.photoinfo[1], save_location=os.path.join(self.photoinfo[2], self.photoinfo[1]))

            #regenerate thumbnail
            app.database_thumbnail_update(self.photoinfo[0], self.photoinfo[2], self.photoinfo[7], self.photoinfo[13], force=True)

            #reload photo image in ui
            self.fullpath = self.photoinfo[0]
            self.refresh_all()
            self.photo = new_original_file
            self.on_photo()
            self.clear_cache()
            app.message("Restored original file.")
            self.set_edit_panel('main')

            #switch active photo in photo list back to image
            self.show_selected()
        else:
            app.popup_message(text='Could not find original file', title='Warning')

    def set_edit_panel(self, panelname):
        """Switches the current edit panel to another.
        Argument:
            panelname: String, the name of the panel.
        """

        if self.edit_panel != panelname:
            self.edit_panel = panelname
            Clock.schedule_once(lambda *dt: self.update_edit_panel())
        elif self.edit_panel == 'main':
            self.edit_panel_object.refresh_buttons()

    def export(self):
        """Switches to export screen."""

        if self.photos:
            app = App.get_running_app()
            app.export_target = self.target
            app.export_type = self.type
            app.show_export()

    def drop_widget(self, fullpath, position, dropped_type='file', aspect=1):
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

    def dismiss_popup(self, *_):
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
            elif self.popup and self.popup.open:
                if key == 'enter':
                    self.popup.content.dispatch('on_answer', 'yes')

    def next_photo(self):
        """Changes the viewed photo to the next photo in the album index."""

        current_photo_index = self.current_photo_index()
        if current_photo_index == len(self.photos) - 1:
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

        app = App.get_running_app()
        if not app.database_scanning:
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
        self.popup = NormalPopup(title='Confirm Delete', content=content, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4), auto_dismiss=False)
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
            if self.type == 'Album':
                index = app.album_find(self.target)
                if index >= 0:
                    app.album_remove_photo(index, fullpath, message=True)
                deleted = True
            elif self.type == 'Tag':
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
                    self.next_photo()
                    Cache.remove('kv.loader')
                    self.cache_nearby_images()
                    #Cache.remove('kv.image')
                    #Cache.remove('kv.texture')
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

    def remove_from_tag(self, remove_from, tag_name):
        app = App.get_running_app()
        app.database_remove_tag(remove_from, tag_name, message=True)
        self.update_tags()
        if tag_name == 'favorite':
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
        if os.path.splitext(self.photo)[1].lower() in imagetypes:
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
        self.set_edit_panel('main')  #Clear the edit panel
        #self.ids['album'].selected = self.fullpath

    def cache_nearby_images(self, *_):
        """Determines the next and previous images in the list, and caches them to speed up browsing."""

        current_photo_index = self.current_photo_index()
        if current_photo_index == len(self.photos) - 1:
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

    def refresh_all(self, *_):
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
        else:
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
                info_panel.add_node(TreeViewInfo(title='Resolution: ' + str(megapixels) + 'MP (' + resolution + ')'))
            else:
                self.image_x = 0
                self.image_y = 0

            #Add exif info
            if exif:
                if 271 in exif:
                    camera_type = exif[271]+' '+exif[272]
                    info_panel.add_node(TreeViewInfo(title='Camera: ' + camera_type))
                if 33432 in exif:
                    copyright = exif[33432]
                    info_panel.add_node(TreeViewInfo(title='Copyright: ' + copyright))
                if 36867 in exif:
                    camera_date = exif[36867]
                    info_panel.add_node(TreeViewInfo(title='Date Taken: ' + camera_date))
                if 33434 in exif:
                    exposure = exif[33434]
                    camera_exposure = str(exposure[0]/exposure[1])+'seconds'
                    info_panel.add_node(TreeViewInfo(title='Exposure Time: ' + camera_exposure))
                if 37377 in exif:
                    try:
                        camera_shutter_speed = str(exif[37377][0]/exif[37377][1])
                        info_panel.add_node(TreeViewInfo(title='Shutter Speed: ' + camera_shutter_speed))
                    except:
                        pass
                if 33437 in exif:
                    f_stop = exif[33437]
                    try:
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
                    camera_iso = str(exif[34855])
                    info_panel.add_node(TreeViewInfo(title='ISO Level: ' + camera_iso))
                if 37385 in exif:
                    flash = bin(exif[37385])[2:].zfill(8)
                    camera_flash = 'Not Used' if flash[1] == '0' else 'Used'
                    info_panel.add_node(TreeViewInfo(title='Flash: ' + str(camera_flash)))
                if 37386 in exif:
                    focal_length = str(exif[37386][0]/exif[37386][1])+'mm'
                    if 41989 in exif:
                        film_focal = exif[41989]
                        if film_focal != 0:
                            focal_length = focal_length+' ('+str(film_focal)+' 35mm equiv.)'
                    info_panel.add_node(TreeViewInfo(title='Focal Length: ' + focal_length))
                if 41988 in exif:
                    digital_zoom = exif[41988]
                    if digital_zoom[0] != 0:
                        digital_zoom_amount = str(round(digital_zoom[0]/digital_zoom[1], 2))+'X'
                        info_panel.add_node(TreeViewInfo(title='Digital Zoom: ' + digital_zoom_amount))
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
                        info_panel.add_node(TreeViewInfo(title='Exposure Mode: ' + program_name))

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
        app.clear_drags()
        right_panel = self.ids['rightpanel']
        #right_panel.width = app.right_panel_width()
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
        #self.on_photo()
        self.update_tags()
        self.refresh_all()

    def update_treeview(self):
        """Called by delete buttons."""

        self.on_enter()
        self.on_photo()

    def on_enter(self):
        """Called when the screen is entered.  Set up variables and widgets, and prepare to view images."""

        self.ffmpeg = ffmpeg
        self.opencv = opencv
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
        self.edit_panel = 'main'
        Clock.schedule_once(lambda *dt: self.update_edit_panel())

    def update_edit_panel(self):
        """Set up the edit panel with the current preset."""

        if self.viewer and isfile2(self.photo):
            self.viewer.stop()
            if self.edit_panel_object:
                self.edit_panel_object.save_last()
            self.viewer.edit_mode = self.edit_panel
            edit_panel_container = self.ids['panelEdit']
            if self.edit_panel == 'main':
                self.edit_panel_object = EditMain(owner=self)
                self.edit_panel_object.update_programs()
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
                        self.edit_panel_object = EditDenoiseImage(owner=self, imagefile=self.photo, image_x=self.viewer.edit_image.original_width, image_y=self.viewer.edit_image.original_height)
                    else:
                        self.edit_panel = 'main'
                        app = App.get_running_app()
                        app.message("Could Not Denoise, OpenCV Not Found")
                elif self.edit_panel == 'crop':
                    self.edit_panel_object = EditCropImage(owner=self, image_x=self.viewer.edit_image.original_width, image_y=self.viewer.edit_image.original_height)
                    self.viewer.edit_image.crop_controls = self.edit_panel_object
                elif self.edit_panel == 'rotate':
                    self.edit_panel_object = EditRotateImage(owner=self)
                elif self.edit_panel == 'convert':
                    if self.view_image:
                        self.edit_panel_object = EditConvertImage(owner=self)
                    else:
                        self.edit_panel_object = EditConvertVideo(owner=self)
            edit_panel_container.change_panel(self.edit_panel_object)
        else:
            if self.edit_panel_object:
                self.edit_panel_object.save_last()
            self.viewer.edit_mode = self.edit_panel
            edit_panel_container = self.ids['panelEdit']
            edit_panel_container.change_panel(None)
            self.edit_panel_object = EditNone(owner=self)

    def save_edit(self):
        if self.view_image:
            self.save_image()
        else:
            self.save_video()

    def save_video(self):
        app = App.get_running_app()
        app.save_encoding_preset()
        self.viewer.stop()

        # Create popup to show progress
        self.cancel_encoding = False
        self.popup = ScanningPopup(title='Processing Video', auto_dismiss=False, size_hint=(None, None), size=(app.popup_x, app.button_scale * 4))
        self.popup.scanning_text = ''
        self.popup.open()
        encoding_button = self.popup.ids['scanningButton']
        encoding_button.bind(on_press=self.cancel_encode)

        # Start encoding thread
        self.encodingthread = threading.Thread(target=self.save_video_process)
        self.encodingthread.start()

    def failed_encode(self, message):
        app = App.get_running_app()
        self.cancel_encode()
        self.dismiss_popup()
        self.encoding = False
        app.popup_message(text=message, title='Warning')

    def save_video_process(self):
        #Function that applies effects to a video and encodes it

        self.encoding = True
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
        start_point = self.viewer.start_point
        end_point = self.viewer.end_point
        pixel_format = edit_image.pixel_format
        input_size = [edit_image.original_width, edit_image.original_height]
        length = edit_image.length
        length = length * (end_point - start_point)
        edit_image.start_video_convert()
        start_seconds = edit_image.start_seconds
        frame_number = 1
        framerate = edit_image.framerate
        duration = edit_image.length
        self.total_frames = (duration * (end_point - start_point)) * (framerate[0] / framerate[1])
        start_frame = int(self.total_frames * start_point)
        command_valid, command, output_filename = self.get_ffmpeg_command(input_file_folder, input_filename, output_file_folder, input_size, noaudio=True, input_file='-', input_images=True, input_framerate=framerate, input_pixel_format=pixel_format, encoding_settings=encoding_settings)
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
        self.encoding_process_thread = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, shell=True)
        # Poll process for new output until finished
        while True:
            if self.cancel_encoding:
                self.dismiss_popup()
                try:
                    self.encoding_process_thread.terminate()
                    self.encoding_process_thread.kill()
                    outs, errs = self.encoding_process_thread.communicate()
                except:
                    pass
                deleted = self.delete_output(output_file)
                if not os.listdir(output_file_folder):
                    os.rmdir(output_file_folder)
                self.encoding = False
                app.message("Canceled video processing.")
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
            scanning_percentage = ((pts - start_seconds)/length) * 95
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
            command_valid, command, output_temp_filename = self.get_ffmpeg_audio_command(output_file_folder, output_filename, input_file_folder, input_filename, output_file_folder, encoding_settings=encoding_settings, start=start_seconds)
            output_temp_file = output_file_folder + os.path.sep + output_temp_filename

            print(command)
            #used to have shell=True in arguments... is it still needed?
            self.encoding_process_thread = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
            #Poll process for new output until finished
            deleted = self.delete_output(output_temp_file)
            if not deleted:
                self.failed_encode('File not encoded, temporary file already existed and could not be replaced')
                return
            while True:
                if self.cancel_encoding:
                    self.dismiss_popup()
                    try:
                        self.encoding_process_thread.kill()
                        outs, errs = self.encoding_process_thread.communicate()
                    except:
                        pass
                    deleted = self.delete_output(output_file)
                    deleted = self.delete_output(output_temp_file)
                    if not os.listdir(output_file_folder):
                        try:
                            os.rmdir(output_file_folder)
                        except:
                            pass
                    self.encoding = False
                    app.message("Canceled video processing.")
                    return

                nextline = self.encoding_process_thread.stdout.readline()
                if nextline == '' and self.encoding_process_thread.poll() is not None:
                    break
                if nextline.startswith('frame= '):
                    self.current_frame = int(nextline.split('frame=')[1].split('fps=')[0].strip())
                    scanning_percentage = 95 + ((self.current_frame - start_frame) / self.total_frames * 5)
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

            if exit_code != 0:
                #failed second encode, clean up
                #self.dismiss_popup()
                #self.delete_output(output_file)
                #self.delete_output(output_temp_file)
                #if not os.listdir(output_file_folder):
                #    os.rmdir(output_file_folder)
                #app.popup_message(text='Second file not encoded, FFMPEG gave exit code '+str(exit_code), title='Warning')
                #return
                #Could not encode audio element, video file may not include audio, warn the user and continue
                no_audio = True
                output_temp_file = output_file
            else:
                #Audio track was encoded properly, delete the first encoded file
                deleted = self.delete_output(output_file)
                no_audio = False

            #encoding completed
            self.viewer.edit_image.close_video()

            new_original_file = input_file_folder+os.path.sep+'.originals'+os.path.sep+input_filename
            if not os.path.isdir(input_file_folder+os.path.sep+'.originals'):
                os.makedirs(input_file_folder+os.path.sep+'.originals')
            new_encoded_file = input_file_folder+os.path.sep+output_filename

            new_photoinfo = list(self.photoinfo)
            #check if original file has been backed up already
            if not os.path.isfile(new_original_file):
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
            if no_audio:
                Clock.schedule_once(lambda x: app.message("Completed encoding file, could not find audio track."))
            else:
                Clock.schedule_once(lambda x: app.message("Completed encoding file '"+self.photo+"'"))
            Clock.schedule_once(lambda x: self.update_video_preview(self.photoinfo))

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
            try:
                self.encoding_process_thread.kill()
                outs, errs = self.encoding_process_thread.communicate()
            except:
                pass

        self.encoding = False
        self.set_edit_panel('main')

    def update_video_preview(self, photoinfo):
        app = App.get_running_app()

        #regenerate thumbnail
        app.database_thumbnail_update(photoinfo[0], photoinfo[2], photoinfo[7], photoinfo[13])

        #reload photo image in ui
        Clock.schedule_once(lambda x: self.clear_cache())

    def save_image(self):
        """Saves any temporary edits on the currently viewed image."""

        app = App.get_running_app()

        #generate full quality image
        edit_image = self.viewer.edit_image.get_full_quality()
        exif = self.viewer.edit_image.exif
        #new_exif = exif[:274] + b'1' + exif[275:]
        #exif = new_exif
        self.viewer.stop()

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
        edit_image.save(photo_file, "JPEG", quality=95, exif=exif)
        if not os.path.isfile(photo_file):
            if os.path.isfile(backup_photo_file):
                copy2(backup_photo_file, photo_file)
                app.popup_message(text='Could not save edited photo, restoring backup', title='Warning')
            else:
                app.popup_message(text='Could not save edited photo', title='Warning')
            return

        #update photo info
        self.photoinfo[10] = agnostic_path(backup_photo_file)
        #self.photoinfo[13] = 1
        self.photoinfo[9] = 1
        self.photoinfo[7] = int(os.path.getmtime(photo_file))
        update_photoinfo = list(self.photoinfo)
        update_photoinfo[0] = agnostic_path(update_photoinfo[0])
        update_photoinfo[1] = agnostic_path(update_photoinfo[1])
        update_photoinfo[2] = agnostic_path(update_photoinfo[2])
        app.database_item_update(update_photoinfo)
        app.save_photoinfo(target=self.photoinfo[1], save_location=os.path.join(self.photoinfo[2], self.photoinfo[1]))

        #regenerate thumbnail
        app.database_thumbnail_update(self.photoinfo[0], self.photoinfo[2], self.photoinfo[7], self.photoinfo[13])

        #reload photo image in ui
        self.clear_cache()

        #close edit panel
        self.set_edit_panel('main')

        #switch active photo in photo list back to image
        self.show_selected()

        app.message("Saved edits to image")


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
    edit_image = ObjectProperty()
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
            self.edit_image = CustomImage(mirror=self.mirror, angle=self.angle, photoinfo=self.photoinfo, source=self.file)
            Clock.schedule_once(self.start_edit_mode)  #Need to delay this because if i add it right away it will show a non-rotated version for some reason

    def start_edit_mode(self, *_):
        image = self.ids['image']
        image.opacity = 0
        viewer = self.ids['photoShow']
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
        self.fullscreen = False
        #if self.edit_image:
        #    self.edit_image.close_image()

    def close(self):
        pass

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
    start_point = NumericProperty(0.0)
    end_point = NumericProperty(1.0)
    fullscreen = BooleanProperty(False)
    overlay = ObjectProperty(allownone=True)

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

    def on_start_point(self, *_):
        if self.edit_image:
            self.edit_image.start_point = self.start_point

    def on_end_point(self, *_):
        if self.edit_image:
            self.edit_image.end_point = self.end_point

    def on_edit_mode(self, *_):
        """Called when the user enters or exits edit mode.
        Adds the edit image widget, and overlay if need be, and sets them up."""

        overlay_container = self.ids['overlay']
        player = self.ids['player']
        self.position = 0
        if self.edit_mode == 'main':
            player.opacity = 1
            overlay_container.opacity = 0
            viewer = self.ids['photoShow']
            if self.edit_image:
                self.edit_image.close_video()
                if self.overlay:
                    viewer.remove_widget(self.overlay)
                viewer.remove_widget(self.edit_image)
                self.edit_image = None
        else:
            self.reset_start_point()
            self.reset_end_point()
            overlay_container.opacity = 1
            player.opacity = 0
            viewer = self.ids['photoShow']
            self.edit_image = CustomImage(mirror=self.mirror, angle=self.angle, photoinfo=self.photoinfo, source=self.file)
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

    def on_fullscreen(self, instance, value):
        player = self.ids['player']
        player.fullscreen = self.fullscreen

    def close(self):
        player = self.ids['player']
        player.close()

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

    def on_texture(self, *kwargs):
        super(PauseableVideo, self).on_texture(*kwargs)
        if self.first_load:
            app = App.get_running_app()
            app.album_screen.refresh_photoinfo_full(video=self._video)
        self.first_load = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.state == 'play':
                self.state = 'pause'
            else:
                self.state = 'play'
            return True


class EditPanelContainer(GridLayout):
    panel = None
    animating = None

    def animation_complete(self, *_):
        app = App.get_running_app()
        self.animating = None
        if self.panel:
            self.clear_widgets()
            self.opacity = 0
            self.add_widget(self.panel)
            self.animating = anim = Animation(opacity=1, duration=app.animation_length)
            anim.start(self)

    def change_panel(self, panel):
        app = App.get_running_app()
        self.panel = panel
        if app.animations:
            self.animating = anim = Animation(opacity=0, duration=app.animation_length)
            anim.start(self)
            anim.bind(on_complete=self.animation_complete)
        else:
            self.clear_widgets()
            self.opacity = 1
            if panel:
                self.add_widget(panel)


class EditNone(GridLayout):
    owner = ObjectProperty()

    def refresh_buttons(self):
        pass

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
        self.refresh_buttons()

    def refresh_buttons(self):
        self.update_undo()
        self.update_delete_original()
        self.update_delete_original_all()

    def save_last(self):
        pass

    def load_last(self):
        pass

    def update_delete_original(self):
        """Checks if the current viewed photo has an original file, enables the 'Delete Original' button if so."""

        delete_original_button = self.ids['deleteOriginal']
        if self.owner.photoinfo[9] == 1 and os.path.isfile(self.owner.photoinfo[10]):
            delete_original_button.disabled = False
        else:
            delete_original_button.disabled = True

    def update_delete_original_all(self):
        """Checks if currently viewing a folder, enables 'Delete All Originals' button if so."""

        delete_original_all_button = self.ids['deleteOriginalAll']
        if self.owner.type == 'Folder':
            delete_original_all_button.disabled = False
        else:
            delete_original_all_button.disabled = True

    def update_undo(self):
        """Checks if the current viewed photo has an original file, enables the 'Restore Original' button if so."""

        undo_button = self.ids['undoEdits']
        if self.owner.photoinfo[9] == 1 and os.path.isfile(self.owner.photoinfo[10]):
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
            program_button.bind(on_release=lambda button: app.program_run(button.index, button))
            program_button.bind(on_remove=lambda button: self.remove_program(button.index))
            program_button.content = ExternalProgramEditor(index=index, name=name, command=command, argument=argument, owner=self)
            external_programs.add_widget(program_button)
            if index == expand_index and expand:
                program_button.expanded = True


class EditPanelBase(GridLayout):
    def set_slider(self, slider, value):
        Clock.schedule_once(lambda x: self.set_slider_delay(slider, value), .1)

    def set_slider_delay(self, slider, value):
        self.ids[slider].value = value


class EditColorImage(EditPanelBase):
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

    def refresh_buttons(self):
        pass

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
        self.owner.saturation = self.saturation
        self.owner.temperature = self.temperature
        self.owner.shadow = self.shadow

    def load_last(self):
        self.equalize = self.owner.equalize
        self.set_slider('equalizeSlider', self.equalize)
        self.autocontrast = self.owner.autocontrast
        self.adaptive = self.owner.adaptive
        self.set_slider('adaptiveSlider', self.adaptive)
        self.brightness = self.owner.brightness
        self.set_slider('brightnessSlider', self.brightness)
        self.gamma = self.owner.gamma
        self.set_slider('gammaSlider', self.gamma)
        self.saturation = self.owner.saturation
        self.set_slider('saturationSlider', self.saturation)
        self.temperature = self.owner.temperature
        self.set_slider('temperatureSlider', self.temperature)
        self.shadow = self.owner.shadow
        self.set_slider('shadowSlider', self.shadow)

    def draw_histogram(self, *_):
        """Draws the histogram image and displays it."""

        if self.owner.viewer.edit_image is None:
            return
        size = 256  #Determines histogram resolution
        size_multiplier = int(256/size)
        histogram_data = self.owner.viewer.edit_image.histogram
        if len(histogram_data) == 768:
            histogram = self.ids['histogram']
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
        self.set_slider('equalizeSlider', self.equalize)

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
        self.set_slider('adaptiveSlider', self.adaptive)

    def on_brightness(self, *_):
        self.owner.viewer.edit_image.brightness = self.brightness

    def reset_brightness(self):
        self.brightness = 0
        self.set_slider('brightnessSlider', self.brightness)

    def on_shadow(self, *_):
        self.owner.viewer.edit_image.shadow = self.shadow

    def reset_shadow(self):
        self.shadow = 0
        self.set_slider('shadowSlider', self.shadow)

    def on_gamma(self, *_):
        self.owner.viewer.edit_image.gamma = self.gamma

    def reset_gamma(self):
        self.gamma = 0
        self.set_slider('gammaSlider', self.gamma)

    def on_saturation(self, *_):
        self.owner.viewer.edit_image.saturation = self.saturation

    def reset_saturation(self):
        self.saturation = 0
        self.set_slider('saturationSlider', self.saturation)

    def on_temperature(self, *_):
        self.owner.viewer.edit_image.temperature = self.temperature

    def reset_temperature(self):
        self.temperature = 0
        self.set_slider('temperatureSlider', self.temperature)

    def reset_all(self):
        """Reset all edit settings on this panel."""

        self.reset_brightness()
        self.reset_shadow()
        self.reset_gamma()
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

    def refresh_buttons(self):
        pass

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


class EditFilterImage(EditPanelBase):
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
        Clock.schedule_once(self.reset_all)
        super(EditFilterImage, self).__init__(**kwargs)

    def refresh_buttons(self):
        pass

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
        self.set_slider('sharpenSlider', self.sharpen)
        self.median = self.owner.median
        self.set_slider('medianSlider', self.median)
        self.bilateral_amount = self.owner.bilateral_amount
        self.set_slider('bilateralAmountSlider', self.bilateral_amount)
        self.bilateral = self.owner.bilateral
        self.set_slider('bilateralSlider', self.bilateral)
        self.vignette_amount = self.owner.vignette_amount
        self.set_slider('vignetteAmountSlider', self.vignette_amount)
        self.vignette_size = self.owner.vignette_size
        self.set_slider('vignetteSizeSlider', self.vignette_size)
        self.edge_blur_amount = self.owner.edge_blur_amount
        self.set_slider('edgeBlurAmountSlider', self.edge_blur_amount)
        self.edge_blur_size = self.owner.edge_blur_size
        self.set_slider('edgeBlurSizeSlider', self.edge_blur_size)
        self.edge_blur_intensity = self.owner.edge_blur_intensity
        self.set_slider('edgeBlurIntensitySlider', self.edge_blur_intensity)

    def on_sharpen(self, *_):
        self.owner.viewer.edit_image.sharpen = self.sharpen

    def reset_sharpen(self):
        self.sharpen = 0
        self.set_slider('sharpenSlider', self.sharpen)

    def on_median(self, *_):
        self.owner.viewer.edit_image.median_blur = self.median

    def reset_median(self):
        self.median = 0
        self.set_slider('medianSlider', self.median)

    def on_bilateral_amount(self, *_):
        self.owner.viewer.edit_image.bilateral_amount = self.bilateral_amount

    def reset_bilateral_amount(self):
        self.bilateral_amount = 0
        self.set_slider('bilateralAmountSlider', self.bilateral_amount)

    def on_bilateral(self, *_):
        self.owner.viewer.edit_image.bilateral = self.bilateral

    def reset_bilateral(self):
        self.bilateral = 0.5
        self.set_slider('bilateralSlider', self.bilateral)

    def on_vignette_amount(self, *_):
        self.owner.viewer.edit_image.vignette_amount = self.vignette_amount

    def reset_vignette_amount(self):
        self.vignette_amount = 0
        self.set_slider('vignetteAmountSlider', self.vignette_amount)

    def on_vignette_size(self, *_):
        self.owner.viewer.edit_image.vignette_size = self.vignette_size

    def reset_vignette_size(self):
        self.vignette_size = 0.5
        self.set_slider('vignetteSizeSlider', self.vignette_size)

    def on_edge_blur_amount(self, *_):
        self.owner.viewer.edit_image.edge_blur_amount = self.edge_blur_amount

    def reset_edge_blur_amount(self):
        self.edge_blur_amount = 0
        self.set_slider('edgeBlurAmountSlider', self.edge_blur_amount)

    def on_edge_blur_size(self, *_):
        self.owner.viewer.edit_image.edge_blur_size = self.edge_blur_size

    def reset_edge_blur_size(self):
        self.edge_blur_size = 0.5
        self.set_slider('edgeBlurSizeSlider', self.edge_blur_size)

    def on_edge_blur_intensity(self, *_):
        self.owner.viewer.edit_image.edge_blur_intensity = self.edge_blur_intensity

    def reset_edge_blur_intensity(self):
        self.edge_blur_intensity = 0.5
        self.set_slider('edgeBlurIntensitySlider', self.edge_blur_intensity)

    def reset_all(self, *_):
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


class EditBorderImage(EditPanelBase):
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
        self.reset_border_opacity()
        Clock.schedule_once(self.add_video_preset)
        Clock.schedule_once(self.populate_borders)
        super(EditBorderImage, self).__init__(**kwargs)

    def refresh_buttons(self):
        pass

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
        self.set_slider('borderXScale', self.border_x_scale)
        self.border_y_scale = self.owner.border_y_scale
        self.set_slider('borderYScale', self.border_y_scale)
        self.border_opacity = self.owner.border_opacity
        self.set_slider('opacitySlider', self.border_opacity)
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
        self.set_slider('borderXScale', self.border_x_scale)

    def on_border_y_scale(self, *_):
        self.owner.viewer.edit_image.border_y_scale = self.border_y_scale

    def reset_border_y_scale(self):
        self.border_y_scale = 0
        self.set_slider('borderYScale', self.border_y_scale)

    def on_border_opacity(self, *_):
        self.owner.viewer.edit_image.border_opacity = self.border_opacity

    def reset_border_opacity(self, *_):
        self.border_opacity = 1
        self.set_slider('opacitySlider', self.border_opacity)

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

    def refresh_buttons(self):
        pass

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
        if self.owner.viewer.edit_image.video:
            self.owner.save_video()
        else:
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
        #Gets the denoised preview image and updates it in the ui

        #convert pil image to bytes and display background image
        app = App.get_running_app()
        if to_bool(app.config.get("Settings", "lowmem")):
            image = self.owner.viewer.edit_image.edit_image
        else:
            image = self.owner.viewer.edit_image.original_image
        noise_preview = self.ids['noisePreview']
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_bytes = BytesIO()
        image.save(image_bytes, 'jpeg')
        image_bytes.seek(0)
        noise_preview._coreimage = CoreImage(image_bytes, ext='jpg')
        noise_preview._on_tex_change()

        #update overlay image
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


class EditCropImage(EditPanelBase):
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
        Clock.schedule_once(self.reset_crop)  #Give the cropper overlay a frame so it can figure out its actual size

    def refresh_buttons(self):
        pass

    def save_image(self, *_):
        if self.owner.viewer.edit_image.video:
            self.owner.save_video()
        else:
            self.owner.save_image()

    def update_crop_size_text(self):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.get_crop_size()

    def update_crop_values(self):
        self.ids['cropLeftSlider'].value = self.crop_left
        self.ids['cropRightSlider'].value = self.crop_right
        self.ids['cropTopSlider'].value = self.crop_top
        self.ids['cropBottomSlider'].value = self.crop_bottom

    def update_crop(self):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            percents = edit_image.get_crop_percent()
            self.crop_top = percents[0]
            self.crop_right = percents[1]
            self.crop_bottom = percents[2]
            self.crop_left = percents[3]
            self.update_crop_values()

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

    def reset_crop_top(self):
        self.crop_top = 0
        self.set_slider('cropTopSlider', self.crop_top)

    def on_crop_right(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('right', self.crop_right)
            self.update_crop_size_text()

    def reset_crop_right(self):
        self.crop_right = 0
        self.set_slider('cropRightSlider', self.crop_right)

    def on_crop_bottom(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('bottom', self.crop_bottom)
            self.update_crop_size_text()

    def reset_crop_bottom(self):
        self.crop_bottom = 0
        self.set_slider('cropBottomSlider', self.crop_bottom)

    def on_crop_left(self, *_):
        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.crop_percent('left', self.crop_left)
            self.update_crop_size_text()

    def reset_crop_left(self):
        self.crop_left = 0
        self.set_slider('cropLeftSlider', self.crop_left)

    def recrop(self):
        """tell image to recrop itself based on an aspect ratio"""

        edit_image = self.owner.viewer.edit_image
        if edit_image:
            edit_image.set_aspect(self.aspect_x, self.aspect_y)
            self.update_crop()

    def reset_crop(self, *_):
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


class EditRotateImage(EditPanelBase):
    """Panel to expose rotation editing options."""

    fine_angle = NumericProperty(0)
    owner = ObjectProperty()

    def refresh_buttons(self):
        pass

    def save_image(self, *_):
        if self.owner.viewer.edit_image.video:
            self.owner.save_video()
        else:
            self.owner.save_image()

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
        self.update_flip_horizontal(flip='up')
        self.ids['flip_horizontal'].state = 'normal'
        self.update_flip_vertical(flip='up')
        self.ids['flip_vertical'].state = 'normal'
        self.reset_fine_angle()

    def update_angle(self, angle):
        self.owner.viewer.edit_image.rotate_angle = angle

    def on_fine_angle(self, *_):
        self.owner.viewer.edit_image.fine_angle = self.fine_angle

    def reset_fine_angle(self, *_):
        self.fine_angle = 0
        self.set_slider('fine_angle', self.fine_angle)

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

    def refresh_buttons(self):
        pass

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

    def refresh_buttons(self):
        pass

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
                self.store_settings()
                return

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
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, before=previous_y, before_distance=previous_distance, after=next_y, after_distance=next_distance, mode='catmull')
            elif interpolation == 'Cubic':
                ys = interpolate(start_y, stop_y, distance, 0, total_bytes, before=previous_y, before_distance=previous_distance, after=next_y, after_distance=next_distance, mode='cubic')
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
            if touch.button == 'left':
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

        content = FileBrowser(ok_text='Select', filters=['*'])
        content.bind(on_cancel=lambda x: self.owner.owner.dismiss_popup())
        content.bind(on_ok=self.select_command_confirm)
        self.owner.owner.popup = filepopup = NormalPopup(title='Select A Program', content=content, size_hint=(0.9, 0.9))
        filepopup.open()

    def select_command_confirm(self, *_):
        """Called when the filebrowser dialog is successfully closed."""

        self.command = self.owner.owner.popup.content.filename
        self.owner.owner.dismiss_popup()
        self.save_program()


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
