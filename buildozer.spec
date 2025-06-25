[app]
# ── metadata ───────────────────────────────────────────────
title            = PortpromptGenie
package.name     = portpromptgenie
package.domain   = io.sfsstudioinc
version          = 1.0.0

# ── källor som ska packas med ─────────────────────────────
source.dir            = .
source.include_exts   = py,csv,json,png,jpg,kv

# ── Python & bibliotek ────────────────────────────────────
#  • Python 3.11 kräver senaste p4a‑release (2024‑04‑08) – funkar.
#  • Pyjnius går *inte* ihop med Cython ≥ 3 ännu ⇒ pinna < 3 .
#  • Pillow 8.4 är snabbare att bygga än 10.x (inget du förlorar här).
requirements = \
    python3==3.11.9,\
    Cython==0.29.36,\
    kivy==2.3.0,\
    kivymd==1.2.0,\
    pillow==8.4.0,\
    requests,\
    fpdf2,\
    pyjnius,\
    six

# ── Android‑parametrar ────────────────────────────────────
android.api              = 34
android.minapi           = 24
android.ndk              = 25b
android.archs            = arm64-v8a        # en arkitektur räcker
android.accept_sdk_license = True
android.permissions      = INTERNET

# ── Buildozer‑beteende ────────────────────────────────────
[buildozer]
log_level    = 2
warn_on_root = 1