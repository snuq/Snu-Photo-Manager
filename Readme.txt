Snu Photo Manager
-----------------

A feature-rich photo manager and editor written in python and using the Kivy library.
It should run on any platform that the required libraries can be run on.  So far, I have made Windows, Linux (Ubuntu 16+) and Android binaries.
Download latest binaries at:
www.snuq.com/snuphotomanager/

Some features that are implemented:
    Photo and video database with folders, albums, tags and favorites.
    Multiple database support (folders), ability to transfer between databases (for archival purposes).
    Importing from multiple sources at once.
    Drag-n-drop organization.
    Touch-friendly interface.
    Simple and advanced color editing: brightness, contrast, saturation, gamma, color curves, tinting.
    Simple and advanced filters: sharpen, soften, vignette, edge blur.
    Noise reduction: Despeckle, edge-preserve blur, non-local means denoise.
    Image edits: rotate (and straighten), crop, image border overlays (frames).
    Most editing features apply to videos as well.
    Video conversions (reencoding using presets).
    Exporting with watermarks and resizing, export to a folder or FTP.

Manual Installation:
    Python is required, tested with 3.4.4 and 3.5.2.
    The following packages are required:
        numpy (Tested with 1.12.1 and 1.13.3)
        Kivy (Tested with 1.10.0)
        opencv-python (Tested with 3.2.0.7 and 3.3.0.10)
        ffpyplayer (Tested with 4.0.1)
        Pillow (Tested with 3.1.2 and 4.1.1)
    
    For video conversions, the ffmpeg executable must be installed in a path that Python can find
    (the root directory of Snu Photo Manager will work).  Tested with 2.8.11