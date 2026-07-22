[app]

title = Food App
package.name = foodapp
package.domain = org.laura

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,csv,ttf

version = 0.1

requirements = python3,kivy,supabase,requests,certifi,urllib3,idna,charset_normalizer

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1