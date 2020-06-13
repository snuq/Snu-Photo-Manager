import os
import re
import time
import math
from io import BytesIO
import PIL
from PIL import Image, ImageEnhance, ImageOps, ImageChops, ImageDraw, ImageFilter, ImageFile

from ffpyplayer.player import MediaPlayer
from ffpyplayer.pic import SWScale
from ffpyplayer import tools as fftools
from kivy.config import Config
Config.window_icon = "data/icon.png"
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.cache import Cache
from kivy.graphics.transformation import Matrix
from kivy.uix.widget import Widget
from kivy.uix.bubble import Bubble
from kivy.uix.behaviors import ButtonBehavior, DragBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.splitter import Splitter
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.treeview import TreeViewNode
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.core.image import ImageLoader
from kivy.uix.scrollview import ScrollView
from kivy.loader import Loader as ThumbLoader
from kivy.core.image.img_pil import ImageLoaderPIL
from kivy.uix.stencilview import StencilView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.slider import Slider

from generalconstants import *
from generalcommands import get_keys_from_list, to_bool, isfile2, rotated_rect_with_max_area

from kivy.lang.builder import Builder
Builder.load_string("""
<-Button,-ToggleButton>:
    state_image: self.background_normal if self.state == 'normal' else self.background_down
    disabled_image: self.background_disabled_normal if self.state == 'normal' else self.background_disabled_down
    canvas:
        Color:
            rgba: self.background_color
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            border: self.border
            pos: self.pos
            size: self.size
            source: self.disabled_image if self.disabled else self.state_image
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

<ClickFade>:
    canvas:
        Color:
            rgba: 1, 1, 1, .5
        Rectangle:
            size: self.size
            pos: root.pos
    size_hint: None, None
    opacity: 0

<SmallBufferY@Widget>:
    size_hint_y: None
    height: int(app.button_scale / 4)

<MediumBufferY@Widget>:
    size_hint_y: None
    height: int(app.button_scale / 2)

<LargeBufferY@Widget>:
    size_hint_y: None
    height: app.button_scale

<SmallBufferX@Widget>:
    size_hint_x: None
    width: int(app.button_scale / 4)

<MediumBufferX@Widget>:
    size_hint_x: None
    width: int(app.button_scale / 2)

<LargeBufferX@Widget>:
    size_hint_x: None
    width: app.button_scale

<HeaderBase@BoxLayout>:
    size_hint_y: None
    orientation: 'horizontal'

<Header@HeaderBase>:
    canvas.before:
        Color:
            rgba: app.theme.header_background
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/headerbg.png'
    height: app.button_scale

<MainHeader@HeaderBase>:
    canvas.before:
        Color:
            rgba: app.theme.header_main_background
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/headerbglight.png'
    height: int(app.button_scale * 1.25)
    padding: int(app.button_scale / 8)

<MainArea@BoxLayout>:
    canvas.before:
        Color:
            rgba: app.theme.main_background
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/mainbg.png'

<ExpandablePanel>:
    cols: 1
    height: 0
    opacity: 0
    size_hint: 1, None

<NormalSlider>:
    #:set sizing 18
    canvas:
        Color:
            rgba: app.theme.slider_background
        BorderImage:
            border: (0, sizing, 0, sizing)
            pos: self.pos
            size: self.size
            source: 'data/sliderbg.png'
        Color:
            rgba: app.theme.slider_grabber
        Rectangle:
            pos: (self.value_pos[0] - app.button_scale/4, self.center_y - app.button_scale/2)
            size: app.button_scale/2, app.button_scale
            source: 'data/buttonflat.png'
    size_hint_y: None
    height: app.button_scale
    min: -1
    max: 1
    value: 0

<HalfSlider>:
    #:set sizing 18
    canvas:
        Color:
            rgba: app.theme.slider_background
        BorderImage:
            border: (0, sizing, 0, sizing)
            pos: self.pos
            size: self.size
            source: 'data/sliderbg.png'
        Color:
            rgba: app.theme.slider_grabber
        Rectangle:
            pos: (self.value_pos[0] - app.button_scale/4, self.center_y - app.button_scale/2)
            size: app.button_scale/2, app.button_scale
            source: 'data/buttonflat.png'
    size_hint_y: None
    height: app.button_scale
    min: 0
    max: 1
    value: 0

<HalfSliderLimited>:
    #:set sizing 18
    canvas:
        Color:
            rgba: app.theme.slider_background
        BorderImage:
            border: (0, sizing, 0, sizing)
            pos: self.pos
            size: self.size
            source: 'data/sliderbg.png'
        Color:
            rgba: 0, 0, 0, .5
        Rectangle:
            pos: 0, 0
            size: self.width * self.start, self.height
        Rectangle:
            pos: self.width * self.end, 0
            size: self.width * (1 - self.end), self.height
        Color:
            rgba: app.theme.slider_grabber
        Rectangle:
            pos: (self.value_pos[0] - app.button_scale/4, self.center_y - app.button_scale/2)
            size: app.button_scale/2, app.button_scale
            source: 'data/buttonflat.png'
    size_hint_y: None
    height: app.button_scale
    min: 0
    max: 1
    value: 0


<NormalLabel>:
    mipmap: True
    color: app.theme.text
    font_size: app.text_scale
    size_hint_y: None
    height: app.button_scale

<LeftNormalLabel>:
    mipmap: True
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_x: 1
    text_size: self.size
    halign: 'left'
    valign: 'middle'

<ShortLabel>:
    mipmap: True
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_x: 1
    size_hint_max_x: self.texture_size[0] + 20
    #width: self.texture_size[0] + 20

<PhotoThumbLabel>:
    mipmap: True
    valign: 'middle'
    text_size: (self.width-10, self.height)
    size_hint_y: None
    size_hint_x: None
    height: (app.button_scale * 4)
    width: (app.button_scale * 4)
    text: ''

<InfoLabel>:
    canvas.before:
        Color:
            rgba: root.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
    mipmap: True
    text: app.infotext
    color: app.theme.info_text

<DatabaseLabel@ShortLabel>:
    mipmap: True
    text: app.database_update_text

<HeaderLabel@Label>:
    mipmap: True
    color: app.theme.header_text
    font_size: int(app.text_scale * 1.5)
    size_hint_y: None
    height: app.button_scale
    bold: True

<MultilineLabel@Label>:
    mipmap: True
    color: app.theme.text
    font_size: app.text_scale
    size_hint_y: None
    multiline: True
    text_size: self.width, None
    size: self.texture_size


<BubbleContent>:
    canvas:
        Clear:
    opacity: .7 if self.disabled else 1
    rows: 1

<InputMenu>:
    canvas.before:
        Color:
            rgba: app.theme.menu_background
        BorderImage:
            size: self.size
            pos: self.pos
            source: 'data/buttonflat.png'
    size_hint: None, None
    size: app.button_scale * 9, app.button_scale
    show_arrow: False
    MenuButton:
        text: 'Select All'
        on_release: root.select_all()
    MenuButton:
        disabled: not root.edit
        text: 'Cut'
        on_release: root.cut()
    MenuButton:
        text: 'Copy'
        on_release: root.copy()
    MenuButton:
        disabled: not root.edit
        text: 'Paste'
        on_release: root.paste()

<-TextInput>:
    canvas.before:
        Color:
            rgba: self.background_color
        BorderImage:
            border: self.border
            pos: self.pos[0] + 3, self.pos[1] + 3
            size: self.size[0] -6, self.size[1] - 6
            source: self.background_active if self.focus else (self.background_disabled_normal if self.disabled else self.background_normal)
        Color:
            rgba:
                (self.cursor_color
                if self.focus and not self._cursor_blink
                else (0, 0, 0, 0))
        Rectangle:
            pos: self._cursor_visual_pos
            size: root.cursor_width, -self._cursor_visual_height
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text else self.foreground_color)

<NormalInput>:
    mipmap: True
    cursor_color: app.theme.text
    write_tab: False
    background_color: app.theme.input_background
    hint_text_color: app.theme.disabled_text
    disabled_foreground_color: 1,1,1,.75
    foreground_color: app.theme.text
    size_hint_y: None
    height: app.button_scale
    font_size: app.text_scale

<FloatInput>:
    write_tab: False
    background_color: .2, .2, .3, .8
    disabled_foreground_color: 1,1,1,.75
    foreground_color: 1,1,1,1
    size_hint_y: None
    height: app.button_scale
    font_size: app.text_scale

<IntegerInput>:
    write_tab: False
    background_color: .2, .2, .3, .8
    disabled_foreground_color: 1,1,1,.75
    foreground_color: 1,1,1,1
    size_hint_y: None
    height: app.button_scale
    font_size: app.text_scale


<ButtonBase>:
    mipmap: True
    size_hint_y: None
    height: app.button_scale
    background_normal: 'data/button.png'
    background_down: 'data/button.png'
    background_disabled_down: 'data/button.png'
    background_disabled_normal: 'data/button.png'
    button_update: app.button_update

<NormalButton>:
    width: self.texture_size[0] + app.button_scale
    size_hint_x: None
    font_size: app.text_scale

<WideButton>:
    font_size: app.text_scale
    text_size: self.size
    halign: 'center'
    valign: 'middle'

<MenuButton>:
    font_size: app.text_scale
    menu: True
    size_hint_x: 1

<RemoveButton>:
    font_size: app.text_scale
    mipmap: True
    size_hint: None, None
    height: app.button_scale
    width: app.button_scale
    warn: True
    text: 'X'

<ExpandableButton>:
    cols: 1
    size_hint: 1, None
    height: self.minimum_height
    GridLayout:
        cols: 3
        size_hint: 1, None
        height: app.button_scale
        CheckBox:
            active: root.expanded
            size_hint: None, None
            height: app.button_scale
            width: app.button_scale
            background_checkbox_normal: 'data/tree_closed.png'
            background_checkbox_down: 'data/tree_opened.png'
            on_press: root.set_expanded(self.active)
        WideButton:
            on_press: root.dispatch('on_press')
            on_release: root.dispatch('on_release')
            text: root.text
        RemoveButton:
            on_release: root.dispatch('on_remove')
    GridLayout:
        canvas.before:
            Color:
                rgba: app.theme.menu_background
            BorderImage:
                pos: self.pos
                size: self.size
                source: 'data/buttonflat.png'
        padding: app.padding
        cols: 1
        size_hint: 1, None
        #height: self.minimum_height
        height: app.padding * 2
        opacity: 0
        id: contentContainer

<TreeViewButton>:
    color_selected: app.theme.selected
    odd_color: app.list_background_odd
    even_color: app.list_background_even
    orientation: 'vertical'
    size_hint_y: None
    height: app.button_scale
    NormalLabel:
        mipmap: True
        markup: True
        text_size: (self.width - 20, None)
        halign: 'left'
        text: root.folder_name + '   [b]' + root.total_photos + '[/b]'
    NormalLabel:
        mipmap: True
        id: subtext
        text_size: (self.width - 20, None)
        font_size: app.text_scale
        color: .66, .66, .66, 1
        halign: 'left'
        size_hint_y: None
        height: 0
        text: root.subtext

<MenuStarterButton@ButtonBase>:
    canvas.after:
        Color:
            rgba: self.color
        Rectangle:
            pos: (root.pos[0]+root.width-(root.height/1.5)), root.pos[1]
            size: root.height/2, root.height
            source: 'data/menuarrows.png'
    menu: True
    size_hint_y: None
    height: app.button_scale
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_max_x: self.texture_size[0] + (app.button_scale * 1.2)

<MenuStarterButtonWide@ButtonBase>:
    canvas.after:
        Color:
            rgba: self.color
        Rectangle:
            pos: (root.pos[0]+root.width-(root.height/1.5)), root.pos[1]
            size: root.height/2, root.height
            source: 'data/menuarrows.png'
    menu: True
    size_hint_y: None
    height: app.button_scale
    text_size: self.size
    halign: 'center'
    valign: 'middle'
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_x: 1

<NormalToggle@ToggleBase>:
    always_release: True
    toggle: True
    font_size: app.text_scale
    size_hint_x: None
    width: self.texture_size[0] + 20

<ReverseToggle@ToggleBase>:
    canvas:
        Color:
            rgba: self.color
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'data/arrowdown.png' if self.state == 'normal' else 'data/arrowup.png'
    menu: True
    font_size: app.text_scale
    size_hint: None, None
    height: app.button_scale
    width: app.button_scale

<SettingsButton@NormalButton>:
    canvas:
        Color:
            rgba: self.background_color if app.simple_interface else (0, 0, 0, 0)
        BorderImage:
            border: self.border
            pos: self.pos
            size: self.size
            source: 'data/settings.png'
    text: '' if app.simple_interface else 'Settings'
    border: (0, 0, 0, 0) if app.simple_interface else (16, 16, 16, 16)
    background_normal: 'data/transparent.png' if app.simple_interface else 'data/button.png'
    background_down: self.background_normal
    on_release: app.open_settings()

<InfoButton>:
    width: (self.texture_size[0] + app.button_scale) if app.infotext_history else 0
    opacity: 1 if app.infotext_history else 0
    disabled: False if app.infotext_history else True
    text: "Messages"

<VerticalButton>:
    size_hint_y: None
    size_hint: None, None
    width: app.button_scale
    height: textArea.texture_size[0] + 100
    background_down: 'data/buttonright.png'
    Label:
        id: textArea
        font_size: app.text_scale
        center: self.parent.center
        canvas.before:
            PushMatrix
            Rotate:
                angle: 90
                axis: 0,0,1
                origin: self.center
        canvas.after:
            PopMatrix
        color: self.parent.color
        text: self.parent.vertical_text

<PhotoRecycleViewButton>:
    canvas.after:
        Color:
            rgba: (1, 1, 1, 0) if self.found else(1, 0, 0, .33)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: app.theme.favorite if self.favorite else [0, 0, 0, 0]
        Rectangle:
            source: 'data/star.png'
            pos: (self.pos[0]+(self.width-(self.height*.5)), self.pos[1]+(self.height*.5)-(self.height*.167))
            size: (self.height*.33, self.height*.33)
        Color:
            rgba: 1, 1, 1, .5 if self.video else 0
        Rectangle:
            source: 'data/play_overlay.png'
            pos: (self.pos[0]+(self.height*.25)), (self.pos[1]+(self.height*.25))
            size: (self.height*.5), (self.height*.5)
    size_hint_x: 1
    height: (app.button_scale * 2)
    AsyncThumbnail:
        id: thumbnail
        #photoinfo: root.photoinfo
        #source: root.source
        size_hint: None, None
        width: (app.button_scale * 2)
        height: (app.button_scale * 2)
    NormalLabel:
        mipmap: True
        size_hint_y: None
        height: (app.button_scale * 2)
        text_size: (self.width - 20, None)
        text: root.text
        halign: 'left'
        valign: 'center'


<NormalPopup>:
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
    background_color: 1, 1, 1, 0
    background: 'data/transparent.png'
    separator_color: 1, 1, 1, .25
    title_size: app.text_scale * 1.25
    title_color: app.theme.header_text

<InfotextPopup>:
    size_hint: .5, None
    title: ''
    title_size: 0
    separator_height: 0

<MessagePopup>:
    cols:1
    NormalLabel:
        text: root.text
    Label:
    GridLayout:
        cols:1
        size_hint_y: None
        height: app.button_scale
        WideButton:
            id: button
            text: root.button_text
            on_release: root.close()

<InputPopup>:
    cols:1
    NormalLabel:
        text: root.text
    NormalInput:
        id: input
        multiline: False
        hint_text: root.hint
        input_filter: app.test_album
        text: root.input_text
        focus: True
    Label:
    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: root.yes_text
            warn: root.warn_yes
            on_release: root.dispatch('on_answer','yes')
        WideButton:
            text: root.no_text
            warn: root.warn_no
            on_release: root.dispatch('on_answer', 'no')

<InputPopupTag>:
    cols:1
    NormalLabel:
        text: root.text
    NormalInput:
        id: input
        multiline: False
        hint_text: root.hint
        input_filter: app.test_tag
        text: root.input_text
        focus: True
    Label:
    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: root.yes_text
            warn: root.warn_yes
            on_release: root.dispatch('on_answer','yes')
        WideButton:
            text: root.no_text
            warn: root.warn_no
            on_release: root.dispatch('on_answer', 'no')

<ScanningPopup>:
    GridLayout:
        cols: 1
        NormalLabel:
            id: scanningText
            text: root.scanning_text
            text_size: self.size
        ProgressBar:
            id: scanningProgress
            value: root.scanning_percentage
            max: 100
        WideButton:
            id: scanningButton
            text: root.button_text

<ConfirmPopup>:
    cols:1
    NormalLabel:
        text: root.text
    Label:
    GridLayout:
        cols: 2
        size_hint_y: None
        height: app.button_scale
        WideButton:
            text: root.yes_text
            on_release: root.dispatch('on_answer','yes')
            warn: root.warn_yes
        WideButton:
            text: root.no_text
            on_release: root.dispatch('on_answer', 'no')
            warn: root.warn_no


<NormalDropDown>:
    canvas.before:
        Color:
            rgba: app.theme.menu_background
        Rectangle:
            size: root.width, root.height * root.show_percent
            pos: root.pos[0], root.pos[1] + (root.height * (1 - root.show_percent)) if root.invert else root.pos[1]
            source: 'data/buttonflat.png'

<AlbumSortDropDown>:
    MenuButton:
        text: 'Name'
        on_release: root.select(self.text)
    MenuButton:
        text: 'Path'
        on_release: root.select(self.text)
    MenuButton:
        text: 'Imported'
        on_release: root.select(self.text)
    MenuButton:
        text: 'Modified'
        on_release: root.select(self.text)

<AlbumExportDropDown>:
    MenuButton:
        text: 'Create Collage'
        disabled: not app.can_export
        on_release: root.dismiss()
        on_release: app.screen_manager.current_screen.collage_screen()
    MenuButton:
        text: 'Export'
        disabled: not app.can_export
        on_release: root.dismiss()
        on_release: app.screen_manager.current_screen.export_screen()


<RecycleItem>:
    canvas.before:
        Color:
            rgba: self.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
    size_hint_x: 1
    height: app.button_scale

<SimpleRecycleItem@RecycleItem>:
    NormalLabel:
        size_hint_y: None
        height: app.button_scale
        text_size: (self.width - 20, None)
        text: root.text
        halign: 'left'
        valign: 'center'

<PhotoRecycleThumb>:
    canvas.before:
        Color:
            rgba: self.underlay_color
            #rgba: app.theme.selected if self.selected else (0, 0, 0, 0)
        Rectangle:
            pos: (self.pos[0]-5, self.pos[1]-5)
            size: (self.size[0]+10, self.size[1]+10)
    canvas.after:
        Color:
            rgba: (1, 1, 1, 0) if self.found else(1, 0, 0, .33)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: app.theme.favorite if root.favorite else [0, 0, 0, 0]
        Rectangle:
            source: 'data/star.png'
            pos: (self.pos[0]+(self.size[0]/2)-(self.size[0]*.05), self.pos[1]+(self.size[0]*.1))
            size: (self.size[0]*.1, self.size[0]*.1)
        Color:
            rgba: 1, 1, 1, .5 if root.video else 0
        Rectangle:
            source: 'data/play_overlay.png'
            pos: (self.pos[0]+self.width/8, self.pos[1]+self.width/8) if self.title else (self.pos[0]+self.width/4, self.pos[1]+self.width/4)
            size: (self.width/4, self.width/4) if self.title else (self.width/2, self.width/2)

    drag_rectangle: self.x, self.y, self.width, self.height
    drag_timeout: 10000000
    drag_distance: 0
    width: (app.button_scale * 4)
    height: (app.button_scale * 4)
    size_hint_y: None
    size_hint_x: None
    orientation: 'horizontal'
    AsyncThumbnail:
        id: thumbnail
        width: self.height
        size_hint_x: None

<PhotoRecycleThumbWide>:
    PhotoThumbLabel:
        text: root.title

<RecycleTreeViewButton>:
    orientation: 'vertical'
    size_hint_y: None
    #height: int((app.button_scale * 1.5 if self.subtext else app.button_scale) + (app.button_scale * .1 if self.end else 0))
    BoxLayout:
        orientation: 'horizontal'
        Widget:
            width: (app.button_scale * .25) + (app.button_scale * 0.5 * root.indent)
            size_hint_x: None
        Image:
            width: self.texture_size[0]
            size_hint_x: None
            source: 'data/tree_opened.png' if root.expanded else 'data/tree_closed.png'
            opacity: 1 if root.expandable else 0
        BoxLayout:
            orientation: 'vertical'
            NormalLabel:
                id: mainText
                markup: True
                text_size: (self.width - 20, None)
                halign: 'left'
                text: ''
            NormalLabel:
                id: subtext
                text_size: (self.width - 20, None)
                font_size: app.text_scale
                color: app.theme.text[0], app.theme.text[1], app.theme.text[2], .5
                halign: 'left'
                size_hint_y: None
                height: app.button_scale * .5 if root.subtext else 0
                text: root.subtext
    Widget:
        canvas.before:
            Color:
                rgba: 0, 0, 0, .2 if root.end else 0
            Rectangle:
                pos: self.pos
                size: self.size
        size_hint_y: None
        height: int(app.button_scale * .1) if root.end else 0

<TreenodeDrag>:
    canvas.before:
        Color:
            rgba: (.2, .2, .4, .4)
        Rectangle:
            pos: self.pos
            size: self.size
    orientation: 'vertical'
    size_hint_x: None
    width: 100
    size_hint_y: None
    height: app.button_scale
    NormalLabel:
        text_size: (self.width - 20, None)
        halign: 'left'
        text: root.text
    NormalLabel:
        id: subtext
        text_size: (self.width - 20, None)
        font_size: app.text_scale
        color: .66, .66, .66, 1
        halign: 'left'
        size_hint_y: None
        height: 0
        text: root.subtext

<SelectableRecycleBoxLayout>:
    default_size_hint: 1, None
    default_size: self.width, app.button_scale
    spacing: 2
    size_hint_x: 1
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    multiselect: False
    touch_multiselect: False

<SelectableRecycleGrid>:
    cols: max(1, int(self.width / ((app.button_scale * 4 * self.scale) + (app.button_scale / 2))))
    spacing: int(app.button_scale / 2)
    padding: int(app.button_scale / 2)
    focus: False
    touch_multiselect: True
    multiselect: True
    default_size: app.button_scale * 4 * self.scale, app.button_scale * 4 * self.scale
    default_size_hint: None, None
    height: self.minimum_height
    size_hint_y: None

<SelectableRecycleGridWide@SelectableRecycleGrid>:
    cols: max(1, int(self.width / ((app.button_scale * 8) + (app.button_scale / 2))))
    default_size: (app.button_scale * 8), (app.button_scale * 4)

<NormalRecycleView>:
    size_hint: 1, 1
    do_scroll_x: False
    do_scroll_y: True
    scroll_distance: 10
    scroll_timeout: 200
    bar_width: int(app.button_scale * .5)
    bar_color: app.theme.scroller_selected
    bar_inactive_color: app.theme.scroller
    scroll_type: ['bars', 'content']

<NormalTreeView@TreeView>:
    color_selected: app.theme.selected
    odd_color: app.list_background_odd
    even_color: app.list_background_even
    indent_level: int(app.button_scale * .5)
    size_hint: 1, None
    height: self.minimum_height
    hide_root: True


<SplitterResizer>:
    background_color: app.theme.sidebar_resizer
    background_normal: 'data/splitterbgup.png'
    background_down: 'data/splitterbgdown.png'
    border: 0, 0, 0, 0

<SplitterPanel>:
    canvas.before:
        Color:
            rgba: app.theme.sidebar_background
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/panelbg.png'
    #keep_within_parent: True
    min_size: int(app.button_scale / 2)
    size_hint: None, 1
    strip_size: int(app.button_scale / 3)

<SplitterPanelLeft>:
    width: self.display_width
    disabled: self.hidden
    sizable_from: 'right'

<SplitterPanelRight>:
    width: self.display_width
    disabled: self.hidden
    sizable_from: 'left'


<CustomImage>:
    canvas.after:
        Color:
            rgba: [0, 0, 0, 0.5]
        Mesh:
            vertices: self.crop_verts
            indices: self.crop_indices
            mode: 'triangles'
    allow_stretch: True

<AsyncThumbnail>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: self.angle
            axis: 0,0,1
            origin: self.center
    canvas.after:
        PopMatrix
    allow_stretch: True

<PhotoDrag>:
    height: (app.button_scale * 4)
    width: (app.button_scale * 4)
    size_hint_y: None
    size_hint_x: None
    Image:
        canvas.before:
            PushMatrix
            Rotate:
                angle: root.angle
                axis: 0,0,1
                origin: root.center
        canvas.after:
            PopMatrix
        id: image
        pos: root.pos
        size: root.size
        size_hint: None, None
        source: root.source
        fullpath: root.fullpath
    ShortLabel:
        pos: root.pos
        text: root.total_drags


<Scroller>:
    scroll_distance: 10
    scroll_timeout: 100
    bar_width: int(app.button_scale * .5)
    bar_color: app.theme.scroller_selected
    bar_inactive_color: app.theme.scroller
    scroll_type: ['bars', 'content']

<ColorPickerCustom_Label@Label>:
    mroot: None
    size_hint_x: None
    width: '30sp'
    text_size: self.size
    halign: "center"
    valign: "middle"

<ColorPickerCustom_Selector@BoxLayout>:
    foreground_color: None
    text: ''
    mroot: None
    mode: 'rgb'
    color: 0
    spacing: '2sp'
    ColorPickerCustom_Label:
        text: root.text
        mroot: root.mroot
        color: root.foreground_color or (1, 1, 1, 1)
    Slider:
        id: sldr
        size_hint: 1, .25
        pos_hint: {'center_y':.5}
        range: 0, 255
        value: root.color * 255
        on_value:
            root.mroot._trigger_update_clr(root.mode, root.clr_idx, args[1])

<ColorPickerCustom>:
    canvas.before:
        Color:
            rgba: self.color
        Rectangle:
            pos: self.pos
            size: self.size

    orientation: 'vertical'
    size_hint_y: None
    height: sp(33)*10 if self. orientation == 'vertical' else sp(33)*5
    foreground_color: (1, 1, 1, 1) if self.hsv[2] * wheel.a < .5 else (0, 0, 0, 1)
    wheel: wheel
    BoxLayout:
        orientation: root.orientation
        spacing: '5sp'
        ColorWheel:
            id: wheel
            color: root.color
            on_color: root.color[:3] = args[1][:3]
        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            canvas:
                Color:
                    rgba: root.color
                Rectangle:
                    size: self.size
                    pos: self.pos

            ColorPickerCustom_Selector:
                mroot: root
                text: 'R'
                clr_idx: 0
                color: wheel.r
                foreground_color: root.foreground_color
                size_hint_y: None
                height: 0
                disabled: True
                opacity: 0

            ColorPickerCustom_Selector:
                mroot: root
                mode: 'hsv'
                text: 'H'
                clr_idx: 0
                color: root.hsv[0]
                foreground_color: root.foreground_color
                size_hint_y: None
                height: app.button_scale

            ColorPickerCustom_Selector:
                mroot: root
                mode: 'hsv'
                text: 'S'
                clr_idx: 1
                color: root.hsv[1]
                foreground_color: root.foreground_color
                size_hint_y: None
                height: app.button_scale

            ColorPickerCustom_Selector:
                mroot: root
                mode: 'hsv'
                text: 'V'
                clr_idx: 2
                color: root.hsv[2]
                foreground_color: root.foreground_color
                size_hint_y: None
                height: app.button_scale

""")


