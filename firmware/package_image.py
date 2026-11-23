"""Merge the bootloader, partition map, OTA selector and application using PlatformIO's build environment."""
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('build',type=Path);a.add_argument('--core',type=Path,default=Path.home()/'.platformio');args=a.parse_args()
b=args.build.resolve();core=args.core.resolve(); image=root/'image'/'R2J-ESP32C6.bin'
# PlatformIO's espressif32 Arduino builder populates these boot_app0 offsets for the default OTA partition scheme.
extras=core/'packages'/'framework-arduinoespressif32'/'tools'/'partitions'/'boot_app0.bin'
items=[('0x0000',b/'bootloader.bin'),('0x8000',b/'partitions.bin'),('0xe000',extras),('0x10000',b/'firmware.bin')]
exe=core/'packages'/'tool-esptoolpy'/'esptool.py'
subprocess.run([sys.executable,str(exe),'--chip','esp32c6','merge-bin','-o',str(image),*[v for off,p in items for v in (off,str(p))]],check=True)
raw=image.read_bytes();get=lambda data:hashlib.sha256(data).hexdigest()
for offset,path in items:
    src=path.read_bytes();n=int(offset,16);assert raw[n:n+len(src)]==src
record={'chip':'ESP32-C6','target':'seeed_xiao_esp32c6','image':image.name,'sha256':get(raw),'bytes':len(raw),'flash_address':0,
        'components':[dict(offset=k,name=p.name,sha256=get(p.read_bytes())) for k,p in items],
        'source_sha256':{p.name:get(p.read_bytes()) for p in sorted((root/'src').glob('*'))},'build_recipe_sha256':{p.name:get(p.read_bytes()) for p in (root/'platformio.ini',root/'repro.py',root/'package_image.py')},'target_flashed':False}
markers=['TPP-R2J','/guard','/receipt','CAL COLD','/status','/config','/actuate','temperature_limit','recalibration_required','guard_required','/config/max_age_ms','/config/guard','WIRES']
app=(b/'firmware.bin').read_bytes()
assert all(mark.encode() in app for mark in markers)
record['application_identity_strings']=markers
record['material_sha256']=get((root/'material.json').read_bytes())
(root/'image'/'build.json').write_text(json.dumps(record,indent=2)+'\n')
