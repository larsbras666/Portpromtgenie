; ==============================================================
;  Buildozer‑spec för PortpromptGenie  —  fungerar för Android
; ==============================================================

[app]
title           = PortpromptGenie
package.name    = portpromptgenie
package.domain  = com.portprompt.genie        # byt om du vill
source.dir      = .
source.include_exts = py,kv,png,jpg,jpeg,json,csv,txt,ttf,otf,md,mp4
version         = 0.1
orientation     = portrait
fullscreen      = 0

# --------------------------------------------------------------
# Viktig rad: **INGEN** versions‑pinning efter python3!
# Pillow låses till 8.4.0 (sista versionen som har recept).
# --------------------------------------------------------------
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,fpdf2,pillow==8.4.0

# Behörigheter som din kod använder
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

# Python‑tolken som p4a ska bygga
p4a.python_version = 3.10

# Android‑SDK/NDK
android.ndk_path    = $ANDROIDNDK
android.sdk_path    = $ANDROIDSDK
android.ndk_api     = 24
android.api         = 34

# Bootstrap
bootstrap = sdl2

# (övriga sektioner behålls som default)
[buildozer]
log_level = 2
warn_on_root = 1