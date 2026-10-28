[app]
title = Pelacak Lokasi
package.name = lokasitracker
package.domain = org.lokasi
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0
requirements = python3,kivy,pyjnius,android,openssl,certifi
orientation = portrait
fullscreen = 0
services = Lokasi:service.py:foreground:sticky
android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_BACKGROUND_LOCATION,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS,RECEIVE_BOOT_COMPLETED,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.add_src = src
android.extra_manifest_application_arguments = receiver.xml
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