#Misc ELements
class ClickFade(Widget):
    animation = None

    def begin(self, mode='opacity'):
        app = App.get_running_app()
        self.opacity = 0

        if app.animations:
            if self.animation:
                self.animation.cancel(self)
            if mode == 'height':
                self.animation = Animation(opacity=1, duration=(app.animation_length / 4)) + Animation(height=0, pos=(self.pos[0], self.pos[1]+self.height), duration=(app.animation_length / 2))
            else:
                self.animation = Animation(opacity=1, duration=(app.animation_length / 4)) + Animation(opacity=0, duration=(app.animation_length / 2))
            self.animation.start(self)
            self.animation.bind(on_complete=self.finish_animation)
        else:
            self.finish_animation()

    def finish_animation(self, *_):
        self.animation = None
        try:
            self.parent.remove_widget(self)
        except:
            pass


class EncodingSettings(Widget):
    name = StringProperty('User Preset')

    file_format = StringProperty('Auto')
    video_codec = StringProperty('Auto')
    audio_codec = StringProperty('Auto')
    resize = BooleanProperty(False)
    resize_width = StringProperty('')
    resize_height = StringProperty('')
    video_bitrate = StringProperty('')
    audio_bitrate = StringProperty('')
    encoding_speed = StringProperty('Auto')
    encoding_color = StringProperty('Auto')
    framerate = StringProperty('')
    deinterlace = BooleanProperty(False)
    command_line = StringProperty('')
    quality = StringProperty('Auto')
    gop = StringProperty('')
    description = StringProperty('')

    def on_gop(self, *_):
        if self.gop:
            try:
                gop = str(abs(int(self.gop)))
                if gop == '0':
                    self.gop = ''
                elif gop != self.gop:
                    self.gop = gop
            except:
                self.gop = ''

    def on_quality(self, *_):
        if self.quality not in encoding_quality_friendly+['Auto']:
            self.quality = 'Auto'

    def on_file_format(self, *_):
        app = App.get_running_app()
        containers_friendly = get_keys_from_list(app.containers)
        if self.file_format not in containers_friendly+['Auto']:
            self.file_format = 'Auto'

    def on_video_codec(self, *_):
        app = App.get_running_app()
        video_codecs_friendly = get_keys_from_list(app.video_codecs)
        if self.video_codec not in video_codecs_friendly+['Auto']:
            self.video_codec = 'Auto'
            self.video_bitrate = ''

    def on_audio_codec(self, *_):
        app = App.get_running_app()
        audio_codecs_friendly = get_keys_from_list(app.audio_codecs)
        if self.audio_codec not in audio_codecs_friendly+['Auto']:
            self.audio_codec = 'Auto'
            self.audio_bitrate = ''

    def on_encoding_color(self, *_):
        if self.encoding_color not in encoding_colors_friendly+['Auto']:
            self.encoding_color = 'Auto'

    def on_framerate(self, *_):
        if self.framerate:
            try:
                framerate = abs(float(self.framerate))
                if framerate == 0:
                    self.framerate = ''
                elif str(framerate) != self.framerate:
                    self.framerate = str(framerate)
            except:
                self.framerate = ''

    def on_resize(self, *_):
        if not self.resize:
            self.resize_width = ''
            self.resize_height = ''

    def on_resize_width(self, *_):
        if self.resize_width:
            try:
                width = str(abs(int(self.resize_width)))
                if width == '0':
                    self.resize_width = ''
                elif width != self.resize_width:
                    self.resize_width = width
            except:
                self.resize_width = ''

    def on_resize_height(self, *_):
        if self.resize_height:
            try:
                height = str(abs(int(self.resize_height)))
                if height == '0':
                    self.resize_height = ''
                elif height != self.resize_height:
                    self.resize_height = height
            except:
                self.resize_height = ''

    def on_video_bitrate(self, *_):
        if self.video_bitrate:
            try:
                bitrate = str(abs(int(self.video_bitrate)))
                if bitrate == '0':
                    self.video_bitrate = ''
                elif bitrate != self.video_bitrate:
                    self.video_bitrate = bitrate
            except:
                self.video_bitrate = ''

    def on_audio_bitrate(self, *_):
        if self.audio_bitrate:
            try:
                bitrate = str(abs(int(self.audio_bitrate)))
                if bitrate == '0':
                    self.audio_bitrate = ''
                elif bitrate != self.audio_bitrate:
                    self.audio_bitrate = bitrate
            except:
                self.audio_bitrate = ''

    def on_encoding_speed(self, *_):
        if self.encoding_speed not in encoding_speeds_friendly+['Auto']:
            self.encoding_speed = 'Auto'

    def get_encoding_preset(self, replace_auto=False):
        app = App.get_running_app()
        containers_friendly = get_keys_from_list(app.containers)
        video_codecs_friendly = get_keys_from_list(app.video_codecs)
        audio_codecs_friendly = get_keys_from_list(app.audio_codecs)

        encoding_settings = {}
        if replace_auto and self.file_format == 'Auto':
            encoding_settings['file_format'] = containers_friendly[0]
        else:
            encoding_settings['file_format'] = self.file_format
        if replace_auto and self.video_codec == 'Auto':
            encoding_settings['video_codec'] = video_codecs_friendly[0]
        else:
            encoding_settings['video_codec'] = self.video_codec
        if replace_auto and self.audio_codec == 'Auto':
            encoding_settings['audio_codec'] = audio_codecs_friendly[0]
        else:
            encoding_settings['audio_codec'] = self.audio_codec

        if not self.resize or (not self.resize_width or not self.resize_height):
            encoding_settings['height'] = ''
            encoding_settings['width'] = ''
            encoding_settings['resize'] = False
        else:
            encoding_settings['height'] = self.resize_height
            encoding_settings['width'] = self.resize_width
            encoding_settings['resize'] = True
        encoding_settings['framerate'] = self.framerate
        encoding_settings['video_bitrate'] = self.video_bitrate
        encoding_settings['audio_bitrate'] = self.audio_bitrate
        encoding_settings['gop'] = self.gop
        if replace_auto and self.quality == 'Auto':
            encoding_settings['quality'] = 'High'
        else:
            encoding_settings['quality'] = self.quality

        encoding_settings['encoding_speed'] = self.encoding_speed
        encoding_settings['command_line'] = self.command_line
        encoding_settings['deinterlace'] = self.deinterlace
        encoding_settings['encoding_color'] = self.encoding_color
        return encoding_settings

    def store_current_encoding_preset(self, store_app=True):
        file_format = self.file_format
        video_codec = self.video_codec
        audio_codec = self.audio_codec
        resize = str(self.resize)
        resize_width = self.resize_width
        resize_height = self.resize_height
        video_bitrate = self.video_bitrate
        audio_bitrate = self.audio_bitrate
        encoding_speed = self.encoding_speed
        deinterlace = str(self.deinterlace)
        encoding_color = self.encoding_color
        framerate = self.framerate
        gop = self.gop
        quality = self.quality
        command_line = self.command_line
        encoding_preset = file_format+','+video_codec+','+audio_codec+','+resize+','+resize_width+','+resize_height+','+framerate+','+video_bitrate+','+audio_bitrate+','+encoding_speed+','+encoding_color+','+deinterlace+','+gop+','+quality+','+command_line
        if store_app:
            app = App.get_running_app()
            app.config.set('Presets', 'encoding', encoding_preset)
        else:
            return encoding_preset

    def load_current_encoding_preset(self, load_from=None):
        if load_from is None:
            app = App.get_running_app()
            encoding_preset_text = app.config.get('Presets', 'encoding')
        else:
            encoding_preset_text = load_from
        if encoding_preset_text:
            encoding_settings = encoding_preset_text.split(',', 14)
            try:
                self.file_format = encoding_settings[0]
                self.video_codec = encoding_settings[1]
                self.audio_codec = encoding_settings[2]
                self.resize = to_bool(encoding_settings[3])
                self.resize_width = encoding_settings[4]
                self.resize_height = encoding_settings[5]
                self.framerate = encoding_settings[6]
                self.video_bitrate = encoding_settings[7]
                self.audio_bitrate = encoding_settings[8]
                self.encoding_speed = encoding_settings[9]
                self.encoding_color = encoding_settings[10]
                self.deinterlace = to_bool(encoding_settings[11])
                self.gop = encoding_settings[12]
                self.quality = encoding_settings[13]
                self.command_line = encoding_settings[14]
            except:
                pass

    def copy_from(self, preset):
        self.name = preset.name
        self.file_format = preset.file_format
        self.video_codec = preset.video_codec
        self.audio_codec = preset.audio_codec
        self.resize = preset.resize
        self.resize_width = preset.resize_width
        self.resize_height = preset.resize_height
        self.video_bitrate = preset.video_bitrate
        self.audio_bitrate = preset.audio_bitrate
        self.encoding_speed = preset.encoding_speed
        self.encoding_color = preset.encoding_color
        self.framerate = preset.framerate
        self.deinterlace = preset.deinterlace
        self.gop = preset.gop
        self.command_line = preset.command_line
        self.quality = preset.quality
        self.description = preset.description


