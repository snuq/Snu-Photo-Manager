'''
Resizable Behavior
===============

The :class:`~kivy.uix.behaviors.resize.ResizableBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides Resize behavior.
When combined with a widget, dragging at the resize enabled widget edge
defined by the
:attr:`~kivy.uix.behaviors.resize.ResizableBehavior.resizable_border`
will resize the widget.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example adds resize behavior to a sidebar to make it resizable

    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.behaviors import ResizableBehavior
    from kivy.uix.label import Label
    from kivy.metrics import cm
    from kivy.uix.button import Button
    from kivy.graphics import *


    class ResizableSideBar(ResizableBehavior, BoxLayout):
        def __init__(self, **kwargs):
            super(ResizableSideBar, self).__init__(**kwargs)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            self.resizable_right = True
            for x in range(1, 10):
                lbl = Label(size_hint=(1, None), height=(cm(1)))
                lbl.text = 'Text '+str(x)
                self.add_widget(lbl)
            self.bind(size=lambda obj, val: setattr(self.bg, 'size', val))

            instr = InstructionGroup()
            instr.add(Color(0.6, 0.6, 0.7, 1))
            instr.add(self.bg)
            self.canvas.before.add(instr)

    class Sample(FloatLayout):
        def __init__(self, **kwargs):
            super(Sample, self).__init__(**kwargs)
            sb = ResizableSideBar(orientation='vertical', size_hint=(None, 1))
            sb.width = cm(4)
            self.add_widget(sb)


    class SampleApp(App):
        def build(self):
            return Sample()


    SampleApp().run()

See :class:`~kivy.uix.behaviors.ResizableBehavior` for details.
'''

from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty
from kivy.metrics import dp, cm
from .modal_cursor import CursorModalView
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.app import App


__all__ = ('ResizableBehavior', )


