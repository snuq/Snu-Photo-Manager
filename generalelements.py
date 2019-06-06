import os
import re
import time
from io import BytesIO
from PIL import Image

from kivy.config import Config
Config.window_icon = "data/icon.png"
from kivy.app import App
from kivy.clock import Clock
from kivy.cache import Cache
from kivy.graphics.transformation import Matrix
from kivy.uix.behaviors import ButtonBehavior, DragBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
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
from generalcommands import to_bool, isfile2

from kivy.lang.builder import Builder
Builder.load_string("""
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
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/headerbg.png'
    height: app.button_scale

<MainHeader@HeaderBase>:
    canvas.before:
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/headerbglight.png'
    height: int(app.button_scale * 1.25)
    padding: int(app.button_scale / 8)

<MainArea@BoxLayout>:
    canvas.before:
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/mainbg.png'

<-NormalSlider@Slider>:
    #:set sizing 18
    canvas:
        Color:
            rgba: 1, 1, 1, 1 if not root.disabled else 0.3
        BorderImage:
            border: (0, sizing, 0, sizing)
            pos: self.pos
            size: self.size
            source: 'data/sliderbg.png'
        Rectangle:
            pos: (self.value_pos[0] - app.button_scale/4, self.center_y - app.button_scale/2)
            size: app.button_scale/2, app.button_scale
            source: 'data/buttontoggleon.png'
    size_hint_y: None
    height: app.button_scale
    min: -1
    max: 1
    value: 0
    cursor_image: 'data/buttontoggleon.png'

<-HalfSlider@Slider>:
    #:set sizing 18
    canvas:
        Color:
            rgba: 1, 1, 1, 1 if not root.disabled else 0.3
        BorderImage:
            border: (0, sizing, 0, sizing)
            pos: self.pos
            size: self.size
            source: 'data/sliderbg.png'
        Rectangle:
            pos: (self.value_pos[0] - app.button_scale/4, self.center_y - app.button_scale/2)
            size: app.button_scale/2, app.button_scale
            source: 'data/buttontoggleon.png'
    size_hint_y: None
    height: app.button_scale
    min: 0
    max: 1
    value: 0

<HalfSliderLimited>:
    #:set sizing 18
    canvas:
        Color:
            rgba: 1, 1, 1, 1 if not root.disabled else 0.3
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
            rgba: 1, 1, 1, 1 if not root.disabled else 0.3
        Rectangle:
            pos: (self.value_pos[0] - app.button_scale/4, self.center_y - app.button_scale/2)
            size: app.button_scale/2, app.button_scale
            source: 'data/buttontoggleon.png'
    size_hint_y: None
    height: app.button_scale
    min: 0
    max: 1
    value: 0


<NormalLabel>:
    mipmap: True
    font_size: app.text_scale
    size_hint_y: None
    height: app.button_scale

<LeftNormalLabel@NormalLabel>:
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
    color: 0, 0, 0, 1

<DatabaseLabel@ShortLabel>:
    mipmap: True
    text: app.database_update_text

<HeaderLabel@Label>:
    mipmap: True
    font_size: int(app.text_scale * 1.5)
    size_hint_y: None
    height: app.button_scale
    bold: True


<NormalInput@TextInput>:
    mipmap: True
    write_tab: False
    use_bubble: True
    background_color: .2, .2, .3, .8
    disabled_foreground_color: 1,1,1,.75
    foreground_color: 1,1,1,1
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


<NormalButton>:
    mipmap: True
    size_hint_y: None
    height: app.button_scale
    width: self.texture_size[0] + app.button_scale
    size_hint_x: None
    font_size: app.text_scale
    background_normal: 'data/buttonwarnup.png' if self.warn else 'data/buttonlightup.png'
    background_down: 'data/buttonwarndown.png' if self.warn else 'data/buttonlightdown.png'
    background_disabled_down: 'data/buttondisabled.png'
    background_disabled_normal: 'data/buttondisabled.png'

<WideButton>:
    size_hint_y: None
    height: app.button_scale
    text_size: self.size
    halign: 'center'
    valign: 'middle'
    font_size: app.text_scale
    background_normal: 'data/buttonwarnup.png' if self.warn else 'data/buttonlightup.png'
    background_down: 'data/buttonwarndown.png' if self.warn else 'data/buttonlightdown.png'
    background_disabled_down: 'data/buttondisabled.png'
    background_disabled_normal: 'data/buttondisabled.png'

<MenuButton>:
    mipmap: True
    font_size: app.text_scale
    size_hint_y: None
    height: app.button_scale
    background_normal: 'data/buttonwarnup.png' if self.warn else 'data/buttonup.png'
    background_down: 'data/buttonwarndown.png' if self.warn else 'data/buttondown.png'
    background_disabled_down: 'data/buttondisabled.png'
    background_disabled_normal: 'data/buttondisabled.png'

<RemoveButton>:
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
                rgba: (1, 1, 1, 1) if root.expanded else (0, 0, 0, 0)
            BorderImage:
                pos: self.pos
                size: self.size
                source: 'data/buttonmenu.png'
        cols: 2
        size_hint: 1, None
        height: self.minimum_height
        GridLayout:
            padding: app.padding
            cols: 1
            size_hint: 1, None
            height: self.minimum_height
            id: contentContainer

<TreeViewButton>:
    color_selected: app.selected_color
    odd_color: app.color_odd
    even_color: app.color_even
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

<MenuStarterButton@Button>:
    canvas.after:
        Color:
            rgba: 1, 1, 1, .5
        Rectangle:
            pos: (root.pos[0]+root.width-(root.height/1.5)), root.pos[1]
            size: root.height/2, root.height
            source: 'data/menuarrows.png'
    mipmap: True
    size_hint_y: None
    height: app.button_scale
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_max_x: self.texture_size[0] + (app.button_scale * 1.2)
    background_normal: 'data/buttonup.png'
    background_down: 'data/buttondown.png'
    background_disabled_down: 'data/buttondisabled.png'
    background_disabled_normal: 'data/buttondisabled.png'

<MenuStarterButtonWide@Button>:
    canvas.after:
        Color:
            rgba: 1, 1, 1, .5
        Rectangle:
            pos: (root.pos[0]+root.width-(root.height/1.5)), root.pos[1]
            size: root.height/2, root.height
            source: 'data/menuarrows.png'
    mipmap: True
    size_hint_y: None
    height: app.button_scale
    text_size: self.size
    halign: 'center'
    valign: 'middle'
    shorten: True
    shorten_from: 'right'
    font_size: app.text_scale
    size_hint_x: 1
    background_normal: 'data/buttonup.png'
    background_down: 'data/buttondown.png'
    background_disabled_down: 'data/buttondisabled.png'
    background_disabled_normal: 'data/buttondisabled.png'

<NormalToggle@ToggleButton>:
    mipmap: True
    font_size: app.text_scale
    size_hint_y: None
    height: app.button_scale
    size_hint_x: None
    width: self.texture_size[0] + 20
    background_normal: 'data/buttontoggleoff.png'
    background_down: 'data/buttontoggleon.png'

<ReverseToggle@ToggleButton>:
    canvas:
        Rectangle:
            pos: self.pos
            size: self.size
            source: 'data/arrowdown.png' if self.state == 'normal' else 'data/arrowup.png'
    mipmap: True
    size_hint: None, None
    height: app.button_scale
    width: app.button_scale
    background_normal: 'data/buttontoggleoff.png'
    background_down: 'data/buttontoggleoff.png'

<SettingsButton@NormalButton>:
    mipmap: True
    text: '' if app.simple_interface else 'Settings'
    border: (0, 0, 0, 0) if app.simple_interface else (16, 16, 16, 16)
    background_normal: 'data/settings.png' if app.simple_interface else 'data/buttonlightup.png'
    background_down: 'data/settings.png' if app.simple_interface else 'data/buttonlightdown.png'
    on_release: app.open_settings()

<VerticalButton@ToggleButton>:
    mipmap: True
    color: 1, 1, 1, 0
    size_hint_y: None
    width: app.button_scale
    size_hint_x: None
    font_size: app.text_scale
    height: self.texture_size[0] + 100
    background_normal: 'data/buttonlightup.png'
    background_down: 'data/buttonsidetabdown.png'
    Label:
        center: self.parent.center
        canvas.before:
            PushMatrix
            Rotate:
                angle: 90
                axis: 0,0,1
                origin: self.center
        canvas.after:
            PopMatrix
        text: self.parent.text

<PhotoRecycleViewButton>:
    canvas.after:
        Color:
            rgba: (1, 1, 1, 0) if self.found else(1, 0, 0, .33)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 1, 1, 1, .5 if self.favorite else 0
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
    background: 'data/panelbg.png'

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
            text: 'OK'
            on_release: root.dispatch('on_answer','yes')
        WideButton:
            text: 'Cancel'
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
            text: 'OK'
            on_release: root.dispatch('on_answer','yes')
        WideButton:
            text: 'Cancel'
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
            text: 'Cancel'

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
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
            source: 'data/buttonmenu.png'

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
            rgba: app.selected_color if self.selected else (0, 0, 0, 0)
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
            rgba: 1, 1, 1, .5 if root.favorite else 0
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
                color: .66, .66, .66, 1
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
    cols: max(1, int(self.width / ((app.button_scale * 4) + (app.button_scale / 2))))
    spacing: int(app.button_scale / 2)
    padding: int(app.button_scale / 2)
    focus: False
    touch_multiselect: True
    multiselect: True
    default_size: app.button_scale * 4, app.button_scale * 4
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
    scroll_type: ['bars', 'content']

<NormalTreeView@TreeView>:
    color_selected: app.selected_color
    odd_color: app.color_odd
    even_color: app.color_even
    indent_level: int(app.button_scale * .5)
    size_hint: 1, None
    height: self.minimum_height
    hide_root: True


<SplitterStrip>:
    background_normal: 'data/splitterbgup.png'
    background_down: 'data/splitterbgdown.png'

<SplitterPanel>:
    canvas.before:
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
    opacity: 0 if self.hidden else 1
    disabled: self.hidden
    sizable_from: 'right'

<SplitterPanelRight>:
    width: self.display_width
    opacity: 0 if self.hidden else 1
    disabled: self.hidden
    sizable_from: 'left'


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
    canvas.before:
        PushMatrix
        Rotate:
            angle: root.angle
            axis: 0,0,1
            origin: root.center
    canvas.after:
        PopMatrix

    height: (app.button_scale * 4)
    width: (app.button_scale * 4)
    size_hint_y: None
    size_hint_x: None


<Scroller>:
    scroll_distance: 10
    scroll_timeout: 200
    bar_width: int(app.button_scale * .5)
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

    size_hint_y: None
    height: sp(33)*10
    foreground_color: (1, 1, 1, 1) if self.hsv[2] * wheel.a < .5 else (0, 0, 0, 1)
    wheel: wheel
    BoxLayout:
        orientation: 'vertical'
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
class HalfSliderLimited(Slider):
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


class PhotoThumbLabel(NormalLabel):
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
                app.drag(self, 'start', window_coords, image=self.image, offset=widget_coords, fullpath=self.fullpath)

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


class TreenodeDrag(BoxLayout):
    """Widget that looks like a treenode thumbnail, used for showing the position of the drag-n-drop."""

    fullpath = StringProperty()
    text = StringProperty()
    subtext = StringProperty()


class SelectableRecycleBoxLayout(RecycleBoxLayout, LayoutSelectionBehavior):
    """Adds selection and focus behavior to the view."""
    selected = DictProperty()
    selects = ListProperty()
    multiselect = BooleanProperty(False)

    def select_range(self):
        select_index = self.parent.data.index(self.selected)
        selected_nodes = []
        if self.selects:
            for select in self.selects:
                selected_nodes.append(self.parent.data.index(select))
        else:
            selected_nodes = [0, len(self.parent.data)]
        closest_node = min(selected_nodes, key=lambda x: abs(x-select_index))

        for index in range(min(select_index, closest_node), max(select_index, closest_node)):
            selected = self.parent.data[index]
            if selected not in self.selects:
                self.selects.append(selected)
        self.selects.append(self.selected)

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

    def check_selected(self):
        temp_selects = []
        for select in self.selects:
            if select in self.parent.data:
                temp_selects.append(select)
        self.selects = temp_selects

    def on_selected(self, *_):
        app = App.get_running_app()
        if self.selected:
            if self.multiselect:
                self.check_selected()
                if self.selected in self.selects:
                    self.selects.remove(self.selected)
                else:
                    if app.shift_pressed:
                        self.select_range()
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
    pass


class NormalRecycleView(RecycleView):
    def get_selected(self):
        selected = []
        for item in self.data:
            if item['selected']:
                selected.append(item)
        return selected


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
class NormalButton(Button):
    """Basic button widget."""

    warn = BooleanProperty(False)


class WideButton(Button):
    """Full width button widget"""

    warn = BooleanProperty(False)


class MenuButton(Button):
    """Basic class for a drop-down menu button item."""

    warn = BooleanProperty(False)


class RemoveButton(NormalButton):
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
            content_container = self.ids['contentContainer']
            if self.expanded:
                content_container.add_widget(self.content)
            else:
                content_container.clear_widgets()

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
    pass


class MessagePopup(GridLayout):
    """Basic popup message with a message and 'ok' button."""

    button_text = StringProperty('OK')
    text = StringProperty()

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


class MoveConfirmPopup(NormalPopup):
    """Popup that asks to confirm a file or folder move."""
    target = StringProperty()
    photos = ListProperty()
    origin = StringProperty()


class ScanningPopup(NormalPopup):
    """Popup for displaying database scanning progress."""
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
    pass


class AlbumSortDropDown(NormalDropDown):
    """Drop-down menu for sorting album elements"""
    pass


#Splitter Panels
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


#Images
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
            self._coreimage = image = ThumbLoader.image(source, load_callback=self.load_thumbnail, nocache=self.nocache, mipmap=self.mipmap, anim_delay=self.anim_delay)
            image.bind(on_load=self._on_source_load)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

    def on_loadfullsize(self, *_):
        if self.thumbnail and not self.is_full_size and self.loadfullsize:
            self._on_source_load()

    def _on_source_load(self, *_):
        image = self._coreimage.image
        if not image:
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


class PhotoDrag(KivyImage):
    """Special image widget for displaying the drag-n-drop location."""

    angle = NumericProperty()
    offset = []
    opacity = .5
    fullpath = StringProperty()


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