class ExpandablePanel(GridLayout):
    animation = None
    expanded = BooleanProperty(False)
    target_size_hint_y = NumericProperty(0)

    def on_expanded(self, *_):
        if self.expanded:
            self.animate_expand()
        else:
            self.animate_close()

    def animate_close(self, instant=False, *_):
        app = App.get_running_app()
        self.unbind(minimum_height=self.set_content_height)
        self.disabled = True
        if app.animations and not instant:
            if self.animation:
                self.animation.cancel(self)
            if self.target_size_hint_y != 0:
                self.size_hint_y = self.target_size_hint_y
                self.animation = Animation(size_hint_y=0, opacity=0, duration=app.animation_length)
            else:
                self.animation = Animation(height=0, opacity=0, duration=app.animation_length)
            self.animation.start(self)
        else:
            self.opacity = 0
            self.height = 0

    def animate_expand(self, instant=False, *_):
        app = App.get_running_app()
        self.disabled = False
        if app.animations and not instant:
            if self.animation:
                self.animation.cancel(self)
            if self.target_size_hint_y != 0:
                self.size_hint_y = 0
                self.animation = Animation(size_hint_y=self.target_size_hint_y, opacity=1, duration=app.animation_length)
            else:
                self.animation = Animation(height=self.minimum_height, opacity=1, duration=app.animation_length)
            self.animation.start(self)
            self.animation.bind(on_complete=self.finish_expand)
        else:
            self.finish_expand()
            self.opacity = 1

    def finish_expand(self, *_):
        self.animation = None
        if self.target_size_hint_y != 0:
            self.size_hint_y = self.target_size_hint_y
        else:
            self.height = self.minimum_height
            self.bind(minimum_height=self.set_content_height)

    def set_content_height(self, *_):
        self.height = self.minimum_height


