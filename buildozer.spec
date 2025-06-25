[app]
title = PortpromptGenie
package.name   = portpromptgenie
package.domain = io.sfsstudioinc

source.dir = .
source.include_exts = py,csv,json,png,jpg,kv
version = 1.0.0

# krav skrivs komma‑separerat på EN rad (eller radbryt med '\')
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,fpdf2,pyjnius,pillow

android.permissions = INTERNET
android.api  = 34
android.ndk  = 25b
# android.exclude_recipe = ffpyplayer   ; aktivera om du får problem med ffpyplayer
android.archs  = arm64-v8a,armeabi-v7a
android.minapi = 24
android.accept_sdk_license = True

[buildozer]
log_level    = 2
warn_on_root = 1