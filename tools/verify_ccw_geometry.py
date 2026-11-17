from pathlib import Path
import trimesh,numpy as np,itertools,json,math,warnings
warnings.filterwarnings('ignore',category=RuntimeWarning)
o=Path('models/grip-ccw');scene=trimesh.load_scene(o/'verification/assembly_geometry.glb');g=scene.geometry
results=[]
for a,b in itertools.combinations(g,2):
 ma,mb=g[a],g[b]
 if np.any(np.minimum(ma.bounds[1],mb.bounds[1])-np.maximum(ma.bounds[0],mb.bounds[0])<1e-5):continue
 q=trimesh.boolean.intersection([ma,mb],engine='manifold');v=abs(float(q.volume));results.append({'pair':[a,b],'intersection_mm3':v})
 print(a,b,round(v,6),flush=True)
 assert v<.01,(a,b,v)
sp=g['03_wheel_spacer']
for i in range(1,4):
 a=g['arm_'+str(i)]
 u=a.centroid.copy();u[2]=0;u/=np.linalg.norm(u)
 for d in [-10,10]:
  b=a.copy();b.apply_translation(d*u);v=abs(float(trimesh.boolean.intersection([b,sp],engine='manifold').volume));print('adjust',i,d,v,flush=True);assert v<.01
(o/'verification/assembly_checks.json').write_text(json.dumps({'pairwise_checks':results,'arm_adjustments_checked_mm':[-10,10],'result':'PASS','note':'Geometric checks at assembly pose; not a physical print or load test.'},indent=2))
