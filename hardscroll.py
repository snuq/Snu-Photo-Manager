__all__ = ('HardScrollEffect', )


from kivy.effects.kinetic import KineticEffect
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty


class HardScrollEffect(KineticEffect):
    friction = NumericProperty(.1)
    last_velocity = NumericProperty(0)
    drag_threshold = NumericProperty('20sp')
    '''Minimum distance to travel before the movement is considered as a drag.

    :attr:`velocity` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 20sp.
    '''

    min = NumericProperty(0)
    '''Minimum boundary to use for scrolling.

    :attr:`min` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    '''

    max = NumericProperty(0)
    '''Maximum boundary to use for scrolling.

    :attr:`max` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    '''

    scroll = NumericProperty(0)
    '''Computed value for scrolling. This value is different from
    :py:attr:`kivy.effects.kinetic.KineticEffect.value`
    in that it will return to one of the min/max bounds.

    :attr:`scroll` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    overscroll = NumericProperty(0)
    '''Computed value when the user over-scrolls i.e. goes out of the bounds.

    :attr:`overscroll` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    target_widget = ObjectProperty(None, allownone=True, baseclass=Widget)
    '''Widget to attach to this effect. Even if this class doesn't make changes
    to the `target_widget` by default, subclasses can use it to change the
    graphics or apply custom transformations.

    :attr:`target_widget` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    displacement = NumericProperty(0)
    '''Cumulative distance of the movement during the interaction. This is used
    to determine if the movement is a drag (more than :attr:`drag_threshold`)
    or not.

    :attr:`displacement` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    def reset(self, pos):
        '''(internal) Reset the value and the velocity to the `pos`.
        Mostly used when the bounds are checked.
        '''
        self.value = pos
        self.velocity = 0
        if self.history:
            val = self.history[-1][1]
            super(HardScrollEffect, self).start(val, None)

    def on_value(self, *args):
        scroll_min = self.min
        scroll_max = self.max
        if scroll_min > scroll_max:
            scroll_min, scroll_max = scroll_max, scroll_min
        if self.value < scroll_min:
            self.overscroll = self.value - scroll_min
            self.reset(scroll_min)
        elif self.value > scroll_max:
            self.overscroll = self.value - scroll_max
            self.reset(scroll_max)
        else:
            self.scroll = self.value

    def start(self, val, t=None):
        self.is_manual = True
        self.displacement = 0
        return super(HardScrollEffect, self).start(val, t)

    def update(self, val, t=None):
        self.displacement += abs(val - self.history[-1][1])
        return super(HardScrollEffect, self).update(val, t)

    def stop(self, val, t=None):
        self.is_manual = False
        self.displacement += abs(val - self.history[-1][1])
        if self.displacement <= self.drag_threshold:
            self.velocity = 0
            return
        return super(HardScrollEffect, self).stop(val, t)
        
    def update_velocity(self, dt):
        if self.velocity == 0 and self.velocity != self.last_velocity:
            self.target_widget.owner.update_preview()
        self.last_velocity = self.velocity
        return super(HardScrollEffect, self).update_velocity(dt)