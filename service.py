"""Layanan latar belakang.
Selalu hidup (standby) dan menanyakan perintah ke spreadsheet tiap 30 detik.
GPS dinyalakan & lokasi dikirim tiap 60 detik jika: pelacakan lokal aktif ATAU sheet 'Perintah' = AKTIF.
"""
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request

import certifi
from android.storage import app_storage_path
from jnius import PythonJavaClass, autoclass, java_method

CFG = os.path.join(app_storage_path(), "cfg.json")
POLL_STANDBY = 30   # detik antar cek perintah saat standby
POLL_AKTIF = 60     # detik antar pengiriman saat aktif

PythonService = autoclass("org.kivy.android.PythonService")
Looper = autoclass("android.os.Looper")
SystemClock = autoclass("android.os.SystemClock")
ctx = PythonService.mService


def baca_cfg():
    try:
        with open(CFG) as f:
            return json.load(f)
    except Exception:
        return {}


cfg = baca_cfg()
NAMA, URL = cfg.get("nama", ""), cfg.get("url", "")
DARI_BOOT = os.environ.get("PYTHON_SERVICE_ARGUMENT", "") == "boot"

if not NAMA or not URL:
    ctx.stopSelf()
    sys.exit(0)

if DARI_BOOT:
    # Mulai 30 detik setelah HP menyala
    sisa = 30 - SystemClock.elapsedRealtime() / 1000.0
    if sisa > 0:
        time.sleep(sisa)

latest = None   # (waktu_detik, lat, lng, akurasi)
antrean = []
terakhir = 0
gps_on = False
remote_aktif = False


class Listener(PythonJavaClass):
    __javainterfaces__ = ["android/location/LocationListener"]
    __javacontext__ = "app"

    @java_method("(Landroid/location/Location;)V")
    def onLocationChanged(self, loc):
        global latest
        latest = (int(loc.getTime() / 1000), loc.getLatitude(), loc.getLongitude(), int(loc.getAccuracy()))

    @java_method("(Ljava/lang/String;)V")
    def onProviderEnabled(self, p):
        pass

    @java_method("(Ljava/lang/String;)V")
    def onProviderDisabled(self, p):
        pass

    @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
    def onStatusChanged(self, p, s, b):
        pass


listener = Listener()
lm = ctx.getSystemService("location")


def gps_nyalakan():
    global gps_on
    if gps_on:
        return
    lm.requestLocationUpdates("gps", 15000, 0.0, listener, Looper.getMainLooper())
    try:
        lm.requestLocationUpdates("network", 15000, 0.0, listener, Looper.getMainLooper())
    except Exception:
        pass
    gps_on = True


def gps_matikan():
    global gps_on, latest
    if not gps_on:
        return
    try:
        lm.removeUpdates(listener)
    except Exception:
        pass
    gps_on = False
    latest = None


def http_get(params):
    c = ssl.create_default_context(cafile=certifi.where())
    q = urllib.parse.urlencode(params)
    return urllib.request.urlopen(URL + "?" + q, timeout=20, context=c).read().decode("utf-8", "ignore")


def kirim(row):
    http_get({"id": NAMA, "timestamp": row[0], "lat": row[1], "lon": row[2], "accuracy": row[3]})


def main():
    global NAMA, URL, terakhir, remote_aktif
    pm = ctx.getSystemService("power")
    wl = pm.newWakeLock(1, "lokasi:tracker")
    wl.acquire()

    while True:
        c = baca_cfg()
        NAMA, URL = c.get("nama", NAMA), c.get("url", URL)
        lokal = bool(c.get("running"))

        # Tanya perintah ke spreadsheet (sekaligus lapor "online")
        try:
            remote_aktif = http_get({"aksi": "perintah", "id": NAMA}).strip().upper() == "AKTIF"
        except Exception:
            pass  # offline: pakai perintah terakhir yang diketahui

        aktif = lokal or remote_aktif
        if aktif:
            gps_nyalakan()
            if latest and latest[0] != terakhir:
                antrean.append(latest)
                terakhir = latest[0]
        else:
            gps_matikan()

        while antrean:
            try:
                kirim(antrean[0])
                antrean.pop(0)
            except Exception:
                break
        del antrean[:-500]

        time.sleep(POLL_AKTIF if aktif else POLL_STANDBY)


main()