class ResizableBehavior(object):
    '''
    The ResizableBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_
    class provides Resize behavior.
    When combined with a widget, dragging at the resize enabled widget edge
    defined by the
    :attr:`~kivy.uix.behaviors.resize.ResizableBehavior.resizable_border`
    will resize the widget. Please see the :mod:`drag behaviors module
    <kivy.uix.behaviors.resize>` documentation for more information.
    '''

    hovering_resizable = BooleanProperty(False)
    '''State of mouse hover.
    It is switched to True when mouse is inside the widgets resize border
    and False when it isn't.

    :attr:`hovering_resizable` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    resizable_border = NumericProperty(dp(20))
    '''Widgets resizable border size on each side.
    Minimum resizing size is limited to resizable_border * 3 on all sides

    :attr:`resizable_border` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 20 dp.
    '''

    resizable_border_offset = NumericProperty(0)
    '''Positive values move the resizable_border outside of the widget
    and negative values put it closer to the center of the widget.
    A value of resizable_border * 0.5 will center it on the widgets border,
    which is the most expected behavior, but can sometimes interfere with
    nearby widgets.

    :attr:`resizable_border_offset` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.
    '''

    min_resizable_width = NumericProperty(0)
    '''Minimum width

    :attr:`min_resizable_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    min_resizable_height = NumericProperty(0)
    '''Minimum height

    :attr:`min_resizable_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    max_resizable_width = NumericProperty(0)
    '''Maximum width

    :attr:`max_resizable_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    max_resizable_height = NumericProperty(0)
    '''Maximum height

    :attr:`max_resizable_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    resizable_left = BooleanProperty(False)
    '''Enable / disable resizing on left side

    :attr:`resizable_left` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizable_right = BooleanProperty(False)
    '''Enable / disable resizing on right side

    :attr:`resizable_right` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizable_up = BooleanProperty(False)
    '''Enable / disable resizing on upper side

    :attr:`resizable_up` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizable_down = BooleanProperty(False)
    '''Enable / disable resizing on lower side

    :attr:`resizable_down` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_left = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative to
    the left resize border
    It is switched to True when mouse is inside the left resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_left` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_right = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative to
    the right resize border
    It is switched to True when mouse is inside the right resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_right` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_up = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative
    to the upper resize border
    It is switched to True when mouse is inside the upper resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_up` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_down = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative
    to the lower resize border
    It is switched to True when mouse is inside the lower resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_down` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing = BooleanProperty(False)
    '''State of widget resizing.
    It is switched to True when a resize border is touched and back to
    False when it is released.
    It manages resizing when touch is moved.

    :attr:`resizing` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    can_move_resize = BooleanProperty(True)
    '''Move widget when resizing down or left.
    To keep position on screen in a floatlayout,
    actual postition has to be adjusted.
    Resizing and changing position variables is problematic
    inside movement restricting widgets,
    (StackLayout, BoxLayout, others) this property manages that.

    :attr:`can_move_resize` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    resize_lock = BooleanProperty(False)
    '''Enable / disable resizing

    :attr:`resize_lock` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    cursor = None
    modalview = None

    def __init__(self, **kwargs):
        super(ResizableBehavior, self).__init__(**kwargs)
        self.modalview = CursorModalView()
        self.cursor = self.modalview.cursor
        Window.bind(mouse_pos=self.on_mouse_move)
        Clock.schedule_once(self.modalview.put_on_top, 0)
        self.oldpos, self.oldsize = [], []

    def on_parent(self, *_):
        if self.parent is None:
            self.modalview.close()
            Window.show_cursor = True

    def on_enter_resizable(self):
        self.cursor.hidden = False

    def on_leave_resizable(self):
        self.cursor.hidden = True

    def on_mouse_move(self, _, pos):
        if self.resize_lock:
            return

        if self.cursor and self.cursor.grabbed_by is None:
            oldhover = self.hovering_resizable
            pos = self.to_widget(pos[0]+self.pos[0], pos[1]+self.pos[1])  #added by Snu
            self.hovering_resizable = self.check_resizable_side(pos[0], pos[1])
            if oldhover != self.hovering_resizable:
                if self.hovering_resizable:
                    self.on_enter_resizable()
                else:
                    self.on_leave_resizable()

    def check_resizable_side(self, x, y):
        # Add small performance increase when distance is too high
        # for possible hovering

        if abs(self.x - x) > self.width + self.resizable_border_offset:
            return False
        elif abs(self.y - y) > self.height + self.resizable_border_offset:
            return False

        startx = self.x - self.resizable_border_offset
        endx = self.right + self.resizable_border_offset
        starty = self.y - self.resizable_border_offset
        endy = self.top + self.resizable_border_offset
        if self.resizable_left:
            self.resizing_left = False
            if startx <= x <= startx + self.resizable_border:
                if starty <= y <= endy:
                    self.resizing_left = True
        if self.resizable_right and not self.resizing_left:
            self.resizing_right = False
            if endx - self.resizable_border <= x <= endx:
                if starty <= y <= endy:
                    self.resizing_right = True
        if self.resizable_up:
            self.resizing_up = False
            if endy - self.resizable_border <= y <= endy:
                if startx <= x <= endx:
                    self.resizing_up = True
        if self.resizable_down and not self.resizing_up:
            self.resizing_down = False
            if starty <= y <= starty + self.resizable_border:
                if startx <= x <= endx:
                    self.resizing_down = True

        if any((self.resizing_left, self.resizing_right,
                self.resizing_up, self.resizing_down)):
            if self.cursor:
                self.cursor.change_side(
                    self.resizing_left, self.resizing_right,
                    self.resizing_up, self.resizing_down)
            return True
        else:
            return False

    def on_touch_down(self, touch):
        if not self.hovering_resizable:
            return super(ResizableBehavior, self).on_touch_down(touch)

        if self.resize_lock:
            return super(ResizableBehavior, self).on_touch_down(touch)

        if not any([
            self.resizing_right, self.resizing_left,
            self.resizing_down, self.resizing_up
        ]):
            return super(ResizableBehavior, self).on_touch_down(touch)

        self.oldpos = list(self.pos)
        self.oldsize = list(self.size)
        self.resizing = True
        self.cursor.grab(self)
        return True

    def on_touch_move(self, touch):
        if not self.resizing:
            return super(ResizableBehavior, self).on_touch_move(touch)
        self.resize_widget(touch)

    def resize_widget(self, touch):
        rb3 = self.resizable_border * 3

        if self.resizing_right:
            if touch.pos[0] > self.pos[0] + rb3:
                self.width = touch.pos[0] - self.pos[0]

        elif self.resizing_left:
            if touch.pos[0] < self.oldpos[0] + self.oldsize[0] - rb3:
                if self.can_move_resize:
                    self.pos[0] = touch.pos[0]
                    self.width = self.oldpos[0] - touch.pos[0] + \
                        self.oldsize[0]
                else:
                    self.width = abs(touch.pos[0] - self.pos[0])
                    if self.width < rb3:
                        self.width = rb3

        if self.resizing_down:
            if touch.pos[1] < self.oldpos[1] + self.oldsize[1] - rb3:
                if self.can_move_resize:
                    self.pos[1] = touch.pos[1]
                    self.height = self.oldpos[1] - touch.pos[1] + \
                        self.oldsize[1]
                else:
                    self.height = abs(touch.pos[1] - self.pos[1])
                    if self.height < rb3:
                        self.height = rb3

        elif self.resizing_up:
            if touch.pos[1] > self.pos[1] + rb3:
                self.height = touch.pos[1] - self.pos[1]

        self.check_min_max_size(touch)
        return True

    def check_min_max_size(self, touch):
        # Resizes widgets back to min / max when smaller / bigger
        # Resets position only when it's necessary
        if self.min_resizable_width:
            if self.width < self.min_resizable_width:
                if self.pos[0] != self.oldpos[0]:
                    self.width = self.min_resizable_width
                    self.pos[0] = self.oldpos[0] + self.oldsize[0] - self.width
                else:
                    self.width = self.min_resizable_width

        if self.max_resizable_width:
            if self.width > self.max_resizable_width:
                if self.pos[0] != self.oldpos[0]:
                    self.width = self.max_resizable_width
                    self.pos[0] = self.oldpos[0] + self.oldsize[0] - self.width
                else:
                    self.width = self.max_resizable_width

        if self.min_resizable_height:
            if self.height < self.min_resizable_height:
                if self.pos[1] != self.oldpos[1]:
                    self.height = self.min_resizable_height
                    self.pos[1] = (
                        self.oldpos[1] + self.oldsize[1] - self.height)
                else:
                    self.height = self.min_resizable_height

        if self.max_resizable_height:
            if self.height > self.max_resizable_height:
                if self.pos[1] != self.oldpos[1]:
                    self.height = self.max_resizable_height
                    self.pos[1] = (
                        self.oldpos[1] + self.oldsize[1] - self.height)
                else:
                    self.height = self.max_resizable_height

    def on_touch_up(self, touch):
        if not self.resizing:
            return super(ResizableBehavior, self).on_touch_up(touch)
        self.resizing = False
        self.resizing_right = False
        self.resizing_left = False
        self.resizing_down = False
        self.resizing_up = False
        self.cursor.ungrab(self)
        self.on_mouse_move(None, touch.pos)
        return True

    def on_resize_lock(self, obj, locked):
        'Resets behavior to default values when resizing is locked'
        if locked:
            self.resizing = False
            self.resizing_right = False
            self.resizing_left = False
            self.resizing_down = False
            self.resizing_up = False
            Window.show_cursor = True
            self.cursor.ungrab(self)
            self.cursor.hidden = True

    def set_cursor_size(self, size):
        '''Default cursor size is (dp(22), dp(22)).
        Use this method to change it
        '''
        self.cursor.size = size

    def set_cursor_icons(self, hor, deg45, deg90, deg135):
        '''Change cursor icon paths.
        Function takes 4 arguments, first is horizontal,
        next 3 are turned 45, 90, 135 degrees clockwise.
        '''
        self.cursor.resize_icon_paths[0] = hor
        self.cursor.resize_icon_paths[1] = deg45
        self.cursor.resize_icon_paths[2] = deg90
        self.cursor.resize_icon_paths[3] = deg135

    def set_cursor_mode(self, value):
        '''Method takes expects one integer
        0 - Disables the resize cursor
        1 - Default mode, os cursor is hidden and replaced with resize cursor
        when mouse position enters widgets resizable_border
        '''
        if value == 0 and not self.cursor.disabled:
            self.cursor.disabled = True
        elif value == 1 and self.cursor.disabled:
            self.cursor.disabled = False
