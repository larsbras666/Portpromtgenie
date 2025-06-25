[app]
title            = PortpromptGenie
package.name     = portpromptgenie               # endast gemener
package.domain   = io.sfsstudioinc               # omvänd domän, gemener

source.dir       = .
source.include_exts = py,csv,json,png,jpg,kv
version          = 1.0.0

# Python‑ & C‑beroenden som p4a skall bygga in
requirements = \
    kivy==2.3.0, \
    kivymd==1.2.0, \
    requests, \
    fpdf2, \
    pyjnius, \
    pillow

android.permissions = INTERNET
android.api      = 34
android.minapi   = 24
android.ndk      = 25b
android.archs    = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
# android.exclude_recipe = ffpyplayer   # av‑kommentera om du får problem

[buildozer]
log_level     = 2
warn_on_root  = 1