class SpecialSlider(Slider):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            #self.reset_value()
            Clock.schedule_once(self.reset_value, 0.15)  #need to delay this more than the scrollview scroll_timeout so it actually works
            return
        super(SpecialSlider, self).on_touch_down(touch)

    def reset_value(self, *_):
        pass


class HalfSlider(SpecialSlider):
    pass


class NormalSlider(SpecialSlider):
    pass


class InputMenu(Bubble):
    owner = ObjectProperty()
    edit = BooleanProperty(True)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.close_bubble()
        else:
            super(InputMenu, self).on_touch_down(touch)
            return True

    def select_all(self, *_):
        if self.owner:
            app = App.get_running_app()
            self.owner.select_all()
            app.close_bubble()

    def cut(self, *_):
        if self.owner:
            app = App.get_running_app()
            self.owner.cut()
            app.close_bubble()

    def copy(self, *_):
        if self.owner:
            app = App.get_running_app()
            self.owner.copy()
            app.close_bubble()

    def paste(self, *_):
        if self.owner:
            app = App.get_running_app()
            self.owner.paste()
            app.close_bubble()


class NormalInput(TextInput):
    messed_up_coords = BooleanProperty(False)
    long_press_time = NumericProperty(1)
    long_press_clock = None
    long_press_pos = None

    def on_touch_up(self, touch):
        if self.long_press_clock:
            self.long_press_clock.cancel()
            self.long_press_clock = None
        return super(NormalInput, self).on_touch_up(touch)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            pos = self.to_window(*touch.pos)
            self.long_press_clock = Clock.schedule_once(self.do_long_press, self.long_press_time)
            self.long_press_pos = pos
            if touch.button == 'right':
                app = App.get_running_app()
                app.popup_bubble(self, pos, edit=not self.disabled)
                return
        return super(NormalInput, self).on_touch_down(touch)

    def do_long_press(self, *_):
        app = App.get_running_app()
        app.popup_bubble(self, self.long_press_pos, edit=not self.disabled)


class HalfSliderLimited(SpecialSlider):
    start = NumericProperty(0.0)
    end = NumericProperty(1.0)


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


#Labels
class NormalLabel(Label):
    """Basic label widget"""
    pass


class ShortLabel(NormalLabel):
    """Label widget that will remain the minimum width"""
    pass


class LeftNormalLabel(NormalLabel):
    """Label widget that displays text left-justified"""
    pass


class PhotoThumbLabel(NormalLabel):
    pass


class InfoLabel(ShortLabel):
    bgcolor = ListProperty([1, 1, 0, 0])
    blinker = ObjectProperty()

    def on_text(self, instance, text):
        del instance
        app = App.get_running_app()
        if self.blinker:
            self.stop_blinking()
        if text:
            no_bg = [.5, .5, .5, 0]
            yes_bg = app.theme.info_background
            self.blinker = Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33) + Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33)
            self.blinker.start(self)

    def stop_blinking(self, *_):
        if self.blinker:
            self.blinker.cancel(self)
        self.bgcolor = [1, 1, 0, 0]


#Text Inputs
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


#RecycleView and Lists
class RecycleItem(RecycleDataViewBehavior, BoxLayout):
    bgcolor = ListProperty([0, 0, 0, 0])
    owner = ObjectProperty()
    text = StringProperty()
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    index = NumericProperty(0)
    data = {}

    def on_selected(self, *_):
        self.set_color()

    def set_color(self):
        app = App.get_running_app()

        if self.selected:
            self.bgcolor = app.theme.selected
        else:
            if self.index % 2 == 0:
                self.bgcolor = app.list_background_even
            else:
                self.bgcolor = app.list_background_odd

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
            app = App.get_running_app()
            self.parent.click_node(self)
            if app.shift_pressed:
                self.parent.select_range(self.index, touch)
            return True


