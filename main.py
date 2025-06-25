# PromptGenie v12.0  (multi‑genre edition)
# --------------------------------------------------
#  • Prompt‑ och portfolio‑verktyg för mohair/fur‑,
#    handritnings‑, arkitektur‑ m.fl. projekt.
#  • Analyzer med fritt utbyggbara attribut.
#  • Fullt Android‑stöd (KivyMD 1.2 + Buildozer).
# --------------------------------------------------

from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.uix.image import AsyncImage
try:
    from ffpyplayer.player import MediaPlayer
except ImportError:
    MediaPlayer = None
import os, shutil, base64, csv, datetime, zipfile, json, requests, sys
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.slider import Slider
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivy.properties import NumericProperty, ListProperty

# ---------- Android‑behörigheter ----------
if platform == "android":
    from android.permissions import request_permissions, Permission
    from jnius import autoclass
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

Window.size = (420, 780)

# ---------- Fil‑/datakataloger ----------
BASE_DIR = os.path.join(os.path.expanduser("~"), "PromptGenieData")
os.makedirs(BASE_DIR, exist_ok=True)
promptbank_path      = os.path.join(BASE_DIR, "PromptGenie_PromptBank.csv")
prompt_history_path  = os.path.join(BASE_DIR, "PromptGenie_History.json")
texture_path         = os.path.join(BASE_DIR, "PromptGenie_TextureRefs.csv")
analyzer_modes_path  = os.path.join(BASE_DIR, "PromptGenie_AnalyzerModes.json")

# ---------- Analyzer‑lägen (kan utökas) ----------
DEFAULT_ANALYSIS_MODES = [
    {
        "key": "fluff",
        "label": "Fluff / Fiber Factor",
        "unit": "%",
        "min": 0, "max": 100, "step": 5,
        "system_template": "Analyze image for mohair/fur garments. Fluff factor={value}%. Describe color, fiber density and cinematic texture."
    },
    {
        "key": "handwriting",
        "label": "Handwriting Detail Level",
        "unit": "/10",
        "min": 0, "max": 10, "step": 1,
        "system_template": "Inspect the drawing or calligraphy. Detail level={value}/10. Comment on line work, shading, historical style and medium."
    },
    {
        "key": "patina",
        "label": "Metal Patina / Plating",
        "unit": "%",
        "min": 0, "max": 100, "step": 5,
        "system_template": "Inspect metal object or jewellery. Patina level={value}%. Describe surface wear, oxidation colours and possible alloy."
    }
]
def load_analysis_modes():
    if os.path.exists(analyzer_modes_path):
        try:
            with open(analyzer_modes_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    with open(analyzer_modes_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_ANALYSIS_MODES, f, indent=4)
    return DEFAULT_ANALYSIS_MODES
ANALYSIS_MODES = load_analysis_modes()

# ---------- Exempelprompter ----------
DEFAULT_PROMPTS = [
    {"name": "Fuzzy Fox Outfit",
     "prompt": "the subject stands in a snowy field, wearing fox fur boots and thick mittens. the camera is at a low angle."},
    {"name": "High Angle Cinematic",
     "prompt": "the camera hovers high above the subject, revealing an expansive landscape. the subject wears a mohair sweater."},
]

# ---------- OpenAI‑hjälpare ----------
def call_ai_service(messages, model="gpt-3.5-turbo", max_tokens=350):
    api_key = PromptGenieApp.api_key if hasattr(PromptGenieApp, 'api_key') else os.getenv("OPENAI_API_KEY", "")
    if not api_key or not api_key.strip() or api_key.startswith("sk-REPLACE"):
        show_api_warning()
        return "[ERROR] No API key set."
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data    = {"model": model, "messages": messages, "max_tokens": max_tokens}
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR] {str(e)}"

# ==================================================
# ------------------  SCREENS  ----------------------
# ==================================================

