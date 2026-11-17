from pathlib import Path
import json, zipfile, itertools, warnings, xml.etree.ElementTree as E
import numpy as np, trimesh
from scipy.spatial import cKDTree
warnings.filterwarnings('ignore',category=RuntimeWarning)
a=Path('models/grip-cw');b=Path('models/grip-ccw');F=np.diag([-1.,1.,1.,1.])
report={'reflection':'X -> -X; determinant -1; reverses angular handedness about vertical Z','parts':{},'projects':{},'assembly':{}}
def compare(m,n,tol=5e-5):
 assert m.is_watertight and n.is_watertight and m.volume>0 and n.volume>0
 d=max(float(cKDTree(m.vertices).query(n.vertices)[0].max()),float(cKDTree(n.vertices).query(m.vertices)[0].max()))
 assert d<tol,d
 assert np.allclose(m.extents,n.extents,atol=tol), (m.extents,n.extents)
 assert abs(m.volume-n.volume)/m.volume<1e-5
 return {'maximum_vertex_deviation_mm':d,'volume_mm3':float(n.volume),'closed_solid':True}
for p in sorted((a/'STL').glob('*.stl')):
 m=trimesh.load_mesh(p);m.apply_transform(F);n=trimesh.load_mesh(b/'STL'/(p.stem+'_CCW.stl'))
 report['parts'][p.stem]=compare(m,n)
 assert len(n.split())==1
 print('STL mirror verified',p.stem,flush=True)
NS='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
map_names={'01_Base_CCW':'01_base_192_M4_CCW','02_Cover_CCW':'02_cover_195_CCW','04_Spacer_CCW':'03_wheel_spacer_CCW'}
for p in sorted((b/'3MF').glob('*.3mf')):
 with zipfile.ZipFile(p) as z:
  r=E.fromstring(z.read('3D/3dmodel.model'));c=E.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
 names={o.get('id'):next(x.get('value') for x in o.findall('metadata') if x.get('key')=='name') for o in c.findall('object')}
 checks=[]
 for o in r.findall('.//'+NS+'resources/'+NS+'object'):
  mesh=o.find(NS+'mesh');v=np.array([[float(q.get(k)) for k in ['x','y','z']] for q in mesh.find(NS+'vertices')]);f=np.array([[int(q.get(k)) for k in ['v1','v2','v3']] for q in mesh.find(NS+'triangles')]);m=trimesh.Trimesh(v,f,process=True)
  name=map_names.get(names[o.get('id')],names[o.get('id')]);n=trimesh.load_mesh(b/'STL'/(name+'.stl'))
  m.apply_translation(n.bounds.mean(0)-m.bounds.mean(0))
  checks.append({'part':name,**compare(m,n)})
 report['projects'][p.name]=checks
 print('3MF/STL verified',p.name,flush=True)
ga=trimesh.load_scene(a/'verification/assembly_geometry.glb').geometry;gb=trimesh.load_scene(b/'verification/assembly_geometry.glb').geometry
for name in ga:
 m=ga[name].copy();m.apply_transform(F)
 report['assembly'][name]=compare(m,gb[name],tol=1e-4)
report['result']='PASS'
(b/'verification/ccw_conversion_checks.json').write_text(json.dumps(report,indent=2))
print('CCW conversion PASS',flush=True)
