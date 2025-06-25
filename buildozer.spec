[app]
title = PortpromptGenie
package.name = Portpromptgenie
package.domain = com.example
source.dir = .
source.include_exts = py,csv,json,png,jpg,kv
version = 1.0.0
requirements = \
    python3, \
    kivy==2.3.0, \
    kivymd==1.2.0, \
    ffpyplayer, \
    requests, \
    fpdf, \
    pyjnius, \
    pillow
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.ndk = 25b
# Om ffpyplayer krånglar – avkommentera nästa rad:
# android.exclude_recipe = ffpyplayer
android.archs = arm64-v8a, armeabi-v7a
android.minapi = 24
[buildozer]
log_level = 2
warn_on_root = 1