# ---------- 1. Analyzer ----------
class TextureAnalyzerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_path = None
        self.mode = ANALYSIS_MODES[0]

        layout = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
        self.add_widget(layout)
        layout.add_widget(MDLabel(text="Analyzer", halign="center", bold=True))

        self.mode_spinner = Spinner(text=self.mode["label"],
                                    values=[m["label"] for m in ANALYSIS_MODES],
                                    size_hint=(1, None), height=dp(40))
        self.mode_spinner.bind(text=self.on_mode_change)
        layout.add_widget(self.mode_spinner)

        self.tex_name = MDTextField(hint_text="Name reference", size_hint=(1, None), height=dp(40))
        layout.add_widget(self.tex_name)

        self.slider_label = Label(text=f"{self.mode['label']} ({self.mode['unit'].strip()})")
        layout.add_widget(self.slider_label)
        self.slider = Slider(min=self.mode["min"], max=self.mode["max"],
                             value=self.mode["min"], step=self.mode["step"],
                             size_hint=(1, None), height=dp(40))
        layout.add_widget(self.slider)

        layout.add_widget(Button(text="Select Image", size_hint=(1, None), height=dp(40),
                                 on_release=self.select_image))
        layout.add_widget(Button(text="Analyze & Save", size_hint=(1, None), height=dp(40),
                                 on_release=self.analyze_and_save))

        self.output = MDTextField(hint_text="AI output", multiline=True,
                                  size_hint=(1, None), height=dp(140))
        layout.add_widget(self.output)

    def on_mode_change(self, _, txt):
        self.mode = next(m for m in ANALYSIS_MODES if m["label"] == txt)
        self.slider.min, self.slider.max, self.slider.step = self.mode["min"], self.mode["max"], self.mode["step"]
        self.slider.value = self.mode["min"]
        self.slider_label.text = f"{self.mode['label']} ({self.mode['unit'].strip()})"

    def select_image(self, _):
        fc  = FileChooserListView(path=os.path.expanduser("~"), filters=["*.jpg", "*.png"])
        box = BoxLayout(orientation='vertical', spacing=5, padding=5); box.add_widget(fc)
        def done(*_):
            if fc.selection: self.image_path = fc.selection[0]
            pop.dismiss()
        box.add_widget(Button(text="Confirm", size_hint=(1, None), height=dp(40), on_release=done))
        pop = Popup(title="Select Image", content=box, size_hint=(0.9, 0.9)); pop.open()

    def analyze_and_save(self, _):
        if not self.image_path:   self.output.text = "No image selected."; return
        nm = self.tex_name.text.strip()
        if not nm:                self.output.text = "Enter a reference name."; return
        value = self.slider.value
        tpl   = self.mode["system_template"].format(value=value)
        try:
            with open(self.image_path, "rb") as f: b64 = base64.b64encode(f.read()).decode("utf-8")[:60]
            messages = [{"role": "system", "content": tpl},
                        {"role": "user",   "content": f"[img base64 len={len(b64)}]"}]
            out = call_ai_service(messages)
            combined = f"{out}\n[{self.mode['label']}={value}{self.mode['unit']}]"
            self.output.text = f"{nm}\n{combined}"

            newfile = not os.path.exists(texture_path) or os.path.getsize(texture_path) == 0
            with open(texture_path, "a", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                if newfile: w.writerow(["RefName", "ModeKey", "Description"])
                w.writerow([nm, self.mode["key"], combined])
        except Exception as e:
            self.output.text = f"Error: {str(e)}"

# ---------- 2. Prompt Builder ----------
class PromptBuilderScreen(Screen):
    fuzzy_factor = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_clothing, self.selected_angles, self.selected_features = set(), set(), set()
        self.prompt_history = []; self.load_prompt_history()

        mainlayout = MDBoxLayout(orientation='vertical', spacing=10, padding=10); self.add_widget(mainlayout)
        mainlayout.add_widget(MDLabel(text="Prompt Builder", halign="center", bold=True))

        self.spinners = {}
        config = {
            "Platform": ["", "Runway", "Mage.space", "Midjourney", "StableDiffusion"],
            "Medium"  : ["", "Sketch", "Hand‑drawn", "Photo", "Blueprint", "Oil Paint", "Digital 3D"],
            "Subject" : ["", "Model", "Figure", "Object", "Building", "Landscape", "Creature"],
            "Style"   : ["", "Fluffy", "Gothic", "Medieval", "Brutalist", "Art‑Nouveau", "Sci‑Fi", "Fantasy"],
            "Camera Motion": ["", "Tracking", "Locked", "Handheld", "Pan", "Steadicam"],
            "Prompt Weighting": ["", "((subject))", "((texture))", "((motion))", "((light))"]
        }
        for label, values in config.items():
            mainlayout.add_widget(MDLabel(text=label))
            sp = Spinner(text="(none)", values=values, size_hint=(1, None), height=dp(40)); mainlayout.add_widget(sp)
            self.spinners[label] = sp

        mainlayout.add_widget(Label(text="Attribute Factor (0..100)"))
        self.slider = Slider(min=0, max=100, value=0, step=5, size_hint=(1, None), height=dp(40))
        self.slider.bind(value=self.on_fuzzy_changed); mainlayout.add_widget(self.slider)

        self.genre  = MDTextField(hint_text="Genre / Style enhancement", size_hint=(1, None), height=dp(40))
        self.extra  = MDTextField(hint_text="Extra motion / mood", multiline=True, size_hint=(1, None), height=dp(60))
        self.prompt_output = MDTextField(hint_text="Prompt Output", multiline=True, size_hint=(1, None), height=dp(120))
        self.bank_name = MDTextField(hint_text="Save as prompt name", size_hint=(1, None), height=dp(40))
        for w in (self.genre, self.extra, self.prompt_output, self.bank_name): mainlayout.add_widget(w)

        self.build_toggle_section(mainlayout, "Clothing / Props:",
                                  ["Hairstyle", "Boots", "Sweater", "Cloak", "Quill", "Shield", "Blueprint Tube"])
        self.build_toggle_section(mainlayout, "Fuzzy Items:",
                                  ["Mohair Sweater", "Fox Fur", "Highness Fur Boots", "Fur Mittens"])
        self.build_toggle_section(mainlayout, "Camera Angles:",
                                  ["High Angle", "Low Angle", "Dutch Angle", "Over‑Shoulder", "POV"], toggle_type="angle")
        self.build_toggle_section(mainlayout, "Model / Object Features:",
                                  ["Big Lips", "Long Pigtails", "Platinum Hair", "Stone Facade", "Flying Buttress", "Piercings"], toggle_type="feature")

        actions = [
            ("Add Story", self.add_story), ("Generate Prompt", self.generate_prompt),
            ("Enhance Prompt", self.enhance_prompt), ("Runway Best", self.runway_best),
            ("Save Bank", self.save_prompt_bank), ("Load Bank", self.load_prompt_bank),
            ("Copy Prompt", self.copy_prompt), ("Export PDF", self.export_pdf),
            ("View History", self.view_prompt_history)
        ]
        for label, func in actions:
            mainlayout.add_widget(Button(text=label, size_hint=(1, None), height=dp(40), on_release=func))

    # ---------- toggles ----------
    def build_toggle_section(self, layout, title, items, toggle_type="clothing"):
        layout.add_widget(MDLabel(text=title, bold=True))
        row = BoxLayout(size_hint=(1, None), height=dp(40))
        for item in items:
            row.add_widget(Button(text=item, on_release=lambda _, x=item: self.toggle_item(x, toggle_type)))
        layout.add_widget(row)
    def toggle_item(self, val, item_type):
        target = {"clothing": self.selected_clothing, "angle": self.selected_angles, "feature": self.selected_features}[item_type]
        target.remove(val) if val in target else target.add(val)
    def on_fuzzy_changed(self, _, val): self.fuzzy_factor = val

    # ---------- prompt ----------
    def generate_prompt(self, _):
        vals = {k: sp.text.strip() for k, sp in self.spinners.items() if sp.text not in ["", "(none)"]}
        if len(vals) < 5: return
        cloth = f"Wearing/Props: {', '.join(self.selected_clothing)}" if self.selected_clothing else "No props."
        angle = f"Camera angles: {', '.join(self.selected_angles)}"   if self.selected_angles else "No angle toggles."
        feat  = f"Features: {', '.join(self.selected_features)}"      if self.selected_features else ""
        attr  = f"Attribute factor: {int(self.fuzzy_factor)}%."       if self.fuzzy_factor else ""
        extr  = self.extra.text.strip() or "subtle emphasis."
        frames = [
            f"[Frame 1] The {vals['Subject']} appears in {vals['Medium']} medium. {cloth} - {vals['Prompt Weighting']}",
            f"[Frame 2] Style: {vals['Style']}, {angle}. Camera: {vals['Camera Motion']}",
            f"[Frame 3] {vals['Platform']} scene builds momentum. {attr}",
            f"[Frame 4] Extra: {extr}", f"[Frame 5] {feat}"
        ]
        res = "\n".join(frames); self.prompt_output.text = res; self.add_history(res)

    def enhance_prompt(self, _):
        prompt = self.prompt_output.text.strip(); plat = self.spinners["Platform"].text.strip()
        if not prompt or not plat: return
        sysmsg = f"Enhance this prompt for a {self.genre.text.strip() or 'cinematic'} style on {plat}."
        res = call_ai_service([{"role": "system", "content": sysmsg}, {"role": "user", "content": prompt}])
        self.prompt_output.text += f"\n[ENHANCED]\n{res}"; self.add_history(res)

    def runway_best(self, _):
        basep = self.prompt_output.text.strip();            if not basep: return
        res = call_ai_service([{"role": "system", "content": "You know Runway Gen‑4 best practices."},
                               {"role": "user", "content": basep}])
        self.prompt_output.text += f"\n[RUNWAY BEST]\n{res}"; self.add_history(res)

    # ---------- bank/historik ----------
    def copy_prompt(self, _):
        from kivy.core.clipboard import Clipboard; Clipboard.copy(self.prompt_output.text)
    def save_prompt_bank(self, _):
        name, content = self.bank_name.text.strip(), self.prompt_output.text.strip()
        if not name or not content: return
        newfile = not os.path.exists(promptbank_path) or os.path.getsize(promptbank_path) == 0
        with open(promptbank_path, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f);  w.writerow(["Name", "Prompt"]) if newfile else None;  w.writerow([name, content])
    def load_prompt_bank(self, _):
        if not os.path.exists(promptbank_path): return
        with open(promptbank_path, "r", encoding="utf-8") as f: rows = list(csv.reader(f))[1:]
        box = BoxLayout(orientation='vertical', spacing=5, padding=5)
        for row in rows:
            if len(row) < 2: continue
            btn = Button(text=row[0], size_hint=(1, None), height=dp(40))
            btn.bind(on_release=lambda _, val=row[1]: self.load_prompt(val)); box.add_widget(btn)
        Popup(title="PromptBank", content=box, size_hint=(0.9, 0.8)).open()
    def load_prompt(self, txt):
        prev = self.prompt_output.text.strip()
        self.prompt_output.text = f"{prev}\n[LOADED]\n{txt}" if prev else txt

    def export_pdf(self, _):
        from fpdf import FPDF; txt = self.prompt_output.text.strip();  outp = os.path.join(BASE_DIR, "PromptGenie_Export.pdf")
        if not txt: return
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        for line in txt.split("\n"): pdf.multi_cell(0, 10, line)
        pdf.output(outp)

    # ---------- story/historik ----------
    def add_story(self, _):
        box = BoxLayout(orientation='vertical', spacing=5, padding=5)
        tx  = MDTextField(hint_text="Short storyline...", multiline=True,
                          size_hint=(1, None), height=dp(120))
        box.add_widget(Label(text="Add story to prompt:", size_hint=(1, None), height=dp(30))); box.add_widget(tx)
        box.add_widget(Button(text="Confirm", size_hint=(1, None), height=dp(40),
                              on_release=lambda _: self.append_story(tx.text)))
        Popup(title="Add Story", content=box, size_hint=(0.9, 0.6)).open()
    def append_story(self, text):
        story = text.strip(); old = self.prompt_output.text.strip()
        if story: self.prompt_output.text = f"{old}\n[STORY]\n{story}" if old else f"[STORY]\n{story}"
    def view_prompt_history(self, _):
        if not self.prompt_history: return
        content = "\n\n".join(f"{h['timestamp']}\n{h['prompt']}" for h in self.prompt_history)
        lb  = Label(text=content, size_hint_y=None); lb.bind(texture_size=lb.setter('size'))
        Popup(title="Prompt History", content=lb, size_hint=(0.9, 0.8)).open()
    def load_prompt_history(self):
        if os.path.exists(prompt_history_path):
            try:  self.prompt_history = json.load(open(prompt_history_path, "r", encoding="utf-8"))
            except: self.prompt_history = []
    def save_prompt_history(self):
        json.dump(self.prompt_history, open(prompt_history_path, "w", encoding="utf-8"), indent=4)
    def add_history(self, txt):
        self.prompt_history.append({"timestamp": datetime.datetime.now().isoformat(), "prompt": txt})
        self.save_prompt_history()

# ---------- 3. Portfolio ----------
class PortfolioScreen(Screen):
    preview_player = None
    image_paths = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', spacing=10, padding=10); self.add_widget(layout)
        layout.add_widget(MDLabel(text="Portfolio++", halign="center", bold=True))
        self.output = MDTextField(hint_text="Results", multiline=True, size_hint=(1, None), height=dp(150)); layout.add_widget(self.output)
        layout.add_widget(Button(text="Select Batch (Images/Videos)", size_hint=(1, None), height=dp(40), on_release=self.pick_files))
        layout.add_widget(Button(text="Analyze + Sort",              size_hint=(1, None), height=dp(40), on_release=self.analyze_sort))
        layout.add_widget(Button(text="Export ZIP + Report",        size_hint=(1, None), height=dp(40), on_release=self.export_zip_and_report))
        layout.add_widget(Button(text="Share Last Export",           size_hint=(1, None), height=dp(40), on_release=self.share_last_export))
        layout.add_widget(Button(text="View Export History",         size_hint=(1, None), height=dp(40), on_release=self.view_export_history))
        layout.add_widget(Button(text="Preview First Video",         size_hint=(1, None), height=dp(40), on_release=self.preview_first_video))

    # ---------- filval ----------
    def pick_files(self, _):
        fc = FileChooserListView(path=os.path.expanduser("~"), filters=["*.jpg", "*.png", "*.mp4"], multiselect=True)
        box = BoxLayout(orientation='vertical', spacing=5, padding=5); box.add_widget(fc)
        def confirm(*_):
            self.image_paths = fc.selection if fc.selection else []
            self.output.text = f"Selected {len(self.image_paths)} files" if self.image_paths else "No files selected"
            pop.dismiss()
        box.add_widget(Button(text="Confirm", size_hint=(1, None), height=dp(40), on_release=confirm))
        pop = Popup(title="Select Media", content=box, size_hint=(0.9, 0.9)); pop.open()

    # ---------- AI‑sortering ----------
    def analyze_sort(self, _):
        if not self.image_paths: self.output.text = "No media loaded"; return
        self.sorted_dir = os.path.join(BASE_DIR, "PortfolioSorted"); os.makedirs(self.sorted_dir, exist_ok=True)
        self.sort_log = ""
        for media_path in self.image_paths:
            filename = os.path.basename(media_path)
            prompt = f"Sort this filename into a logical folder by visual/motion/style pattern: {filename}"
            label = call_ai_service([{"role": "system", "content": "You organize creative assets."},
                                     {"role": "user",   "content": prompt}]).strip().replace(" ", "_")[:30]
            target_dir = os.path.join(self.sorted_dir, label); os.makedirs(target_dir, exist_ok=True)
            shutil.copy(media_path, os.path.join(target_dir, filename))
            self.sort_log += f"Moved {filename} => {label}\n"
        self.output.text = self.sort_log

    # ---------- export ----------
    def export_zip_and_report(self, _):
        if not hasattr(self, 'sorted_dir') or not os.path.exists(self.sorted_dir):
            self.output.text = "Nothing to export"; return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); self.base_export = os.path.join(BASE_DIR, f"Export_{ts}")
        os.makedirs(self.base_export, exist_ok=True)
        self.zip_path    = os.path.join(self.base_export, "sorted_media.zip")
        self.report_path = os.path.join(self.base_export, "summary.txt")
        with zipfile.ZipFile(self.zip_path, 'w') as zipf:
            for folder, _, files in os.walk(self.sorted_dir):
                for f in files:
                    full = os.path.join(folder, f); zipf.write(full, arcname=os.path.relpath(full, self.sorted_dir))
        open(self.report_path, "w").write(self.sort_log or "No sorting log available.")
        self.output.text += f"\nZIP: {self.zip_path}\nReport: {self.report_path}"
        self.record_export_history(self.zip_path, self.report_path)
        if platform == "android": self.android_share_files([self.zip_path, self.report_path])

    # ---------- dela ----------
    def share_last_export(self, _):
        if hasattr(self, 'zip_path') and os.path.exists(self.zip_path):
            self.android_share_files([self.zip_path, self.report_path])
        else: self.output.text = "No export found. Run 'Export ZIP + Report' first."

    def android_share_files(self, filepaths):
        if platform != "android": return
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent, File, Uri = (autoclass('android.content.Intent'),
                             autoclass('java.io.File'),
                             autoclass('android.net.Uri'))
        FileProvider   = autoclass('androidx.core.content.FileProvider')
        ArrayList      = autoclass('java.util.ArrayList')
        context = PythonActivity.mActivity; uris = ArrayList()
        for path in filepaths:
            uri = FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", File(path))
            uris.add(uri)
        intent = Intent(Intent.ACTION_SEND_MULTIPLE); intent.setType("*/*")
        intent.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris)
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        context.startActivity(Intent.createChooser(intent, "Share files via..."))

    # ---------- historik ----------
    def record_export_history(self, zip_path, report_path):
        open(os.path.join(BASE_DIR, "export_history.txt"), "a").write(f"ZIP: {zip_path}\nREPORT: {report_path}\n")
    def view_export_history(self, _):
        hf = os.path.join(BASE_DIR, "export_history.txt")
        self.output.text = f"Export History:\n{open(hf).read()}" if os.path.exists(hf) else "No export history found."

    # ---------- video ----------
    def preview_first_video(self, _):
        if not self.image_paths: self.output.text = "No videos selected."; return
        video = next((f for f in self.image_paths if f.lower().endswith('.mp4')), None)
        if not video: self.output.text = "No .mp4 found in selection."; return
        if MediaPlayer is None: self.output.text = "ffpyplayer not available."; return
        self.output.text = f"Previewing: {os.path.basename(video)}\n(Not embedded – play externally)"

