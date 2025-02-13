# Snu Photo Manager

A feature-rich photo manager with photo and video editing capabilities, written in python and using the Kivy library.
* Sort photos and videos with a database, easily import files from your camera or phone.
* Edit photos and videos with color adjustments, filters, rotation, cropping and more.
* Export your photos for websites, create collages, or convert your videos to a smaller format.

It should run on any platform that the required libraries can be run on.  


This program is released under the GNU General Public License.

Watch the demo video:

[![Demo Video](https://img.youtube.com/vi/1Bgc5UyPOS4/0.jpg)](https://www.youtube.com/watch?v=1Bgc5UyPOS4)


## Some features that are implemented:  
* Photo and video database with folders, tags and favorites.  
* Multiple database support (folders), ability to transfer between databases (for archival purposes).  
* Importing from multiple sources at once.  
* Drag-n-drop organization.  
* Touch-friendly interface.  
* Image color editing: brightness, contrast, saturation, gamma, color curves, tinting.  
* Image filters: sharpen, soften, vignette, edge blur.  
* Noise reduction: Despeckle, edge-preserve blur, non-local means denoise.  
* Image edits: rotate (and straighten), crop, image border overlays (frames).  
* All editing features can apply to videos as well.  
* Video conversion, simple with presets, or use the video editing screen to tweak settings or batch process videos.
* Collage creation from any number of photos.  
* Exporting with watermarks and resizing, export to a folder or FTP.  


## Installation:  


### Windows:  
* Download latest binaries at: www.snuq.com/snuphotomanager/  
* Depending on your browser, left-clicking the files may not download them, you may need to right click on the file and select save as, or save link as.  
* Download the "Snu Photo Manager Installer v#.#.###.exe" file.  
* Run the file.  


### Linux:  
Due to many differences in linux desktop environments, it is very difficult to include a pre-compiled version.  It is recommended to follow the manual installation instructions, then edit "SnuPhotoManager.sh" as needed to run the correct python version.


### Manual Installation:  
* Install Python 3, preferred version is 3.10.  
* Install the Python packages:  
   * Kivy (Tested with 2.2)  
   * ffpyplayer  
   * Pillow  
   * numpy (not strictly required, but some features will be missing without it).  
   * opencv-python or opencv-python-headless (same as numpy).  
* Download the repository.  
* Unzip the repository to the location of your choice.  
* For video conversions, the ffmpeg executable must be installed in a path that Python can find (the root directory of Snu Photo Manager will work).  Tested with 2.8.11.  
* Run "main.py".