class PhotoRecycleThumb(DragBehavior, BoxLayout, RecycleDataViewBehavior):
    """Wrapper widget for image thumbnails.  Used for displaying images in grid views."""

    underlay_color = ListProperty([0, 0, 0, 0])
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

    def on_selected(self, *_):
        app = App.get_running_app()
        if self.selected:
            new_color = app.theme.selected
        else:
            new_color = [0, 0, 0, 0]
        if app.animations:
            anim = Animation(underlay_color=new_color, duration=app.animation_length)
            anim.start(self)
        else:
            self.underlay_color = new_color

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
        super().on_touch_down(touch)
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
                thumbnail = self.ids['thumbnail']
                self.drag = True
                app = App.get_running_app()
                temp_coords = self.to_parent(touch.opos[0], touch.opos[1])
                widget_coords = (temp_coords[0] - thumbnail.pos[0], temp_coords[1] - thumbnail.pos[1])
                window_coords = self.to_window(touch.pos[0], touch.pos[1])
                try:
                    num_photos = self.owner.get_selected_photos(fullpath=True)
                    num_photos.append(self.fullpath)
                    num_photos = len(set(num_photos))
                except:
                    num_photos = 1
                app.drag(self, 'start', window_coords, image=self.image, offset=widget_coords, fullpath=self.fullpath, photos=num_photos)

    def on_touch_move(self, touch):
        #super().on_touch_move(touch)
        if self.drag:
            if not self.selected:
                self.parent.select_node(self.index)
                self.owner.update_selected()
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag(self, 'move', window_coords)

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        if self.drag:
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag(self, 'end', window_coords)
            self.drag = False


class PhotoRecycleThumbWide(PhotoRecycleThumb):
    pass


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
        app = App.get_running_app()
        if self.collide_point(*touch.pos):
            if touch.is_double_tap and not app.shift_pressed:
                if self.displayable:
                    if self.total_photos_numeric > 0:
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
                touch.grab(self, exclusive=True)  #Enuser that on_touch_up and on_touch_move are called even if this widget is dragged out of the treeview
                app.drag_treeview(self, 'start', window_coords, offset=widget_coords)

    def on_press(self):
        self.owner.type = self.type
        self.owner.displayable = self.displayable
        #self.owner.set_selected(self.target)
        self.owner.selected = ''
        self.owner.selected = self.target
        self.parent.click_node(self)

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


class TreenodeDrag(BoxLayout):
    """Widget that looks like a treenode thumbnail, used for showing the position of the drag-n-drop."""

    fullpath = StringProperty()
    text = StringProperty()
    subtext = StringProperty()


class SelectableRecycleBoxLayout(RecycleBoxLayout, LayoutSelectionBehavior):
    """Adds selection and focus behavior to the view."""
    owner = ObjectProperty()
    selected = DictProperty()
    selects = ListProperty()
    multiselect = BooleanProperty(False)

    def clear_selects(self):
        self.selects = []

    def refresh_selection(self):
        self.selects = []
        self.selected = {}
        for node in self.children:
            try:  #possible for nodes to not be synched with data
                data = self.parent.data[node.index]
                node.selected = data['selected']
                if node.selected:
                    self.selected = data
                    self.selects.append(data)
            except:
                pass

    def deselect_all(self):
        for data in self.parent.data:
            data['selected'] = False
        self.refresh_selection()
        self.selects = []
        self.selected = {}

    def select_all(self):
        self.selects = []
        for data in self.parent.data:
            if data['selectable']:
                data['selected'] = True
                self.selects.append(data)
                self.selected = data
        self.refresh_selection()

    def select_node(self, node):
        super().select_node(node)
        if not self.multiselect:
            self.deselect_all()
        node.selected = True
        self.selects.append(node.data)
        self.parent.data[self.parent.data.index(node.data)]['selected'] = True
        node.data['selected'] = True
        self.selected = node.data

    def deselect_node(self, node):
        super().deselect_node(node)
        if node.data in self.selects:
            self.selects.remove(node.data)
        if self.selected == node.data:
            if self.selects:
                self.selected = self.selects[-1]
            else:
                self.selected = {}
        if node.data in self.parent.data:
            parent_index = self.parent.data.index(node.data)
            parent_data = self.parent.data[parent_index]
            parent_data['selected'] = False
        node.selected = False
        node.data['selected'] = False

    def click_node(self, node):
        #Called by a child widget when it is clicked on
        if node.selected:
            if self.multiselect:
                self.deselect_node(node)
            else:
                pass
                #self.deselect_all()
        else:
            if not self.multiselect:
                self.deselect_all()
            self.select_node(node)
            self.selected = node.data

    def select_range(self, *_):
        if self.multiselect and self.selected and self.selected['selectable']:
            select_index = self.parent.data.index(self.selected)
            selected_nodes = []
            if self.selects:
                for select in self.selects:
                    if select['selectable']:
                        index = self.parent.data.index(select)
                        if index != select_index:
                            selected_nodes.append(index)
            else:
                selected_nodes = [0, len(self.parent.data)]
            closest_node = min(selected_nodes, key=lambda x: abs(x-select_index))

            for index in range(min(select_index, closest_node), max(select_index, closest_node)):
                selected = self.parent.data[index]
                selected['selected'] = True
                if selected not in self.selects:
                    self.selects.append(selected)

            self.parent.refresh_from_data()

    def toggle_select(self, *_):
        if self.multiselect:
            if self.selects:
                self.deselect_all()
            else:
                self.select_all()
        else:
            if self.selected:
                self.selected = {}


class SelectableRecycleLayout(LayoutSelectionBehavior):
    """Custom selectable grid layout widget."""
    multiselect = BooleanProperty(True)

    def __init__(self, **kwargs):
        """ Use the initialize method to bind to the keyboard to enable
        keyboard interaction e.g. using shift and control for multi-select.
        """

        super(SelectableRecycleLayout, self).__init__(**kwargs)
        if str(platform) in ('linux', 'win', 'macosx'):
            keyboard = Window.request_keyboard(None, self)
            keyboard.bind(on_key_down=self.select_with_key_down, on_key_up=self.select_with_key_up)

    def toggle_select(self):
        if self.selected_nodes:
            selected = True
        else:
            selected = False
        self.clear_selection()
        if not selected:
            self.select_all()

    def select_all(self):
        for node in range(0, len(self.parent.data)):
            self.select_node(node)

    def select_with_touch(self, node, touch=None):
        if not self.multiselect:
            self.clear_selection()
        self._shift_down = False
        super(SelectableRecycleLayout, self).select_with_touch(node, touch)

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


class SelectableRecycleGrid(SelectableRecycleLayout, RecycleGridLayout):
    scale = NumericProperty(1)


class NormalRecycleView(RecycleView):
    pass


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


#Buttons
class ButtonBase(Button):
    """Basic button widget."""

    warn = BooleanProperty(False)
    target_background = ListProperty()
    target_text = ListProperty()
    background_animation = ObjectProperty()
    text_animation = ObjectProperty()
    last_disabled = False
    menu = BooleanProperty(False)
    toggle = BooleanProperty(False)

    button_update = BooleanProperty()

    def __init__(self, **kwargs):
        self.background_animation = Animation()
        self.text_animation = Animation()
        app = App.get_running_app()
        self.background_color = app.theme.button_up
        self.target_background = self.background_color
        self.color = app.theme.button_text
        self.target_text = self.color
        super(ButtonBase, self).__init__(**kwargs)

    def on_button_update(self, *_):
        Clock.schedule_once(self.set_color_instant)

    def set_color_instant(self, *_):
        self.set_color(instant=True)

    def set_color(self, instant=False):
        app = App.get_running_app()
        if self.disabled:
            self.set_text(app.theme.button_disabled_text, instant=instant)
            self.set_background(app.theme.button_disabled, instant=instant)
        else:
            self.set_text(app.theme.button_text, instant=instant)
            if self.menu:
                if self.state == 'down':
                    self.set_background(app.theme.button_menu_down, instant=True)
                else:
                    self.set_background(app.theme.button_menu_up, instant=instant)
            elif self.toggle:
                if self.state == 'down':
                    self.set_background(app.theme.button_toggle_true, instant=instant)
                else:
                    self.set_background(app.theme.button_toggle_false, instant=instant)

            elif self.warn:
                if self.state == 'down':
                    self.set_background(app.theme.button_warn_down, instant=True)
                else:
                    self.set_background(app.theme.button_warn_up, instant=instant)
            else:
                if self.state == 'down':
                    self.set_background(app.theme.button_down, instant=True)
                else:
                    self.set_background(app.theme.button_up, instant=instant)

    def on_disabled(self, *_):
        self.set_color()

    def on_menu(self, *_):
        self.set_color(instant=True)

    def on_toggle(self, *_):
        self.set_color(instant=True)

    def on_warn(self, *_):
        self.set_color(instant=True)

    def on_state(self, *_):
        self.set_color()

    def set_background(self, color, instant=False):
        if self.target_background == color:
            return
        app = App.get_running_app()
        self.background_animation.stop(self)
        if app.animations and not instant:
            self.background_animation = Animation(background_color=color, duration=app.animation_length)
            self.background_animation.start(self)
        else:
            self.background_color = color
        self.target_background = color

    def set_text(self, color, instant=False):
        if self.target_text == color:
            return
        app = App.get_running_app()
        self.text_animation.stop(self)
        if app.animations and not instant:
            self.text_animation = Animation(color=color, duration=app.animation_length)
            self.text_animation.start(self)
        else:
            self.color = color
        self.target_text = color


class ToggleBase(ToggleButton, ButtonBase):
    pass


class VerticalButton(ToggleBase):
    vertical_text = StringProperty('')


class NormalButton(ButtonBase):
    """Basic button widget."""
    pass


class WideButton(ButtonBase):
    """Full width button widget"""
    pass


class MenuButton(ButtonBase):
    """Basic class for a drop-down menu button item."""

    remember = None


class InfoButton(NormalButton):
    history_popup = ObjectProperty(allownone=True)

    def on_release(self, *_):
        self.history_popup = None
        window_pos = self.to_window(*self.pos)
        self.history_popup = InfotextPopup(ypos=window_pos[1])
        self.history_popup.open(self)


class RemoveButton(ButtonBase):
    """Base class for a button to remove an item from a list."""

    remove = True
    to_remove = StringProperty()
    remove_from = StringProperty()
    owner = ObjectProperty()