# ---------- 4. Settings ----------
class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = MDBoxLayout(orientation='vertical', spacing=10, padding=10); self.add_widget(layout)
        layout.add_widget(MDLabel(text="Settings", halign="center", bold=True))
        self.api_field = MDTextField(hint_text="Enter OpenAI API Key", password=True,
                                     size_hint=(1, None), height=dp(60)); layout.add_widget(self.api_field)
        layout.add_widget(Button(text="Save API Key", size_hint=(1, None), height=dp(40), on_release=self.save_key))
        self.status_label = Label(text="", size_hint=(1, None), height=dp(30)); layout.add_widget(self.status_label)
        self.api_file = os.path.join(BASE_DIR, "apikey.txt")
        if os.path.exists(self.api_file):
            key = open(self.api_file).read().strip(); self.api_field.text = key
            PromptGenieApp.api_key = key; self.status_label.text = "✅ API Key loaded."
    def save_key(self, _):
        PromptGenieApp.api_key = self.api_field.text.strip()
        if PromptGenieApp.api_key:
            self.status_label.text = "✅ API Key set."
            open(self.api_file, "w").write(PromptGenieApp.api_key)
        else:
            self.status_label.text = "❌ API Key empty."; os.remove(self.api_file) if os.path.exists(self.api_file) else None

