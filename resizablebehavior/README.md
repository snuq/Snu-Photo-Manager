# Resizable Behavior

A behavior for kivy widgets that allows them to be resized by touching/clickin on a corner and dragging.    
     
     
[Youtube demostration video](https://www.youtube.com/watch?v=8VqLV4McmK0)     
      
      
Below is also a **screenshot of the included resizable widget application**.     
     
     
![ScreenShot](https://raw.github.com/kivy-garden/garden.resizable_behavior/master/doc/screenshot.png)

## Usage    

Import and inherit like any other kivy behavior
```python
from kivy.garden.resizable_behavior import ResizableBehavior
from kivy.uix.Button import Button

class ResizableButton(ResizableBehavior, Button):
    pass
```

Enable / disable resizing of a specific side in kwargs or after
```python
res_button = ResizableButton(
    resizable_left = False,
    resizable_right = True,
    resizable_up = False,
    resizable_down = True)

res_button.resizable_left = False
res_button.resizable_right = True
res_button.resizable_up = False
res_button.resizable_down = True
```

Lock / unlock resizing
```python
res_button.resize_lock = True
```
    
Adjust the size of resizable border in kwargs or after
```python
res_button = ResizableButton(resizable_border=8999)

res_button.resizable_border = 100
```

Offset the resizable_border (by default it is inside the widget) in kwargs or after     
```python
res_button = ResizableButton(resizable_border_offset=100)

#A value of resizable_border * 0.5 will center it on the edge of the ResizableButton
res_button.resizable_border_offset = res_button.resizable_border * 0.5
```

Set min and max sizes in kwargs or after     
```python
res_button = ResizableButton(
    min_resizable_width = 100,
    min_resizable_height = 101,
    max_resizable_width = 102,
    max_resizable_height = 103)
    
res_button.min_resizable_width = 100
res_button.min_resizable_height = 101
res_button.max_resizable_width = 102
res_button.max_resizable_height = 103
```

Enable / disable the cursor
```python
res_button.set_cursor_mode(0) # Disabled
res_button.set_cursor_mode(1) # Enabled
# SDL2 system cursors might be added to kivy core in future
```

Change the size of the cursor
```python
res_button.set_cursor_size(width_int, height_int)
```

Change cursor icons
```python
res_button.set_cursor_icons(
    'img/1.png',     # The horizontal icon
    'img/2.png',     # The 45 degree clockwise icon
    'img/3.png',     # The 90 degree clockwise icon
    'img/4.png')     # The 135 degree clockwise icon
```
