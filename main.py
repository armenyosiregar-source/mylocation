import json
import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import platform

PERMISSIONS = [
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.POST_NOTIFICATIONS",
]


class Root(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", padding=24, spacing=14, **kw)
        self.app = app
        cfg = app.load_cfg()
        self.add_widget(Label(text="Pelacak Lokasi", font_size="26sp", size_hint_y=None, height=60))
        self.nama = TextInput(text=cfg.get("nama", ""), hint_text="Nama perangkat",
                              multiline=False, size_hint_y=None, height=90)
        self.url = TextInput(text=cfg.get("url", ""), hint_text="URL Apps Script (/exec)",
                             multiline=False, size_hint_y=None, height=90)
        self.status = Label(text="", size_hint_y=None, height=90)
        self.btn = Button(text="Mulai Lacak", font_size="20sp", size_hint_y=None, height=140)
        self.btn.bind(on_release=self.toggle)
        for w in (self.nama, self.url, self.btn, self.status):
            self.add_widget(w)
        self.add_widget(Label())
        self.running = cfg.get("running", False)
        self.refresh()

    def refresh(self):
        self.btn.text = "Jeda Pelacakan" if self.running else "Mulai Lacak"
        self.status.text = ("Melacak tiap 1 menit" if self.running else
                            "Standby: menunggu perintah AKTIF dari spreadsheet")

    def toggle(self, *_):
        nama, url = self.nama.text.strip(), self.url.text.strip()
        if self.running:
            self.running = False
            self.app.save_cfg({"nama": nama, "url": url, "running": False})
        else:
            if not nama or not url.startswith("https://"):
                self.status.text = "Isi nama dan URL (https) dulu"
                return
            self.running = True
            self.app.save_cfg({"nama": nama, "url": url, "running": True})
            self.app.start_service(minta_baterai=True)
        self.refresh()


class LokasiApp(App):
    def cfg_path(self):
        # Lokasi yang sama dibaca oleh service.py (termasuk saat auto-start setelah boot)
        if platform == "android":
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), "cfg.json")
        return os.path.join(self.user_data_dir, "cfg.json")

    def load_cfg(self):
        try:
            with open(self.cfg_path()) as f:
                return json.load(f)
        except Exception:
            return {}

    def save_cfg(self, d):
        with open(self.cfg_path(), "w") as f:
            json.dump(d, f)

    def build(self):
        if platform == "android":
            from android.permissions import request_permissions
            request_permissions(PERMISSIONS)
        return Root(self)

    def on_start(self):
        # Pastikan layanan standby hidup setiap aplikasi dibuka
        c = self.load_cfg()
        if c.get("nama") and str(c.get("url", "")).startswith("https://"):
            self.start_service()

    def minta_abaikan_baterai(self):
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Settings = autoclass("android.provider.Settings")
            Uri = autoclass("android.net.Uri")
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            pkg = act.getPackageName()
            if not act.getSystemService("power").isIgnoringBatteryOptimizations(pkg):
                i = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                i.setData(Uri.parse("package:" + pkg))
                act.startActivity(i)
        except Exception:
            pass

    def start_service(self, minta_baterai=False):
        if platform != "android":
            return
        from android import AndroidService
        if minta_baterai:
            self.minta_abaikan_baterai()
        self.service = AndroidService("Pelacak Lokasi", "Standby / melacak lokasi")
        self.service.start("manual")  # aman dipanggil berulang: layanan yang sudah hidup tidak digandakan


if __name__ == "__main__":
    LokasiApp().run()