# ---------- Root ----------
class RootManager(ScreenManager): pass
def show_api_warning():
    def close(*_): popup.dismiss()
    box = BoxLayout(orientation='vertical', spacing=10, padding=10)
    box.add_widget(Label(text="OpenAI API‑nyckel saknas. Gå till Settings först.", halign="center"))
    box.add_widget(Button(text="OK", size_hint=(1, None), height=dp(40), on_release=close))
    popup = Popup(title="🔐 API‑nyckel krävs", content=box, size_hint=(0.8, 0.4)); Clock.schedule_once(lambda dt: popup.open(), 0.3)

# ---------- App ----------
class PromptGenieApp(MDApp):
    api_key = ""
    def build(self):
        self.theme_cls.theme_style = "Dark"; self.theme_cls.primary_palette = "Purple"
        root_box = BoxLayout(orientation='vertical', spacing=5, padding=5)
        nav = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, None), height=dp(40)); root_box.add_widget(nav)
        self.sm = RootManager()
        for name, scr in [("builder", PromptBuilderScreen()),
                          ("texture", TextureAnalyzerScreen()),
                          ("portfolio", PortfolioScreen()),
                          ("settings", SettingsScreen())]:
            scr.name = name; self.sm.add_widget(scr)
        for lbl, tgt in [("Prompt Builder","builder"), ("Analyzer","texture"),
                         ("Portfolio","portfolio"), ("Settings","settings")]:
            nav.add_widget(Button(text=lbl, on_release=lambda _, t=tgt: self.sm_switch(t)))
        root_box.add_widget(self.sm); return root_box
    def sm_switch(self, name): self.sm.current = name
    def on_start(self): self.populate_defaults()
    def populate_defaults(self):
        if not os.path.exists(promptbank_path) or os.path.getsize(promptbank_path) == 0: self.write_defaults()
        else:
            with open(promptbank_path, "r", encoding="utf-8") as f:
                if len(list(csv.reader(f))) <= 1: self.write_defaults()
    def write_defaults(self):
        with open(promptbank_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["Name", "Prompt"])
            for dp in DEFAULT_PROMPTS: w.writerow([dp["name"], dp["prompt"]])

if __name__ == "__main__":
    PromptGenieApp().run()
