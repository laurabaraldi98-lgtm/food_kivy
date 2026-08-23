[app]

title = Food App
package.name = foodapp
package.domain = org.laura

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,csv,ttf

version = 0.1

requirements = python3,kivy,supabase==2.31.0,supabase_auth==2.31.0,pydantic==2.12.3,requests,certifi,urllib3,idna,charset_normalizer

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.accept_sdk_license = True

p4a.branch = develop
p4a.commit = 0382d27de2f7315ed98e74884bafb30365decdee


[buildozer]

log_level = 2
warn_on_root = 1