class ExpandableButton(GridLayout):
    """Base class for a button with a checkbox to enable/disable an extra area.
    It also features an 'x' remove button that calls 'on_remove' when clicked."""

    text = StringProperty()  #Text shown in the main button area
    expanded = BooleanProperty(False)  #Determines if the expanded area is displayed
    content = ObjectProperty()  #Widget to be displayed when expanded is enabled
    index = NumericProperty()  #The button's index in the list - useful for the remove function
    animation = None

    def __init__(self, **kwargs):
        super(ExpandableButton, self).__init__(**kwargs)
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        self.register_event_type('on_expanded')
        self.register_event_type('on_remove')

    def set_expanded(self, expanded):
        self.expanded = expanded

    def on_expanded(self, *_):
        if self.content:
            if self.expanded:
                Clock.schedule_once(lambda x: self.animate_expand())
            else:
                self.animate_close()

    def animate_close(self, instant=False, *_):
        app = App.get_running_app()
        content_container = self.ids['contentContainer']
        content_container.unbind(minimum_height=self.set_content_height)
        if app.animations and not instant:
            anim = Animation(height=app.padding * 2, opacity=0, duration=app.animation_length)
            anim.start(content_container)
        else:
            content_container.opacity = 0
            content_container.height = app.padding * 2
        content_container.clear_widgets()

    def animate_expand(self, instant=False, *_):
        content_container = self.ids['contentContainer']
        app = App.get_running_app()
        content_container.add_widget(self.content)
        if app.animations and not instant:
            if self.animation:
                self.animation.cancel(content_container)
            self.animation = Animation(height=(self.content.height + (app.padding * 2)), opacity=1, duration=app.animation_length)
            self.animation.start(content_container)
            self.animation.bind(on_complete=self.finish_expand)
        else:
            self.finish_expand()
            content_container.opacity = 1

    def finish_expand(self, *_):
        self.animation = None
        content_container = self.ids['contentContainer']
        content_container.bind(minimum_height=self.set_content_height)

    def set_content_height(self, *_):
        content_container = self.ids['contentContainer']
        content_container.height = content_container.minimum_height

    def on_press(self):
        pass

    def on_release(self):
        pass

    def on_remove(self):
        pass


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
        super().on_touch_down(touch)
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
        super().on_touch_up(touch)
        if self.drag:
            app = App.get_running_app()
            window_coords = self.to_window(touch.pos[0], touch.pos[1])
            app.drag_treeview(self, 'end', window_coords)
            self.drag = False
        if self.collide_point(*touch.pos):
            self.on_release()


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


#Popups
class NormalPopup(Popup):
    """Basic popup widget."""

    def open(self, *args, **kwargs):
        app = App.get_running_app()
        if app.animations:
            self.opacity = 0
            height = self.height
            self.height = 4 * self.height
            anim = Animation(opacity=1, height=height, duration=app.animation_length)
            anim.start(self)
        else:
            self.opacity = 1
        super(NormalPopup, self).open(*args, **kwargs)

    def dismiss(self, *args, **kwargs):
        app = App.get_running_app()
        if app.animations:
            anim = Animation(opacity=0, height=0, duration=app.animation_length)
            anim.start(self)
            anim.bind(on_complete=self.finish_dismiss)
        else:
            super(NormalPopup, self).dismiss()

    def finish_dismiss(self, *_):
        super(NormalPopup, self).dismiss()


class InfotextPopup(NormalPopup):
    ypos = NumericProperty(0)

    def open(self, *args, **kwargs):
        app = App.get_running_app()
        if not app.infotext_history:
            return
        top_pos = self.ypos / Window.height
        self.height = (.5 + len(app.infotext_history)) * app.button_scale
        self.pos_hint = {'right': 1, 'top': top_pos}
        content = BoxLayout(orientation='vertical')
        for data in app.infotext_history:
            date, text = data
            content.add_widget(LeftNormalLabel(text='['+date+'] '+text))
        self.add_widget(content)
        super().open(*args, **kwargs)


class MessagePopup(GridLayout):
    """Basic popup message with a message and 'ok' button."""

    button_text = StringProperty('OK')
    text = StringProperty()

    def close(self, *_):
        app = App.get_running_app()
        app.popup.dismiss()


