# Snu Photo Manager

A feature-rich photo manager with photo and video editing capabilities, written in python and using the Kivy library.
* Sort photos and videos with a database, easily import files from your camera or phone.
* Edit photos and videos with color adjustments, filters, rotation, cropping and more.
* Export your photos for websites, create collages, or convert your videos to a smaller format.

It should run on any platform that the required libraries can be run on.  So far, I have made Windows, Linux (Ubuntu 16+) and Android binaries.  It should be possible to create OSX and ios binaries as well, but I do not have the required hardware to do so.  
Download latest binaries at: www.snuq.com/snuphotomanager/  

Note that the android version is very beta - some features are missing, it is pretty slow, and it is not yet a signed executable (debug only for now).  

This program is released under the GNU General Public License.

Watch the demo video:

[![Demo Video](https://img.youtube.com/vi/1Bgc5UyPOS4/0.jpg)](https://www.youtube.com/watch?v=1Bgc5UyPOS4)


## Some features that are implemented:  
* Photo and video database with folders, albums, tags and favorites.  
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
Depending on your browser, left clicking the files may not download them, you may need to right click on the file and select save as, or save link as.  


### Windows:  
* Download the "Snu Photo Manager Installer v#.#.###.exe" file.  
* Run the file.  


### Linux:  
Due to many differences in linux desktop environments, the install script may not work.  If this is the case, you will need to extract the .tar.gz file and create a shortcut yourself.  
* Download both files in the 'linux' subdirectory.  
* Place the files in the location where you would like the 'Snu Photo Manager' folder to be (such as in your home directory).  
* Run the 'snuphotomanagerinstall' file.  Double clicking may work, otherwise open a terminal, go to the directory, and type "./snuphotomanagerinstall" (without the quotes).
* A new shortcut file should be created in the current folder: 'Snu Photo Manager.desktop', this may be moved to your desktop or any other location.  


### Android:  
For now, side-loading of apps is required to be enabled.  Depending on your device, this may be enabled already, or may be impossible to enable.  
* Download "snuphotomanager-#.#.###-debug.apk" to your android device, or transfer from a computer using your preferred method.  
* Run the file from your file manager of choice.  


### Manual Installation:  
* Install Python 3, should work well on 3.7, 3.8 and 3.9.  
* Install the Python packages:  
   * Kivy (Tested with 1.11.1, 2.0.0 mostly works but has some bugs for now)  
   * ffpyplayer  
   * Pillow  
   * numpy (not strictly required, but some features will be missing without it).  
   * opencv-python (same as numpy).  
* Download the repository.  
* Unzip the repository to the location of your choice.  
* For video conversions, the ffmpeg executable must be installed in a path that Python can find (the root directory of Snu Photo Manager will work).  Tested with 2.8.11.  
* Run "main.py".