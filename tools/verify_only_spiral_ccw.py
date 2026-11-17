from pathlib import Path
import numpy as np,trimesh,math,json,itertools,warnings
warnings.filterwarnings('ignore',category=RuntimeWarning)
A=trimesh.load_scene('models/grip-cw/verification/assembly_geometry.glb').geometry
n=np.array([.927033,-.374981,0]);n/=np.linalg.norm(n);r=np.array([-n[1],n[0],0]);theta=math.atan2(r[1],r[0]);T=np.eye(4);T[:3,:3]-=2*np.outer(n,n)
report={'method':'Original cover, sliders, shim and support parts; replace spiral base only. Align reflected base relative to existing cover slots.','symmetry_checks':{},'mixed_assembly_checks':[]}
for name in ['02_cover_195','05_low_slider']:
 a=A[name];b=a.copy();b.apply_transform(T)
 pts=trimesh.sample.sample_surface(a,6000,seed=7)[0]
 dist=trimesh.proximity.closest_point(b,pts)[1]
 report['symmetry_checks'][name]={'sampled_surface_points':len(pts),'max_deviation_mm':float(dist.max()),'p99_deviation_mm':float(np.quantile(dist,.99))}
 print(name,report['symmetry_checks'][name],flush=True)
B={k:v.copy() for k,v in A.items()};B['01_base_192_M4'].apply_transform(T)
# Reuse original arms and spacer with rotations only (proper rigid transforms).
mount=math.radians(14.3363662176278+107)
for i in range(3):
 angle=mount+i*math.tau/3
 rot=trimesh.transformations.rotation_matrix(2*(theta-angle),[0,0,1])
 B['arm_'+str(i+1)].apply_transform(rot)
B['03_wheel_spacer'].apply_transform(trimesh.transformations.rotation_matrix(2*(theta-mount),[0,0,1]))
for a,b in itertools.combinations(B,2):
 ma,mb=B[a],B[b]
 if np.any(np.minimum(ma.bounds[1],mb.bounds[1])-np.maximum(ma.bounds[0],mb.bounds[0])<1e-5):continue
 v=abs(float(trimesh.boolean.intersection([ma,mb],engine='manifold').volume))
 report['mixed_assembly_checks'].append({'parts':[a,b],'intersection_mm3':v})
 print(a,b,round(v,6),flush=True)
 assert v<.01,(a,b,v)
report['result']='PASS';report['limitation']='Geometric check in assembled pose; physical fit and full travel untested.'
Path('models/grip-ccw/verification/only_spiral_replacement.json').write_text(json.dumps(report,indent=2))
scene=trimesh.Scene()
for name,m in B.items():scene.add_geometry(m,node_name=name,geom_name=name)
scene.export('models/grip-ccw/verification/only_spiral_assembly.glb')
print('Only spiral replacement: PASS',flush=True)
