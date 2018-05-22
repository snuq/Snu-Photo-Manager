from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.graphics import InstructionGroup
from kivy.uix.modalview import ModalView
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.metrics import dp, cm
from time import time
import os
path = os.path.split(os.path.realpath(__file__))[0]


class CursorModalView(ModalView):
    '''
    The CursorModalView is the parent of ResizeCursor
    '''

    last_opened = 0.0

    def __init__(self, **kwargs):
        super(CursorModalView, self).__init__(**kwargs)
        self.auto_dismiss = False
        self.size_hint = (None, None)
        self.background_color = (0, 0, 0, 0)
        self.pos = (-9999, -9999)
        self.cursor = ResizeCursor()
        self.add_widget(self.cursor)
        self.open()

    def open(self, *largs):
        self._window = self._search_window()
        if not self._window:
            Logger.warning('ModalView: cannot open view, no window found.')
            return
        self._window.add_widget(self)

    def put_on_top(self, *args):
        self.dismiss()
        self.open()

    def on_hidden(self, val):
        # View has to be reopened to get it on top of other widgets
        timenow = time()
        if not val and timenow > self.last_opened + 1:
            self.dismiss()
            self.open()
            self.last_opened = timenow

    def on_touch_down(self, *args):
        pass

    def on_touch_up(self, *args):
        pass

    def on_touch_move(self, *args):
        pass


class ResizeCursor(Widget):
    '''
    The ResizeCursor is the mouse cursor
    '''

    hidden = BooleanProperty(True)
    '''State of cursors visibility
    It is switched to True when mouse is inside the widgets resize border
    and False when it isn't.

    :attr:`hidden` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    resize_icon_paths = ListProperty([
    '{}/resize_horizontal.png'.format(path),
    '{}/resize2.png'.format(path),
    '{}/resize_vertical.png'.format(path),
    '{}/resize1.png'.format(path),
    ])
    '''Cursor icon paths,

    :attr:`resize_icon_paths` is a :class:`~kivy.properties.ListProperty` and
    defaults to [
    'resize_horizontal.png',
    'resize2.png',
    'resize_vertical.png',
    'resize1.png',
    ]
    '''

    grabbed_by = None
    '''Object reference.
    Is used to prevent attribute changes from multiple widgets at same time.

    :attr:`grabbed_by` defaults to None.
    '''

    sides = ()
    source = StringProperty('')

    def __init__(self, **kwargs):
        super(ResizeCursor, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.pos_hint = (None, None)
        self.source = ''
        self.rect = Rectangle(pos=(-9998,-9998), size=(1, 1))
        self.size = (dp(22), dp(22))
        self.pos = [-9998, -9998]

        # Makes an instruction group with a rectangle and
        # loads an image inside it
        # Binds its properties to mouse positional changes and events triggered
        instr = InstructionGroup()
        instr.add(self.rect)
        self.canvas.after.add(instr)
        self.bind(pos=lambda obj, val: setattr(self.rect, 'pos', val))
        self.bind(source=lambda obj, val: setattr(self.rect, 'source', val))
        self.bind(hidden=lambda obj, val: self.on_mouse_move(Window.mouse_pos))
        Window.bind(mouse_pos=lambda obj, val: self.on_mouse_move(val))

    def on_size(self, obj, val):
        self.rect.size = val

    def on_hidden(self, obj, val):
        if not self.disabled:
            self.parent.on_hidden(val)
            if val:
                Window.show_cursor = True
            else:
                Window.show_cursor = False

    def on_mouse_move(self, val):
        if self.hidden or self.disabled or not self.source:
            if self.pos[0] != -9999:
                self.pos[0] = -9999
        else:
            self.pos[0] = val[0] - self.width / 2.0
            self.pos[1] = val[1] - self.height / 2.0

    def change_side(self, left, right, up, down):
        # Changes images when ResizableBehavior.hovering_resizable
        # state changes
        if self.disabled:
            return
        if not self.hidden and self.sides != (left, right, up, down):
            if left and up or right and down:
                self.source = self.resize_icon_paths[1]
            elif left and down or right and up:
                self.source = self.resize_icon_paths[3]
            elif left or right:
                self.source = self.resize_icon_paths[0]
            elif up or down:
                self.source = self.resize_icon_paths[2]
            else:
                if not any((left, right, up, down)):
                    self.pos[0] = -9999
            self.sides = (left, right, up, down)

    def grab(self, wid):
        self.grabbed_by = wid

    def ungrab(self, wid):
        if self.grabbed_by == wid:
            self.grabbed_by = None

    def on_disabled(self, obj, val):
        if not val:
            Window.show_cursor = True
