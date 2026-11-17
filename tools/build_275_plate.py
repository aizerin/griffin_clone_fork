"""Build the complete 275 mm hardware plate from the two checked Prusa projects.
Standard library only. Run from any directory. Original slider support overrides stay intact.
"""
from pathlib import Path
import copy, zipfile, re, xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with zipfile.ZipFile(path) as z: return {n:z.read(n) for n in z.namelist()}
k='Metadata/Slic3r_PE_model.config'; model='3D/3dmodel.model'
old=read(ROOT/'models/grip-cw/3MF/03_Arms_sliders_shim.3mf')
short=read(ROOT/'models/arms-275/3MF/01_One_arm_275mm_v2.3mf')
cfg=E.fromstring(old[k]);template=E.fromstring(short[k]).find('object/volume')
# Replace only the three meshes in their original local frames. Both arm types
# are 16.5 mm tall, centered in XY, and use the same print orientation.
def mesh_block(match):
    oid=match.group(1)
    o=cfg.find(f"object[@id='{oid}']")
    if not any(e.get('value')=='06_adjustable_arm_14in' for e in o.findall('metadata')):return match.group(0)
    for e in o.iter('metadata'):
        if e.get('key')=='name':e.set('value','06_adjustable_arm_275mm_v2')
    vol=o.find('volume');vol.set('lastid',template.get('lastid'))
    return re.sub(r'<mesh>.*?</mesh>',lambda _:newmesh,match.group(0),count=1,flags=re.S)
newmesh=re.search(r'<mesh>.*?</mesh>',short[model].decode(),re.S)[0]
s=re.sub(r'<object id="(\d+)"[^>]*>.*?</object>',mesh_block,old[model].decode(),flags=re.S)
s=s.replace('03_Arms_sliders_shim','03_Hardware_275mm').replace('Vevor 14 inch','275 mm wheelhead')
for e in cfg.iter('metadata'):
    if e.get('key')=='source_file':e.set('value','03_Hardware_275mm.3mf')
assert sum(e.get('value')=='06_adjustable_arm_275mm_v2' for e in cfg.findall('object/metadata'))==3
old[k]=E.tostring(cfg,encoding='utf-8',xml_declaration=True);old[model]=s.encode()
out=ROOT/'print/03_Hardware_275mm.3mf';out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for n,d in old.items():z.writestr(n,d)
