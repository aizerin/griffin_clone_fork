from pathlib import Path
import json,numpy as np,trimesh,warnings
warnings.filterwarnings('ignore',category=RuntimeWarning)
O=Path('models/centering-reticle')
g=trimesh.load_scene('models/arms-275/verification/assembly_275mm.glb').geometry
m=trimesh.load_mesh(O/'verification/reticle_assembly_coordinates.ply')
used=['01_base_192_M4','03_wheel_spacer','arm_1','arm_2','arm_3']
checks={}
for name in used:
 other=g[name]
 if np.any(np.minimum(m.bounds[1],other.bounds[1])-np.maximum(m.bounds[0],other.bounds[0])<1e-6):v=0.
 else:v=abs(float(trimesh.boolean.intersection([m,other],engine='manifold').volume))
 checks[name]=v;assert v<.01,(name,v)
 print(name,v,flush=True)
# Cone seats on the bore rim: it clears upon extraction and cannot fall through.
base=g['01_base_192_M4']
up=m.copy();up.apply_translation([0,0,.5]);up_volume=abs(float(trimesh.boolean.intersection([up,base],engine='manifold').volume));assert up_volume<.01
low=m.copy();low.apply_translation([0,0,-.5]);low_volume=abs(float(trimesh.boolean.intersection([low,base],engine='manifold').volume));assert low_volume>.02,low_volume
# An unobstructed axial ray goes through the entire reticle center.
p,_,_=m.ray.intersects_location([[0,0,30]],[[0,0,-1]])
assert len(p)==0,p
p,_,_=m.ray.intersects_location([[3,0,30]],[[0,0,-1]])
assert len(p)==2 and np.allclose(sorted(p[:,2]),[2.5,3.1],atol=.001),p
scene=trimesh.Scene()
for name in used:scene.add_geometry(g[name],node_name=name,geom_name=name)
scene.add_geometry(m,node_name='centering_reticle',geom_name='centering_reticle')
scene.export(O/'verification/bare_base_with_reticle.glb')
report={'result':'PASS','nominal_part_intersections_mm3':checks,'raised_half_mm_intersection_mm3':up_volume,'insertion_beyond_seat_half_mm_intersection_mm3':low_volume,'clear_sight_through_exact_center':True,'cross_height_above_wheel_mm':[2.5,3.1],'mating_bore_mm':15.6,'cone_diameter_at_bore_lip_mm':15.6,'requires':'bare base without cover/axle; no original retaining shim or O-ring in the bore','limitations':'Checks are geometric; printed fit and centering accuracy are unmeasured.'}
(O/'verification/fit_checks.json').write_text(json.dumps(report,indent=2))
print('PASS',report,flush=True)