class InputPopup(GridLayout):
    """Basic text input popup message.  Calls 'on_answer' when either button is clicked."""

    yes_text = StringProperty('OK')
    warn_yes = BooleanProperty(False)
    no_text = StringProperty('Cancel')
    warn_no = BooleanProperty(False)
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

    yes_text = StringProperty('OK')
    warn_yes = BooleanProperty(False)
    no_text = StringProperty('Cancel')
    warn_no = BooleanProperty(False)
    input_text = StringProperty()
    text = StringProperty()  #Text that the user has input
    hint = StringProperty()  #Grayed-out hint text in the input field

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(InputPopupTag, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass


class MoveConfirmPopup(NormalPopup):
    """Popup that asks to confirm a file or folder move."""
    target = StringProperty()
    photos = ListProperty()
    origin = StringProperty()


class ScanningPopup(NormalPopup):
    """Popup for displaying database scanning progress."""

    button_text = StringProperty('Cancel')
    scanning_percentage = NumericProperty(0)
    scanning_text = StringProperty('Building File List...')


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


#Menus
class NormalDropDown(DropDown):
    """Base dropdown menu class."""

    show_percent = NumericProperty(1)
    invert = BooleanProperty(False)
    basic_animation = BooleanProperty(False)

    def open(self, *args, **kwargs):
        super(NormalDropDown, self).open(*args, **kwargs)
        self.opacity = 0
        Clock.schedule_once(self.open_animation)

    def open_animation(self, *_):
        app = App.get_running_app()
        if app.animations:
            if self.basic_animation:
                #Dont do fancy child opacity animation
                self.opacity = 0
                self.show_percent = 1
                anim = Animation(opacity=1, duration=app.animation_length)
                anim.start(self)
            else:
                #determine if we opened up or down
                attach_to_window = self.attach_to.to_window(*self.attach_to.pos)
                if attach_to_window[1] > self.pos[1]:
                    self.invert = True
                    children = reversed(self.container.children)
                else:
                    self.invert = False
                    children = self.container.children

                #Animate background
                self.opacity = 1
                self.show_percent = 0
                anim = Animation(show_percent=1, duration=app.animation_length)
                anim.start(self)

                if len(self.container.children) > 0:
                    item_delay = app.animation_length / len(self.container.children)
                else:
                    item_delay = 0

                for i, w in enumerate(children):
                    anim = (Animation(duration=i * item_delay) + Animation(opacity=1, duration=app.animation_length))
                    w.opacity = 0
                    anim.start(w)
        else:
            self.opacity = 1

    def dismiss(self, *args, **kwargs):
        app = App.get_running_app()
        if app.animations:
            anim = Animation(opacity=0, duration=app.animation_length)
            anim.start(self)
            anim.bind(on_complete=self.finish_dismiss)
        else:
            self.finish_dismiss()

    def finish_dismiss(self, *_):
        super(NormalDropDown, self).dismiss()


class AlbumSortDropDown(NormalDropDown):
    """Drop-down menu for sorting album elements"""
    pass


class AlbumExportDropDown(NormalDropDown):
    """Drop-down menu for album operations"""
    pass


#Splitter Panels
class SplitterResizer(Button):
    pass


class SplitterPanel(Splitter):
    """Base class for the left and right adjustable panels"""
    hidden = BooleanProperty(False)
    display_width = NumericProperty(0)
    animating = None
    strip_cls = SplitterResizer

    def done_animating(self, *_):
        self.animating = None
        if self.width == 0:
            self.opacity = 0
        else:
            self.opacity = 1

    def on_hidden(self, *_):
        app = App.get_running_app()
        if self.animating:
            self.animating.cancel(self)
        if self.hidden:
            if app.animations:
                self.animating = anim = Animation(width=0, opacity=0, duration=app.animation_length)
                anim.bind(on_complete=self.done_animating)
                anim.start(self)
            else:
                self.opacity = 0
                self.width = 0
        else:
            if app.animations:
                self.animating = anim = Animation(width=self.display_width, opacity=1, duration=app.animation_length)
                anim.bind(on_complete=self.done_animating)
                anim.start(self)
            else:
                self.opacity = 1
                self.width = self.display_width


class SplitterPanelLeft(SplitterPanel):
    """Left-side adjustable width panel."""

    def __init__(self, **kwargs):
        app = App.get_running_app()
        self.display_width = app.left_panel_width()
        super(SplitterPanelLeft, self).__init__(**kwargs)

    def on_hidden(self, *_):
        app = App.get_running_app()
        self.display_width = app.left_panel_width()
        super(SplitterPanelLeft, self).on_hidden()

    def on_width(self, instance, width):
        """When the width of the panel is changed, save to the app settings."""

        del instance
        if self.animating:
            return
        if width > 0 and not self.hidden:
            app = App.get_running_app()
            widthpercent = (width/Window.width)
            app.config.set('Settings', 'leftpanel', widthpercent)
        if self.hidden:
            self.width = 0


class SplitterPanelRight(SplitterPanel):
    """Right-side adjustable width panel."""

    def __init__(self, **kwargs):
        app = App.get_running_app()
        self.display_width = app.right_panel_width()
        super(SplitterPanelRight, self).__init__(**kwargs)

    def on_hidden(self, *_):
        app = App.get_running_app()
        self.display_width = app.right_panel_width()
        super(SplitterPanelRight, self).on_hidden()

    def on_width(self, instance, width):
        """When the width of the panel is changed, save to the app settings."""

        del instance
        if self.animating:
            return
        if width > 0 and not self.hidden:
            app = App.get_running_app()
            widthpercent = (width/Window.width)
            app.config.set('Settings', 'rightpanel', widthpercent)
        if self.hidden:
            self.width = 0


#Images
class CustomImage(KivyImage):
    """Custom image display widget.
    Enables editing operations, displaying them in real-time using a low resolution preview of the original image file.
    All editing variables are watched by the widget and it will automatically update the preview when they are changed.
    """

    norm_image_pos = ListProperty([100, 100])
    o_a = NumericProperty(0)
    o_b = NumericProperty(0)
    o_c = NumericProperty(0)
    o_d = NumericProperty(0)
    i_a = NumericProperty(0)
    i_b = NumericProperty(0)
    i_c = NumericProperty(0)
    i_d = NumericProperty(0)
    crop_verts = ListProperty()
    crop_indices = ListProperty()

    exif = ''
    pixel_format = ''
    length = NumericProperty(0)
    framerate = ListProperty()
    video = BooleanProperty(False)
    player = ObjectProperty(None, allownone=True)
    position = NumericProperty(0.0)
    start_point = NumericProperty(0.0)
    end_point = NumericProperty(1.0)
    original_image = ObjectProperty(allownone=True)
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
    curve_points = ListProperty()
    crop_top = NumericProperty(0)
    crop_bottom = NumericProperty(0)
    crop_left = NumericProperty(0)
    crop_right = NumericProperty(0)
    filter = StringProperty('')
    filter_amount = NumericProperty(0)
    autocontrast = BooleanProperty(False)
    equalize = NumericProperty(0)
    histogram = ListProperty()
    edit_image = ObjectProperty(allownone=True)
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
    cropper = ObjectProperty(allownone=True)  #Holder for the cropper overlay
    crop_controls = ObjectProperty(allownone=True)  #Holder for the cropper edit panel object
    crop_text = StringProperty('')
    adaptive_clip = NumericProperty(0)
    border_opacity = NumericProperty(1)
    border_image = ListProperty()
    border_tint = ListProperty([1.0, 1.0, 1.0, 1.0])
    border_x_scale = NumericProperty(.5)
    border_y_scale = NumericProperty(.5)
    crop_min = NumericProperty(100)
    size_multiple = NumericProperty(1)
    aspect = NumericProperty(1)
    lock_aspect = BooleanProperty(False)

    #Denoising variables
    denoise = BooleanProperty(False)
    luminance_denoise = NumericProperty(10)
    color_denoise = NumericProperty(10)
    search_window = NumericProperty(15)
    block_size = NumericProperty(5)

    frame_number = 0
    max_frames = 0
    start_seconds = 0
    first_frame = None

    def update_norm_image_pos(self, *_):
        self.norm_image_pos = [self.pos[0] + ((self.width - self.norm_image_size[0]) / 2), self.pos[1] + ((self.height - self.norm_image_size[1]) / 2)]

    def on_norm_image_size(self, *_):
        self.update_norm_image_pos()
        self.update_crop_rectangle()

    def update_crop_rectangle(self, *_):
        self.o_a = self.norm_image_pos[0]
        self.o_b = self.norm_image_pos[1]
        self.o_c = self.norm_image_pos[0] + self.norm_image_size[0]
        self.o_d = self.norm_image_pos[1] + self.norm_image_size[1]

        self.i_a = self.o_a + (self.norm_image_size[0] * self.crop_left)
        self.i_b = self.o_b + (self.norm_image_size[1] * self.crop_bottom)
        self.i_c = self.o_c - (self.norm_image_size[0] * self.crop_right)
        self.i_d = self.o_d - (self.norm_image_size[1] * self.crop_top)

        v_1 = [self.o_a, self.o_b, 0, 0]
        v_2 = [self.o_c, self.o_b, 0, 0]
        v_3 = [self.o_a, self.o_d, 0, 0]
        v_4 = [self.o_c, self.o_d, 0, 0]
        v_5 = [self.i_a, self.i_b, 0, 0]
        v_6 = [self.i_c, self.i_b, 0, 0]
        v_7 = [self.i_a, self.i_d, 0, 0]
        v_8 = [self.i_c, self.i_d, 0, 0]

        t_1 = [0, 1, 5]
        t_2 = [0, 5, 4]
        t_3 = [0, 4, 2]
        t_4 = [4, 6, 2]
        t_5 = [2, 6, 3]
        t_6 = [6, 7, 3]
        t_7 = [7, 3, 1]
        t_8 = [7, 5, 1]

        self.crop_verts = v_1 + v_2 + v_3 + v_4 + v_5 + v_6 + v_7 + v_8
        self.crop_indices = t_1 + t_2 + t_3 + t_4 + t_5 + t_6 + t_7 + t_8

    def start_video_convert(self):
        self.close_video()
        self.player = MediaPlayer(self.source, ff_opts={'paused': True, 'ss': 0.0, 'an': True})
        #self.player.set_volume(0)  #crashes sometimes... hopefully not necessary
        self.frame_number = 0
        if self.start_point > 0 or self.end_point < 1:
            all_frames = self.length * (self.framerate[0] / self.framerate[1])
            self.max_frames = all_frames * (self.end_point - self.start_point)
        else:
            self.max_frames = 0

        #need to wait for load so the seek routine doesnt crash python
        self.first_frame = self.wait_frame()

        if self.start_point > 0:
            self.start_seconds = self.length * self.start_point
            self.first_frame = self.seek_player(self.start_seconds, precise=True)

    def wait_frame(self):
        #Ensures that a frame is gotten
        frame = None
        while not frame:
            frame, value = self.player.get_frame(force_refresh=True)
        return frame

    def start_seek(self, seek):
        #tell the player to seek to a position
        self.player.set_pause(False)
        self.player.seek(pts=seek, relative=False, accurate=True)
        self.player.set_pause(True)

    def seek_player(self, seek, precise=False):
        if precise:
            max_loops = 60
            seek_distance = 1
        else:
            max_loops = 30
            seek_distance = 2
        self.start_seek(seek)

        framerate = self.framerate[0] / self.framerate[1]
        target_seek_frame = seek * framerate

        loops = 0
        total_loops = 0
        while True:
            loops += 1
            total_loops += 1
            if loops > 5:
                #seek has been stuck for a while, try to seek again
                self.start_seek(seek)
                loops = 0
            #check if seek has gotten within a couple frames yet
            frame = self.wait_frame()
            current_seek = frame[1]
            current_seek_frame = current_seek * framerate
            frame_distance = abs(target_seek_frame - current_seek_frame)
            if frame_distance < seek_distance or total_loops >= max_loops:
                #seek has finished, or give up after a lot of tries to not freeze the program...
                break
            time.sleep(0.05)
        return frame

    def get_converted_frame(self):
        self.first_frame = None
        self.player.set_pause(False)
        frame = None
        while not frame:
            try:
                frame, value = self.player.get_frame()
            except Exception as e:
                #getting the frame failed for some reason
                return [None, e]
            if value == 'eof':
                return None
        self.player.set_pause(True)
        self.frame_number = self.frame_number + 1
        if self.max_frames:
            if self.frame_number > self.max_frames:
                return None
        try:
            frame_image, frame_data = frame
            frame = None
            frame_size = frame_image.get_size()
            current_pixel_format = frame_image.get_pixel_format()
            if current_pixel_format != 'rgb24':
                frame_converter = SWScale(frame_size[0], frame_size[1], current_pixel_format, ofmt='rgb24')
                frame_image = frame_converter.scale(frame_image)
            frame_converter = None
            image_data = bytes(frame_image.to_bytearray()[0])  #can cause out of memory errors...
            frame_image = None
            image = Image.frombuffer(mode='RGB', size=(frame_size[0], frame_size[1]), data=image_data, decoder_name='raw')
            image_data = None
            #for some reason, video frames are read upside-down? fix it here...
            image = image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            #basic frame manipulation failed, probably a memory error...
            return [None, e]
        if image.mode != 'RGB':
            image = image.convert('RGB')
        try:
            image = self.adjust_image(image, preview=False)
        except Exception as e:
            #image creation may not succeed for various reasons.
            return [None, e]
        return [image, frame_data]

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

    def set_aspect(self, aspect_x=None, aspect_y=None, force=None):
        """Adjusts the cropping of the image to be a given aspect ratio.
        Attempts to keep the image as large as possible
        Arguments:
            aspect_x: Horizontal aspect ratio element, numerical value.
            aspect_y: Vertical aspect ratio element, numerical value.
            force: Forces the recrop function to horizontal or vertical.  Must be None, 'h' or 'v'
        """

        width = 1 - self.crop_left - self.crop_right
        height = 1 - self.crop_top - self.crop_bottom
        if height == 0:
            return
        if aspect_x is not None and aspect_y is not None:
            self.aspect = aspect_x / aspect_y
        current_ratio = width / height
        image_ratio = self.original_width / self.original_height
        target_ratio = self.aspect / image_ratio
        if (force is None and target_ratio > current_ratio) or force == 'v':
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
        self.crop_top = self.crop_top + crop_top
        self.crop_right = self.crop_right + crop_right
        self.crop_bottom = self.crop_bottom + crop_bottom
        self.crop_left = self.crop_left + crop_left
        self.update_cropper()

    def on_crop_top(self, *_):
        if (self.crop_top + self.crop_bottom) > 0.9:
            self.crop_top = 0.9 - self.crop_bottom
            self.update_crop_controls()
        else:
            self.update_cropper()

    def on_crop_right(self, *_):
        if (self.crop_left + self.crop_right) > 0.9:
            self.crop_right = 0.9 - self.crop_left
            self.update_crop_controls()
        else:
            self.update_cropper()

    def on_crop_bottom(self, *_):
        if (self.crop_top + self.crop_bottom) > 0.9:
            self.crop_bottom = 0.9 - self.crop_top
            self.update_crop_controls()
        else:
            self.update_cropper()

    def on_crop_left(self, *_):
        if (self.crop_left + self.crop_right) > 0.9:
            self.crop_left = 0.9 - self.crop_right
            self.update_crop_controls()
        else:
            self.update_cropper()

    def set_crop_text(self):
        #Sets some text that describes the current crop settings

        crop_left = self.original_width * self.crop_left
        crop_right = self.original_width * self.crop_right
        crop_top = self.original_height * self.crop_top
        crop_bottom = self.original_height * self.crop_bottom
        new_width = self.original_width - crop_left - crop_right
        new_height = self.original_height - crop_top - crop_bottom
        if new_height != 0:
            new_aspect = new_width / new_height
        else:
            new_aspect = 0
        old_aspect = self.original_width / self.original_height
        self.crop_text = "Size: "+str(int(new_width))+"x"+str(int(new_height))+", Aspect: "+str(round(new_aspect, 2))+" (Original: "+str(round(old_aspect, 2))+")"

    def reset_crop(self):
        """Sets the crop values back to 0 for all sides"""

        self.crop_top = 0
        self.crop_bottom = 0
        self.crop_left = 0
        self.crop_right = 0
        self.update_cropper(setup=True)

    def on_cropper(self, *_):
        self.update_cropper(setup=True)

    def update_cropper(self, setup=False):
        """Updates the position and size of the cropper overlay object."""

        if self.cropper:
            texture_size = self.get_texture_size()
            texture_top_edge = texture_size[0]
            texture_right_edge = texture_size[1]
            texture_bottom_edge = texture_size[2]
            texture_left_edge = texture_size[3]

            texture_width = (texture_right_edge - texture_left_edge)
            texture_height = (texture_top_edge - texture_bottom_edge)

            top_edge = texture_top_edge - (self.crop_top * texture_height)
            bottom_edge = texture_bottom_edge + (self.crop_bottom * texture_height)
            left_edge = texture_left_edge + (self.crop_left * texture_width)
            right_edge = texture_right_edge - (self.crop_right * texture_width)
            width = right_edge - left_edge
            height = top_edge - bottom_edge

            self.cropper.pos = [left_edge, bottom_edge]
            self.cropper.size = [width, height]
            if setup:
                self.cropper.max_resizable_width = width
                self.cropper.max_resizable_height = height
        self.set_crop_text()
        self.update_crop_rectangle()

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
        texture_height = (texture_top_edge - texture_bottom_edge)
        if left_crop < 0:
            self.crop_left = 0
        else:
            self.crop_left = left_crop / texture_width
        if right_crop < 0:
            self.crop_right = 0
        else:
            self.crop_right = right_crop / texture_width
        if top_crop < 0:
            self.crop_top = 0
        else:
            self.crop_top = top_crop / texture_height
        if bottom_crop < 0:
            self.crop_bottom = 0
        else:
            self.crop_bottom = bottom_crop / texture_height
        #self.update_preview(recrop=False)
        self.update_crop_controls()

    def update_crop_controls(self):
        if self.crop_controls:
            self.crop_controls.update_crop_sliders()

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
        self.update_cropper(setup=True)
        self.update_norm_image_pos()

    def on_source(self, *_):
        """The source file has been changed, reload image and regenerate preview."""

        app = App.get_running_app()
        self.video = os.path.splitext(self.source)[1].lower() in app.movietypes
        if self.video:
            self.open_video()
        self.reload_edit_image()
        self.update_texture(self.edit_image)
        self.update_aspect()
        #self.update_preview()

    def on_position(self, *_):
        self.reload_video_edit_image()

    def reload_video_edit_image(self):
        location = self.length * self.position
        frame = self.seek_player(location)
        Clock.schedule_once(self.reload_edit_image)

    def get_original_image(self, reload=False):
        if reload or self.original_image is None:
            if self.video:
                if not self.player:
                    return
                location = self.length * self.position
                frame = self.seek_player(location)
                frame = frame[0]
                frame_size = frame.get_size()
                pixel_format = frame.get_pixel_format()
                if pixel_format != 'rgb24':
                    frame_converter = SWScale(frame_size[0], frame_size[1], pixel_format, ofmt='rgb24')
                    frame = frame_converter.scale(frame)
                image_data = bytes(frame.to_bytearray()[0])
                original_image = Image.frombuffer(mode='RGB', size=(frame_size[0], frame_size[1]), data=image_data, decoder_name='raw')
                #for some reason, video frames are read upside-down? fix it here...
                original_image = original_image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
            else:
                original_image = Image.open(self.source)
                try:
                    self.exif = original_image.info.get('exif', b'')
                except:
                    self.exif = ''
                if self.angle != 0:
                    if self.angle == 90:
                        original_image = original_image.transpose(PIL.Image.ROTATE_90)
                    if self.angle == 180:
                        original_image = original_image.transpose(PIL.Image.ROTATE_180)
                    if self.angle == 270:
                        original_image = original_image.transpose(PIL.Image.ROTATE_270)
            self.original_width = original_image.size[0]
            self.original_height = original_image.size[1]
            self.original_image = original_image
        else:
            original_image = self.original_image
        return original_image

    def reload_edit_image(self, *_):
        """Regenerate the edit preview image."""

        original_image = self.get_original_image(reload=True)
        image = original_image.copy()
        image_width = Window.width * .75
        width = int(image_width)
        height = int(image_width*(image.size[1]/image.size[0]))
        if width < 10:
            width = 10
        if height < 10:
            height = 10
        image = image.resize((width, height))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        self.size_multiple = self.original_width / image.size[0]
        self.edit_image = image
        Clock.schedule_once(self.update_preview)
        #Clock.schedule_once(self.update_histogram)  #Need to delay this because kivy will mess up the drawing of it on first load.
        #self.histogram = image.histogram()

    def update_histogram(self, *_):
        self.histogram = self.edit_image.histogram()

    def update_aspect(self):
        self.aspect = self.edit_image.width / self.edit_image.height

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
        original_image = self.get_original_image()
        if not original_image:
            return None
        preview = original_image.crop(box=(left, upper, right, lower))
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

    def update_preview(self, *_, denoise=False, recrop=True):
        """Update the preview image."""

        if self.edit_image:
            image = self.adjust_image(self.edit_image)
            if denoise and opencv:
                open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
                open_cv_image = cv2.fastNlMeansDenoisingColored(open_cv_image, None, self.luminance_denoise, self.color_denoise, self.search_window, self.block_size)
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(open_cv_image)

            self.update_texture(image)
            self.histogram = image.histogram()
            if recrop:
                self.update_cropper(setup=True)

    def adjust_image(self, image, preview=True):
        """Applies all current editing opterations to an image.
        Arguments:
            image: A PIL image.
            preview: Generate edit image in preview mode (faster)
        Returns: A PIL image.
        """

        if not preview and self.photoinfo:
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
            offset = 255 - min(kelvin)
            kelvin_r = (kelvin[0] + offset) / 255.0
            kelvin_g = (kelvin[1] + offset) / 255.0
            kelvin_b = (kelvin[2] + offset) / 255.0
            matrix = (kelvin_r, 0.0, 0.0, 0.0,
                      0.0, kelvin_g, 0.0, 0.0,
                      0.0, 0.0, kelvin_b, 0.0)
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
            open_cv_image = None

        if self.adaptive_clip > 0 and opencv:
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2Lab)
            channels = cv2.split(open_cv_image)
            clahe = cv2.createCLAHE(clipLimit=(self.adaptive_clip * 4), tileGridSize=(8, 8))
            clahe_image = clahe.apply(channels[0])
            clahe = None
            channels[0] = clahe_image
            clahe_image = None
            open_cv_image = cv2.merge(channels)
            channels = None
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_Lab2RGB)
            image = Image.fromarray(open_cv_image)
            open_cv_image = None

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
            open_cv_image = None
        if self.bilateral != 0 and self.bilateral_amount != 0 and opencv:
            diameter = int(self.bilateral * 10 * size_multiple)
            if diameter < 1:
                diameter = 1
            sigma_color = self.bilateral_amount * 100 * size_multiple
            if sigma_color < 1:
                sigma_color = 1
            sigma_space = sigma_color
            open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            open_cv_image = cv2.bilateralFilter(open_cv_image, diameter, sigma_color, sigma_space)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(open_cv_image)
            open_cv_image = None
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
            border_image = border_image.crop((border_crop_x, border_crop_y, border_image.size[0] - border_crop_x, border_image.size[1] - border_crop_y))
            border_image = border_image.resize(image.size, resample)

            if os.path.splitext(image_file)[1].lower() == '.jpg':
                alpha_file = os.path.splitext(image_file)[0]+'-mask.jpg'
                if not os.path.exists(alpha_file):
                    alpha_file = image_file
                alpha = Image.open(alpha_file)
                alpha = alpha.convert('L')
                alpha = alpha.crop((border_crop_x, border_crop_y, alpha.size[0] - border_crop_x, alpha.size[1] - border_crop_y))
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

        if self.crop_top != 0 or self.crop_bottom != 0 or self.crop_left != 0 or self.crop_right != 0:
            if preview:
                pass
                """
                #Draw a darkened overlay on cropped out edges
                overlay = Image.new(mode='RGB', size=image.size, color=(0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                draw.rectangle([0, 0, (self.crop_left * image.size[0]), image.size[1]], fill=(255, 255, 255))
                draw.rectangle([0, 0, image.size[0], (self.crop_top * image.size[1])], fill=(255, 255, 255))
                draw.rectangle([(image.size[0] - (self.crop_right * image.size[0])), 0, (image.size[0]), image.size[1]], fill=(255, 255, 255))
                draw.rectangle([0, (image.size[1] - (self.crop_bottom * image.size[1])), image.size[0], image.size[1]], fill=(255, 255, 255))
                bright = ImageEnhance.Brightness(overlay)
                overlay = bright.enhance(.333)
                image = ImageChops.subtract(image, overlay)
                """
            else:
                #actually crop the image
                crop_left = int(self.crop_left * image.size[0])
                crop_right = int(image.size[0] - (self.crop_right * image.size[0]))
                crop_top = int(self.crop_top * image.size[1])
                crop_bottom = int(image.size[1] - (self.crop_bottom * image.size[1]))
                if self.video:
                    #ensure that image size is divisible by 2
                    new_width = crop_right - crop_left
                    new_height = crop_bottom - crop_top
                    if new_width % 2 == 1:
                        if crop_right < image.size[0]:
                            crop_right = crop_right + 1
                        else:
                            crop_right = crop_right - 1
                    if new_height % 2 == 1:
                        if crop_bottom < image.size[1]:
                            crop_bottom = crop_bottom + 1
                        else:
                            crop_bottom = crop_bottom - 1
                image = image.crop((crop_left, crop_top, crop_right, crop_bottom))

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

        original_image = self.get_original_image()
        image = original_image.copy()
        #if not self.video:
        #    if self.angle != 0:
        #        if self.angle == 90:
        #            image = image.transpose(PIL.Image.ROTATE_90)
        #        if self.angle == 180:
        #            image = image.transpose(PIL.Image.ROTATE_180)
        #        if self.angle == 270:
        #            image = image.transpose(PIL.Image.ROTATE_270)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image = self.adjust_image(image, preview=False)
        return image

    def close_image(self):
        try:
            self.original_image.close()
        except:
            pass
        self.original_image = None

    def clear_image(self):
        self.close_video()
        self.close_image()
        self.cropper = None
        self.crop_controls = None
        self.first_frame = None
        self.edit_image = None


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
    aspect = NumericProperty(1)
    lowmem = BooleanProperty(False)
    thumbnail = ObjectProperty()
    is_full_size = BooleanProperty(False)
    disable_rotate = BooleanProperty(False)

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
                    app.database_thumbnail_update(photo[0], photo[2], modified_date, photo[13], temporary=self.temporary)
            thumbnail_image = app.database_thumbnail_get(photo[0], temporary=self.temporary)
            if thumbnail_image:
                imagedata = bytes(thumbnail_image[2])
                data = BytesIO()
                data.write(imagedata)
                data.seek(0)
                image = CoreImage(data, ext='jpg')
            else:
                if file_found:
                    updated = app.database_thumbnail_update(photo[0], photo[2], modified_date, photo[13], temporary=self.temporary)
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
        if not self.disable_rotate:
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
            ThumbLoader.num_workers = 2
            ThumbLoader.loading_image = 'data/loadingthumbnail.png'
            self._coreimage = image = ThumbLoader.image(source, load_callback=self.load_thumbnail, nocache=self.nocache, mipmap=self.mipmap, anim_delay=self.anim_delay)
            image.bind(on_load=self._on_source_load)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

    def on_loadfullsize(self, *_):
        if self.thumbnail and not self.is_full_size and self.loadfullsize:
            self._on_source_load()

    def _on_source_load(self, *_):
        try:
            image = self._coreimage.image
            if not image:
                return
        except:
            return
        self.thumbnail = image
        self.thumbsize = image.size
        self.texture = image.texture
        self.aspect = image.size[1] / image.size[0]

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
        if not self.lowmem:
            low_memory = to_bool(app.config.get("Settings", "lowmem"))
        else:
            low_memory = True
        if not low_memory:
            #load a screen-sized image instead of full-sized to save memory
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

    def on_texture(self, *_):
        if self.loadfullsize:
            self.is_full_size = True

    def texture_update(self, *largs):
        pass


class PhotoDrag(FloatLayout):
    """Special image widget for displaying the drag-n-drop location."""

    angle = NumericProperty()
    offset = []
    opacity = .5
    fullpath = StringProperty()
    source = StringProperty()
    total_drags = StringProperty('')


#Scrollers
class Scroller(ScrollView):
    """Generic scroller container widget."""
    pass


class ScrollViewCentered(ScrollView):
    """Special ScrollView that begins centered"""

    def __init__(self, **kwargs):
        self.scroll_x = 0.5
        self.scroll_y = 0.5
        super(ScrollViewCentered, self).__init__(**kwargs)

    def window_to_parent(self, x, y, relative=False):
        return self.to_parent(*self.to_widget(x, y))


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
