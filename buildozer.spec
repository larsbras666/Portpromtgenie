[app]
title           = PortpromptGenie
package.name    = portpromptgenie          # endast gemener
package.domain  = io.sfsstudioinc          # omvänd domän, små bokstäver

# Källkod
source.dir              = .
source.include_exts     = py,csv,json,png,jpg,kv
version                 = 1.0.0

# Python‑ och Kivy‑beroenden
requirements = python3==3.11.5,kivy==2.3.0,kivymd==1.2.0,requests,fpdf2,pyjnius,pillow

# Android‑inställningar
android.permissions      = INTERNET
android.api              = 34
android.minapi           = 24
android.ndk              = 25b
android.archs            = arm64-v8a        # en enda arkitektur räcker
android.accept_sdk_license = True

[buildozer]
log_level     = 2          # 0=quiet, 1=info, 2=debug
warn_on_root  = 1