[app]

# (str) Title of your application
title = Snu Photo Manager

# (str) Package name
package.name = SnuPhotoManager

# (str) Package domain (needed for android/ios packaging)
package.domain = com.snuq

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt,ini

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin

# (str) Application versioning (method 1)
version = 0.9.008

# (list) Application requirements
# comma seperated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,ffpyplayer_codecs,ffpyplayer==4.2.0,pillow,sqlite3,opencv

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/splash.jpg

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = landscape

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86
android.arch = armeabi-v7a

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: buildozer ios list_identities
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
